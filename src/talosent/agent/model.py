"""Core agent state objects."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "arguments": dict(self.arguments),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ToolCall":
        call_id = _require_text(data.get("id"), "ToolCall.id")
        name = _require_text(data.get("name"), "ToolCall.name")
        arguments = data.get("arguments") or {}
        if not isinstance(arguments, Mapping):
            raise TypeError("ToolCall.arguments must be a mapping")
        return cls(id=call_id, name=name, arguments=dict(arguments))


@dataclass(slots=True)
class AgentMessage:
    role: str
    content: str
    name: str | None = None
    tool_call_id: str | None = None
    tool_calls: tuple[ToolCall, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "name": self.name,
            "tool_call_id": self.tool_call_id,
            "tool_calls": [tool_call.to_dict() for tool_call in self.tool_calls],
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "AgentMessage":
        role = _require_text(data.get("role"), "AgentMessage.role")
        content = str(data.get("content") or "")
        name = _optional_text(data.get("name"))
        tool_call_id = _optional_text(data.get("tool_call_id"))
        tool_calls_raw = data.get("tool_calls") or ()
        if isinstance(tool_calls_raw, Mapping) or isinstance(tool_calls_raw, (str, bytes)):
            raise TypeError("AgentMessage.tool_calls must be an iterable of mappings")
        tool_calls = tuple(ToolCall.from_dict(tool_call) for tool_call in tool_calls_raw)
        metadata = data.get("metadata") or {}
        if not isinstance(metadata, Mapping):
            raise TypeError("AgentMessage.metadata must be a mapping")
        return cls(
            role=role,
            content=content,
            name=name,
            tool_call_id=tool_call_id,
            tool_calls=tool_calls,
            metadata=dict(metadata),
        )


@dataclass(slots=True)
class Artifact:
    name: str
    data: Any
    mime_type: str = "text/plain"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "data": self.data,
            "mime_type": self.mime_type,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "Artifact":
        name = _require_text(data.get("name"), "Artifact.name")
        metadata = data.get("metadata") or {}
        if not isinstance(metadata, Mapping):
            raise TypeError("Artifact.metadata must be a mapping")
        return cls(
            name=name,
            data=data.get("data"),
            mime_type=str(data.get("mime_type") or "text/plain"),
            metadata=dict(metadata),
        )


@dataclass(slots=True)
class AgentContext:
    conversation_id: str = "default"
    messages: list[AgentMessage] = field(default_factory=list)
    artifacts: list[Artifact] = field(default_factory=list)
    state: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_message(
        self,
        role: str,
        content: str,
        *,
        name: str | None = None,
        tool_call_id: str | None = None,
        tool_calls: tuple[ToolCall, ...] | list[ToolCall] = (),
        **metadata: Any,
    ) -> AgentMessage:
        message = AgentMessage(
            role=role,
            content=content,
            name=name,
            tool_call_id=tool_call_id,
            tool_calls=tuple(tool_calls),
            metadata=dict(metadata),
        )
        self.messages.append(message)
        return message

    def add_messages(self, messages: Iterable[AgentMessage]) -> tuple[AgentMessage, ...]:
        appended: list[AgentMessage] = []
        for message in messages:
            self.messages.append(message)
            appended.append(message)
        return tuple(appended)

    def add_tool_message(
        self,
        tool_call_id: str,
        name: str,
        content: str,
        **metadata: Any,
    ) -> AgentMessage:
        return self.add_message(
            "tool",
            content,
            name=name,
            tool_call_id=tool_call_id,
            **metadata,
        )

    def add_artifact(
        self,
        name: str,
        data: Any,
        *,
        mime_type: str = "text/plain",
        **metadata: Any,
    ) -> Artifact:
        artifact = Artifact(
            name=name,
            data=data,
            mime_type=mime_type,
            metadata=dict(metadata),
        )
        self.artifacts.append(artifact)
        return artifact

    def add_artifacts(self, artifacts: Iterable[Artifact]) -> tuple[Artifact, ...]:
        appended: list[Artifact] = []
        for artifact in artifacts:
            self.artifacts.append(artifact)
            appended.append(artifact)
        return tuple(appended)

    def last_message(self, role: str | None = None) -> AgentMessage | None:
        for message in reversed(self.messages):
            if role is None or message.role == role:
                return message
        return None

    def clear(self) -> None:
        self.messages.clear()
        self.artifacts.clear()
        self.state.clear()
        self.metadata.clear()

    def copy(self) -> "AgentContext":
        return AgentContext.from_dict(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "conversation_id": self.conversation_id,
            "messages": [message.to_dict() for message in self.messages],
            "artifacts": [artifact.to_dict() for artifact in self.artifacts],
            "state": dict(self.state),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "AgentContext":
        conversation_id = str(data.get("conversation_id") or "default")
        messages_raw = data.get("messages") or ()
        artifacts_raw = data.get("artifacts") or ()
        state = data.get("state") or {}
        metadata = data.get("metadata") or {}

        if isinstance(messages_raw, Mapping) or isinstance(messages_raw, (str, bytes)):
            raise TypeError("AgentContext.messages must be an iterable of mappings")
        if isinstance(artifacts_raw, Mapping) or isinstance(artifacts_raw, (str, bytes)):
            raise TypeError("AgentContext.artifacts must be an iterable of mappings")
        if not isinstance(state, Mapping):
            raise TypeError("AgentContext.state must be a mapping")
        if not isinstance(metadata, Mapping):
            raise TypeError("AgentContext.metadata must be a mapping")

        return cls(
            conversation_id=conversation_id,
            messages=[AgentMessage.from_dict(message) for message in messages_raw],
            artifacts=[Artifact.from_dict(artifact) for artifact in artifacts_raw],
            state=dict(state),
            metadata=dict(metadata),
        )


@dataclass(slots=True)
class WorkflowResult:
    messages: list[AgentMessage] = field(default_factory=list)
    artifacts: list[Artifact] = field(default_factory=list)
    state: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def append_message(self, message: AgentMessage) -> AgentMessage:
        self.messages.append(message)
        return message

    def append_artifact(self, artifact: Artifact) -> Artifact:
        self.artifacts.append(artifact)
        return artifact

    def merge(self, other: "WorkflowResult") -> "WorkflowResult":
        self.messages.extend(other.messages)
        self.artifacts.extend(other.artifacts)
        self.state.update(other.state)
        self.metadata.update(other.metadata)
        return self

    def copy(self) -> "WorkflowResult":
        return WorkflowResult.from_dict(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "messages": [message.to_dict() for message in self.messages],
            "artifacts": [artifact.to_dict() for artifact in self.artifacts],
            "state": dict(self.state),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "WorkflowResult":
        messages_raw = data.get("messages") or ()
        artifacts_raw = data.get("artifacts") or ()
        state = data.get("state") or {}
        metadata = data.get("metadata") or {}

        if isinstance(messages_raw, Mapping) or isinstance(messages_raw, (str, bytes)):
            raise TypeError("WorkflowResult.messages must be an iterable of mappings")
        if isinstance(artifacts_raw, Mapping) or isinstance(artifacts_raw, (str, bytes)):
            raise TypeError("WorkflowResult.artifacts must be an iterable of mappings")
        if not isinstance(state, Mapping):
            raise TypeError("WorkflowResult.state must be a mapping")
        if not isinstance(metadata, Mapping):
            raise TypeError("WorkflowResult.metadata must be a mapping")

        return cls(
            messages=[AgentMessage.from_dict(message) for message in messages_raw],
            artifacts=[Artifact.from_dict(artifact) for artifact in artifacts_raw],
            state=dict(state),
            metadata=dict(metadata),
        )

    def apply_to(self, context: AgentContext) -> None:
        context.messages.extend(self.messages)
        context.artifacts.extend(self.artifacts)
        context.state.update(self.state)
        context.metadata.update(self.metadata)


def _require_text(value: Any, label: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{label} is required")
    return text


def _optional_text(value: Any) -> str | None:
    text = str(value).strip() if value is not None else ""
    return text or None
