#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
# Gitleaks v8.30.1, pinned multi-platform image digest.
scanner=ghcr.io/gitleaks/gitleaks@sha256:c00b6bd0aeb3071cbcb79009cb16a60dd9e0a7c60e2be9ab65d25e6bc8abbb7f
mode=${1:-history}
revision=${2:---all}
files=$(mktemp)
trap 'rm -f "$files"' EXIT
case "$mode" in
  staged) git diff --cached --name-only --diff-filter=ACMR -z > "$files" ;;
  history)
    git rev-parse --verify HEAD >/dev/null
    git log --format= --name-only -z "$revision" -- > "$files"
    ;;
  *) echo "Usage: $0 staged | history [revision]" >&2; exit 2 ;;
esac
blocked=0
while IFS= read -r -d '' path; do
  [[ -z "$path" ]] && continue
  case "$path" in
    .env.example|*/.env.example) ;;
    .env|.env.*|*/.env|*/.env.*|auth.json|*/auth.json|.codex/*|*/.codex/*|.aws/*|*/.aws/*|*.pem|*.key|*.p12|*.pfx|id_rsa|*/id_rsa|id_ed25519|*/id_ed25519|*codex-auth*|*postgres-data*|*model-data*)
      printf 'Blocked credential/data path: %q
' "$path" >&2
      blocked=1 ;;
  esac
done < "$files"
[[ "$blocked" == 0 ]] || exit 1
# Disable Git Bash path rewriting; the Windows path remains a host mount source.
export MSYS_NO_PATHCONV=1
root=$(pwd -P)
if command -v cygpath >/dev/null; then root=$(cygpath -w "$root"); fi
args=(git /repo --redact=100 --no-banner --ignore-gitleaks-allow --gitleaks-ignore-path /dev/null)
if [[ "$mode" == staged ]]; then
  args+=(--pre-commit --staged)
else
  args+=(--log-opts="$revision")
fi
# Read-only mount and no network access while scanning. Missing image may be pulled
# by Docker first; any download, engine, or scanner error blocks the operation.
docker run --rm --network none -v "$root:/repo:ro" "$scanner" "${args[@]}"
