#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
# Gitleaks v8.30.1, pinned multi-platform image digest.
scanner=ghcr.io/gitleaks/gitleaks@sha256:c00b6bd0aeb3071cbcb79009cb16a60dd9e0a7c60e2be9ab65d25e6bc8abbb7f
mode=${1:-history}
revision=${2:---all}
files=$(mktemp)
snapshot=''
trap 'rm -f "$files"; if [[ -n "$snapshot" ]]; then rm -rf "$snapshot"; fi' EXIT
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
# Export the actual index: Git hooks may use a temporary GIT_INDEX_FILE which
# is visible to host Git but not to Git inside the scanner container.
common=(--redact=100 --no-banner --ignore-gitleaks-allow --gitleaks-ignore-path /dev/null)
if [[ "$mode" == staged ]]; then
  snapshot=$(mktemp -d)
  git checkout-index --all --prefix="$snapshot/"
  scan_root="$snapshot"
  if command -v cygpath >/dev/null; then scan_root=$(cygpath -w "$snapshot"); fi
  docker run --rm --network none -v "$scan_root:/scan:ro" -v "$root/.gitleaks.toml:/config.toml:ro" \
    "$scanner" dir /scan --config /config.toml "${common[@]}"
else
  docker run --rm --network none -v "$root:/repo:ro" \
    "$scanner" git /repo --log-opts="$revision" "${common[@]}"
fi
