"""Conversation memory snapshots and lightweight extraction heuristics."""

from __future__ import annotations

import re
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from collections.abc import Mapping, Sequence
from typing import Any

from talosent.agent.model import AgentMessage


_FACT_PATTERNS: tuple[tuple[str, re.Pattern[str], float], ...] = (
    (
        "user.name",
        re.compile(
            r"(?:my name is|i am called|call me|i am|i'm|i’m|我叫|我的名字是|叫我)\s+(?P<value>[^。！？,;:\n]+)",
            re.IGNORECASE,
        ),
        0.98,
    ),
    (
        "user.location",
        re.compile(
            r"(?:i live in|i'm in|i am in|based in|my home is in|我住在|我在|我来自)\s+(?P<value>[^。！？,;:\n]+)",
            re.IGNORECASE,
        ),
        0.9,
    ),
    (
        "user.timezone",
        re.compile(
            r"(?:my timezone is|timezone is|in the timezone of|时区是|我的时区是)\s+(?P<value>[^。！？,;:\n]+)",
            re.IGNORECASE,
        ),
        0.96,
    ),
    (
        "user.preference.response_style",
        re.compile(
            r"(?:i prefer|please keep|keep it|please respond in|请保持|请用|我希望|我偏好)\s+(?P<value>[^。！？,;:\n]+)",
            re.IGNORECASE,
        ),
        0.88,
    ),
    (
        "user.preference.topics",
        re.compile(
            r"(?:i like|i love|i enjoy|我喜欢|我爱)\s+(?P<value>[^。！？,;:\n]+)",
            re.IGNORECASE,
        ),
        0.82,
    ),
    (
        "project.goal",
        re.compile(
            r"(?:we are building|we're building|the project is|our project is|we are working on|我们正在做|我们的项目是|我正在做)\s+(?P<value>[^。！？,;:\n]+)",
            re.IGNORECASE,
        ),
        0.74,
    ),
    (
        "user.reminder",
        re.compile(
            r"(?:remember(?: that)?|please remember|记住|帮我记住)\s*(?P<value>[^。！？,;:\n]+)",
            re.IGNORECASE,
        ),
        0.7,
    ),
)


@dataclass(slots=True)
class MemoryFact:
    key: str
    value: str
    source: str = "heuristic"
    confidence: float = 0.5
    evidence: str = ""
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "value": self.value,
            "source": self.source,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "updated_at": self.updated_at.isoformat(),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "MemoryFact":
        key = _require_text(data.get("key"), "MemoryFact.key")
        metadata = data.get("metadata") or {}
        if not isinstance(metadata, Mapping):
            raise TypeError("MemoryFact.metadata must be a mapping")
        confidence_raw = data.get("confidence")
        try:
            confidence = float(confidence_raw) if confidence_raw is not None else 0.5
        except (TypeError, ValueError):
            confidence = 0.5
        return cls(
            key=key,
            value=str(data.get("value") or ""),
            source=str(data.get("source") or "heuristic"),
            confidence=max(0.0, min(1.0, confidence)),
            evidence=str(data.get("evidence") or ""),
            updated_at=_parse_datetime(data.get("updated_at")),
            metadata=dict(metadata),
        )

    def describe(self) -> str:
        return f"{self.key}: {self.value}".strip()


@dataclass(slots=True)
class ConversationMemory:
    summary: str = ""
    facts: tuple[MemoryFact, ...] = ()
    retained_turns: int = 0
    dropped_turns: int = 0
    source_turns: int = 0
    source_messages: int = 0
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary": self.summary,
            "facts": [fact.to_dict() for fact in self.facts],
            "retained_turns": self.retained_turns,
            "dropped_turns": self.dropped_turns,
            "source_turns": self.source_turns,
            "source_messages": self.source_messages,
            "updated_at": self.updated_at.isoformat(),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ConversationMemory":
        facts_raw = data.get("facts") or ()
        if isinstance(facts_raw, Mapping) or isinstance(facts_raw, (str, bytes)):
            raise TypeError("ConversationMemory.facts must be an iterable of mappings")
        metadata = data.get("metadata") or {}
        if not isinstance(metadata, Mapping):
            raise TypeError("ConversationMemory.metadata must be a mapping")
        return cls(
            summary=str(data.get("summary") or ""),
            facts=tuple(MemoryFact.from_dict(item) for item in facts_raw),
            retained_turns=_safe_int(data.get("retained_turns")),
            dropped_turns=_safe_int(data.get("dropped_turns")),
            source_turns=_safe_int(data.get("source_turns")),
            source_messages=_safe_int(data.get("source_messages")),
            updated_at=_parse_datetime(data.get("updated_at")),
            metadata=dict(metadata),
        )

    def copy(self) -> "ConversationMemory":
        return ConversationMemory.from_dict(self.to_dict())

    def is_empty(self) -> bool:
        return not self.summary.strip() and not self.facts

    def format_summary(self) -> str:
        text = self.summary.strip()
        if not text:
            return ""
        return text if text.startswith("Conversation summary:") else f"Conversation summary:\n{text}"

    def format_facts(self, *, limit: int = 8) -> str:
        facts = self.facts[: max(0, limit)]
        if not facts:
            return ""
        lines = ["Key memory:"]
        for fact in facts:
            lines.append(f"- {fact.describe()}")
        if len(self.facts) > len(facts):
            lines.append(f"- ... {len(self.facts) - len(facts)} more omitted")
        return "\n".join(lines)

    def to_system_messages(self, workflow_name: str, *, fact_limit: int = 8) -> tuple[AgentMessage, ...]:
        messages: list[AgentMessage] = []
        if self.facts:
            messages.append(
                AgentMessage(
                    role="system",
                    content=self.format_facts(limit=fact_limit),
                    name=workflow_name,
                    metadata={
                        "conversation_memory_facts": True,
                        "memory_fact_count": len(self.facts),
                    },
                )
            )
        summary_text = self.format_summary()
        if summary_text:
            messages.append(
                AgentMessage(
                    role="system",
                    content=summary_text,
                    name=workflow_name,
                    metadata={
                        "conversation_memory_summary": True,
                        "summary_turns": self.source_turns,
                        "dropped_turns": self.dropped_turns,
                    },
                )
            )
        return tuple(messages)

    def merge(self, other: "ConversationMemory") -> "ConversationMemory":
        merged_facts = _merge_facts(self.facts, other.facts)
        summary = other.summary.strip() or self.summary.strip()
        if self.summary.strip() and other.summary.strip():
            summary = f"{self.summary.strip()}\n\n{other.summary.strip()}"
        metadata = dict(self.metadata)
        metadata.update(other.metadata)
        return ConversationMemory(
            summary=summary,
            facts=merged_facts,
            retained_turns=max(self.retained_turns, other.retained_turns),
            dropped_turns=max(self.dropped_turns, other.dropped_turns),
            source_turns=max(self.source_turns, other.source_turns),
            source_messages=max(self.source_messages, other.source_messages),
            updated_at=max(self.updated_at, other.updated_at),
            metadata=metadata,
        )


def extract_memory_facts(
    messages: Sequence[AgentMessage],
    *,
    existing: Sequence[MemoryFact] = (),
    limit: int = 8,
) -> tuple[MemoryFact, ...]:
    facts: dict[str, MemoryFact] = {fact.key: fact for fact in existing}
    for message in messages:
        if message.role != "user":
            continue
        text = _normalize_text(message.content)
        if not text:
            continue
        for key, pattern, confidence in _FACT_PATTERNS:
            match = pattern.search(text)
            if match is None:
                continue
            value = _clean_fact_value(match.group("value"))
            if not value:
                continue
            candidate = MemoryFact(
                key=key,
                value=value,
                confidence=confidence,
                evidence=text,
            )
            facts[key] = _merge_fact(facts.get(key), candidate)
    ordered = list(facts.values())
    if limit > 0:
        ordered = ordered[:limit]
    return tuple(ordered)


def build_history_summary(
    existing_summary: str,
    dropped_turns: Sequence[Sequence[AgentMessage]],
    *,
    turn_preview_limit: int = 8,
    summary_char_limit: int = 2000,
) -> str:
    sections: list[str] = []
    cleaned_existing = existing_summary.strip()
    if cleaned_existing:
        sections.append(cleaned_existing)

    if dropped_turns:
        sections.append("Recently compressed turns:")
        for index, turn in enumerate(dropped_turns, start=1):
            sections.append(f"- Turn {index}: {_preview_turn(turn, turn_preview_limit)}")

    summary = "\n".join(sections).strip()
    return _trim_text(summary, summary_char_limit)


def split_turns(messages: Sequence[AgentMessage]) -> tuple[tuple[AgentMessage, ...], ...]:
    turns: list[list[AgentMessage]] = []
    current: list[AgentMessage] = []
    seen_user = False

    for message in messages:
        if message.role == "user" and seen_user and current:
            turns.append(current)
            current = [message]
            continue
        if message.role == "user":
            seen_user = True
        current.append(message)

    if current:
        turns.append(current)

    return tuple(tuple(turn) for turn in turns if turn)


def is_memory_message(message: AgentMessage) -> bool:
    return bool(message.metadata.get("conversation_memory_facts"))


def is_summary_message(message: AgentMessage) -> bool:
    return bool(message.metadata.get("conversation_memory_summary"))


def is_system_prompt_message(message: AgentMessage) -> bool:
    return bool(message.metadata.get("talosent_system_prompt"))


def _preview_turn(turn: Sequence[AgentMessage], limit: int) -> str:
    pieces: list[str] = []
    for message in turn[:limit]:
        if message.role == "assistant" and message.tool_calls:
            tool_names = ", ".join(call.name or "unknown" for call in message.tool_calls[:3])
            if len(message.tool_calls) > 3:
                tool_names += ", ..."
            content = f"tool calls: {tool_names}"
        else:
            content = " ".join(str(message.content or "").split())
        if message.role == "tool" and message.name:
            content = f"tool[{message.name}]: {content}"
        elif message.role == "assistant":
            content = f"assistant: {content}"
        elif message.role == "user":
            content = f"user: {content}"
        elif message.role == "system":
            content = f"system: {content}"
        pieces.append(_trim_text(content or "(empty)", 180))
    if len(turn) > limit:
        pieces.append(f"... {len(turn) - limit} more messages")
    return " | ".join(pieces) or "(empty turn)"


def _merge_fact(existing: MemoryFact | None, candidate: MemoryFact) -> MemoryFact:
    if existing is None:
        return candidate

    existing_values = _split_fact_values(existing.value)
    if candidate.value not in existing_values:
        existing_values.append(candidate.value)

    merged_evidence = candidate.evidence or existing.evidence
    metadata = dict(existing.metadata)
    metadata.update(candidate.metadata)
    return replace(
        existing,
        value="; ".join(existing_values),
        confidence=max(existing.confidence, candidate.confidence),
        evidence=merged_evidence,
        source=candidate.source or existing.source,
        updated_at=max(existing.updated_at, candidate.updated_at),
        metadata=metadata,
    )


def _merge_facts(existing: Sequence[MemoryFact], new: Sequence[MemoryFact]) -> tuple[MemoryFact, ...]:
    facts: dict[str, MemoryFact] = {fact.key: fact for fact in existing}
    for fact in new:
        facts[fact.key] = _merge_fact(facts.get(fact.key), fact)
    return tuple(facts.values())


def _split_fact_values(value: str) -> list[str]:
    values = [part.strip() for part in re.split(r"\s*;\s*", value or "") if part.strip()]
    return values or [value.strip()]


def _clean_fact_value(value: str) -> str:
    text = _normalize_text(value)
    return text.strip(" \t\r\n。！？,;:，、")


def _normalize_text(value: Any) -> str:
    return " ".join(str(value or "").split()).strip()


def _trim_text(text: str, limit: int) -> str:
    if limit <= 0 or len(text) <= limit:
        return text
    return f"{text[: max(0, limit - 3)].rstrip()}..."


def _require_text(value: Any, label: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{label} is required")
    return text


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _parse_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)
    text = str(value or "").strip()
    if not text:
        return datetime.now(timezone.utc)
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed
