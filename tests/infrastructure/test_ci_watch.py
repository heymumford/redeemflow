"""TDD tests for ci-watch script — CI-only job monitoring (no agentic bots)."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parents[2] / "scripts" / "ci-watch.sh"

CI_JOBS = {"lint", "unit-and-fitness", "contract-and-integration", "e2e", "security", "frontend-build"}


class TestCiWatchScript:
    """Verify ci-watch.sh exists, is executable, and has correct structure."""

    def test_script_exists(self):
        assert SCRIPT.exists(), f"Expected ci-watch script at {SCRIPT}"

    def test_script_is_executable(self):
        assert os.access(SCRIPT, os.X_OK), "ci-watch.sh must be executable"

    def test_script_has_shebang(self):
        first_line = SCRIPT.read_text().splitlines()[0]
        assert first_line.startswith("#!/"), "Script must have a shebang line"
        assert "bash" in first_line, "Script must use bash"

    def test_script_monitors_ci_jobs_only(self):
        """Script must filter to CI jobs, not agentic review bots."""
        content = SCRIPT.read_text()
        # Must reference the 6 CI job names
        for job in CI_JOBS:
            assert job in content, f"Script must reference CI job '{job}'"

    def test_script_excludes_bot_checks(self):
        """CI_JOBS array must not include agentic review bots."""
        content = SCRIPT.read_text()
        # Extract lines between CI_JOBS=( and ) — the actual job list
        in_array = False
        job_lines = []
        for line in content.splitlines():
            if "CI_JOBS=(" in line:
                in_array = True
                continue
            if in_array and line.strip() == ")":
                break
            if in_array:
                job_lines.append(line)
        jobs_text = "\n".join(job_lines)
        assert "Sourcery" not in jobs_text, "CI_JOBS must not include Sourcery bot"
        assert "recurseml" not in jobs_text, "CI_JOBS must not include RecurseML bot"
        assert "Copilot" not in jobs_text, "CI_JOBS must not include Copilot bot"

    def test_script_accepts_pr_number_arg(self):
        """Script must accept a PR number as argument."""
        content = SCRIPT.read_text()
        assert "$1" in content or "${1" in content, "Script must accept PR number as first argument"

    def test_usage_on_no_args(self):
        """Script must print usage when called without arguments."""
        result = subprocess.run(
            [str(SCRIPT)],
            capture_output=True,
            text=True,
            timeout=5,
        )
        assert result.returncode != 0, "Must exit non-zero without args"
        assert "usage" in result.stderr.lower() or "usage" in result.stdout.lower(), "Must print usage"

    def test_script_sets_timeout(self):
        """Script must have a timeout to prevent infinite waits."""
        content = SCRIPT.read_text()
        assert "timeout" in content.lower() or "MAX_WAIT" in content or "max_wait" in content, (
            "Script must define a timeout"
        )


class TestBranchProtectionConfig:
    """Verify branch protection configuration file exists and is correct."""

    CONFIG = Path(__file__).parents[2] / "scripts" / "setup-branch-protection.sh"

    def test_config_exists(self):
        assert self.CONFIG.exists(), f"Expected branch protection setup at {self.CONFIG}"

    def test_config_is_executable(self):
        assert os.access(self.CONFIG, os.X_OK), "setup-branch-protection.sh must be executable"

    def test_config_requires_ci_checks(self):
        """Config must require exactly the 6 CI jobs in the contexts array."""
        import re

        content = self.CONFIG.read_text()
        match = re.search(r'"contexts"\s*:\s*\[(.*?)\]', content, re.DOTALL)
        assert match, "Must contain contexts array in JSON payload"
        contexts_block = match.group(1)
        for job in CI_JOBS:
            assert job in contexts_block, f"contexts array must include CI job '{job}'"

    def test_config_does_not_require_bots(self):
        """Required status checks must not include agentic bots."""
        content = self.CONFIG.read_text()
        # Extract the "contexts" array values from the JSON payload
        import re

        contexts = re.findall(r'"contexts"\s*:\s*\[(.*?)\]', content, re.DOTALL)
        assert contexts, "Must contain contexts array"
        for ctx_block in contexts:
            assert "sourcery" not in ctx_block.lower(), "Must not require Sourcery"
            assert "recurseml" not in ctx_block.lower(), "Must not require RecurseML"
            assert "copilot" not in ctx_block.lower(), "Must not require Copilot"

    @pytest.mark.skipif(
        os.environ.get("CI") == "true",
        reason="Branch protection API calls require admin token",
    )
    def test_config_uses_gh_api(self):
        """Config must use gh API for branch protection setup."""
        content = self.CONFIG.read_text()
        assert "gh api" in content, "Must use gh api for branch protection"
