#!/usr/bin/env bash
# Run the test suite. Unit + integration by default; --all includes e2e.
set -euo pipefail
cd "$(dirname "$0")/.."

if [[ "${1:-}" == "--all" ]]; then
  python -m pytest tests/
elif [[ "${1:-}" == "--cov" ]]; then
  python -m pytest tests/unit tests/integration --cov=src/talosent --cov-report=term-missing
else
  python -m pytest tests/unit tests/integration
fi
