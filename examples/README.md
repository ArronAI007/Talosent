# Examples

Runnable reference integrations. Execute them from the repository root — no package install or API key required.

| Example | Demonstrates | Run |
| --- | --- | --- |
| [custom_tool.py](custom_tool.py) | Registering a custom `ToolSpec` and driving a full provider ⇄ tool agent loop with a scripted provider | `python examples/custom_tool.py` |

Guidelines for new examples:

- Keep them small and focused on one concept.
- No network calls or API keys; use scripted providers (see `tests/integration/test_chat_workflow.py` for the pattern).
- Print a short, human-readable summary at the end.
