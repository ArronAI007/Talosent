# Development Rules

These rules apply to humans and agents working in this repository.

## Conversational Style

- Keep answers short and concise.
- No emojis in commits, issues, PR comments, or code.
- No fluff or cheerful filler text.
- Technical prose only, be direct.
- When the user asks a question, answer it first before making edits or running implementation commands.
- When responding to user feedback or an analysis, explicitly say whether you agree or disagree before saying what you changed.

## Code Quality

- Read files in full before wide-ranging changes and before editing files you have not fully inspected. Do not rely on search snippets for broad changes.
- Type annotations on all function signatures. No untyped `dict`/`Any` leakage across module boundaries unless absolutely necessary.
- Prefer `@dataclass(slots=True)` for data carriers and `Protocol` for structural interfaces, matching the existing codebase style.
- Inline single-use helpers; extract shared logic only when repetition is real.
- No `print()` in library code (`src/talosent/`); use the `logging` module via `talosent.observability`. `print()` is acceptable in CLI entrypoints and examples.
- Check installed dependency source for external API behavior; do not guess.
- Always ask before removing functionality or code that appears intentional.
- Do not add backward-compatibility shims unless the user asks for them.
- The core library (`src/talosent/`) must stay dependency-free; new third-party deps need explicit user approval.
- Keep provider, tool, and workflow boundaries intact: `providers/` talks to LLMs, `tools/` executes capabilities, `agent/workflows/` orchestrates. Do not cross-wire them.

## Commands

- Run tests with `./scripts/test.sh` from the repo root (unit + integration). Use `./scripts/test.sh --all` to include e2e.
- If you create or modify a test file, run it and iterate until it passes.
- Lint with `ruff check src tests apps examples` and format check with `ruff format --check` when `ruff` is installed. Fix all findings you introduced before committing.
- Do not run the full e2e suite repeatedly while iterating; run the specific test file first: `python -m pytest tests/unit/test_settings.py`.
- For ad-hoc scripts, write them to a temp file (e.g. `/tmp`), run, edit if needed, remove when done. Do not embed multi-line scripts in shell one-liners.
- Never commit unless the user asks.

## Dependency and Environment Security

- Treat dependency and lockfile changes as reviewed code.
- Never commit secrets. `.env` is gitignored; keep it that way and mirror new variables in `.env.example` with empty or placeholder values.
- Validate required configuration at startup and fail with a clear message instead of falling back silently.

## Git

Multiple sessions may be running in this directory at the same time, each modifying different files. Git operations that touch unstaged, staged, or untracked files outside your own changes will stomp on other sessions' work. Follow these rules.

Committing:

- Only commit files YOU changed in THIS session.
- Stage explicit paths (`git add <path1> <path2>`); never `git add -A` / `git add .`.
- Before committing, run `git status` and verify you are only staging your files.
- Message format: `{feat,fix,docs,refactor,test,chore,perf,ci}[(web,tui,agent,providers,tools)]: <summary>`. Informative and concise.

Never run (destroys other sessions' work or bypasses checks):

- `git reset --hard`, `git checkout .`, `git clean -fd`, `git stash`, `git add -A`, `git add .`, `git commit --no-verify`.

If rebase conflicts occur:

- Resolve conflicts only in files you modified.
- If a conflict is in a file you did not modify, abort and ask the user.
- Never force push.

## Project Layout

- `src/talosent/` — core library, no third-party dependencies
- `apps/` — repo-local launchers (tui, web), thin wrappers only
- `tests/` — `unit/` (isolated), `integration/` (wired modules), `e2e/` (subprocess surfaces)
- `docs/` — architecture and extension guides
- `examples/` — runnable reference integrations
- `scripts/` — dev entry points (`test.sh`, `dev.sh`)

See `docs/architecture.md` for module boundaries and `docs/extending.md` for how to add providers, tools, and workflows.
