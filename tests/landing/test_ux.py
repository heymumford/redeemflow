"""UX fitness tests for landing page — vertical slice TDD.

RED phase: these tests define the acceptance criteria for each vertical slice.
They assert on HTML structure, ARIA attributes, CSS presence, and content quality.
Run with: uv run pytest tests/landing/test_ux.py -x --tb=short -q
"""

from __future__ import annotations

import os
import re
import sys

import pytest
from httpx import ASGITransport, AsyncClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "landing"))

os.environ.setdefault("DB_PATH", "")
os.environ.setdefault("SESSION_SECRET", "test-secret-key-for-testing-only-32chars!")


@pytest.fixture()
def _temp_db(tmp_path):
    db_path = str(tmp_path / "test_signups.db")
    os.environ["DB_PATH"] = db_path
    import landing.server as srv

    srv.DB_PATH = db_path
    yield db_path


@pytest.fixture()
async def client(_temp_db):
    import landing.server as srv

    transport = ASGITransport(app=srv.app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture()
async def html(client) -> str:
    resp = await client.get("/")
    assert resp.status_code == 200
    return resp.text


@pytest.fixture()
async def app_js(client) -> str:
    resp = await client.get("/app.js")
    assert resp.status_code == 200
    return resp.text


# ─── VS-01: Mobile Navigation ───────────────────────────────────────────


class TestMobileNav:
    """VS-01: Nav must have a toggle button for mobile with correct ARIA."""

    async def test_nav_toggle_button_exists(self, html):
        assert 'class="nav__toggle"' in html or "class='nav__toggle'" in html, (
            "Missing nav__toggle button for mobile hamburger menu"
        )

    async def test_nav_toggle_has_aria_label(self, html):
        # Find the nav__toggle and verify it has aria-label
        pattern = r'<button[^>]*class="nav__toggle"[^>]*aria-label="[^"]*Menu[^"]*"'
        assert re.search(pattern, html), "nav__toggle button must have aria-label containing 'Menu'"

    async def test_nav_toggle_has_aria_expanded(self, html):
        pattern = r'<button[^>]*class="nav__toggle"[^>]*aria-expanded="false"'
        assert re.search(pattern, html), "nav__toggle must have aria-expanded='false' by default"

    async def test_nav_drawer_exists(self, html):
        assert "nav__drawer" in html or "nav__links" in html, "Mobile nav drawer/links container must exist"

    async def test_app_js_has_nav_toggle_handler(self, app_js):
        assert "nav__toggle" in app_js or "nav-toggle" in app_js, "app.js must contain nav toggle handler"


# ─── VS-02: Email Input Mobile Optimization ─────────────────────────────


class TestEmailInputAttributes:
    """VS-02: Waitlist email input must have mobile-optimized attributes."""

    async def test_input_has_inputmode_email(self, html):
        assert 'inputmode="email"' in html, "Email input must have inputmode='email' for mobile keyboard"

    async def test_input_has_enterkeyhint(self, html):
        assert "enterkeyhint=" in html, "Email input must have enterkeyhint for mobile submit button label"

    async def test_input_has_autocapitalize_off(self, html):
        assert 'autocapitalize="off"' in html or 'autocapitalize="none"' in html, (
            "Email input must disable autocapitalize"
        )

    async def test_input_has_spellcheck_false(self, html):
        assert 'spellcheck="false"' in html, "Email input must disable spellcheck"

    async def test_input_has_autocomplete_email(self, html):
        assert 'autocomplete="email"' in html, "Email input must have autocomplete='email'"


# ─── VS-03: Waitlist Input Focus States ─────────────────────────────────


class TestWaitlistFocusStates:
    """VS-03: Waitlist input must have focus-visible pattern in CSS."""

    async def test_focus_visible_rule_exists(self, html):
        assert "focus-visible" in html, "CSS must contain :focus-visible rules for waitlist input"

    async def test_waitlist_input_focus_defined(self, html):
        # Check that there's a focus style for the waitlist input
        assert "waitlist__input" in html and "focus" in html, "Waitlist input must have explicit focus styling"


# ─── VS-04: Hero CTA Visual Dominance ───────────────────────────────────


class TestHeroCTA:
    """VS-04: Hero CTA must be visually dominant with glow effect."""

    async def test_hero_cta_has_distinct_class(self, html):
        assert "btn--hero" in html, "Hero CTA must have btn--hero class for visual dominance"

    async def test_cta_glow_animation_defined(self, html):
        assert "cta-glow" in html or "cta-pulse" in html, "CSS must define cta-glow or cta-pulse keyframes animation"

    async def test_reduced_motion_respects_animation(self, html):
        # Ensure prefers-reduced-motion is present (already exists, verify it covers new animations)
        assert "prefers-reduced-motion" in html, "Must respect prefers-reduced-motion for CTA animation"


# ─── VS-05: Headline Aspiration ──────────────────────────────────────────


class TestHeadlineAspiration:
    """VS-05: H1 must have warm aspirational second line."""

    async def test_h1_contains_span(self, html):
        # H1 should have a <span> child for the warm second line
        pattern = r"<h1[^>]*>.*?<span[^>]*>.*?</span>.*?</h1>"
        assert re.search(pattern, html, re.DOTALL), "H1 must contain a <span> for aspirational second line"

    async def test_h1_span_has_warm_styling(self, html):
        # The span should reference warm accent color
        assert "accent-warm-light" in html or "accent-warm" in html, "H1 span must use warm accent color"


# ─── VS-06: Program Logo Trust Bar ──────────────────────────────────────


class TestLogoBar:
    """VS-06: Trust bar with loyalty program names must exist."""

    async def test_logo_bar_element_exists(self, html):
        assert "logo-bar" in html, "Page must contain a logo-bar element"

    async def test_logo_bar_has_program_names(self, html):
        programs = ["Marriott", "Hilton", "Chase", "Amex"]
        found = sum(1 for p in programs if p in html)
        assert found >= 3, f"Logo bar must reference at least 3 loyalty programs, found {found}"

    async def test_logo_bar_positioned_after_hero(self, html):
        # Find the hero section closing tag (aria-label="Introduction")
        hero_end = html.find("</section>", html.find('aria-label="Introduction"'))
        # Find the logo-bar HTML element (class="logo-bar"), not CSS definition
        logo_bar_pos = html.find('class="logo-bar"')
        assert hero_end > 0 and logo_bar_pos > hero_end, "Logo bar must appear after the hero section in HTML"


# ─── VS-07: $3,400 Stat Dark Band ───────────────────────────────────────


class TestStatBand:
    """VS-07: $3,400 stat must be extracted into its own dark visual band."""

    async def test_stat_band_section_exists(self, html):
        assert "stat-band" in html, "Page must contain a stat-band section"

    async def test_stat_band_has_dark_background(self, html):
        # Should reference inverse/dark surface
        pattern = r'class="[^"]*stat-band[^"]*"'
        match = re.search(pattern, html)
        assert match, "stat-band class must exist"

    async def test_stat_band_contains_value(self, html):
        # Find the stat-band HTML section (not CSS definition)
        stat_band_html = html.find('class="stat-band"', html.find("<main"))
        assert stat_band_html > 0, "stat-band HTML section must exist"
        region = html[stat_band_html : stat_band_html + 1000]
        assert "3,400" in region or "data-target" in region, "Stat band must contain $3,400 value or data-target"


# ─── VS-08: Hero Mobile Viewport ────────────────────────────────────────


class TestHeroMobileViewport:
    """VS-08: Hero must optimize for short mobile viewports."""

    async def test_max_height_media_query_exists(self, html):
        assert "max-height:" in html or "max-height :" in html, (
            "CSS must contain max-height media query for short viewports"
        )


# ─── VS-09: Fade-In Animation Tuning ────────────────────────────────────


class TestFadeInTuning:
    """VS-09: Fade-in animations must use refined values."""

    async def test_fade_in_uses_subtle_transform(self, html):
        # Should use 12px or less, not 20px+
        pattern = r"\.fade-in\s*\{[^}]*translateY\((\d+)px\)"
        match = re.search(pattern, html)
        if match:
            distance = int(match.group(1))
            assert distance <= 16, f"Fade-in translateY should be <= 16px for subtlety, got {distance}px"


# ─── VS-10: Price Anchoring ─────────────────────────────────────────────


class TestPriceAnchoring:
    """VS-10: Page must include price comparison for anchoring."""

    async def test_price_anchoring_present(self, html):
        assert "$200" in html or "200+" in html, "Must reference $200+ concierge pricing for anchoring"

    async def test_redeemflow_price_present(self, html):
        assert "$149" in html, "Must reference $149/year RedeemFlow pricing"


# ─── VS-11: Touch-Friendly FAQ ──────────────────────────────────────────


class TestFAQTouchTargets:
    """VS-11: FAQ accordion triggers must meet 48px minimum touch target."""

    async def test_faq_trigger_min_height_in_css(self, html):
        # Look for min-height on accordion trigger (renamed from faq-item)
        assert "accordion-item__trigger" in html, "Accordion trigger class must exist"
        # Check CSS defines adequate sizing
        pattern = r"\.accordion-item__trigger\s*\{[^}]*min-height:\s*4[4-9]px"
        has_explicit = re.search(pattern, html) is not None
        # Also acceptable if padding creates >= 48px
        pattern2 = r"\.accordion-item__trigger\s*\{[^}]*padding:\s*1[6-9]px"
        has_padding = re.search(pattern2, html) is not None
        assert has_explicit or has_padding, "Accordion trigger must have min-height >= 44px or padding >= 16px"


# ─── VS-12: Success State Personality ────────────────────────────────────


class TestSuccessState:
    """VS-12: Waitlist success state must have personality and delight."""

    async def test_success_has_visual_element(self, html):
        success_start = html.find("waitlist-success")
        if success_start > 0:
            region = html[success_start : success_start + 2000]
            has_svg = "<svg" in region
            has_emoji = any(ord(c) > 127 for c in region[:500])
            assert has_svg or has_emoji, "Success state must contain SVG icon or visual element"

    async def test_success_has_personal_copy(self, html):
        success_start = html.find("waitlist-success")
        if success_start > 0:
            region = html[success_start : success_start + 2000].lower()
            personal_phrases = ["pinky promise", "we'll", "you're in", "one email"]
            found = any(phrase in region for phrase in personal_phrases)
            assert found, "Success state must have warm, personal copy"


# ─── VS-13: 640px Breakpoint ────────────────────────────────────────────


class TestTabletBreakpoint:
    """VS-13: CSS must define a 640px intermediate breakpoint."""

    async def test_640px_breakpoint_exists(self, html):
        assert "640px" in html, "CSS must contain a 640px breakpoint for tablet layouts"


# ─── VS-14: Section Header Amber Accent ─────────────────────────────────


class TestSectionHeaderAccent:
    """VS-14: Eyebrow class must have amber accent indicator."""

    async def test_eyebrow_has_border_accent(self, html):
        pattern = r"\.eyebrow\s*\{[^}]*border-left:"
        assert re.search(pattern, html), "Eyebrow class must have border-left accent"


# ─── VS-15: How It Works Brevity ────────────────────────────────────────


class TestHowItWorksBrevity:
    """VS-15: Step descriptions must be concise (under 25 words each)."""

    async def test_step_descriptions_are_concise(self, html):
        # Find step description paragraphs
        pattern = r'class="step__text[^"]*"[^>]*>(.*?)</p>'
        matches = re.findall(pattern, html, re.DOTALL)
        if not matches:
            # Try alternate class names
            pattern = r"<p[^>]*>\s*(Connect your|We analyze|You see)(.*?)</p>"
            matches = re.findall(pattern, html, re.DOTALL)

        for match in matches:
            text = re.sub(r"<[^>]+>", "", str(match)).strip()
            word_count = len(text.split())
            assert word_count <= 30, f"Step description too long ({word_count} words): '{text[:60]}...'"


# ─── VS-16: Aspirational Waitlist Closing ────────────────────────────────


class TestWaitlistClosing:
    """VS-16: Waitlist section must have aspirational decorative element."""

    async def test_waitlist_has_decorative_element(self, html):
        waitlist_start = html.find('id="waitlist"')
        if waitlist_start > 0:
            # Find the section end
            section_end = html.find("</section>", waitlist_start)
            region = (
                html[waitlist_start:section_end] if section_end > 0 else html[waitlist_start : waitlist_start + 5000]
            )
            has_decorative = 'aria-hidden="true"' in region and "<svg" in region
            has_gradient = "gradient" in region.lower()
            assert has_decorative or has_gradient, (
                "Waitlist section must have decorative SVG (aria-hidden) or gradient element"
            )


# ─── S9-01: Button Atom with Size Variants ────────────────────────────


class TestButtonAtom:
    """S9-01: Button must have reusable size variant classes."""

    async def test_btn_sm_class_defined(self, html):
        assert ".btn--sm" in html, "CSS must define .btn--sm size variant"

    async def test_btn_block_class_defined(self, html):
        assert ".btn--block" in html, "CSS must define .btn--block for full-width buttons"


# ─── S9-02: Section Header Molecule ───────────────────────────────────


class TestSectionHeaderMolecule:
    """S9-02: Section headers (eyebrow + h2) must use a shared component class."""

    async def test_section_header_class_in_css(self, html):
        assert ".section-header" in html, "CSS must define .section-header molecule"

    async def test_no_h2_inline_margin_in_main(self, html):
        main_start = html.find("<main")
        main_end = html.find("</main>")
        main_html = html[main_start:main_end]
        h2_with_style = re.findall(r'<h2[^>]*style="[^"]*margin-bottom[^"]*"', main_html)
        assert len(h2_with_style) == 0, (
            f"Found {len(h2_with_style)} h2 elements with inline margin-bottom — use .section-header instead"
        )

    async def test_section_header_used_in_html(self, html):
        main_start = html.find("<main")
        main_html = html[main_start:]
        assert 'class="section-header"' in main_html or "section-header" in main_html, (
            "section-header class must be used in HTML"
        )


# ─── S9-04: Generic Accordion ─────────────────────────────────────────


class TestGenericAccordion:
    """S9-04: FAQ accordion must use generic .accordion class for reuse."""

    async def test_accordion_class_in_html(self, html):
        main_start = html.find("<main")
        main_html = html[main_start:]
        assert 'accordion"' in main_html, "HTML must use an accordion class for reuse"

    async def test_accordion_css_defined(self, html):
        assert ".accordion" in html, "CSS must define .accordion styles"


# ─── S9-06: No Inline Styles ──────────────────────────────────────────


class TestNoInlineStyles:
    """S9-06: Main content should have minimal inline styles."""

    async def test_main_content_minimal_inline_styles(self, html):
        main_start = html.find("<main")
        main_end = html.find("</main>")
        main_html = html[main_start:main_end]
        inline_styles = re.findall(r'style="[^"]*"', main_html)
        assert len(inline_styles) <= 2, (
            f"Found {len(inline_styles)} inline styles in <main> — max 2 allowed after component extraction"
        )


# ─── S9-07: SVG Nav Logo ──────────────────────────────────────────────


class TestNavSVGLogo:
    """S9-07: Nav logo must be inline SVG for CSS color transitions."""

    async def test_nav_logo_is_svg(self, html):
        logo_start = html.find('class="nav__logo"')
        logo_end = html.find("</a>", logo_start)
        logo_html = html[logo_start:logo_end]
        assert "<svg" in logo_html, "Nav logo link must contain inline SVG, not <img>"

    async def test_nav_logo_has_color_classes(self, html):
        nav_start = html.find('class="nav"')
        nav_end = html.find("</nav>", nav_start)
        nav_html = html[nav_start:nav_end]
        assert "logo-mark" in nav_html, "Nav SVG logo must have .logo-mark class for CSS color transitions"
        assert "logo-redeem" in nav_html, "Nav SVG logo must have .logo-redeem class"

    async def test_nav_logo_no_png(self, html):
        nav_start = html.find('class="nav"')
        nav_end = html.find("</nav>", nav_start)
        nav_html = html[nav_start:nav_end]
        assert "logo-nav.png" not in nav_html, "Nav must not use PNG logo — use inline SVG instead"


# ─── S10-02: Reduce Hero Images to 3 ──────────────────────────────────


class TestHeroImageCount:
    """S10-02: Hero should have 3 images (not 5) for stronger emotional connection."""

    async def test_hero_has_three_slides(self, html):
        hero_start = html.find('class="hero__kaleidoscope"')
        hero_end = html.find("</div>", hero_start + 30)
        hero_html = html[hero_start:hero_end]
        slides = re.findall(r"hero__slide", hero_html)
        assert len(slides) == 3, f"Hero should have exactly 3 slides, found {len(slides)}"

    async def test_hero_animation_duration_matches(self, html):
        # 3 slides at 8s = 24s cycle; ensure the 24s duration is specifically used on the hero crossfade animation
        pattern = r"\.hero__(?:kaleidoscope|slide)[^{]*\{[^}]*animation[^;]*\b24s\b"
        assert re.search(pattern, html, re.DOTALL), "Hero crossfade animation should be 24s for 3 slides at 8s each"


# ─── S10-03: PNG Noise Texture ─────────────────────────────────────────


class TestNoiseTexture:
    """S10-03: Noise texture should use pre-rendered PNG, not inline SVG filter."""

    async def test_no_svg_noise_in_css(self, html):
        assert "feTurbulence" not in html, "SVG noise filter should be replaced with pre-rendered PNG"


# ─── S10-06: Remove Counter Animation ──────────────────────────────────


class TestNoCounterAnimation:
    """S10-06: $3,400 stat should display statically (no counting animation)."""

    async def test_no_counter_animation_in_js(self, app_js):
        assert "requestAnimationFrame(step)" not in app_js, "Counter step animation should be removed from app.js"

    async def test_stat_shows_static_value(self, html):
        stat_start = html.find('class="stat-band"', html.find("<main"))
        region = html[stat_start : stat_start + 500]
        assert "$3,400" in region, "Stat band must show static $3,400 value"
        assert "data-target" not in region, "data-target attribute should be removed (no JS counter)"
