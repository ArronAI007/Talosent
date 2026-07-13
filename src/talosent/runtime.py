"""Composition root for Talosent runtimes."""

from __future__ import annotations

from talosent.agent.workflows import ChatWorkflow, DEFAULT_SYSTEM_PROMPT, WorkflowSpec
from talosent.config import Settings, load_settings
from talosent.providers import ChatProvider, build_provider
from talosent.tools import ToolRegistry, build_tool_registry


def build_chat_workflow(
    settings: Settings | None = None,
    *,
    provider: ChatProvider | None = None,
    tools: ToolRegistry | None = None,
    max_turns: int = 4,
) -> ChatWorkflow:
    runtime_settings = settings or load_settings()
    runtime_provider = provider or build_provider(runtime_settings)
    runtime_tools = tools or build_tool_registry()
    return ChatWorkflow(
        spec=WorkflowSpec(name="chat", summary="Interactive chat workflow."),
        provider=runtime_provider,
        tools=runtime_tools,
        system_prompt=DEFAULT_SYSTEM_PROMPT,
        max_turns=max_turns,
    )


__all__ = ["build_chat_workflow", "build_provider", "build_tool_registry"]
