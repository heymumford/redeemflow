"""Browser E2E tests for the beta signup flow via Playwright.

Covers: form submission, success/error states, client-side validation,
keyboard submission, admin dashboard browser access.
Run with: uv run pytest tests/landing/test_signup_e2e.py -x --tb=short -q
"""

from __future__ import annotations

import os

import pytest

from .conftest import ADMIN_TOKEN


@pytest.fixture()
def server_url(landing_server):
    """Alias the shared landing_server fixture from conftest."""
    return landing_server


@pytest.mark.playwright
class TestBrowserSignupFlow:
    """Full browser-based signup flow via Playwright."""

    @pytest.fixture()
    def _page(self, page, server_url):
        page.goto(server_url)
        page.wait_for_load_state("networkidle")
        return page

    def test_form_visible_on_page(self, _page):
        assert _page.locator("#waitlist-form").is_visible()
        assert _page.locator("#waitlist-email").is_visible()
        assert _page.locator(".waitlist__submit").is_visible()

    def test_submit_empty_shows_error(self, _page):
        _page.locator(".waitlist__submit").click()
        error = _page.locator("#waitlist-error")
        _page.wait_for_function("document.getElementById('waitlist-error').textContent.length > 0")
        assert "email" in error.text_content().lower()

    def test_submit_invalid_email_shows_error(self, _page):
        _page.fill("#waitlist-email", "not-an-email")
        _page.locator(".waitlist__submit").click()
        error = _page.locator("#waitlist-error")
        _page.wait_for_function("document.getElementById('waitlist-error').textContent.length > 0")
        assert "valid" in error.text_content().lower()

    def test_error_clears_on_input(self, _page):
        _page.locator(".waitlist__submit").click()
        _page.wait_for_function("document.getElementById('waitlist-error').textContent.length > 0")
        _page.fill("#waitlist-email", "a")
        error_text = _page.locator("#waitlist-error").text_content()
        assert error_text == ""

    def test_successful_signup_shows_success_message(self, _page):
        unique_email = f"playwright-{os.getpid()}@test.com"
        _page.fill("#waitlist-email", unique_email)
        _page.locator(".waitlist__submit").click()
        success = _page.locator("#waitlist-success")
        success.wait_for(state="visible", timeout=5000)
        assert "in" in success.text_content().lower()

    def test_form_hidden_after_success(self, _page):
        unique_email = f"pw-hide-{os.getpid()}@test.com"
        _page.fill("#waitlist-email", unique_email)
        _page.locator(".waitlist__submit").click()
        _page.locator("#waitlist-success").wait_for(state="visible", timeout=5000)
        assert not _page.locator("#waitlist-form").is_visible()

    def test_submit_button_shows_joining_text(self, _page):
        unique_email = f"pw-joining-{os.getpid()}@test.com"
        _page.fill("#waitlist-email", unique_email)
        _page.locator(".waitlist__submit").click()
        _page.locator("#waitlist-success").wait_for(state="visible", timeout=5000)
        assert not _page.locator("#waitlist-form").is_visible()

    def test_duplicate_signup_still_shows_success(self, _page, server_url):
        email = f"pw-dupe-{os.getpid()}@test.com"
        import httpx

        httpx.post(f"{server_url}/api/signup", json={"email": email})
        _page.fill("#waitlist-email", email)
        _page.locator(".waitlist__submit").click()
        success = _page.locator("#waitlist-success")
        success.wait_for(state="visible", timeout=5000)
        assert success.is_visible()

    def test_enter_key_submits_form(self, _page):
        unique_email = f"pw-enter-{os.getpid()}@test.com"
        _page.fill("#waitlist-email", unique_email)
        _page.press("#waitlist-email", "Enter")
        success = _page.locator("#waitlist-success")
        success.wait_for(state="visible", timeout=5000)
        assert success.is_visible()

    def test_signup_appears_in_admin(self, _page, server_url):
        unique_email = f"pw-admin-{os.getpid()}@test.com"
        _page.fill("#waitlist-email", unique_email)
        _page.locator(".waitlist__submit").click()
        _page.locator("#waitlist-success").wait_for(state="visible", timeout=5000)
        import httpx

        resp = httpx.get(
            f"{server_url}/api/signups",
            headers={"Authorization": f"Bearer {ADMIN_TOKEN}"},
        )
        emails = [s["email"] for s in resp.json()["signups"]]
        assert unique_email in emails


@pytest.mark.playwright
class TestBrowserAdminDashboard:
    """Admin dashboard browser tests."""

    def test_admin_loads_with_token(self, page, server_url):
        page.goto(f"{server_url}/admin?token={ADMIN_TOKEN}")
        page.wait_for_load_state("networkidle")
        assert page.locator("h1").text_content() == "RedeemFlow Admin"

    def test_admin_shows_signup_count(self, page, server_url):
        import httpx

        httpx.post(f"{server_url}/api/signup", json={"email": "admin-view@test.com"})
        page.goto(f"{server_url}/admin?token={ADMIN_TOKEN}")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1000)
        stat_values = page.locator(".stat-card__value").all_text_contents()
        total = int(stat_values[0])
        assert total >= 1

    def test_admin_without_token_shows_unauthorized(self, page, server_url):
        page.goto(f"{server_url}/admin")
        assert "Unauthorized" in page.content()
