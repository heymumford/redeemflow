"""Landing test conftest — shared server and collection ordering.

pytest-playwright's sync API creates an internal event loop that
conflicts with pytest-asyncio fixtures. We enforce collection order:
async-only modules run first, then playwright modules.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time

import httpx
import pytest

ADMIN_TOKEN = "test-admin-token-e2e"

# Modules that use pytest-asyncio (must run before Playwright modules)
_ASYNC_ONLY_MODULES = {"test_server.py", "test_ux.py", "test_signup_api.py"}


def pytest_collection_modifyitems(items: list) -> None:
    """Sort async-only tests before Playwright tests to prevent event loop contamination."""

    def sort_key(item):
        module_name = item.module.__name__.rsplit(".", 1)[-1] + ".py"
        return (0 if module_name in _ASYNC_ONLY_MODULES else 1, item.fspath, item.name)

    items.sort(key=sort_key)


@pytest.fixture(scope="session")
def landing_server():
    """Start a real landing server subprocess for Playwright tests.

    Uses a subprocess (not a thread) to avoid event loop contamination
    with pytest-asyncio fixtures.
    """
    db_path = "/tmp/test-landing-e2e.db"
    if os.path.exists(db_path):
        os.unlink(db_path)

    env = {
        **os.environ,
        "DB_PATH": db_path,
        "ADMIN_TOKEN": ADMIN_TOKEN,
        "SESSION_SECRET": "test-secret-key-for-testing-only-32chars!",
        "LOG_FORMAT": "text",
    }

    # Find a free port
    import socket

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()

    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "server:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=os.path.join(os.path.dirname(__file__), "..", "..", "landing"),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    for _ in range(30):
        try:
            r = httpx.get(f"http://127.0.0.1:{port}/health", timeout=1.0)
            if r.status_code == 200:
                break
        except httpx.ConnectError:
            time.sleep(0.5)
    else:
        proc.kill()
        raise RuntimeError(f"Landing server failed to start on port {port}")

    yield f"http://127.0.0.1:{port}"

    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
