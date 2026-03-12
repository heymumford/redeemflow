#!/usr/bin/env bash
# ci-watch.sh — Watch CI jobs only (excludes agentic review bots).
# Usage: ./scripts/ci-watch.sh <PR_NUMBER>
#
# Polls only the 6 CI pipeline jobs, ignoring Sourcery/RecurseML/Copilot/Gemini
# review bots that can take 10-25 minutes. Exits 0 when all CI jobs pass,
# exits 1 on any failure, exits 2 on timeout.

set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <PR_NUMBER>" >&2
  exit 1
fi

PR_NUMBER="$1"
MAX_WAIT=300  # 5 minutes — CI should finish well within this
POLL_INTERVAL=10

# The 6 CI jobs from .github/workflows/ci.yml
CI_JOBS=(
  "lint"
  "unit-and-fitness"
  "contract-and-integration"
  "e2e"
  "security"
  "frontend-build"
)

elapsed=0

while (( elapsed < MAX_WAIT )); do
  all_done=true
  any_failed=false

  checks_json=$(gh pr checks "$PR_NUMBER" --json name,state 2>/dev/null || echo "[]")

  for job in "${CI_JOBS[@]}"; do
    state=$(echo "$checks_json" | jq -r --arg name "$job" '.[] | select(.name == $name) | .state' 2>/dev/null)

    case "$state" in
      SUCCESS)
        printf "  ✓ %s\n" "$job"
        ;;
      FAILURE|ERROR)
        printf "  ✗ %s (FAILED)\n" "$job"
        any_failed=true
        ;;
      *)
        printf "  ⏳ %s (%s)\n" "$job" "${state:-pending}"
        all_done=false
        ;;
    esac
  done

  if $any_failed; then
    echo ""
    echo "CI FAILED — one or more jobs failed." >&2
    exit 1
  fi

  if $all_done; then
    echo ""
    echo "All 6 CI jobs passed."
    exit 0
  fi

  echo ""
  echo "Waiting ${POLL_INTERVAL}s... (${elapsed}s / ${MAX_WAIT}s timeout)"
  sleep "$POLL_INTERVAL"
  elapsed=$(( elapsed + POLL_INTERVAL ))
done

echo "CI watch timed out after ${MAX_WAIT}s" >&2
exit 2
