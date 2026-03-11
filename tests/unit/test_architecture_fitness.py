"""Architectural fitness functions — CI-enforced guardrails.

Fowler: Fitness functions are executable assertions about architecture.
These verify structural invariants, not behavioral correctness.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

SRC_ROOT = Path(__file__).resolve().parents[2] / "src" / "redeemflow"

# Modules that own port definitions
PORT_MODULES = {
    "portfolio": "ports.py",
    "valuations": "ports.py",
    "optimization": "ports.py",
    "charity": "ports.py",
    "search": "ports.py",
    "billing": "ports.py",
    "notifications": "ports.py",
}


def _get_python_files(directory: Path) -> list[Path]:
    """Recursively find all .py files under a directory."""
    return sorted(directory.rglob("*.py"))


def _parse_imports(filepath: Path) -> list[tuple[str, str]]:
    """Parse all import statements from a Python file.

    Returns list of (module_path, imported_name) tuples.
    """
    try:
        tree = ast.parse(filepath.read_text())
    except SyntaxError:
        return []

    imports: list[tuple[str, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            for alias in node.names:
                imports.append((node.module, alias.name))
    return imports


def _module_name(filepath: Path) -> str:
    """Extract the module name from a file path relative to SRC_ROOT."""
    rel = filepath.relative_to(SRC_ROOT)
    parts = rel.parts
    if len(parts) >= 1:
        return parts[0]
    return ""


@pytest.mark.fitness
class TestNoProtocolCrossModuleImports:
    """Protocol definitions must not be imported across module boundaries.

    Each module owns its ports.py. Other modules should NOT import Protocol
    classes from another module's ports.py — they should depend on the
    Protocol at the composition root (app.py), not at the module level.

    Allowed: portfolio/fake_adapter.py imports portfolio/ports.py (same module)
    Forbidden: billing/routes.py imports portfolio/ports.py (cross-module)

    Exception: tests/ and app.py (composition root) may import any port.
    """

    def test_no_cross_module_port_imports(self):
        violations: list[str] = []
        all_files = _get_python_files(SRC_ROOT)

        for filepath in all_files:
            # Skip __pycache__, __init__.py, and the composition root
            if "__pycache__" in str(filepath):
                continue
            if filepath.name == "__init__.py":
                continue
            if filepath.name == "app.py":
                continue

            file_module = _module_name(filepath)
            imports = _parse_imports(filepath)

            for module_path, name in imports:
                # Check if this imports from another module's ports.py
                if ".ports" not in module_path:
                    continue

                # Extract the module owning the port
                parts = module_path.split(".")
                # e.g., "redeemflow.portfolio.ports" -> "portfolio"
                if len(parts) >= 2:
                    port_owner = parts[-2] if parts[-1] == "ports" else ""
                else:
                    continue

                # Same module is fine
                if port_owner == file_module:
                    continue

                violations.append(
                    f"{filepath.relative_to(SRC_ROOT)}: imports '{name}' from {module_path} "
                    f"(file is in '{file_module}', port belongs to '{port_owner}')"
                )

        assert violations == [], (
            f"Cross-module Protocol imports detected ({len(violations)} violations):\n"
            + "\n".join(f"  - {v}" for v in violations)
        )


@pytest.mark.fitness
class TestEveryModuleHasPortsFile:
    """Every domain module with external dependencies must have a ports.py."""

    def test_port_files_exist(self):
        missing: list[str] = []
        for module_name, port_file in PORT_MODULES.items():
            port_path = SRC_ROOT / module_name / port_file
            if not port_path.exists():
                missing.append(f"{module_name}/{port_file}")

        assert missing == [], f"Missing port files: {missing}"


@pytest.mark.fitness
class TestEveryModuleHasFakeAdapter:
    """Every domain module with a port must have a fake_adapter.py."""

    def test_fake_adapter_files_exist(self):
        missing: list[str] = []
        for module_name in PORT_MODULES:
            fake_path = SRC_ROOT / module_name / "fake_adapter.py"
            if not fake_path.exists():
                missing.append(f"{module_name}/fake_adapter.py")

        assert missing == [], f"Missing fake adapter files: {missing}"


@pytest.mark.fitness
class TestPortsUseProtocolNotABC:
    """All port definitions must use typing.Protocol, never abc.ABC."""

    def test_no_abc_in_ports(self):
        abc_violations: list[str] = []
        for module_name, port_file in PORT_MODULES.items():
            port_path = SRC_ROOT / module_name / port_file
            if not port_path.exists():
                continue

            content = port_path.read_text()
            if "abc.ABC" in content or "from abc import" in content:
                abc_violations.append(f"{module_name}/{port_file}")

        assert abc_violations == [], f"Ports using ABC instead of Protocol: {abc_violations}"


@pytest.mark.fitness
class TestFutureAnnotationsInAllNewFiles:
    """Every .py file in src/redeemflow must have 'from __future__ import annotations'."""

    def test_future_annotations_present(self):
        missing: list[str] = []
        for filepath in _get_python_files(SRC_ROOT):
            if "__pycache__" in str(filepath):
                continue
            if filepath.name == "__init__.py":
                content = filepath.read_text().strip()
                if not content:
                    continue  # Empty __init__.py is fine

            content = filepath.read_text()
            if "from __future__ import annotations" not in content:
                missing.append(str(filepath.relative_to(SRC_ROOT)))

        assert missing == [], f"Files missing 'from __future__ import annotations' ({len(missing)}):\n" + "\n".join(
            f"  - {f}" for f in missing
        )
