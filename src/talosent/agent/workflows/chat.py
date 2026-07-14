"""Chat workflow that keeps recent turns, summary, and key memory in sync."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from talosent.agent.model import AgentContext, AgentMessage, WorkflowResult
from talosent.agent.workflows.base import WorkflowSpec
from talosent.memory import (
    ConversationMemory,
    MemoryEntry,
    MemoryFact,
    MemoryStore,
    build_history_summary,
    extract_memory_facts,
    is_memory_message,
    is_summary_message,
    is_system_prompt_message,
    split_turns,
)
from talosent.providers.runtime import ChatProvider
from talosent.tools.registry import ToolRegistry

DEFAULT_SYSTEM_PROMPT = (
    "You are Talosent, a concise and helpful agent. "
    "Use tools when they help answer the user, especially current_time for time questions."
)


@dataclass(slots=True)
class ChatWorkflow:
    spec: WorkflowSpec
    provider: ChatProvider
    tools: ToolRegistry
    system_prompt: str = DEFAULT_SYSTEM_PROMPT
    max_turns: int = 4
    memory_store: MemoryStore | None = None
    memory_key_prefix: str = "sessions"
    recent_turns: int = 4
    memory_fact_limit: int = 8
    summary_turn_preview_limit: int = 8
    summary_char_limit: int = 2000
    compression_max_messages: int = 24
    compression_keep_messages: int = 12
    compression_summary_items: int = 8
    compression_summary_chars: int = 2000

    def run(self, context: AgentContext) -> WorkflowResult:
        result = WorkflowResult()
        final_message = ""
        restored = self._restore_context(context)
        memory_state = self._load_conversation_memory(context)
        prompt_state = self._refresh_context(context, memory_state)

        turns = 0
        while turns < self.max_turns:
            turns += 1
            try:
                response = self.provider.complete(context.messages, tools=self.tools.specs())
            except Exception as exc:
                error_message = context.add_message("assistant", f"Provider error: {exc}")
                result.messages.append(error_message)
                result.state["error"] = str(exc)
                break

            if response.content:
                assistant_message = context.add_message(
                    "assistant",
                    response.content,
                    name=getattr(self.provider, "name", None),
                )
                result.messages.append(assistant_message)
                final_message = response.content

            if not response.tool_calls:
                break

            tool_request_message = context.add_message(
                "assistant",
                "",
                name=getattr(self.provider, "name", None),
                tool_calls=response.tool_calls,
            )
            result.messages.append(tool_request_message)

            for tool_call in response.tool_calls:
                try:
                    value = self.tools.invoke(tool_call.name, tool_call.arguments)
                    tool_message = context.add_tool_message(
                        tool_call.id,
                        tool_call.name,
                        _stringify_tool_result(value),
                    )
                except Exception as exc:
                    tool_message = context.add_tool_message(
                        tool_call.id,
                        tool_call.name,
                        f"ERROR: {exc}",
                        error=True,
                    )
                result.messages.append(tool_message)

        final_state = self._refresh_context(context, prompt_state)
        session_info = {
            "conversation_id": context.conversation_id,
            "loaded": restored or bool(context.metadata.get("_memory_hydrated")) or self._has_persistent_memory(context.conversation_id),
            "saved": False,
            "memory_key": self.session_key(context.conversation_id) if self.memory_store else None,
            "messages": len(context.messages),
            "artifacts": len(context.artifacts),
            "source_turns": final_state.source_turns,
            "retained_turns": final_state.retained_turns,
            "dropped_turns": prompt_state.dropped_turns,
            "memory_facts": len(final_state.facts),
            "summary_chars": len(final_state.summary),
            "prompt_source_turns": prompt_state.source_turns,
            "prompt_retained_turns": prompt_state.retained_turns,
            "prompt_dropped_turns": prompt_state.dropped_turns,
        }

        try:
            self.save_session(context)
            session_info["saved"] = self.memory_store is not None
        except Exception as exc:  # pragma: no cover - defensive fallback
            session_info["error"] = str(exc)
            result.state["session_error"] = str(exc)

        result.state["turns"] = turns
        result.state["final_message"] = final_message
        result.state["provider"] = getattr(self.provider, "name", self.provider.__class__.__name__)
        result.state["session"] = session_info
        return result

    def load_session(self, conversation_id: str | None = None) -> AgentContext:
        resolved_id = self._resolve_conversation_id(conversation_id)
        stored_context = self._load_stored_context(resolved_id)
        if stored_context is None:
            return AgentContext(conversation_id=resolved_id)

        stored_context.conversation_id = resolved_id
        stored_context.metadata["_memory_hydrated"] = True
        stored_context.metadata["_memory_loaded_at"] = datetime.now(timezone.utc).isoformat()
        stored_context.metadata["_memory_key"] = self.session_key(resolved_id)
        return stored_context

    def save_session(self, context: AgentContext) -> None:
        if self.memory_store is None:
            return

        payload = context.to_dict()
        metadata = payload.get("metadata")
        if isinstance(metadata, dict):
            payload["metadata"] = {
                str(key): value for key, value in metadata.items() if not str(key).startswith("_memory_")
            }

        entry = MemoryEntry(
            key=self.session_key(context.conversation_id),
            value=payload,
            tags=("session", self.spec.name, getattr(self.provider, "name", self.provider.__class__.__name__)),
            metadata={
                "workflow": self.spec.name,
                "provider": getattr(self.provider, "name", self.provider.__class__.__name__),
                "message_count": len(context.messages),
                "artifact_count": len(context.artifacts),
                "saved_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        self.memory_store.put(entry)

    def clear_session(self, conversation_id: str) -> None:
        if self.memory_store is None:
            return
        self.memory_store.delete(self.session_key(conversation_id))

    def session_key(self, conversation_id: str) -> str:
        return f"{self.memory_key_prefix}/{self.spec.name}/{_require_text(conversation_id, 'conversation_id')}"

    def _refresh_context(self, context: AgentContext, existing_state: ConversationMemory) -> ConversationMemory:
        system_messages = self._collect_system_messages(context)
        chat_messages = self._collect_chat_messages(context)
        turns = split_turns(chat_messages)

        keep_turns = self._retained_turns()
        retained_turns = turns[-keep_turns:] if turns else ()
        dropped_turns = turns[:-keep_turns] if len(turns) > keep_turns else ()

        facts = extract_memory_facts(chat_messages, existing=existing_state.facts, limit=self.memory_fact_limit)
        summary = build_history_summary(
            existing_state.summary,
            dropped_turns,
            turn_preview_limit=self.summary_turn_preview_limit,
            summary_char_limit=self.summary_char_limit,
        )

        memory_state = ConversationMemory(
            summary=summary,
            facts=facts,
            retained_turns=len(retained_turns),
            dropped_turns=len(dropped_turns),
            source_turns=len(turns),
            source_messages=len(chat_messages),
            updated_at=datetime.now(timezone.utc),
            metadata=dict(existing_state.metadata),
        )

        prompt_messages: list[AgentMessage] = [
            *system_messages,
            *memory_state.to_system_messages(self.spec.name, fact_limit=self.memory_fact_limit),
            *self._flatten_turns(retained_turns),
        ]
        if self.system_prompt and not self._has_system_prompt(prompt_messages):
            prompt_messages.insert(0, self._system_prompt_message())

        context.messages[:] = prompt_messages
        context.metadata["conversation_memory"] = memory_state.to_dict()
        context.metadata["_memory_hydrated"] = True
        context.metadata["_memory_loaded_at"] = datetime.now(timezone.utc).isoformat()
        context.metadata["_memory_key"] = self.session_key(context.conversation_id)
        return memory_state

    def _load_conversation_memory(self, context: AgentContext) -> ConversationMemory:
        payload = context.metadata.get("conversation_memory")
        if isinstance(payload, dict):
            try:
                return ConversationMemory.from_dict(payload)
            except Exception:
                pass

        stored_context = self._load_stored_context(context.conversation_id)
        if stored_context is not None:
            stored_payload = stored_context.metadata.get("conversation_memory")
            if isinstance(stored_payload, dict):
                try:
                    return ConversationMemory.from_dict(stored_payload)
                except Exception:
                    pass

        return self._derive_memory_from_messages(context.messages)

    def _restore_context(self, context: AgentContext) -> bool:
        if self.memory_store is None:
            return False
        if context.metadata.get("_memory_hydrated"):
            return False
        if context.messages and any(message.role in {"assistant", "tool"} for message in context.messages):
            return False

        stored_context = self._load_stored_context(context.conversation_id)
        if stored_context is None:
            return False

        merged_context = stored_context.copy()
        if context.messages:
            merged_context.messages.extend(context.messages)
        if context.artifacts:
            merged_context.artifacts.extend(context.artifacts)
        merged_context.state.update(context.state)
        merged_context.metadata.update(context.metadata)
        self._copy_context_into(context, merged_context)
        context.metadata["_memory_hydrated"] = True
        context.metadata["_memory_loaded_at"] = datetime.now(timezone.utc).isoformat()
        context.metadata["_memory_key"] = self.session_key(context.conversation_id)
        return True

    def _derive_memory_from_messages(self, messages: list[AgentMessage]) -> ConversationMemory:
        summary_lines = [
            message.content.strip()
            for message in messages
            if is_summary_message(message) and message.content.strip()
        ]
        facts = self._facts_from_memory_messages(messages)
        return ConversationMemory(
            summary="\n\n".join(summary_lines),
            facts=facts,
            retained_turns=0,
            dropped_turns=0,
            source_turns=len(split_turns(self._collect_chat_messages_from(messages))),
            source_messages=len(self._collect_chat_messages_from(messages)),
        )

    def _facts_from_memory_messages(self, messages: list[AgentMessage]) -> tuple[MemoryFact, ...]:
        facts: list[MemoryFact] = []
        for message in messages:
            if not is_memory_message(message):
                continue
            for line in message.content.splitlines():
                line = line.strip("- ").strip()
                if ":" not in line or line.startswith("Key memory"):
                    continue
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()
                if not key or not value:
                    continue
                facts.append(
                    MemoryFact(
                        key=key,
                        value=value,
                        source="summary",
                        confidence=0.75,
                        evidence=message.content,
                    )
                )
        return tuple(facts)

    def _copy_context_into(self, target: AgentContext, source: AgentContext) -> None:
        target.conversation_id = source.conversation_id
        target.messages[:] = list(source.messages)
        target.artifacts[:] = list(source.artifacts)
        target.state.clear()
        target.state.update(source.state)
        target.metadata.clear()
        target.metadata.update(source.metadata)

    def _collect_system_messages(self, context: AgentContext) -> list[AgentMessage]:
        return [
            message
            for message in context.messages
            if message.role == "system"
            and not is_memory_message(message)
            and not is_summary_message(message)
        ]

    def _collect_chat_messages(self, context: AgentContext) -> list[AgentMessage]:
        return self._collect_chat_messages_from(context.messages)

    def _collect_chat_messages_from(self, messages: list[AgentMessage] | tuple[AgentMessage, ...]) -> list[AgentMessage]:
        return [message for message in messages if message.role != "system"]

    def _flatten_turns(self, turns: tuple[tuple[AgentMessage, ...], ...]) -> list[AgentMessage]:
        messages: list[AgentMessage] = []
        for turn in turns:
            messages.extend(turn)
        return messages

    def _system_prompt_message(self) -> AgentMessage:
        return AgentMessage(
            role="system",
            content=self.system_prompt,
            name=self.spec.name,
            metadata={"talosent_system_prompt": True},
        )

    def _has_system_prompt(self, messages: list[AgentMessage] | tuple[AgentMessage, ...]) -> bool:
        prompt = self.system_prompt.strip()
        for message in messages:
            if is_system_prompt_message(message):
                return True
            if message.role != "system":
                continue
            if prompt and message.content.strip() == prompt and (message.name in {None, self.spec.name}):
                return True
        return False

    def _retained_turns(self) -> int:
        return max(1, self.recent_turns)

    def _load_stored_context(self, conversation_id: str | None) -> AgentContext | None:
        if self.memory_store is None:
            return None

        resolved_id = self._resolve_conversation_id(conversation_id)
        entry = self.memory_store.get(self.session_key(resolved_id))
        if entry is None:
            return None
        return self._context_from_entry(entry)

    def _context_from_entry(self, entry: MemoryEntry) -> AgentContext:
        value = entry.value
        if isinstance(value, AgentContext):
            context = value.copy()
        elif isinstance(value, dict):
            context = AgentContext.from_dict(value)
        else:
            try:
                payload = json.loads(str(value))
            except json.JSONDecodeError as exc:
                raise TypeError("Stored session payload must be a mapping or JSON object") from exc
            if not isinstance(payload, dict):
                raise TypeError("Stored session payload must be a JSON object")
            context = AgentContext.from_dict(payload)

        context.conversation_id = entry.key.rsplit("/", 1)[-1]
        return context

    def _has_persistent_memory(self, conversation_id: str) -> bool:
        if self.memory_store is None:
            return False
        return self.memory_store.get(self.session_key(conversation_id)) is not None

    def _resolve_conversation_id(self, conversation_id: str | None) -> str:
        text = str(conversation_id or "").strip()
        return text or uuid4().hex


def _stringify_tool_result(value: Any) -> str:
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except TypeError:
        return str(value)


def _require_text(value: Any, label: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{label} is required")
    return text
