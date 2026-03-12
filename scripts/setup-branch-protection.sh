#!/usr/bin/env bash
# setup-branch-protection.sh — Configure main branch protection with required CI checks.
#
# Requires: gh CLI with admin access to the repo.
# Requires the 6 CI jobs as status checks:
#   lint, unit-and-fitness, contract-and-integration, e2e, security, frontend-build
#
# Does NOT require agentic review bots (Sourcery, RecurseML, Copilot, Gemini).

set -euo pipefail

REPO="${1:-heymumford/redeemflow}"
BRANCH="main"

echo "Setting up branch protection for ${REPO}:${BRANCH}..."

gh api "repos/${REPO}/branches/${BRANCH}/protection" \
  --method PUT \
  --input - <<'JSON'
{
  "required_status_checks": {
    "strict": true,
    "contexts": [
      "lint",
      "unit-and-fitness",
      "contract-and-integration",
      "e2e",
      "security",
      "frontend-build"
    ]
  },
  "enforce_admins": false,
  "required_pull_request_reviews": null,
  "restrictions": null
}
JSON

echo "Branch protection configured:"
echo "  Required CI checks: lint, unit-and-fitness, contract-and-integration, e2e, security, frontend-build"
echo "  Strict status checks: true (branch must be up to date)"
echo "  Enforce admins: false"
echo "  PR reviews: not required (agentic review bots are advisory)"
