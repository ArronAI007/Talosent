# Contributing

## Setup

```bash
python -m pip install -e .[dev]
```

Or use the bootstrap script:

```bash
./scripts/dev.sh
```

## Workflow

1. Create a branch from `main`.
2. Make your change following the rules in [AGENTS.md](AGENTS.md).
3. Add or update tests. Unit tests live in `tests/unit/`, integration in `tests/integration/`, e2e in `tests/e2e/`.
4. Run `./scripts/test.sh` and `ruff check src tests apps examples` until clean.
5. Open a PR with a clear summary and test plan.

## Commit Messages

```
<type>[(scope)]: <summary>
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`, `ci`.
Scopes (optional): `web`, `tui`, `agent`, `providers`, `tools`, `config`.

## What to Contribute

Good first contributions:

- New providers in `src/talosent/providers/` (see `docs/extending.md`)
- New tools in `src/talosent/tools/` (see `docs/extending.md`)
- Regression tests for reported issues
- Documentation improvements in `docs/`

Please open an issue before large changes (new workflows, new dependencies, restructuring) so the approach can be agreed on first.

## Reporting Security Issues

Do not open public issues for security reports. See [SECURITY.md](SECURITY.md).
