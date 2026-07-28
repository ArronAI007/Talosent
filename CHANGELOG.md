# Changelog

All notable changes to this project are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- Repository governance files: `AGENTS.md`, `CONTRIBUTING.md`, `SECURITY.md`
- CI workflow (lint + tests on Python 3.10-3.13) and GitHub issue templates
- Ruff, pytest, and mypy configuration in `pyproject.toml`
- `scripts/test.sh` and `scripts/dev.sh` developer entry points
- `docs/architecture.md` and `docs/extending.md`
- `examples/custom_tool.py` runnable example

## [0.1.0]

### Added

- Core agent runtime with provider-agnostic chat workflow
- Local heuristic provider and OpenAI-compatible provider
- Built-in `current_time` tool and tool registry
- Conversation memory with recent turns, running summary, and key facts
- Terminal UI (`talosent-tui`) and browser UI (`talosent-web`)
- `doctor` and `config` CLI inspection commands
