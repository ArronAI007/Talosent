"""Interactive terminal UI for chatting with the Talosent runtime."""

from __future__ import annotations

import argparse
import os
import sys
import time
from collections.abc import Sequence
from uuid import uuid4

from talosent.agent.model import AgentContext, AgentMessage
from talosent.agent.workflows import ChatWorkflow
from talosent.config import load_settings
from talosent.observability import configure_logging
from talosent.runtime import build_chat_workflow


class Colors:
    """ANSI color codes for terminal output."""

    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    # Foreground colors
    ORANGE = "\033[38;5;214m"
    BLUE = "\033[34m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    RED = "\033[31m"
    CYAN = "\033[36m"
    GRAY = "\033[90m"

    @staticmethod
    def supports_color() -> bool:
        """Check if terminal supports colors."""
        return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="talosent-tui",
        description="Start the Talosent terminal chat UI.",
        add_help=True,
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
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    use_color = Colors.supports_color() and not args.no_color
    settings = load_settings()
    configure_logging(settings.log_level)
    workflow = build_chat_workflow(settings, max_turns=args.max_turns)
    session = AgentContext(conversation_id=uuid4().hex)

    _print_welcome_screen(workflow.provider.name, settings.default_model, workflow.tools.names(), use_color)

    if args.prompt:
        _run_turn(session, workflow, args.prompt, use_color)
        return 0

    _interactive_loop(session, workflow, use_color)
    return 0


def _print_welcome_screen(
    provider_name: str, model_name: str, tool_names: tuple[str, ...], use_color: bool = True
) -> None:
    """Print a welcome screen similar to Claude Code."""
    if use_color:
        orange = Colors.ORANGE
        bold = Colors.BOLD
        dim = Colors.DIM
        reset = Colors.RESET
        cyan = Colors.CYAN
    else:
        orange = bold = dim = reset = cyan = ""

    # Get username for personalized greeting
    username = os.getenv("USER", "there")

    # Top border with version
    border = "─" * 70
    if use_color:
        print(f"{orange}┌─ Talosent v0.1.0 {border[30:]}{reset}")
    else:
        print(f"┌─ Talosent v0.1.0 {border[30:]}")

    print()

    # Main content area - two columns
    left_width = 35

    # Welcome message with ASCII art
    welcome_lines = [
        f"{bold}Welcome back {username}!{reset}",
        "",
        "  ░░░░░░░░",
        "  ░░▓▓░▓▓░",
        "  ░░▓▓░▓▓░",
        "  ░░░░░░░░",
        "  ░░▓░░▓░░",
    ]

    # Right panel - tips
    tips_title = f"{orange}{bold}Tips for getting started{reset}"
    tips_lines = [
        f"{cyan}Run /help{reset}",
        f"{dim}to see all available commands{reset}",
        "",
        f"{orange}{bold}Quick commands{reset}",
        f"{cyan}/stats{reset}     {dim}Show conversation stats{reset}",
        f"{cyan}/reset{reset}     {dim}Clear history{reset}",
        f"{cyan}/exit{reset}      {dim}Exit the chat{reset}",
    ]

    # Print left column
    max_left_lines = max(len(welcome_lines), len(tips_lines))
    for i in range(max_left_lines):
        left = welcome_lines[i] if i < len(welcome_lines) else ""
        right = tips_lines[i] if i < len(tips_lines) else ""

        if i == 0 and use_color:
            # Title for right panel
            print(f"{left:<{left_width}}  │  {tips_title}")
        elif i == 1:
            print(f"{left:<{left_width}}  │")
        else:
            if use_color:
                print(f"{left:<{left_width}}  │  {right}")
            else:
                print(f"{left:<{left_width}}  │  {right}")

    print()

    # Bottom border with system info
    cwd = os.getcwd().replace(os.path.expanduser("~"), "~")
    system_info = f"{dim}{model_name} · {provider_name} · {username} ~ {cwd}{reset}"

    if use_color:
        print(f"{orange}└─ {system_info}{reset}")
    else:
        print(f"└─ {system_info}")

    print()


def _interactive_loop(session: AgentContext, workflow: ChatWorkflow, use_color: bool = True) -> None:
    """Run the interactive chat loop."""
    prompt_prefix = "> "

    while True:
        try:
            user_input = input(prompt_prefix).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            if use_color:
                print(f"{Colors.DIM}Goodbye!{Colors.RESET}")
            else:
                print("Goodbye!")
            return

        if not user_input:
            continue

        if user_input == "/help":
            _print_help(use_color)
            continue

        if user_input in {"/exit", "/quit"}:
            if use_color:
                print(f"{Colors.DIM}Goodbye!{Colors.RESET}")
            else:
                print("Goodbye!")
            return

        if user_input == "/reset":
            workflow.clear_session(session.conversation_id)
            session.clear()
            if use_color:
                print(f"{Colors.GREEN}✓ Session cleared{Colors.RESET}")
            else:
                print("✓ Session cleared")
            print()
            continue

        if user_input == "/stats":
            _print_session_stats(session, use_color)
            continue

        _run_turn(session, workflow, user_input, use_color)


def _print_help(use_color: bool = True) -> None:
    """Print detailed help message with available commands and examples."""
    if use_color:
        title = f"{Colors.BOLD}{Colors.ORANGE}Help & Documentation{Colors.RESET}"
        section = f"{Colors.BOLD}{Colors.ORANGE}"
        reset = Colors.RESET
        dim = Colors.DIM
        cyan = Colors.CYAN
        green = Colors.GREEN
    else:
        title = "Help & Documentation"
        section = ""
        reset = ""
        dim = ""
        cyan = ""
        green = ""

    print(title)
    print()

    print(f"{section}Commands:{reset}")
    print(f"  {cyan}/help{reset}       {dim}Show this help message{reset}")
    print(f"  {cyan}/reset{reset}      {dim}Clear conversation history{reset}")
    print(f"  {cyan}/stats{reset}      {dim}Show conversation statistics{reset}")
    print(f"  {cyan}/exit{reset}       {dim}Exit the chat{reset}")
    print()

    print(f"{section}Usage Examples:{reset}")
    print(f"  {green}>{reset} {dim}Ask a question: 'What time is it?'{reset}")
    print(f"  {green}>{reset} {dim}Get help: 'Tell me about Python'{reset}")
    print(f"  {green}>{reset} {dim}Clear history: Use /reset command{reset}")
    print()

    print(f"{section}Tips & Tricks:{reset}")
    print(f"  {dim}• The assistant can use the {cyan}current_time{reset}{dim} tool{reset}")
    print(f"  {dim}• Conversation history is automatically managed{reset}")
    print(f"  {dim}• Type /reset to start a fresh conversation{reset}")
    print(f"  {dim}• Use Ctrl+C or type /exit to quit{reset}")
    print()


def _run_turn(session: AgentContext, workflow: ChatWorkflow, prompt: str, use_color: bool = True) -> None:
    """Run one conversation turn and print the response."""
    start_index = len(session.messages)
    session.add_message("user", prompt)

    if use_color:
        print(f"{Colors.DIM}⟳ Processing...{Colors.RESET}", end="\r", flush=True)

    start_time = time.time()
    result = workflow.run(session)
    elapsed = time.time() - start_time

    if use_color:
        print(" " * 25 + "\r", end="", flush=True)

    for message in session.messages[start_index + 1 :]:
        _print_message(message, use_color)

    # Print metadata
    turns = result.state.get("turns", 0)
    if use_color:
        timing = f"{Colors.DIM}({elapsed:.2f}s · {turns} turn{'s' if turns != 1 else ''}){Colors.RESET}"
    else:
        timing = f"({elapsed:.2f}s · {turns} turn{'s' if turns != 1 else ''})"
    print(timing)
    print()


def _print_message(message: AgentMessage, use_color: bool = True) -> None:
    """Print a single message with appropriate formatting."""
    if message.role == "system":
        return

    if use_color:
        if message.role == "assistant" and not message.content and message.tool_calls:
            tool_names = ", ".join(call.name or "unknown" for call in message.tool_calls)
            icon = f"{Colors.BOLD}{Colors.YELLOW}🔧{Colors.RESET}"
            prefix = f"{icon} {Colors.YELLOW}assistant{Colors.RESET}"
            print(f"{prefix}  {Colors.DIM}requesting: {tool_names}{Colors.RESET}")
        elif message.role == "tool":
            icon = f"{Colors.GREEN}✓{Colors.RESET}"
            tool_name = f"{Colors.CYAN}{message.name}{Colors.RESET}"
            content = _format_content(message.content, use_color)
            print(f"{icon} {tool_name}")
            _print_indented_content(content, use_color)
        elif message.role == "assistant":
            icon = f"{Colors.BOLD}{Colors.BLUE}✦{Colors.RESET}"
            prefix = f"{icon} {Colors.BOLD}{Colors.BLUE}assistant{Colors.RESET}"
            content = _format_content(message.content, use_color)
            print(f"{prefix}")
            _print_indented_content(content, use_color)
    else:
        if message.role == "assistant" and not message.content and message.tool_calls:
            tool_names = ", ".join(call.name or "unknown" for call in message.tool_calls)
            print(f"🔧 assistant  requesting: {tool_names}")
        elif message.role == "tool":
            print(f"✓ {message.name}")
            _print_indented_content(message.content, use_color)
        elif message.role == "assistant":
            print("✦ assistant")
            _print_indented_content(message.content, use_color)


def _format_content(content: str, use_color: bool = True) -> str:
    """Format message content for display."""
    return content.strip()


def _print_indented_content(content: str, use_color: bool = True, indent: int = 2) -> None:
    """Print content with indentation."""
    indent_str = " " * indent
    for line in content.split("\n"):
        if use_color:
            print(f"{indent_str}{Colors.DIM}{line}{Colors.RESET}")
        else:
            print(f"{indent_str}{line}")


def _print_session_stats(session: AgentContext, use_color: bool = True) -> None:
    """Print conversation statistics."""
    user_msgs = sum(1 for m in session.messages if m.role == "user")
    assistant_msgs = sum(1 for m in session.messages if m.role == "assistant")
    tool_msgs = sum(1 for m in session.messages if m.role == "tool")

    if use_color:
        title = f"{Colors.BOLD}{Colors.ORANGE}Session Statistics{Colors.RESET}"
        dim = Colors.DIM
        reset = Colors.RESET
    else:
        title = "Session Statistics"
        dim = ""
        reset = ""

    print(title)
    print(f"  Messages: {user_msgs + assistant_msgs + tool_msgs} total")
    print(f"    {dim}• User: {user_msgs}{reset}")
    print(f"    {dim}• Assistant: {assistant_msgs}{reset}")
    print(f"    {dim}• Tool: {tool_msgs}{reset}")
    print(f"  Session ID: {session.conversation_id[:12]}...")
    print()


if __name__ == "__main__":
    raise SystemExit(main())
