# RedeemFlow Product Plan — CL-0feb6c6563

**Lens ID:** CL-0feb6c6563
**Date:** 2026-03-09
**Research basis:** 12 parallel research agents, ~300 web sources synthesized
**Mode:** standard (full UDPETM cycle)

---

## SUMMARY (Phase 1: UNDERSTAND)

### What RedeemFlow Is

RedeemFlow is the first women-first travel rewards optimization platform. It fills an
unoccupied market niche: no existing product combines travel points optimization with
female-first design, community pooling for charitable impact, or state-by-state women-led
charity partner networks.

### Market Opportunity

| Metric | Value | Source |
|--------|-------|--------|
| Women-owned businesses in US | 14.5M (39.2% of all businesses) | Wells Fargo 2025 |
| New businesses started by women (2024) | 49% of all new businesses | Gusto 2025 |
| Women as share of business travelers | ~45% | Expensify 2024 |
| Women as share of solo travelers | 75-85% | Multiple sources |
| Women making travel decisions | 82% | Skift 2024 |
| Average small business monthly card spend | $23,000 | Ramp 2025 |
| Solo travel market | $482B (2024), projected $1.07T by 2030 | Grand View Research |
| Women-focused travel rewards tools | **ZERO** | Competitive analysis |

### Why Now

1. **Regulatory tailwind**: DOT/CFPB joint probe into airline rewards programs (Sep 2024). Protect Your Points Act (S. 5272) would mandate transparency. CFPB Circular 2024-07 creates enforcement risk for deceptive programs. Consumer-first platforms benefit.
2. **Market gap confirmed**: Ellevest does investing. Sequin does debit rewards. NomadHer does travel community. Nobody combines points optimization + women-first + charity.
3. **API infrastructure mature**: Pledge.to and Change (getchange.io) provide production-ready donation APIs with 50-state commercial co-venturer compliance.
4. **Community pooling unoccupied**: Family pooling exists (United, Aeroplan, BA, JetBlue). Individual-to-charity exists (every major program). But pooling points from unrelated people toward shared community goals does not exist as a consumer product.

### Key Research Findings

**Women & Travel Rewards:**
- Women-owned startups lean on credit cards MORE heavily than men-owned firms for financing
- Women book flights 2 days earlier than men, saving ~2% per ticket
- 41% of female business travelers extend trips for leisure (vs 34% of men)
- 83% of female business travelers experienced safety-related concerns
- Only 27% of companies have female-specific travel policies
- Learning points optimization serves as a gateway to broader financial literacy for women

**Travel Points Landscape:**
- Programs devalue 5-15% per year on average; structural shift to dynamic pricing accelerating
- $9.99/month ($99.99/year) is the proven price point for travel reward tools
- Free calculators are the #1 SEO acquisition channel (every competitor uses them)
- The "Big 6" transferable currencies: Chase UR, Amex MR, Citi TY, Capital One, Bilt, Wells Fargo
- Transfer bonuses (20-50% extra) appear monthly across ecosystems
- Points donated to charity are NOT tax-deductible to consumers (IRS treats as rebate)

**Charity Infrastructure:**
- 13 organizations verified with all-50-state presence
- 10 anchor partners guarantee every state, every category
- API platforms (Pledge.to, Change, Benevity) handle donation processing + compliance
- Kind Traveler model proves "give to unlock" works in travel
- B1G1 micro-impact units enable measurable reporting

---

## LENS_SPEC_YAML (Phase 2: DESIGN)

### Product Tiers

```
FREE TIER (Zero Barrier)
├── Points Value Calculator (CPP for all major programs)
├── Best Card Per Purchase Recommender
├── Transfer Ratio Explorer (all Big 6 ecosystems)
├── Devaluation Alert Feed (public, delayed)
├── Savings Dashboard ("You could save $X this month")
├── Basic Sweet Spot Directory
└── Community Forum Access

PREMIUM TIER ($9.99/month or $99.99/year)
├── Everything in Free, plus:
├── Real-Time Devaluation Alerts (push/SMS)
├── Personalized Optimization Engine (your balances → your best moves)
├── Transfer Bonus Tracker + Notifications
├── Award Availability Search (via Seats.aero integration)
├── Bank vs Burn Advisor (AI-powered timing recommendations)
├── Auto-Activate Credit Card Offers
├── Points Expiration Tracker + Reminders
├── Charity Partner Directory (browse by state/category)
├── One-Click Donate to Charity of Choice
└── Premium Community Access

PRO TIER ($24.99/month or $249.99/year)
├── Everything in Premium, plus:
├── Business Travel Optimizer (multi-card stacking advisor)
├── Team Points Dashboard (small business, up to 10 cards)
├── Conference Travel Planner (points-optimized)
├── Community Points Pool (create/join pools for charity)
├── Auto-Donate Expiring Points (configurable rules)
├── Impact Dashboard (your donations, your community's impact)
├── Concierge Booking Assistance (complex itineraries)
├── API Access (for developers/businesses)
├── Tax Season Export (donation receipts, spending summaries)
└── Exclusive: Women Founders Travel Network
```

### Curated Product Ideas — Complete List

#### FREE TIER FEATURES (Value for Everyone)

| # | Feature | Description | Competitive Advantage |
|---|---------|-------------|----------------------|
| F1 | **Points Value Calculator** | Enter any program balance → see current CPP valuation from 4 sources (OMAAT, TPG, NerdWallet, Upgraded Points) with min/median/max | Aggregates 4 valuations; competitors show only their own |
| F2 | **Savings Dashboard** | "Your 50,000 Chase UR points are worth $850-$1,000 for travel, but only $500 as cash back. You're leaving $350-$500 on the table." | Quantifies the gap to motivate optimization |
| F3 | **Best Card Recommender** | Enter a merchant → see which card in your wallet earns the most | Similar to CardPointers but free and web-based |
| F4 | **Transfer Ratio Explorer** | Interactive graph showing all transfer paths between Big 6 currencies and 40+ airline/hotel programs with current ratios | Visual, NetworkX-powered; competitors have static lists |
| F5 | **Sweet Spot Directory** | Curated list of best-value redemptions (ANA First via Virgin at 60K, Qatar Qsuite via AA at 70K, Hyatt all-inclusives at 20K) | Free content that drives SEO and establishes authority |
| F6 | **Devaluation News Feed** | Aggregated feed of program changes, devaluations, new offers (delayed 24hr from premium) | Builds habit; premium gets real-time |
| F7 | **New User Point Strategy Quiz** | "Answer 5 questions → get your personalized starter strategy" | Conversion tool; captures user profile for premium upsell |
| F8 | **Annual Fee Calculator** | Enter your cards → see net cost after credits, points value, and break-even spend | Solves the #1 pain point for startup founders |

#### PREMIUM TIER FEATURES ($9.99/month)

| # | Feature | Description | Competitive Advantage |
|---|---------|-------------|----------------------|
| P1 | **Personalized Optimization Engine** | Connect your loyalty accounts (via AwardWallet API) → AI analyzes your balances, spending, travel patterns → recommends best moves | Personalized; competitors are generic |
| P2 | **Real-Time Alert System** | Push/SMS alerts for: transfer bonuses, devaluation announcements, sweet spot availability, expiring points | MaxRewards charges $108/yr for less |
| P3 | **Bank vs Burn Advisor** | AI-powered timing engine: "Transfer your 80K Amex MR to ANA now — 30% bonus active + premium cabin availability to Tokyo in October" | Nobody offers personalized timing advice |
| P4 | **Award Availability Search** | Search award flights across programs (via Seats.aero API) with "your points can book this" overlay | Combines search + personal balance context |
| P5 | **Transfer Bonus Tracker** | Dashboard showing all active transfer bonuses across Big 6 currencies, with your personal "action items" | Frequent Miler tracks these; nobody personalizes them |
| P6 | **Points Expiration Manager** | Tracks all expiration policies per program; sends alerts 90/60/30 days before; suggests activity to reset clock | AwardWallet charges $49.99 for this alone |
| P7 | **Credit Card Offer Auto-Activate** | Auto-enroll in Amex Offers, Chase Offers, Citi Merchant Offers | MaxRewards' premium feature; we include it |
| P8 | **Charity Partner Directory** | Browse women-led charities by state and category; see impact metrics; one-click donate points | **Industry first** |
| P9 | **One-Click Point Donation** | Select charity → enter points amount → donation processed via Pledge.to/Change API | **Industry first** for self-service point-to-charity |
| P10 | **Women's Travel Safety Layer** | Hotel safety scores, neighborhood ratings, "women travelers recommend" badges on properties | Addresses the 83% safety concern gap |

#### PRO TIER FEATURES ($24.99/month)

| # | Feature | Description | Competitive Advantage |
|---|---------|-------------|----------------------|
| R1 | **Business Travel Optimizer** | Multi-card stacking advisor for business expenses: "Put your SaaS on Ink Cash (5x), advertising on Amex Gold (4x), travel on CSR (3x)" | Built for the 14.5M women business owners |
| R2 | **Team Points Dashboard** | Track up to 10 employee cards; see consolidated earning; recommend card assignments per expense category | Brex/Ramp do this for cash back; nobody for points |
| R3 | **Conference Travel Planner** | Enter conference dates/location → see best redemption options from your balances → book-ready recommendations | Built for the dense women's founder conference calendar |
| R4 | **Community Points Pool** | Create a pool → invite members → set a charity goal → members pledge points → goal reached → donation executed | **Industry first** — nobody does community pooling for charity |
| R5 | **Auto-Donate Expiring Points** | Configure rules: "If my Marriott points will expire in 60 days and I have no travel plans, auto-donate to [selected charity]" | **Industry first** — prevents point waste + generates impact |
| R6 | **Impact Dashboard** | Personal: "You've donated $450 to Girls Who Code this year." Community: "RedeemFlow users have donated $12,000 to women-led orgs in Ohio." | Kind Traveler-style impact reporting |
| R7 | **Concierge Booking** | Complex itinerary assistance from human experts (discount vs. point.me's $260/yr tier) | Competes with point.me Premium at lower price |
| R8 | **API Access** | Developer API for points data, valuations, transfer ratios | Only AwardWallet and Seats.aero offer APIs; we open a third |
| R9 | **Women Founders Travel Network** | Private community: verified women business owners sharing strategies, deals, travel companions, local recommendations | Combines Wanderful ($249/yr) community value into Pro tier |
| R10 | **Multigenerational Trip Planner** | Plan trips for 3+ travelers across different loyalty programs; optimize who books what for maximum collective value | 47% of 2025 travelers opted multigenerational; nobody tools this |
| R11 | **Subscription Charity Alignment** | Choose a subscription "flavor": "My $24.99/mo subscription benefits [Girls Who Code / Junior League / Best Friends / AAUW]" with 5% of subscription donated | **Industry first** — subscription revenue directly funds women-led programs |

### The 50-State Charity Partner Network

#### Anchor Partners (Guaranteed All-50-State Coverage)

| # | Organization | Category | Coverage | Accepts Donations | Digital Portal |
|---|-------------|----------|----------|-------------------|----------------|
| 1 | **SBA Women's Business Centers** | Business | 50/50 states, 152+ centers | Via host nonprofits | sba.gov |
| 2 | **Girl Scouts of the USA** | Youth | 50/50 states, 111 councils | 501(c)(3) | girlscouts.org |
| 3 | **Girls Who Code** | Youth/STEM | 50/50 states, 5,700+ clubs | 501(c)(3) | girlswhocode.com |
| 4 | **Junior League (AJLI)** | Community | 50/50 states, ~295 chapters | 501(c)(3) | thejuniorleagueinternational.org |
| 5 | **League of Women Voters** | Civic | 50/50 states, 800+ leagues | 501(c)(3) Ed Fund | lwv.org |
| 6 | **AAUW** | Education | 50/50 states, ~1,000 branches | 501(c)(3) | aauw.org |
| 7 | **GFWC** | Community | 50/50 states, ~2,300 clubs | 501(c)(3) | gfwc.org |
| 8 | **National PTA** | Schools | 50/50 states, 4M members | 501(c)(3) | pta.org |
| 9 | **Best Friends Animal Society** | Animal Welfare | 50/50 states, 5,500+ network partners | 501(c)(3) | bestfriends.org |
| 10 | **Habitat for Humanity Women Build** | Community | 50/50 states, 1,100+ affiliates | 501(c)(3) | habitat.org |

#### Supplementary Partners (Strong Coverage)

| Organization | Category | Coverage | Notes |
|-------------|----------|----------|-------|
| WBENC (14 RPOs) | Business | 50/50 | Certification-focused |
| YWCA | Community | ~45-48/50 | 194 associations |
| Zonta International | Community | 46/50 | 300+ US clubs |
| P.E.O. Sisterhood | Education | 50/50 | $398M+ distributed |
| Girls Inc. | Youth | ~30/50 | 81+ affiliates |
| Dress for Success | Workforce | ~35-40/50 | 130+ affiliates |
| DV Coalitions (NNEDV) | Safety | 50/50 + territories | 2,200+ shelters |
| Women's Funding Network | Grants | 120+ funds | State-level women's foundations |
| United Way Women United | Multi | 50/50 via United Way | 70,000+ members |
| Big Brothers Big Sisters | Youth | 50/50 | 230+ agencies |

#### State Coverage Matrix

Every state guaranteed minimum 10 partner organizations across categories:
- **Business**: SBA WBC + WBENC RPO + NAWBO (where chapter exists)
- **Youth**: Girl Scouts + Girls Who Code + Girls Inc. (where affiliate exists)
- **Community**: Junior League + LWV + GFWC + YWCA + Zonta
- **Education**: AAUW + P.E.O. + National PTA
- **Animal Welfare**: Best Friends network partner + state-level women-led rescues
- **Arts**: Women's Caucus for Art (23 states) + state arts council women's programs
- **Safety**: State DV coalition + local shelters

**Gap: Arts/Culture** is the weakest category (no single org covers 50 states). Supplemented by:
- Women's Caucus for Art (23 chapters)
- National Museum of Women in the Arts (27 volunteer committees)
- State-by-state curation of women-led galleries, theater companies, cooperatives

### Donation Pipeline Architecture

```
User selects charity → Points converted to dollar value at program's CPP →
→ Change/Pledge.to API processes donation → Cash sent to 501(c)(3) →
→ Impact tracking updated → User sees "Your 10,000 Hilton points = $40 to
  Girls Who Code Oregon" → Annual impact report generated
```

**Technical stack:**
- **Donation API**: Change (getchange.io) — handles 50-state CCV compliance, nonprofit verification, disbursement
- **Backup**: Pledge.to — 2M+ nonprofits, free API, aggregated billing
- **DAF option**: Daffy — for users wanting tax-optimized cash donations alongside point conversions
- **Impact tracking**: B1G1-style micro-impact units + Kind Traveler-style live dashboards

**Compliance requirements:**
- Register as commercial co-venturer in ~25 states (Change handles this)
- Clear disclosure: point donations are NOT tax-deductible to consumer
- Terms of service: conversion rates, donation timing, processing fees
- State-by-state charitable solicitation registration (41 states + DC)

---

## SPRINT_ORCHESTRATION (Phase 3: PLAN)

### Initiative: RedeemFlow MVP → Growth → Impact

**Goal:** Launch free tier → convert to premium → activate charity network
**Scope:** 5 epics, 6 sprints
**Success criteria:**
- Free tier live with calculator + transfer explorer
- Premium subscribers paying $9.99/month
- First point-to-charity donation completed
- Charity partners in all 50 states activated

---

### Epic 1: Free Tier Calculator Engine (E1)

**Business value:** Acquire users with zero-barrier free tools. Drive SEO. Establish authority.
**Risk level:** Low — mostly frontend + static data.
**Dependencies:** Existing FastAPI backend + NetworkX graph engine.

| Task ID | Title | Acceptance Criteria | Files | Depends On |
|---------|-------|-------------------|-------|------------|
| E1-T01 | CPP valuation data model | Frozen dataclass for program valuations from 4 sources; test roundtrip | `src/redeemflow/valuations/` | — |
| E1-T02 | Points Value Calculator API | POST /calculate with program + balance → returns min/median/max CPP + dollar value | `src/redeemflow/valuations/routes.py` | E1-T01 |
| E1-T03 | Transfer Ratio Graph (seed data) | NetworkX graph populated with Big 6 currencies + 40 airline/hotel programs + current ratios | `src/redeemflow/optimization/transfer_graph.py` | — |
| E1-T04 | Transfer Explorer API | GET /transfers/{program} → returns all outbound transfer paths with ratios | `src/redeemflow/optimization/routes.py` | E1-T03 |
| E1-T05 | Best Card Recommender API | POST /recommend-card with merchant category → returns ranked cards by earn rate | `src/redeemflow/recommendations/card_recommender.py` | — |
| E1-T06 | Savings Dashboard API | POST /savings with user balances → returns "you're leaving $X on the table" analysis | `src/redeemflow/optimization/savings.py` | E1-T01, E1-T03 |
| E1-T07 | Annual Fee Calculator API | POST /fee-analysis with cards held + annual spend → net cost/benefit per card | `src/redeemflow/valuations/fee_calculator.py` | E1-T01 |
| E1-T08 | Free tier frontend (Next.js) | Calculator page, transfer explorer (interactive graph viz), card recommender, savings dashboard | `frontend/src/pages/`, `frontend/src/components/` | E1-T02 through E1-T07 |

### Epic 2: Premium Subscription + Optimization (E2)

**Business value:** Convert free users to $9.99/month subscribers. Core revenue.
**Risk level:** Medium — requires AwardWallet/Seats.aero API integrations.
**Dependencies:** E1 (free tier as foundation).

| Task ID | Title | Acceptance Criteria | Files | Depends On |
|---------|-------|-------------------|-------|------------|
| E2-T01 | Stripe subscription integration | Create/manage subscriptions for Premium/Pro tiers; webhook handling | `src/redeemflow/billing/` | — |
| E2-T02 | AwardWallet API integration | Connect user loyalty accounts; fetch balances; store encrypted | `src/redeemflow/portfolio/awardwallet.py` | — |
| E2-T03 | Personalized optimization engine | Analyze user's specific balances → generate ranked action items ("Transfer 30K MR to ANA now — 30% bonus active") | `src/redeemflow/optimization/personal_optimizer.py` | E1-T03, E2-T02 |
| E2-T04 | Alert system (devaluation + transfer bonus) | Monitor program changes; send push/email alerts; user preference management | `src/redeemflow/notifications/alerts.py` | E2-T02 |
| E2-T05 | Bank vs Burn advisor | AI-powered timing engine using CPP trends, devaluation history, current bonuses | `src/redeemflow/optimization/timing_advisor.py` | E1-T01, E1-T03 |
| E2-T06 | Seats.aero integration | Award availability search with "your points can book this" overlay | `src/redeemflow/search/award_search.py` | E2-T02 |
| E2-T07 | Points expiration manager | Track expiration policies; send 90/60/30 day alerts; suggest activity resets | `src/redeemflow/portfolio/expiration.py` | E2-T02 |
| E2-T08 | Premium frontend | Dashboard, optimization recommendations, alerts, award search, expiration tracker | `frontend/src/pages/dashboard/` | E2-T01 through E2-T07 |

### Epic 3: Charity Partner Network (E3)

**Business value:** Industry-first differentiator. Social impact. PR/marketing flywheel.
**Risk level:** Medium — legal compliance for 50-state operation.
**Dependencies:** E2 (subscription infrastructure).

| Task ID | Title | Acceptance Criteria | Files | Depends On |
|---------|-------|-------------------|-------|------------|
| E3-T01 | Charity data model | State, category, org name, chapter URL, donation URL, 501c3 status, accepts_points_donation flag | `src/redeemflow/charity/models.py` | — |
| E3-T02 | 50-state charity directory seed | Populate database with 10 anchor partners × all states + supplementary orgs | `data/charity_partners.json`, migration | E3-T01 |
| E3-T03 | Charity directory API | GET /charities?state=OH&category=youth → browse by state and category | `src/redeemflow/charity/routes.py` | E3-T02 |
| E3-T04 | Donation pipeline (Change API) | User selects charity + points amount → Change API processes conversion + donation | `src/redeemflow/charity/donation_flow.py` | E3-T01, E2-T01 |
| E3-T05 | Impact tracking | Track per-user and aggregate donations; micro-impact units; live dashboard | `src/redeemflow/charity/impact.py` | E3-T04 |
| E3-T06 | Charity directory frontend | Browse by state (interactive US map), filter by category, one-click donate | `frontend/src/pages/charities/` | E3-T03, E3-T04 |

### Epic 4: Community Pools + Pro Features (E4)

**Business value:** Industry-first community pooling. Pro tier revenue. Network effects.
**Risk level:** High — novel feature with no market precedent.
**Dependencies:** E3 (charity infrastructure).

| Task ID | Title | Acceptance Criteria | Files | Depends On |
|---------|-------|-------------------|-------|------------|
| E4-T01 | Community pool data model | Pool entity with members, target charity, goal amount, pledge tracking, status | `src/redeemflow/community/models.py` | E3-T01 |
| E4-T02 | Pool creation + management API | POST /pools (create), POST /pools/{id}/pledge, GET /pools/{id}/status | `src/redeemflow/community/routes.py` | E4-T01 |
| E4-T03 | Auto-donate rules engine | User configures: "If [program] points unused for [N days], donate to [charity]" | `src/redeemflow/charity/auto_donate.py` | E3-T04, E2-T07 |
| E4-T04 | Business travel optimizer | Multi-card stacking advisor; expense category → optimal card mapping | `src/redeemflow/optimization/business_optimizer.py` | E1-T05 |
| E4-T05 | Team points dashboard | Small business view: consolidated earning across employee cards | `src/redeemflow/portfolio/team_dashboard.py` | E2-T02 |
| E4-T06 | Subscription charity alignment | Pro subscribers choose charity "flavor"; 5% of subscription auto-donated | `src/redeemflow/billing/charity_alignment.py` | E2-T01, E3-T04 |
| E4-T07 | Pro frontend | Community pools, business optimizer, team dashboard, impact reporting | `frontend/src/pages/pro/` | E4-T01 through E4-T06 |

### Epic 5: Women's Travel Community (E5)

**Business value:** Retention moat. Network effects. Content generation.
**Risk level:** Medium — social features are hard to bootstrap.
**Dependencies:** E2 (user accounts).

| Task ID | Title | Acceptance Criteria | Files | Depends On |
|---------|-------|-------------------|-------|------------|
| E5-T01 | Community forum (Pro tier) | Discussion boards: strategies, deals, travel companions, local recs | `src/redeemflow/community/forum.py` | E2-T01 |
| E5-T02 | Women Founders Travel Network | Verified women business owners (NAWBO/WBENC link); private community | `src/redeemflow/community/founders_network.py` | E5-T01 |
| E5-T03 | Conference travel planner | Enter conference → see optimized travel from your balances | `src/redeemflow/search/conference_planner.py` | E2-T03, E2-T06 |
| E5-T04 | Multigenerational trip planner | Plan for 3+ travelers across programs; optimize collective value | `src/redeemflow/optimization/multi_traveler.py` | E2-T03 |
| E5-T05 | Safety layer | Hotel safety scores, neighborhood ratings, "women recommend" badges | `src/redeemflow/search/safety_scores.py` | — |

---

### Sprint Sequencing

#### Sprint 1: Walking Skeleton — Free Calculator (E1)

**Goal:** Free tier live with Points Value Calculator, Transfer Explorer, Best Card Recommender.
**Scope:** E1-T01 through E1-T08.
**Market differentiator:** Free aggregated CPP valuations from 4 sources (nobody else does this).
**Demo:** User enters "50,000 Chase UR" → sees "$850-$1,000 travel value vs $500 cash back."
**Quality gates:** All API endpoints return correct valuations. Transfer graph has 40+ programs. Frontend renders interactive graph.
**Rollback:** Revert to landing page only.

#### Sprint 2: Premium Foundation — Accounts + Billing (E2-T01, E2-T02)

**Goal:** User accounts with AwardWallet integration and Stripe billing.
**Scope:** Auth0 login, AwardWallet API connection, Stripe subscription creation.
**Market differentiator:** Connect real loyalty accounts (not manual entry).
**Demo:** User signs up → connects AwardWallet → sees all balances in one dashboard.
**Quality gates:** OAuth flow works. Balances refresh. Subscription creates/cancels cleanly.
**Rollback:** Disable premium features; free tier continues working.

#### Sprint 3: Premium Intelligence — Optimization Engine (E2-T03 through E2-T08)

**Goal:** Premium subscribers get personalized recommendations, alerts, and award search.
**Scope:** Optimization engine, alert system, Bank vs Burn advisor, Seats.aero search.
**Market differentiator:** "Your points, your best moves" — personalized, not generic.
**Demo:** User with 80K Amex MR sees: "Transfer to ANA now — 30% bonus + business class to Tokyo available Oct 15."
**Quality gates:** Recommendations are specific to user's balances. Alerts fire within 1hr of program changes.
**Rollback:** Disable optimization features; dashboard shows balances only.

#### Sprint 4: Charity Network — Directory + Donations (E3)

**Goal:** 50-state charity directory live with one-click point donations.
**Scope:** Charity data model, 50-state seed data, Change API donation flow, impact tracking.
**Market differentiator:** First platform connecting travel points to women-led charities.
**Demo:** User in Ohio browses charities → selects Girls Who Code → donates 10,000 Hilton points ($40) → sees confirmation + impact update.
**Quality gates:** Every state has 3+ charities. Donation flow completes end-to-end. Impact dashboard updates.
**Rollback:** Disable donation feature; directory remains browsable.

#### Sprint 5: Community — Pools + Pro Features (E4)

**Goal:** Community points pools live. Pro tier with business features.
**Scope:** Pool creation, auto-donate rules, business optimizer, subscription charity alignment.
**Market differentiator:** Industry-first community pooling for collective charitable impact.
**Demo:** 5 users create a pool targeting Junior League of Columbus → pledge points → goal reached → donation executed → impact dashboard shows "$500 from RedeemFlow community."
**Quality gates:** Pool lifecycle works end-to-end. Auto-donate fires on schedule. Business optimizer covers Big 6 ecosystems.
**Rollback:** Disable pools; individual donations continue working.

#### Sprint 6: Network Effects — Community + Safety (E5)

**Goal:** Women's travel community live. Safety layer active. Conference planner working.
**Scope:** Forum, founders network, conference planner, multigenerational planner, safety scores.
**Market differentiator:** The community moat — women helping women travel better.
**Demo:** Verified women business owner joins Founders Network → asks about SFO→NRT for WBENC conference → gets community recommendations + points-optimized booking plan.
**Quality gates:** Forum functional. Conference planner returns results. Safety data integrated.
**Rollback:** Disable community features; core product continues.

---

## GIT_EXECUTION_PLAN (Phase 4: EXECUTE)

### Branch Strategy

- **Main:** Production (landing page + stable releases only)
- **Feature branches:** `feature/CL-0feb6c6563-{slug}`
  - `feature/CL-0feb6c6563-free-calculator` (Sprint 1)
  - `feature/CL-0feb6c6563-premium-accounts` (Sprint 2)
  - `feature/CL-0feb6c6563-optimization-engine` (Sprint 3)
  - `feature/CL-0feb6c6563-charity-network` (Sprint 4)
  - `feature/CL-0feb6c6563-community-pools` (Sprint 5)
  - `feature/CL-0feb6c6563-travel-community` (Sprint 6)

### Commit Convention

```
type(scope): message — rationale

Types: feat, fix, refactor, test, data, infra
Scopes: valuations, optimization, charity, community, billing, frontend, search
```

### Ship Gates (per sprint)

1. All tests pass (unit + integration)
2. ruff format + ruff check clean
3. PR reviewed (agentic + manual)
4. CI green
5. Demo verified on staging
6. Rollback tested

---

## TEST_STRATEGY (Phase 5: TEST)

### Test Pyramid

| Level | Target | Coverage |
|-------|--------|----------|
| **Unit** | Valuation calculations, transfer ratio math, optimization logic, fee calculations | Every API endpoint |
| **Integration** | AwardWallet API, Seats.aero API, Change/Pledge.to API, Stripe webhooks | All external integrations |
| **Contract** | API response schemas, charity data format, donation flow protocol | All cross-boundary interfaces |
| **Scenario** | Free user → calculator → savings insight; Premium user → connect accounts → get recommendations → search awards; Pro user → create pool → donate | All user journeys |
| **Property-based** | Transfer ratio transitivity, CPP valuation bounds, fee calculation arithmetic | Mathematical invariants |
| **Regression** | Known devaluation edge cases, timezone handling, currency rounding | Guard against past failures |

### CI Gates

- Coverage >= 80%
- All tests pass
- No new ruff warnings
- No security vulnerabilities (PyJWT, httpx)
- API response time < 500ms (p95)

### Test Data

- Deterministic seed: 6 loyalty programs, 3 user profiles (solo, business, family), 10 charity partners
- Fixtures: AwardWallet mock responses, Seats.aero mock responses, Change API mock responses

---

## OBSERVABILITY_PLAN (Phase 6: MANAGE)

### Metrics

| Name | Unit | Type | Threshold |
|------|------|------|-----------|
| `calculations_per_day` | count | counter | — |
| `premium_subscribers` | count | gauge | — |
| `pro_subscribers` | count | gauge | — |
| `points_optimized_value` | USD | counter | — |
| `points_donated_value` | USD | counter | — |
| `donations_completed` | count | counter | — |
| `charity_partners_active` | count | gauge | >= 500 (10/state) |
| `community_pools_active` | count | gauge | — |
| `api_response_time_p95` | ms | histogram | < 500 |
| `external_api_error_rate` | ratio | gauge | < 0.05 |

### SLOs

| Service | SLO | Window |
|---------|-----|--------|
| Calculator API | 99.5% availability | 30 days |
| Donation pipeline | 99% completion rate | 30 days |
| Alert delivery | < 1hr from program change | continuous |

### Alerts

| Condition | Action |
|-----------|--------|
| API p95 > 1000ms for 5min | Page on-call |
| Donation failure rate > 10% | Page on-call |
| AwardWallet API error > 5% | Notify + fallback to cached data |
| Stripe webhook failure | Retry + notify |

---

## LEDGER_APPEND (Phase 6: MANAGE)

```json
{
  "lens_id": "CL-0feb6c6563",
  "conversation_fingerprint": "0feb6c6563f98189cb3be098079c15a789669f95be8f9de844c94cc467d018be",
  "slug": "redeemflow-product-plan",
  "work_items": 36,
  "adr_count": 0,
  "sprints": 6,
  "timestamp_utc": "2026-03-09T20:00:00Z",
  "author": "heymumford",
  "status": "planned",
  "sprint_sequence": [
    "free-calculator",
    "premium-accounts",
    "optimization-engine",
    "charity-network",
    "community-pools",
    "travel-community"
  ]
}
```

---

## APPENDIX A: Research Agent Index

| Agent | Domain | Key Finding |
|-------|--------|-------------|
| 1 | Women-Owned Business Trends | 14.5M businesses, 49% of new businesses, $3.3T revenue |
| 2 | Female CEO Travel Patterns | 45% of biz travelers, book 2 days earlier, 83% safety concerns |
| 3 | Travel Points Trading/Exchange | Big 6 currencies, Protect Your Points Act, Bilt at $3.25B |
| 4 | Point Maximization Strategies | Hotel/airline/train/car programs, credit card stacking, hot offers |
| 5 | Point Sharing & Donation | Community pooling unoccupied, API infrastructure mature |
| 6 | Women-Led Charities by Category | 10 anchor partners, every state coverable by 10+ orgs |
| 7 | Freemium Travel Tech Models | $9.99/mo sweet spot, no women-focused tool exists, free calcs = #1 SEO |
| 8 | Women Startups & Travel Rewards | Lean on credit cards more, cash flow / annual fee tension |
| 9 | 50-State Women Programs Map | 13 orgs with all-50-state presence, arts/culture weakest |
| 10 | Banking vs Spending Points | 5-15% annual devaluation, earn-and-burn safer, flexible currencies best |
| 11 | Women Travel Lifestyle Benefits | 75-85% of solo travelers, gateway to financial literacy |
| 12 | Subscription Charity Models | Change/Pledge.to handle compliance, points not tax-deductible |

## APPENDIX B: Competitive Positioning

```
                    Women-Focused
                         ▲
                         │
                         │  ★ RedeemFlow
                         │  (optimization + charity + community)
                         │
        Ellevest ●       │
        (investing)      │
                         │
        NomadHer ●       │       ● Wanderful
        (travel community)       (travel community)
                         │
 ───────────────────────────────────────────────► Points Optimization
                         │
        ● NerdWallet     │     ● AwardWallet
        (free content)   │     (balance tracking)
                         │
        ● TPG            │     ● MaxRewards
        (free content)   │     (auto-activation)
                         │
        ● Seats.aero     │     ● point.me
        (award search)   │     (award search + concierge)
                         │
                    Generic
```

RedeemFlow occupies the upper-right quadrant: women-focused AND points-optimized.
Nobody else is there.
