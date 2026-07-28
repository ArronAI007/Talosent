#!/usr/bin/env bash
# Bootstrap a local development environment: editable install + dev dependencies.
set -euo pipefail
cd "$(dirname "$0")/.."

python -m pip install -e .[dev]

echo
echo "Done. Useful commands:"
echo "  ./scripts/test.sh        # unit + integration tests"
echo "  ./scripts/test.sh --all  # include e2e"
echo "  ruff check src tests apps examples"
echo "  talosent doctor"
