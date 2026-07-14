"""Chat workflow that closes the loop between provider, tools, and sessions."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from talosent.agent.model import AgentContext, AgentMessage, WorkflowResult
from talosent.agent.workflows.base import WorkflowSpec
from talosent.memory import MemoryEntry, MemoryStore
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
    compression_max_messages: int = 24
    compression_keep_messages: int = 12
    compression_summary_items: int = 8
    compression_summary_chars: int = 2000

    def run(self, context: AgentContext) -> WorkflowResult:
        result = WorkflowResult()
        final_message = ""
        session_loaded = self._restore_context(context)

        if self.system_prompt and not any(message.role == "system" for message in context.messages):
            system_message = AgentMessage(role="system", content=self.system_prompt, name=self.spec.name)
            context.messages.insert(0, system_message)
            result.messages.append(system_message)

        turns = 0
        while turns < self.max_turns:
            compression_info = self._compress_context(context)
            if compression_info is not None:
                result.messages.append(compression_info["message"])
                result.state.setdefault("compressions", []).append(compression_info["summary"])
                result.state["compression"] = compression_info["summary"]

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

        compression_info = self._compress_context(context)
        if compression_info is not None:
            result.messages.append(compression_info["message"])
            result.state.setdefault("compressions", []).append(compression_info["summary"])
            result.state["compression"] = compression_info["summary"]

        session_info = {
            "conversation_id": context.conversation_id,
            "loaded": bool(context.metadata.get("_memory_hydrated")) or session_loaded,
            "saved": False,
            "memory_key": self.session_key(context.conversation_id) if self.memory_store else None,
            "messages": len(context.messages),
            "artifacts": len(context.artifacts),
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
                "compressed": bool(context.metadata.get("compression")),
                "saved_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        self.memory_store.put(entry)

    def session_key(self, conversation_id: str) -> str:
        return f"{self.memory_key_prefix}/{self.spec.name}/{_require_text(conversation_id, 'conversation_id')}"

    def _restore_context(self, context: AgentContext) -> bool:
        if self.memory_store is None:
            return False
        if context.metadata.get("_memory_hydrated"):
            return False
        if not self._should_restore_context(context):
            return False

        stored_context = self._load_stored_context(context.conversation_id)
        if stored_context is None:
            return False

        merged_context = self._merge_contexts(stored_context, context)
        self._copy_context_into(context, merged_context)
        context.metadata["_memory_hydrated"] = True
        context.metadata["_memory_loaded_at"] = datetime.now(timezone.utc).isoformat()
        context.metadata["_memory_key"] = self.session_key(context.conversation_id)
        return True

    def _should_restore_context(self, context: AgentContext) -> bool:
        if self.memory_store is None:
            return False
        if self._load_stored_context(context.conversation_id) is None:
            return False
        if not context.messages:
            return True
        return not any(message.role in {"assistant", "tool"} for message in context.messages)

    def _load_stored_context(self, conversation_id: str) -> AgentContext | None:
        if self.memory_store is None:
            return None

        entry = self.memory_store.get(self.session_key(conversation_id))
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

    def _merge_contexts(self, stored: AgentContext, current: AgentContext) -> AgentContext:
        merged = stored.copy()
        if current.messages:
            merged.messages.extend(current.messages)
        if current.artifacts:
            merged.artifacts.extend(current.artifacts)
        merged.state.update(current.state)
        merged.metadata.update(current.metadata)
        merged.conversation_id = current.conversation_id or stored.conversation_id
        return merged

    def _copy_context_into(self, target: AgentContext, source: AgentContext) -> None:
        target.conversation_id = source.conversation_id
        target.messages[:] = list(source.messages)
        target.artifacts[:] = list(source.artifacts)
        target.state.clear()
        target.state.update(source.state)
        target.metadata.clear()
        target.metadata.update(source.metadata)

    def _compress_context(self, context: AgentContext) -> dict[str, Any] | None:
        if len(context.messages) <= self.compression_max_messages:
            return None

        last_user_index = self._last_message_index(context.messages, "user")
        if last_user_index >= 0:
            prefix_messages = context.messages[:last_user_index]
            tail_messages = context.messages[last_user_index:]
        else:
            keep_from = max(0, len(context.messages) - self.compression_keep_messages)
            prefix_messages = context.messages[:keep_from]
            tail_messages = context.messages[keep_from:]

        summary_messages = [message for message in prefix_messages if self._is_summary_message(message)]
        raw_messages = [
            message
            for message in prefix_messages
            if message.role != "system" and not self._is_summary_message(message)
        ]

        if not raw_messages and len(summary_messages) <= 1:
            return None

        preserved_system_messages = [
            message
            for message in prefix_messages
            if message.role == "system" and not self._is_summary_message(message)
        ]
        existing_summary = "\n\n".join(
            self._message_preview(message, limit=self.compression_summary_chars)
            for message in summary_messages
            if message.content.strip()
        )
        summary_text = self._build_summary_text(existing_summary, raw_messages)
        summary_message = AgentMessage(
            role="system",
            content=summary_text,
            name=self.spec.name,
            metadata={
                "compressed_context": True,
                "compression_source_count": len(raw_messages),
                "compression_summary_count": len(summary_messages),
                "compression_tail_count": len(tail_messages),
            },
        )

        context.messages[:] = [*preserved_system_messages, summary_message, *tail_messages]
        summary_state = {
            "applied": True,
            "removed_messages": len(prefix_messages) - len(preserved_system_messages),
            "removed_non_system_messages": len(raw_messages),
            "tail_messages": len(tail_messages),
            "summary_messages": len(summary_messages),
            "conversation_id": context.conversation_id,
            "memory_key": self.session_key(context.conversation_id),
        }
        context.metadata["compression"] = summary_state
        return {"message": summary_message, "summary": summary_state}

    def _build_summary_text(self, existing_summary: str, dropped_messages: list[AgentMessage]) -> str:
        lines = [
            "Conversation history compressed to preserve context.",
        ]
        if existing_summary.strip():
            lines.append("Previous summary:")
            lines.extend(f"  {line}" for line in existing_summary.strip().splitlines())
        if dropped_messages:
            lines.append("Dropped messages:")
            for message in dropped_messages[: self.compression_summary_items]:
                label = message.role
                if message.name:
                    label += f"[{message.name}]"
                lines.append(f"- {label}: {self._message_preview(message)}")
            remaining = len(dropped_messages) - self.compression_summary_items
            if remaining > 0:
                lines.append(f"- ... {remaining} more messages omitted")
        return self._trim_text("\n".join(lines), self.compression_summary_chars)

    def _message_preview(self, message: AgentMessage, *, limit: int = 120) -> str:
        if message.tool_calls:
            tool_names = ", ".join(
                tool_call.name or "unknown" for tool_call in message.tool_calls[: self.compression_summary_items]
            )
            if len(message.tool_calls) > self.compression_summary_items:
                tool_names += ", ..."
            preview = f"tool calls: {tool_names}"
        else:
            preview = " ".join(message.content.split())
        if not preview:
            preview = "(empty)"
        return self._trim_text(preview, limit)

    def _trim_text(self, text: str, limit: int) -> str:
        if limit <= 0 or len(text) <= limit:
            return text
        return f"{text[: max(0, limit - 3)].rstrip()}..."

    def _is_summary_message(self, message: AgentMessage) -> bool:
        return bool(message.metadata.get("compressed_context") or message.metadata.get("compression_summary"))

    def _last_message_index(self, messages: list[AgentMessage], role: str) -> int:
        for index in range(len(messages) - 1, -1, -1):
            if messages[index].role == role:
                return index
        return -1

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
