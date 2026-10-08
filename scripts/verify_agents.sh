#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
cmp AGENTS.md CLAUDE.md
echo "AGENTS.md dan CLAUDE.md identik"
