#!/usr/bin/env bash
# Run from a reviewed checkout. Credentials are never collected by this script.
set -euo pipefail
cd "$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"

case "${1:-}" in
  ""|--no-interview) ;;
  *) echo 'Usage: bash scripts/install.sh [--no-interview]' >&2; exit 2 ;;
esac

if ! command -v uv >/dev/null 2>&1; then
  echo 'Install uv first: https://docs.astral.sh/uv/getting-started/installation/' >&2
  echo 'On macOS with Homebrew: brew install uv node' >&2
  exit 1
fi
if ! command -v node >/dev/null 2>&1 || ! node -e 'process.exit(Number(process.versions.node.split(".")[0]) >= 22 ? 0 : 1)'; then
  echo 'Node.js 22 or newer is required for X search: https://nodejs.org/en/download' >&2
  exit 1
fi
if [[ "$(uname -s)" != Darwin ]]; then
  echo 'macOS is the validated browser-auth platform; other platforms need their own live X verification.'
fi

uv sync --locked --python 3.12
uv run invest --help >/dev/null
echo 'Installed. Python dependencies and the read-only Bird adapter are ready.'
if [[ "${1:-}" == --no-interview || ! -t 0 ]]; then
  echo 'Next: uv run invest setup'
  echo 'For an agent-led interview, read docs/setup.md and .agents/skills/setup/SKILL.md.'
else
  exec uv run invest setup
fi
