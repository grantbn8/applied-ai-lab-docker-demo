#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
command -v docker >/dev/null || { echo "Install and start Docker Desktop first." >&2; exit 1; }
docker info >/dev/null
# Refuse to silently replace another hook setup.
existing=$(git config --local --get core.hooksPath || true)
if [[ -n "$existing" && "$existing" != .githooks ]]; then
  echo "Existing hooksPath: $existing. Integrate the security hooks before continuing." >&2
  exit 1
fi
git config --local core.hooksPath .githooks
bash scripts/security-check.sh staged
echo "Security hooks installed. Commits and pushes fail if scanning fails."
