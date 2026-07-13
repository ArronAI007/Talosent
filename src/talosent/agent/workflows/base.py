"""Workflow contracts and a tiny sequential runner."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Protocol

from talosent.agent.model import AgentContext, WorkflowResult


@dataclass(slots=True)
class WorkflowSpec:
    name: str
    summary: str = ""
    tags: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


class Workflow(Protocol):
    spec: WorkflowSpec

    def run(self, context: AgentContext) -> WorkflowResult:
        """Execute the workflow and return the accumulated result."""


StepHandler = Callable[[AgentContext], WorkflowResult | None]


@dataclass(slots=True)
class WorkflowStep:
    name: str
    handler: StepHandler
    summary: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class SequentialWorkflow:
    spec: WorkflowSpec
    steps: tuple[WorkflowStep, ...] = ()

    def run(self, context: AgentContext) -> WorkflowResult:
        result = WorkflowResult()
        for step in self.steps:
            step_result = step.handler(context)
            if step_result is None:
                continue
            step_result.apply_to(context)
            result.messages.extend(step_result.messages)
            result.artifacts.extend(step_result.artifacts)
            result.state.update(step_result.state)
            result.metadata.update(step_result.metadata)
        return result
