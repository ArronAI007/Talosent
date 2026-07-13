"""Core agent state objects."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class AgentMessage:
    role: str
    content: str
    name: str | None = None
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
        **metadata: Any,
    ) -> AgentMessage:
        message = AgentMessage(
            role=role,
            content=content,
            name=name,
            metadata=dict(metadata),
        )
        self.messages.append(message)
        return message

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

