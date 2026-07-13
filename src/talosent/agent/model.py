"""Core agent state objects."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class AgentMessage:
    role: str
    content: str
    name: str | None = None
    tool_call_id: str | None = None
    tool_calls: tuple[ToolCall, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Artifact:
    name: str
    data: Any
    mime_type: str = "text/plain"
    metadata: dict[str, Any] = field(default_factory=dict)


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

    def last_message(self, role: str | None = None) -> AgentMessage | None:
        for message in reversed(self.messages):
            if role is None or message.role == role:
                return message
        return None


@dataclass(slots=True)
class WorkflowResult:
    messages: list[AgentMessage] = field(default_factory=list)
    artifacts: list[Artifact] = field(default_factory=list)
    state: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def apply_to(self, context: AgentContext) -> None:
        context.messages.extend(self.messages)
        context.artifacts.extend(self.artifacts)
        context.state.update(self.state)
        context.metadata.update(self.metadata)
