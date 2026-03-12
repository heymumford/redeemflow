"""TDD fitness tests for React 19 + Tailwind 4 migration."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

FRONTEND = Path(__file__).parents[2] / "frontend"
PACKAGE_JSON = FRONTEND / "package.json"


@pytest.fixture()
def pkg():
    return json.loads(PACKAGE_JSON.read_text())


class TestReact19Migration:
    """React 19 upgrade — verify package.json dependencies."""

    def test_react_version_19(self, pkg):
        react = pkg["dependencies"]["react"]
        assert react.startswith("^19") or react.startswith("19"), f"Expected React 19, got {react}"

    def test_react_dom_version_19(self, pkg):
        react_dom = pkg["dependencies"]["react-dom"]
        assert react_dom.startswith("^19") or react_dom.startswith("19"), f"Expected React DOM 19, got {react_dom}"

    def test_types_react_19(self, pkg):
        types_react = pkg["devDependencies"]["@types/react"]
        assert types_react.startswith("^19") or types_react.startswith("19"), (
            f"Expected @types/react 19, got {types_react}"
        )

    def test_types_react_dom_19(self, pkg):
        types_dom = pkg["devDependencies"]["@types/react-dom"]
        assert types_dom.startswith("^19") or types_dom.startswith("19"), (
            f"Expected @types/react-dom 19, got {types_dom}"
        )


class TestTailwind4Migration:
    """Tailwind 4 upgrade — verify config migration."""

    def test_tailwind_version_4(self, pkg):
        tw = pkg["devDependencies"]["tailwindcss"]
        assert tw.startswith("^4") or tw.startswith("4"), f"Expected Tailwind 4, got {tw}"

    def test_postcss_uses_tailwindcss_postcss(self):
        """Tailwind 4 uses @tailwindcss/postcss instead of tailwindcss plugin."""
        postcss = FRONTEND / "postcss.config.mjs"
        content = postcss.read_text()
        assert "@tailwindcss/postcss" in content, "PostCSS must use @tailwindcss/postcss for Tailwind 4"

    def test_autoprefixer_removed_from_postcss(self):
        """Tailwind 4 includes autoprefixer — separate plugin unnecessary."""
        postcss = FRONTEND / "postcss.config.mjs"
        content = postcss.read_text()
        assert "autoprefixer" not in content, "Tailwind 4 includes autoprefixer, remove it from PostCSS"

    def test_globals_css_uses_import(self):
        """Tailwind 4 uses @import instead of @tailwind directives."""
        css = FRONTEND / "app" / "globals.css"
        content = css.read_text()
        assert "@tailwind" not in content, "Tailwind 4 uses @import, not @tailwind directives"
        assert '@import "tailwindcss"' in content, "Must import tailwindcss via @import"

    def test_globals_css_has_theme(self):
        """Custom theme values must be in CSS @theme block for Tailwind 4."""
        css = FRONTEND / "app" / "globals.css"
        content = css.read_text()
        assert "@theme" in content, "Tailwind 4 custom colors must be in @theme block"

    def test_tailwind_config_removed(self):
        """Tailwind 4 uses CSS-based config — tailwind.config.ts should be removed."""
        assert not (FRONTEND / "tailwind.config.ts").exists(), "tailwind.config.ts should be removed for Tailwind 4"
        assert not (FRONTEND / "tailwind.config.js").exists(), "tailwind.config.js should be removed for Tailwind 4"

    def test_autoprefixer_removed_from_devdeps(self, pkg):
        """Tailwind 4 includes autoprefixer — separate dependency unnecessary."""
        assert "autoprefixer" not in pkg["devDependencies"], "autoprefixer should be removed — Tailwind 4 includes it"

    def test_tailwindcss_postcss_in_devdeps(self, pkg):
        """@tailwindcss/postcss must be in devDependencies."""
        assert "@tailwindcss/postcss" in pkg["devDependencies"], "@tailwindcss/postcss must be in devDependencies"


class TestEslintMigration:
    """ESLint + eslint-config-next alignment."""

    def test_eslint_config_next_matches_next(self, pkg):
        """eslint-config-next version should match next version."""
        eslint_next = pkg["devDependencies"].get("eslint-config-next", "")
        next_major = pkg["dependencies"]["next"].split(".")[0]
        assert next_major in eslint_next, f"eslint-config-next should match Next {next_major}, got {eslint_next}"


class TestBuildVerification:
    """Build must succeed after migration."""

    @pytest.mark.skipif(
        not (FRONTEND / "node_modules").exists(),
        reason="node_modules not installed — run npm ci first",
    )
    def test_next_build_succeeds(self):
        import shutil
        import subprocess

        npm_path = shutil.which("npm")
        assert npm_path, "npm not found in PATH"
        result = subprocess.run(
            [npm_path, "run", "build"],
            cwd=str(FRONTEND),
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert result.returncode == 0, f"Build failed:\n{result.stderr[-500:]}"
