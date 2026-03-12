# World Cafe UX Overhaul — Vertical Slice TDD Backlog

**Source:** 17-critic design bash (Norman, Krug, Wroblewski, Walter, Zhuo, Ive, Rams, Kare, Monteiro, Mall, Frost, Soueidan, van Schneider, Hische, Vignelli, Scher, Ogilvy) + Phase 3 critic refresh (Norman, Krug, Wroblewski, Walter)

**Quality bar:** Marriott Bonvoy, Stripe, Linear

**Test infrastructure:** `tests/landing/test_server.py` (28 tests, httpx/ASGI) + `tests/landing/test_ux.py` (new, UX fitness functions)

---

## Phase 1-2: Complete (v0.8.0)

<details>
<summary>Sprints 1-8 — 67 of 81 items done (click to expand)</summary>

### Sprint 1: Design Foundation (spacing, tokens, grid)
> "Without mathematical consistency, bolder type and richer color will still feel amateurish" — Vignelli

- [x] S1-01: Define 8px spacing scale as CSS custom properties (--space-1 through --space-11)
- [x] S1-02: Replace all 17 ad-hoc spacing values with scale tokens
- [x] S1-03: Define type scale tokens (--text-xs through --text-2xl)
- [x] S1-04: Unify border-radius to 2 values: --radius-sm (4px), --radius-lg (12px)
- [x] S1-05: Define shadow system: --shadow-sm, --shadow-md, --shadow-lg, --shadow-accent
- [x] S1-06: Add semantic color tokens: --interactive, --interactive-hover, --error, --success
- [x] S1-07: Define transition duration tokens: --duration-fast, --duration-normal, --duration-slow
- [x] S1-08: Add scroll-margin-top: 80px to all section[id] elements

### Sprint 2: Typography Overhaul
> "You picked interesting fonts and then used them in the most boring way possible" — Hische

- [x] S2-01: Hero H1 to clamp(56px, 8vw, 120px), weight 400, opsz 144, letter-spacing -0.04em
- [x] S2-02: H2 to clamp(36px, 4.5vw, 64px), weight 400, opsz 72
- [x] S2-03: H3 switch from Inter to Fraunces at weight 500, size 20px, opsz 24
- [x] S2-04: $3,400 stat to clamp(48px, 8vw, 96px), weight 300 — typographic event
- [x] S2-05: Hero stats: strong as block display, serif 28px, with small 11px labels below
- [x] S2-06: Waitlist headline to clamp(48px, 7vw, 88px), span at 0.7em for size contrast
- [x] S2-07: Eyebrow to 12px, weight 500, letter-spacing 1.5px, warm accent color
- [x] S2-08: Body line-height from 1.65 to 1.55 globally (keep 1.65 for long-form)
- [x] S2-09: Hero subtitle to 20px, weight 400, brighter opacity (0.80)
- [x] S2-10: Load Fraunces weight 300 for display numbers

### Sprint 3: Color & Surface System
> "The page reads like a content wireframe that shipped" — van Schneider

- [x] S3-01: Replace flat #FAF8F5 sections with gradient: linear-gradient(168deg, #F7F4F0, #EDE7DF)
- [x] S3-02: Add --accent-vivid (#4A7FD4) for hover/active states
- [x] S3-03: Hero overlay shift warm: rgba(15,12,10,...) instead of cold navy
- [x] S3-04: CTA button gradient: linear-gradient(135deg, #9B5B2A, #7A4219) + inset highlight
- [x] S3-05: Waitlist kaleidoscope opacity from 0.3 to 0.45, add warm tones
- [x] S3-06: Footer gradient: linear-gradient(180deg, #151515, #0D0D0D)
- [x] S3-07: Remove unused --green, --amber. Consolidate hardcoded #7A4219 into token
- [x] S3-08: Fix hero text contrast: trust line to rgba(255,255,255,0.75), muted to 0.72

### Sprint 4: Feature Cards & Icons
> "The cards are 'less' but not 'better'" — Rams

- [x] S4-01: Feature cards: white bg on warm section, border 1px solid rgba(0,0,0,0.06), elevated shadow
- [x] S4-02: Card hover: translateY(-4px), shadow-lg, smooth transition
- [x] S4-03: Icons from 40x40 to 48x48, minimum stroke-width 2.0, primary shapes 2.5
- [x] S4-04: Add icon background container: 64px, accent-pale bg, 16px radius
- [x] S4-05: Redesign icon 1 (network → dashboard/consolidated view metaphor)
- [x] S4-06: Redesign icon 2 (radar → bell/notification metaphor)
- [x] S4-07: Redesign icon 3 (calendar+clock → value discovery/search metaphor)
- [x] S4-08: Add warm accent fill element to each icon (two-color system)
- [x] S4-09: Feature card h3 benefit-oriented: "See every point" / "Never lose points" / "Get 2-3x more"

### Sprint 5: Page Structure & Rhythm
> "5 consecutive light sections. That is monotonous." — van Schneider

- [x] S5-01: Insert dark statement-break section between What We Do and How It Works
- [x] S5-02: Insert full-bleed photography moment (parallax) between scenarios and FAQ
- [x] S5-03: Merge scenario sections: combine single + grid into one labeled section
- [x] S5-04: Section padding rhythm: 80px (light), 100px (dense), 120px (hero/CTA)
- [x] S5-05: Reduce section count from 10 to 7-8 by merging related content
- [x] S5-06: Step numbers: remove solid fill, use serif 48px light weight numerals
- [x] S5-08: Move hero stats ABOVE the CTA button (build urgency before action)

### Sprint 6: Scenario Visualization
> "The most compelling data is buried in paragraphs" — Scher

- [x] S6-01: Main scenario as visual before/after comparison columns (CASH OUT → TRANSFER)
- [x] S6-02: Large numbers ($1,200 vs $4,800) with visual treatment, not inline text
- [x] S6-03: Scenario card warm gradient background, larger padding, decorative quote mark
- [x] S6-04: Named character in scenarios ("Sarah had 200,000 Marriott points...")
- [x] S6-05: Add "honest" scenario: one where keeping points as cash is the right call

### Sprint 7: Accessibility & Ethics
> "Screen reader users cannot access mobile CTA" — Soueidan

- [x] S7-01: Toggle aria-hidden on mobile CTA in JS (false when visible, true when hidden)
- [x] S7-02: Add privacy policy and terms of service footer links
- [x] S7-03: FAQ regions: add aria-labelledby pointing to trigger buttons
- [x] S7-05: Add prefers-contrast media query (boost muted opacities)
- [x] S7-06: Add forced-colors support (borders on cards, buttons, step numbers)
- [x] S7-07: $3,400 stat: add inline qualifier "for frequent travelers"
- [x] S7-08: Surface pricing in Features section, not just FAQ/waitlist note
- [x] S7-09: Add "who we are" line in footer with founder name
- [x] S7-10: Waitlist consent line: "One email when access opens. No spam."
- [x] S7-11: Structured data: fix price from "0" to represent both tiers honestly

### Sprint 8: Conversion & Copy
> "Every section tells me WHAT. No section shows me what it LOOKS LIKE." — Ogilvy

- [x] S8-01: Hero CTA: change to "Check My Points Free" (3-4 words)
- [x] S8-02: Trust badge: pill shape with shield icon ABOVE the CTA, not below
- [x] S8-03: Hero subtitle: one sentence ("See what your points are actually worth...")
- [x] S8-04: What We Do headline: "Your points are disappearing." (visceral, not generic)
- [x] S8-05: FAQ post-section CTA: "Still have questions?" + email + waitlist button
- [x] S8-06: Waitlist urgency: "Limited Early Access" eyebrow

</details>

---

## Phase 3: Vertical Slice TDD Implementation

**Methodology:** Each slice is RED → GREEN → REFACTOR. Tests written first in `tests/landing/test_ux.py` (HTML content assertions via httpx) or `tests/landing/test_server.py` (server behavior). Each slice touches HTML + CSS + JS (if needed) + test. Independently deployable.

**Critic sources:** Norman (N), Krug (K), Wroblewski (W), Walter (Wa)

---

### VS-01: Mobile Navigation ⬡ [P0, K]
> "Nav links hidden on mobile with no alternative" — Krug

**RED:** Test that index HTML contains a `<button>` with class `nav__toggle` and `aria-label="Menu"`. Test that `.nav__links` has a mobile-hidden class. Test that app.js contains toggle handler.
**GREEN:** Add hamburger button (3-line SVG, 44x44 touch target), slide-in nav drawer on mobile `<768px`. CSS: `transform: translateX(100%)` → `translateX(0)` on `.nav--open`. JS: toggle class + aria-expanded + focus trap.
**REFACTOR:** Extract nav toggle into reusable pattern.

- [x] VS-01a: Add `nav__toggle` button with hamburger SVG icon (HTML)
- [x] VS-01b: Add mobile nav drawer CSS (slide-in, backdrop blur)
- [x] VS-01c: Add nav toggle JS handler with focus trap + escape key
- [x] VS-01d: Test: `nav__toggle` exists with correct ARIA, links hidden on mobile intent

### VS-02: Email Input Mobile Optimization ⬡ [P0, W]
> "Missing inputmode, enterkeyhint, autocapitalize, spellcheck" — Wroblewski

**RED:** Test that `<input id="waitlist-email">` has attributes: `inputmode="email"`, `enterkeyhint="join"`, `autocapitalize="off"`, `spellcheck="false"`, `autocomplete="email"`.
**GREEN:** Add 5 attributes to the email input element.
**REFACTOR:** None needed — single element change.

- [x] VS-02a: Add mobile-optimized attributes to waitlist email input
- [x] VS-02b: Test: all 5 input attributes present in HTML response

### VS-03: Waitlist Input Focus States ⬡ [P0, W + S7-04]
> "Fix waitlist form stacking on mobile" — Wroblewski

**RED:** Test that CSS contains `:focus-visible` rule for `.waitlist__input`. Test that mobile input has visible border.
**GREEN:** Add `:focus` base style (subtle ring), `:focus:not(:focus-visible)` reset, `:focus-visible` prominent ring. Add `border: 1px solid rgba(255,255,255,0.2)` to mobile input. Increase input height to 52px on mobile.
**REFACTOR:** Consolidate with existing focus-visible pattern in `:root`.

- [x] VS-03a: Add focus-visible pattern to waitlist input (CSS)
- [x] VS-03b: Add visible mobile input border + 52px height at `<768px`
- [x] VS-03c: Test: CSS contains `.waitlist__input` focus-visible rules

### VS-04: Hero CTA Visual Dominance ⬡ [P0, K]
> "CTA button blends into the hero composition" — Krug

**RED:** Test that hero CTA has class `btn--hero` (distinct from nav CTA). Test CSS contains `@keyframes cta-glow`.
**GREEN:** Add glow box-shadow to hero CTA: `0 0 0 1px rgba(196,135,59,0.3), 0 4px 20px rgba(140,77,31,0.4)`. Add subtle pulse animation after 3s delay. Increase padding to 18px 44px, font-size 17px.
**REFACTOR:** Ensure `prefers-reduced-motion` disables the pulse.

- [x] VS-04a: Add `btn--hero` class with glow shadow + enlarged padding
- [x] VS-04b: Add `@keyframes cta-glow` pulse animation with 3s delay
- [x] VS-04c: Test: `btn--hero` class exists on hero CTA, animation defined in CSS

### VS-05: Headline Aspiration ⬡ [P0, Wa]
> "Leading with guilt — 'Stop wasting' is negative framing" — Walter

**RED:** Test that `<h1>` contains a `<span>` child with warm accent styling. Test the headline has two emotional beats (negative → positive arc).
**GREEN:** Add second line to H1: `<span>Start using them.</span>` in `--accent-warm-light`. CSS: `h1 span { color: var(--accent-warm-light); display: block; font-size: 0.7em; margin-top: 8px; }`.
**REFACTOR:** Verify contrast ratio of warm-light on dark hero background.

- [x] VS-05a: Add aspirational `<span>` to H1 (HTML + CSS)
- [x] VS-05b: Test: H1 contains `<span>` child, not just flat text

### VS-06: Program Logo Trust Bar ⬡ [P0, Wa + S5-07]
> "Absence of partner logos is the page's most conspicuous gap" — Walter

**RED:** Test for element with class `logo-bar` between hero and first content section. Test it contains at least 4 program name references. Test logos use `filter: grayscale(1) opacity(0.5)` for subtlety.
**GREEN:** Add full-width strip with text-based program names (Marriott Bonvoy, Hilton Honors, Chase Ultimate Rewards, Amex Membership Rewards, United MileagePlus). Styled as subtle, grayscale, evenly spaced. Mobile: horizontal scroll with `overflow-x: auto`.
**REFACTOR:** Use `--font-sans` at `--text-xs`, letter-spacing for premium feel.

- [x] VS-06a: Add `.logo-bar` section with 5+ program names (HTML + CSS)
- [x] VS-06b: Mobile horizontal scroll with fade-out edges
- [x] VS-06c: Test: `logo-bar` element exists with program name content

### VS-07: $3,400 Stat Dark Band ⬡ [P0, N]
> "The single most conversion-driving number is buried in body text" — Norman

**RED:** Test for a `section` or `div` with class `stat-band` using `--surface-inverse` background. Test the stat value is displayed at `clamp(56px, 8vw, 96px)` scale.
**GREEN:** Extract $3,400 into its own full-width dark band (~200px tall). Background: `var(--surface-inverse)`. Stat in `--accent-warm-light` at display scale. Labels: "Average left on the table each year" above, "per household" below.
**REFACTOR:** Move counter animation to target the new element. Ensure `prefers-reduced-motion` shows final value.

- [x] VS-07a: Create `.stat-band` dark section with extracted stat (HTML + CSS)
- [x] VS-07b: Retarget counter animation JS to new element
- [x] VS-07c: Test: `stat-band` section exists with dark background class, stat content present

### VS-08: Hero Mobile Viewport Optimization ⬡ [P0, W]
> "Hero consumes too much viewport on short mobile screens" — Wroblewski

**RED:** Test CSS contains `@media (max-height: 700px)` rules for `.hero`. Test hero padding reduces on short viewports.
**GREEN:** Add `@media (max-height: 700px) and (max-width: 768px)` with reduced hero padding (80px top vs 120px), smaller H1 floor (44px vs 56px), tighter stat spacing.
**REFACTOR:** Test against iPhone SE (375x667) viewport dimensions.

- [x] VS-08a: Add short-viewport media query for hero section
- [x] VS-08b: Test: CSS contains max-height media query for hero

### VS-09: Fade-In Animation Timing ⬡ [P0, N]
> "Elements pop in too late, creating jarring jumps during scroll" — Norman

**RED:** Test that `.fade-in` CSS has `transform: translateY(12px)` (not 20px+). Test IntersectionObserver rootMargin is `0px 0px -20px 0px` (not -40px).
**GREEN:** Reduce translateY from 20px to 12px for subtler entrance. Change rootMargin to -20px for earlier trigger. Add `will-change: transform, opacity` for GPU acceleration.
**REFACTOR:** Verify `prefers-reduced-motion` still skips all animation.

- [x] VS-09a: Tune fade-in transform distance and observer trigger threshold
- [x] VS-09b: Test: fade-in CSS uses refined values

### VS-10: Price Anchoring ⬡ [P1, S8-07]
> "$200+ concierge vs $9.99/month RedeemFlow" — Ogilvy

**RED:** Test that Features section contains text mentioning both "$200+" and "$9.99".
**GREEN:** Add a comparison line in the pricing-visible area: "Full concierge services charge $200+/year. RedeemFlow: $9.99/month — or free to start."
**REFACTOR:** Ensure structured data pricing stays consistent.

- [x] VS-10a: Add price comparison copy to Features section
- [x] VS-10b: Test: price anchoring text present in HTML

### VS-11: Touch-Friendly FAQ Accordion ⬡ [P1, W]
> "FAQ touch targets below 44px minimum" — Wroblewski

**RED:** Test that `.faq-item__trigger` has `min-height: 48px` in CSS. Test padding provides adequate touch area.
**GREEN:** Increase FAQ trigger padding to `16px 20px` (from current). Set `min-height: 48px`. Add `:active` feedback state for touch.
**REFACTOR:** Apply to generic `.accordion` class (S9-04 prep).

- [x] VS-11a: Increase FAQ trigger touch targets to 48px minimum
- [x] VS-11b: Test: FAQ trigger CSS has min-height >= 48px

### VS-12: Waitlist Success State Personality ⬡ [P1, Wa]
> "Zero delight moments — not even on form success" — Walter

**RED:** Test that `#waitlist-success` contains an SVG or emoji element. Test success message has warm, personal copy (not just "You're on the list").
**GREEN:** Add checkmark SVG animation, warm copy: "You're in. We'll send one email when early access opens — pinky promise." Add a share prompt: "Know someone sitting on unused points?"
**REFACTOR:** Ensure success state is `role="alert"` or `aria-live="polite"`.

- [x] VS-12a: Redesign success state with personality (SVG + warm copy)
- [x] VS-12b: Test: success element contains SVG, personal copy, share prompt

### VS-13: 640px Tablet Breakpoint ⬡ [P1, W]
> "Missing intermediate breakpoint — content jumps from 1-col to 3-col" — Wroblewski

**RED:** Test CSS contains `@media (min-width: 640px)` rules. Test feature cards use 2-col grid at 640px.
**GREEN:** Add breakpoint at 640px: feature cards 2-col, step cards 2-col (third wraps), scenario grid 2-col. Adjust section padding for tablet: 64px.
**REFACTOR:** Ensure 640px + 768px + 1024px form coherent responsive system.

- [x] VS-13a: Add 640px breakpoint with 2-col layouts
- [x] VS-13b: Test: CSS contains 640px media query rules

### VS-14: Section Header Amber Accent ⬡ [P1, K]
> "No visual signpost between sections" — Krug

**RED:** Test that `.eyebrow` class has a left border or accent element. Test all section eyebrows use consistent `.eyebrow` class.
**GREEN:** Add `border-left: 3px solid var(--accent-warm)` to `.eyebrow` with `padding-left: 12px`. Creates a warm vertical accent bar as section signpost.
**REFACTOR:** Verify all 6+ eyebrow instances use the unified class (S9-03 already started this).

- [x] VS-14a: Add amber left-border accent to `.eyebrow` class
- [x] VS-14b: Test: eyebrow class has border-left styling

### VS-15: How It Works Cognitive Load Reduction ⬡ [P1, N]
> "Step descriptions are 45 words each — users won't parse during a skim" — Norman

**RED:** Test that each `.step__text` or equivalent contains fewer than 25 words.
**GREEN:** Cut each step to 15-20 words. Move the "$4,000 flight" example to scenario section. Add dashed connector line between step numbers on desktop.
**REFACTOR:** Verify step numbers have hover micro-interaction.

- [x] VS-15a: Trim step descriptions to 15-20 words each
- [x] VS-15b: Add visual connector between step numbers (dashed line)
- [x] VS-15c: Test: step descriptions under 25 words each

### VS-16: Aspirational Waitlist Closing ⬡ [P1, Wa]
> "Waitlist section ends with a thud — no emotional send-off" — Walter

**RED:** Test waitlist section contains an image or decorative SVG element.
**GREEN:** Add a subtle travel-themed decorative element (palm tree silhouette SVG or gradient sunset band) below the form. Use `opacity: 0.15` for subtlety. Warm gradient bottom border on the section.
**REFACTOR:** Ensure decorative element is `aria-hidden="true"`.

- [x] VS-16a: Add aspirational decorative element to waitlist section
- [x] VS-16b: Test: waitlist section contains decorative SVG with aria-hidden

---

### Remaining from Original Sprints (unchanged)

#### Sprint 9: Component Architecture
> "Every section is bespoke. If you built a second page, you'd copy-paste everything." — Frost

- [x] S9-01: Extract Button atom with size variants (--sm, --md, --lg, --block)
- [x] S9-02: Extract Section Header molecule (eyebrow + h2, replaces 6 inline styles)
- [x] S9-04: Rename FAQ accordion to generic .accordion for reuse
- [x] S9-06: Replace inline styles with utility/component classes
- [x] S9-07: Replace nav PNG logo with inline SVG for CSS color transitions

#### Sprint 10: Performance & Polish
> "Five JPGs totaling ~1.45MB. No responsive sizes, no modern formats." — Rams

- [x] S10-01: Convert hero images to WebP, add `<picture>` with srcset (640w, 1024w, 1920w)
- [x] S10-02: Reduce hero images from 5 to 3 (8s per image = more emotional connection)
- [x] S10-03: Replace SVG noise texture with pre-rendered PNG (hardware acceleration)
- [x] S10-05: Extract critical CSS inline (~700 lines), move rest to external stylesheet (1063 lines)
- [x] S10-06: Remove counter animation on $3,400 (adds no info, GPU cost)
- [x] S10-08: Playwright visual regression tests: desktop (1440px) + mobile (375px) — 14 tests

---

### P2 Icebox (future consideration)

| ID | Item | Critic | Effort |
|----|------|--------|--------|
| ICE-01 | Savings calculator interactive widget | Norman | L |
| ICE-02 | Scroll progress bar at viewport top | Wroblewski | M |
| ICE-03 | Horizontal-scroll feature cards on tablet | Wroblewski | S |
| ICE-04 | Section progress sidebar on desktop | Krug | M |
| ICE-05 | "Savings reveal" two-stage animation ($1,200 strikethrough → $3,400) | Walter | M |
| ICE-06 | Collapse "What We Do" on mobile (progressive disclosure) | Wroblewski | M |
| ICE-07 | Travel imagery injection below fold (blurred backgrounds) | Norman | M |
| ICE-08 | Emotional contrast between sections (color-arc design) | Norman | M |
| ICE-09 | Step number hover micro-interactions | Walter | S |
| ICE-10 | Shorten FAQ answers by 30% | Krug | S |

---

## Progress Summary

| Category | Sprint(s) | Total | Done | Remaining |
|----------|-----------|-------|------|-----------|
| Design System Foundation | 1 | 8 | 8 | 0 |
| Typography | 2 | 10 | 10 | 0 |
| Color & Surface | 3 | 8 | 8 | 0 |
| Components (cards, icons) | 4 | 9 | 9 | 0 |
| Page Structure & Rhythm | 5 | 8 | 8 | 0 |
| Content Visualization | 6 | 5 | 5 | 0 |
| Accessibility & Ethics | 7 | 11 | 11 | 0 |
| Conversion Copy | 8 | 7 | 7 | 0 |
| **Phase 3 Vertical Slices** | VS | **16** | **16** | **0** |
| Component Architecture | 9 | 5 | 5 | 0 |
| Performance & Testing | 10 | 6 | 6 | 0 |
| P2 Icebox | — | 10 | — | — |
| **TOTAL (active)** | | **93** | **93** | **0** |

## Vertical Slice Execution Order

```
Session A (P0 — Mobile & Forms):     VS-01 → VS-02 → VS-03 → VS-08
Session B (P0 — Hero & Conversion):  VS-04 → VS-05 → VS-06 → VS-07 → VS-09
Session C (P1 — Content & Layout):   VS-10 → VS-11 → VS-13 → VS-14 → VS-15
Session D (P1 — Delight & Polish):   VS-12 → VS-16 + Sprint 9 items
Session E (Performance):             Sprint 10 items
```

Each session: write test_ux.py tests first (RED), implement (GREEN), verify with Playwright screenshot (REFACTOR). Ship when green.
