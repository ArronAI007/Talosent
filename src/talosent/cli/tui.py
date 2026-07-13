"""Interactive terminal UI for chatting with the Talosent runtime."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from uuid import uuid4

from talosent.agent.model import AgentContext, AgentMessage
from talosent.agent.workflows import ChatWorkflow
from talosent.config import load_settings
from talosent.observability import configure_logging
from talosent.runtime import build_chat_workflow


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="talosent-tui",
        description="Start the Talosent terminal chat UI.",
    )
    parser.add_argument(
        "--prompt",
        help="Send one prompt, print the response, and exit.",
    )
    parser.add_argument(
        "--max-turns",
        type=int,
        default=4,
        help="Maximum provider/tool turns per prompt.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    settings = load_settings()
    configure_logging(settings.log_level)
    workflow = build_chat_workflow(settings, max_turns=args.max_turns)
    session = AgentContext(conversation_id=uuid4().hex)

    _print_header(workflow.provider.name, settings.default_model, workflow.tools.names())

    if args.prompt:
        _run_turn(session, workflow, args.prompt)
        return 0

    _interactive_loop(session, workflow)
    return 0


def _print_header(provider_name: str, model_name: str, tool_names: tuple[str, ...]) -> None:
    tools = ", ".join(tool_names) if tool_names else "(none)"
    print(f"Talosent TUI | provider={provider_name} | model={model_name} | tools={tools}")
    print("Type /exit to quit, /reset to clear the conversation.")


def _interactive_loop(session: AgentContext, workflow: ChatWorkflow) -> None:
    while True:
        try:
            prompt = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return

        if not prompt:
            continue
        if prompt in {"/exit", "/quit"}:
            return
        if prompt == "/reset":
            session.messages.clear()
            session.artifacts.clear()
            session.state.clear()
            session.metadata.clear()
            print("session reset")
            continue

        _run_turn(session, workflow, prompt)


def _run_turn(session: AgentContext, workflow: ChatWorkflow, prompt: str) -> None:
    start_index = len(session.messages)
    session.add_message("user", prompt)
    workflow.run(session)

    for message in session.messages[start_index + 1 :]:
        _print_message(message)

    print()


def _print_message(message: AgentMessage) -> None:
    if message.role == "system":
        return
    if message.role == "assistant" and not message.content and message.tool_calls:
        tool_names = ", ".join(call.name or "unknown" for call in message.tool_calls)
        print(f"assistant> requesting tool: {tool_names}")
        return
    if message.role == "tool":
        print(f"tool[{message.name}]> {message.content}")
        return
    if message.role == "assistant":
        print(f"assistant> {message.content}")
        return
    if message.role == "user":
        print(f"user> {message.content}")


if __name__ == "__main__":
    raise SystemExit(main())
