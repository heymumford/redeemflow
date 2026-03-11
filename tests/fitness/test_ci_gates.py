"""CI pipeline fitness functions — verify quality gates are configured correctly."""

from __future__ import annotations

import pathlib

import pytest
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[2]


@pytest.mark.fitness
class TestCIGatesConfigured:
    """Verify CI pipeline enforces all required quality gates."""

    def _load_ci(self) -> dict:
        ci_path = ROOT / ".github" / "workflows" / "ci.yml"
        assert ci_path.exists(), "CI workflow missing"
        return yaml.safe_load(ci_path.read_text())

    def test_lint_job_exists(self):
        ci = self._load_ci()
        assert "lint" in ci["jobs"]

    def test_unit_job_has_coverage_gate(self):
        ci = self._load_ci()
        unit_job = ci["jobs"].get("unit-and-fitness", {})
        steps_text = str(unit_job.get("steps", []))
        assert "cov-fail-under" in steps_text, "Unit tests must enforce coverage threshold"

    def test_security_job_exists(self):
        ci = self._load_ci()
        assert "security" in ci["jobs"], "CI must include security scanning job"

    def test_security_job_runs_pip_audit(self):
        ci = self._load_ci()
        security_steps = str(ci["jobs"]["security"].get("steps", []))
        assert "pip-audit" in security_steps, "Security job must run pip-audit"

    def test_security_job_runs_bandit(self):
        ci = self._load_ci()
        security_steps = str(ci["jobs"]["security"].get("steps", []))
        assert "bandit" in security_steps, "Security job must run bandit"

    def test_dependabot_configured(self):
        dependabot = ROOT / ".github" / "dependabot.yml"
        assert dependabot.exists(), "Dependabot configuration missing"
        config = yaml.safe_load(dependabot.read_text())
        ecosystems = {u["package-ecosystem"] for u in config.get("updates", [])}
        assert "pip" in ecosystems, "Dependabot must monitor Python dependencies"

    def test_deploy_workflow_has_smoke_test(self):
        deploy_path = ROOT / ".github" / "workflows" / "deploy.yml"
        assert deploy_path.exists(), "Deploy workflow missing"
        deploy = yaml.safe_load(deploy_path.read_text())
        assert "smoke-test" in deploy["jobs"], "Deploy must include smoke tests"
