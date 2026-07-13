"""Chat workflow that closes the loop between provider and tools."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from talosent.agent.model import AgentContext, AgentMessage, WorkflowResult
from talosent.agent.workflows.base import WorkflowSpec
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

    def run(self, context: AgentContext) -> WorkflowResult:
        result = WorkflowResult()
        final_message = ""

        if self.system_prompt and not any(message.role == "system" for message in context.messages):
            system_message = AgentMessage(role="system", content=self.system_prompt, name=self.spec.name)
            context.messages.insert(0, system_message)
            result.messages.append(system_message)

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

        result.state["turns"] = turns
        result.state["final_message"] = final_message
        result.state["provider"] = getattr(self.provider, "name", self.provider.__class__.__name__)
        return result


def _stringify_tool_result(value: Any) -> str:
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except TypeError:
        return str(value)
