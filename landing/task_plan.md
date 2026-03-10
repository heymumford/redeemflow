# World Cafe UX Overhaul — 10-Sprint MECE Backlog

**Source:** 17-critic design bash (Norman, Krug, Wroblewski, Walter, Zhuo, Ive, Rams, Kare, Monteiro, Mall, Frost, Soueidan, van Schneider, Hische, Vignelli, Scher, Ogilvy)

**Quality bar:** Marriott Bonvoy, Stripe, Linear

## Sprint 1: Design Foundation (spacing, tokens, grid)
> "Without mathematical consistency, bolder type and richer color will still feel amateurish" — Vignelli

- [x] S1-01: Define 8px spacing scale as CSS custom properties (--space-1 through --space-11)
- [x] S1-02: Replace all 17 ad-hoc spacing values with scale tokens
- [x] S1-03: Define type scale tokens (--text-xs through --text-2xl)
- [x] S1-04: Unify border-radius to 2 values: --radius-sm (4px), --radius-lg (12px)
- [x] S1-05: Define shadow system: --shadow-sm, --shadow-md, --shadow-lg, --shadow-accent
- [x] S1-06: Add semantic color tokens: --interactive, --interactive-hover, --error, --success
- [x] S1-07: Define transition duration tokens: --duration-fast, --duration-normal, --duration-slow
- [x] S1-08: Add scroll-margin-top: 80px to all section[id] elements

## Sprint 2: Typography Overhaul
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

## Sprint 3: Color & Surface System
> "The page reads like a content wireframe that shipped" — van Schneider

- [x] S3-01: Replace flat #FAF8F5 sections with gradient: linear-gradient(168deg, #F7F4F0, #EDE7DF)
- [x] S3-02: Add --accent-vivid (#4A7FD4) for hover/active states
- [x] S3-03: Hero overlay shift warm: rgba(15,12,10,...) instead of cold navy
- [x] S3-04: CTA button gradient: linear-gradient(135deg, #9B5B2A, #7A4219) + inset highlight
- [x] S3-05: Waitlist kaleidoscope opacity from 0.3 to 0.45, add warm tones
- [x] S3-06: Footer gradient: linear-gradient(180deg, #151515, #0D0D0D)
- [x] S3-07: Remove unused --green, --amber. Consolidate hardcoded #7A4219 into token
- [x] S3-08: Fix hero text contrast: trust line to rgba(255,255,255,0.75), muted to 0.72

## Sprint 4: Feature Cards & Icons
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

## Sprint 5: Page Structure & Rhythm
> "5 consecutive light sections. That is monotonous." — van Schneider

- [x] S5-01: Insert dark statement-break section between What We Do and How It Works
- [x] S5-02: Insert full-bleed photography moment (parallax) between scenarios and FAQ
- [x] S5-03: Merge scenario sections: combine single + grid into one labeled section
- [x] S5-04: Section padding rhythm: 80px (light), 100px (dense), 120px (hero/CTA)
- [x] S5-05: Reduce section count from 10 to 7-8 by merging related content
- [x] S5-06: Step numbers: remove solid fill, use serif 48px light weight numerals
- [ ] S5-07: Add program logo bar (Marriott, Hilton, Chase, Amex) as credibility strip
- [x] S5-08: Move hero stats ABOVE the CTA button (build urgency before action)

## Sprint 6: Scenario Visualization
> "The most compelling data is buried in paragraphs" — Scher

- [x] S6-01: Main scenario as visual before/after comparison columns (CASH OUT → TRANSFER)
- [x] S6-02: Large numbers ($1,200 vs $4,800) with visual treatment, not inline text
- [x] S6-03: Scenario card warm gradient background, larger padding, decorative quote mark
- [x] S6-04: Named character in scenarios ("Sarah had 200,000 Marriott points...")
- [x] S6-05: Add "honest" scenario: one where keeping points as cash is the right call

## Sprint 7: Accessibility & Ethics
> "Screen reader users cannot access mobile CTA" — Soueidan

- [x] S7-01: Toggle aria-hidden on mobile CTA in JS (false when visible, true when hidden)
- [x] S7-02: Add privacy policy and terms of service footer links
- [x] S7-03: FAQ regions: add aria-labelledby pointing to trigger buttons
- [ ] S7-04: Fix waitlist input focus: use :focus + :focus:not(:focus-visible) pattern
- [x] S7-05: Add prefers-contrast media query (boost muted opacities)
- [x] S7-06: Add forced-colors support (borders on cards, buttons, step numbers)
- [x] S7-07: $3,400 stat: add inline qualifier "for frequent travelers"
- [x] S7-08: Surface pricing in Features section, not just FAQ/waitlist note
- [x] S7-09: Add "who we are" line in footer with founder name
- [x] S7-10: Waitlist consent line: "One email when access opens. No spam."
- [x] S7-11: Structured data: fix price from "0" to represent both tiers honestly

## Sprint 8: Conversion & Copy
> "Every section tells me WHAT. No section shows me what it LOOKS LIKE." — Ogilvy

- [x] S8-01: Hero CTA: change to "Check My Points Free" (3-4 words)
- [x] S8-02: Trust badge: pill shape with shield icon ABOVE the CTA, not below
- [x] S8-03: Hero subtitle: one sentence ("See what your points are actually worth...")
- [x] S8-04: What We Do headline: "Your points are disappearing." (visceral, not generic)
- [x] S8-05: FAQ post-section CTA: "Still have questions?" + email + waitlist button
- [x] S8-06: Waitlist urgency: "Limited Early Access" eyebrow
- [ ] S8-07: Price anchoring in body: "$200+ concierge vs $149/year RedeemFlow"

## Sprint 9: Component Architecture
> "Every section is bespoke. If you built a second page, you'd copy-paste everything." — Frost

- [ ] S9-01: Extract Button atom with size variants (--sm, --md, --lg, --block)
- [ ] S9-02: Extract Section Header molecule (eyebrow + h2, replaces 6 inline styles)
- [x] S9-03: Unify eyebrow class across footer col titles, citations header
- [ ] S9-04: Rename FAQ accordion to generic .accordion for reuse
- [x] S9-05: Extract container width variants: --narrow (720px), --tight (560px)
- [ ] S9-06: Replace inline styles with utility/component classes
- [ ] S9-07: Replace nav PNG logo with inline SVG for CSS color transitions

## Sprint 10: Performance & Polish
> "Five JPGs totaling ~1.45MB. No responsive sizes, no modern formats." — Rams

- [ ] S10-01: Convert hero images to WebP, add <picture> with srcset (640w, 1024w, 1920w)
- [ ] S10-02: Reduce hero images from 5 to 3 (8s per image = more emotional connection)
- [ ] S10-03: Replace SVG noise texture with pre-rendered PNG (hardware acceleration)
- [x] S10-04: Add font-display: swap to Google Fonts URL
- [ ] S10-05: Extract critical CSS inline (~400 lines), move rest to external stylesheet
- [ ] S10-06: Remove counter animation on $3,400 (adds no info, GPU cost)
- [x] S10-07: Slow hero crossfade to 40s total (vs current 30s)
- [ ] S10-08: Playwright visual regression tests: desktop (1440px) + mobile (375px)

## Progress Summary
| Category | Sprint(s) | Total | Done | Remaining |
|----------|-----------|-------|------|-----------|
| Design System Foundation | 1 | 8 | 8 | 0 |
| Typography | 2 | 10 | 10 | 0 |
| Color & Surface | 3 | 8 | 8 | 0 |
| Components (cards, icons) | 4 | 9 | 9 | 0 |
| Page Structure & Rhythm | 5 | 8 | 7 | 1 |
| Content Visualization | 6 | 5 | 5 | 0 |
| Accessibility & Ethics | 7 | 11 | 10 | 1 |
| Conversion Copy | 8 | 7 | 6 | 1 |
| Component Architecture | 9 | 7 | 2 | 5 |
| Performance & Testing | 10 | 8 | 2 | 6 |
| **TOTAL** | | **81** | **67** | **14** |
