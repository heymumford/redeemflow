# RedeemFlow Partner Integration Plan — CL-107b6e3b65

**Lens ID:** CL-107b6e3b65
**Date:** 2026-03-12
**Research basis:** 5 parallel research agents + existing research (hotel/airline JSON, 6-sheet Excel)
**Mode:** standard (full UDPETM cycle)

---

## SUMMARY (Phase 1: UNDERSTAND)

### Statement of Intent

Build production partner integrations with loyalty program intermediaries (not programs directly) to enable balance reads, award search, and point commerce. Research and document every major program's API landscape, contacts, contracts, and legal constraints. Populate partner Excel with actionable outreach data.

### Critical Discovery: The Intermediary Layer

**No loyalty program exposes a public API for balance reads or point transfers.** This is the single most important finding. RedeemFlow's integration strategy must go through intermediary platforms, not directly to programs.

```
RedeemFlow ──→ Intermediary Platform ──→ Loyalty Program
                    │
                    ├── AwardWallet (balance reads — screen scraping)     ✅ DONE
                    ├── Seats.aero (award availability search)            ✅ DONE
                    ├── Points.com/Plusgrade (buy/sell/transfer/exchange)  ⬜ NOT STARTED
                    ├── Currency Alliance (brand-to-brand exchange)       ⬜ NOT STARTED
                    ├── Duffel (flight booking via NDC)                   ⬜ NOT STARTED
                    └── 30K Milefy (miles calculation)                    ⬜ NOT STARTED
```

### What You're Forgetting (Gaps Surfaced)

1. **Legal risk is asymmetric.** Air Canada sued Seats.aero (2023) for $2M+ per trademark, alleging computer fraud and trademark infringement for screen-scraping award availability. AwardWallet operates on the same scraping model. RedeemFlow's liability exposure scales with how aggressively we access program data without bilateral agreements.

2. **Points.com is the gatekeeper, not programs.** Points.com (Plusgrade subsidiary) powers buy/sell/transfer for 60+ programs. They process 92B+ points/year. You don't negotiate point transfers with United — you negotiate with Points.com. This is a B2B enterprise sales cycle.

3. **Currency Alliance is the dark horse.** API-first, ~30 endpoints, supports brand-to-brand point exchange, free integration for brands, IATA experience. Purpose-built for what RedeemFlow needs. Less established than Points.com but more accessible for a startup.

4. **Financial aggregators split on rewards.** Plaid CANNOT read loyalty balances. Yodlee CAN (explicit "reward" container type). MX CAN (documented rewards support). This matters for the OAuth balance-read path as an alternative to AwardWallet's scraping.

5. **Program consolidation reduces the target list.** SPG → Marriott Bonvoy. Radisson Americas → Choice Privileges. Mileage Plan → Atmos Rewards. Hawaiian Miles → merged into Atmos. The actual number of distinct programs is ~25, not 40+.

6. **Tenant architecture must precede partner integration.** Commercial accounts need isolated point pools, separate billing, team management. Individual accounts under a shared tenant. This is the multi-tenancy question you raised — industry standard is tenant-per-organization with a shared "individual" tenant for B2C users.

7. **Donation compliance is per-state.** The Change API handles 50-state commercial co-venturer registration. But if RedeemFlow facilitates point-to-cash conversions for donation, that may trigger money transmitter licensing in some states. Legal review needed before any point-to-dollar flow goes live.

### Entity Inventory

| Entity | Count | Status |
|--------|-------|--------|
| Hotel loyalty programs | 10 | Researched |
| Airline loyalty programs | 15 | Researched |
| Bank transfer currencies | 6 | Researched |
| Exchange platforms | 6 | Researched |
| Financial aggregators | 5 | Researched |
| Car rental programs | 4 | Researched |
| Retail programs | 4 | Researched |
| **Total distinct programs** | ~50 | Cataloged |

### UNKNOWN Inventory (Requires Investigation)

| # | Unknown | Blocking? | Resolution Path |
|---|---------|-----------|-----------------|
| U1 | Points.com partnership terms (revenue share, minimums, timeline) | Yes | Contact Points.com BD team |
| U2 | Currency Alliance startup pricing and onboarding | Yes | Contact Currency Alliance |
| U3 | Yodlee reward container: which programs does it actually cover? | No | Test with Yodlee sandbox |
| U4 | Legal review: is RedeemFlow an "optimization advisor" or "point broker"? | Yes | Engage fintech attorney |
| U5 | Money transmitter licensing requirements for point-to-dollar flows | Yes | Legal counsel |
| U6 | AwardWallet TOS risk: which programs actively block scrapers? | No | AwardWallet partnership team |
| U7 | Seats.aero lawsuit outcome — does it set precedent? | No | Monitor case status |
| U8 | Multi-tenancy architecture for commercial vs individual accounts | No | Design decision |

---

## LENS_SPEC_YAML (Phase 2: DESIGN)

### Integration Tier Architecture

```
TIER 0: READ-ONLY (balance + valuation)
├── AwardWallet API (700+ programs, screen-scraping)     ✅ Adapter exists
├── Yodlee Reward Container (OAuth, ~50 programs)        ⬜ Alternative path
├── MX Technologies (OAuth, rewards support)             ⬜ Alternative path
└── Internal valuation engine (CPP from 4 sources)       ✅ Built

TIER 1: SEARCH (award availability)
├── Seats.aero API (award flights)                       ✅ Adapter exists
├── Duffel API (NDC flight booking, 300+ airlines)       ⬜ New integration
└── Google Hotel Prices API                              ⬜ Future

TIER 2: COMMERCE (buy/sell/transfer/exchange)
├── Points.com LCP API (60+ programs)                    ⬜ Enterprise partnership
├── Currency Alliance API (~30 endpoints)                ⬜ Startup-friendly
└── Program-direct APIs (Lufthansa only has public)      ⬜ One-off

TIER 3: DONATE (point-to-charity)
├── Change API (getchange.io)                            ✅ Adapter exists
├── Pledge.to API (2M+ nonprofits)                       ⬜ Backup
└── Daffy (DAF option for tax-optimized)                 ⬜ Future
```

### Partner Entity Model

```yaml
partner:
  id: str                    # deterministic slug (e.g., "marriott-bonvoy")
  display_name: str
  parent_company: str
  program_type: enum         # hotel | airline | bank | car_rental | retail | exchange
  alliance: str | None       # oneworld | star_alliance | skyteam | none

  integration:
    tier: int                # 0=read, 1=search, 2=commerce, 3=donate
    status: enum             # researched | contacted | negotiating | contracted | integrated | blocked
    intermediary: str | None # "awardwallet" | "points_com" | "currency_alliance" | "direct"
    api_type: enum           # public | partner | b2b_only | scraping | none
    api_url: str | None
    api_auth: enum           # oauth2 | api_key | partner_credential | none
    has_sandbox: bool
    loyalty_balance_api: bool

  contacts:
    partnership_email: str | None
    partnership_phone: str | None
    developer_portal: str | None
    named_contact: str | None

  program_data:
    members_millions: float
    cpp_valuation: float
    valuation_source: str
    transfer_partners_in: list[str]   # bank programs that transfer IN
    transfer_partners_out: list[str]  # programs you can transfer OUT to

  legal:
    tos_prohibits_third_party: bool | None  # UNKNOWN for most
    lawsuit_history: str | None
    compliance_notes: str | None

  contract:
    type: enum              # none | affiliate | technology_partner | strategic
    revenue_model: str | None
    minimum_volume: str | None
    estimated_timeline: str | None
```

### Architecture Decision: Intermediary-First

**Decision:** RedeemFlow integrates with intermediary platforms, never directly with loyalty programs (except Lufthansa Miles & More, which has the only public loyalty API).

**Rationale:**
- Direct program APIs don't exist for loyalty operations
- Intermediaries handle compliance, authentication, rate limiting
- Single integration point covers 60+ programs
- Reduces legal exposure (intermediary holds the program relationship)

**Trade-off:** Revenue share with intermediary reduces margin. But the alternative (bilateral B2B deals with 25+ programs) requires a BD team we don't have.

### Tenant Architecture (Pre-Requisite)

```
INDIVIDUAL TENANT (shared, default)
├── Free tier users
├── Premium tier users ($9.99/mo)
└── Pro tier users ($24.99/mo)

COMMERCIAL TENANTS (isolated, per-organization)
├── Team members (up to 10 cards)
├── Admin dashboard
├── Consolidated billing
├── Separate point pools
└── API access (Pro tier)
```

Industry standard: Auth0 Organizations or equivalent. Tenant ID on every request. Row-level security in database. Isolated billing via Stripe Connected Accounts or separate subscriptions.

---

## SPRINT_ORCHESTRATION (Phase 3: PLAN)

### Initiative: Partner Integration Foundation

**Goal:** Move from demo/fake adapters to production partner integrations with documented contracts, contacts, and APIs.
**Scope:** 3 epics, 4 sprints
**Success criteria:**
- Excel partner sheet enriched with contacts, contracts, legal risk for all 50 programs
- Points.com or Currency Alliance partnership initiated
- Yodlee/MX evaluated as AwardWallet alternative
- Multi-tenancy architecture designed
- Product definition statement for partner relationships published

---

### Epic PI1: Partner Research Enrichment

**Business value:** Can't build integrations without knowing who to contact, what contracts look like, and where legal risk lies.
**Risk level:** Low — research only, no code.
**Dependencies:** None.

| Task ID | Title | Acceptance Criteria | Depends On |
|---------|-------|-------------------|------------|
| PI1-T01 | Enrich Excel: hotel program contacts | Partnership email/phone, developer portal URL, named BD contact for all 10 hotel programs. Source: program websites, LinkedIn, press releases. | — |
| PI1-T02 | Enrich Excel: airline program contacts | Same for all 15 airline programs. Include alliance membership and parent company. | — |
| PI1-T03 | Enrich Excel: bank program contacts | Partnership/developer contacts for Big 6 currencies. Include transfer partner lists with ratios. | — |
| PI1-T04 | Enrich Excel: exchange platform contacts | Points.com, Currency Alliance, Arrivia, Switchfly, Loyalty Prime contacts. Include API docs URLs, pricing models. | — |
| PI1-T05 | Legal risk assessment | Document TOS restrictions for each program. Catalog known lawsuits (Air Canada v. Seats.aero). Identify money transmitter risk. Draft legal questions for attorney review. | — |
| PI1-T06 | Consolidate into product definition statement | 1-page document: how RedeemFlow maintains partner relationships, integration tiers, contact protocol, contract templates. | PI1-T01..T05 |

### Epic PI2: Platform Evaluation & Outreach

**Business value:** Determine which intermediary platform(s) to build on.
**Risk level:** Medium — external dependency on partner responsiveness.
**Dependencies:** PI1 (need to know who to contact).

| Task ID | Title | Acceptance Criteria | Depends On |
|---------|-------|-------------------|------------|
| PI2-T01 | Points.com/Plusgrade evaluation | Contact BD team. Document: API capabilities, program coverage, revenue share model, onboarding timeline, minimum volume, sandbox access. | PI1-T04 |
| PI2-T02 | Currency Alliance evaluation | Same as above. Evaluate ~30 API endpoints. Test sandbox if available. | PI1-T04 |
| PI2-T03 | Yodlee reward container evaluation | Sign up for developer sandbox. Test reward container: which programs supported? What data returned? Compare to AwardWallet. | PI1-T04 |
| PI2-T04 | MX Technologies evaluation | Same as Yodlee. Test rewards data access. | PI1-T04 |
| PI2-T05 | Duffel flight booking API evaluation | Sign up (free). Test flight search. Evaluate as complement to Seats.aero for booking (not just search). | — |
| PI2-T06 | Platform selection decision | ADR documenting: which platform(s) selected, why, trade-offs, cost projections, timeline to production. | PI2-T01..T05 |

### Epic PI3: Multi-Tenancy Foundation

**Business value:** Commercial accounts require tenant isolation before partner APIs can serve multiple organizations.
**Risk level:** Medium — architectural change touching auth, database, and API layers.
**Dependencies:** PI2-T06 (need to know which platform APIs shape the data model).

| Task ID | Title | Acceptance Criteria | Depends On |
|---------|-------|-------------------|------------|
| PI3-T01 | Tenant data model | Tenant entity (id, name, type, billing_id). TenantMembership (user_id, tenant_id, role). Alembic migration. | — |
| PI3-T02 | Auth0 Organization integration | Configure Auth0 Organizations for multi-tenancy. Tenant ID in JWT claims. Test with individual + commercial tenants. | PI3-T01 |
| PI3-T03 | Row-level tenant isolation | All database queries scoped by tenant_id. Middleware extracts tenant from JWT. Test: user A cannot see user B's data across tenants. | PI3-T01, PI3-T02 |
| PI3-T04 | Stripe tenant billing | Separate Stripe subscriptions per tenant. Commercial accounts billed at organization level. Individual accounts billed per-user. | PI3-T01 |
| PI3-T05 | Tenant-scoped partner API adapters | AwardWallet, Seats.aero, Change API calls scoped by tenant. Rate limiting per-tenant. | PI3-T03 |
| PI3-T06 | Admin dashboard for commercial tenants | Team management, consolidated balances, billing overview. | PI3-T03, PI3-T04 |

### Sprint Sequencing

#### Sprint R1: Partner Research Deep Dive

**Goal:** Enrich Excel with contacts, contracts, legal risk for all programs.
**Scope:** PI1-T01 through PI1-T06.
**Demo:** Updated Excel with contacts sheet, legal risk column, product definition statement.
**Quality gates:** Every program has at least one contact path documented. Legal risk categorized (low/medium/high) for each.
**Rollback:** N/A — research only.

#### Sprint R2: Platform Evaluation

**Goal:** Evaluate Points.com, Currency Alliance, Yodlee, MX, Duffel. Select platform(s).
**Scope:** PI2-T01 through PI2-T06.
**Demo:** ADR with platform selection rationale, sandbox test results, cost projections.
**Quality gates:** At least 2 platforms evaluated hands-on. Decision documented with trade-offs.
**Rollback:** N/A — evaluation only.

#### Sprint R3: Multi-Tenancy Architecture

**Goal:** Tenant data model, Auth0 Organizations, row-level isolation.
**Scope:** PI3-T01 through PI3-T03.
**Demo:** Two tenants (individual + test commercial) with isolated data.
**Quality gates:** User in tenant A cannot access tenant B data. JWT contains tenant_id. Alembic migration reversible.
**Rollback:** Revert migration, remove tenant middleware.

#### Sprint R4: Tenant Billing & Partner Scoping

**Goal:** Stripe per-tenant billing, tenant-scoped adapters, admin dashboard.
**Scope:** PI3-T04 through PI3-T06.
**Demo:** Commercial tenant with 3 team members, separate billing, consolidated balance view.
**Quality gates:** Billing isolated. Rate limiting per-tenant. Admin can manage team.
**Rollback:** Disable commercial tenant features, individual billing continues.

---

## GIT_EXECUTION_PLAN (Phase 4: EXECUTE)

### Branch Strategy

- **Feature branches:** `feature/CL-107b6e3b65-{slug}`
  - `feature/CL-107b6e3b65-partner-research` (Sprint R1)
  - `feature/CL-107b6e3b65-platform-eval` (Sprint R2)
  - `feature/CL-107b6e3b65-multi-tenancy` (Sprint R3)
  - `feature/CL-107b6e3b65-tenant-billing` (Sprint R4)

### Commit Convention

```
type(scope): message — rationale

Types: research, feat, refactor, test, data, infra
Scopes: partners, tenancy, billing, adapters
```

### Ship Gates (per sprint)

1. All tests pass (unit + integration)
2. ruff format + ruff check clean
3. PR reviewed (agentic + manual)
4. CI green
5. Excel updated (R1/R2)
6. ADR published (R2)

---

## TEST_STRATEGY (Phase 5: TEST)

### Test Pyramid

| Level | Target | Coverage |
|-------|--------|----------|
| **Unit** | Tenant model, tenant middleware, row-level isolation, billing logic | Every new endpoint |
| **Integration** | Auth0 Organization flow, Stripe tenant billing, platform API sandboxes | All external integrations |
| **Contract** | Tenant-scoped API responses, partner data schema, JWT claims | All cross-boundary interfaces |
| **Scenario** | Individual signup → default tenant; Commercial signup → create org → invite team → billing | All user journeys |
| **Property-based** | Tenant isolation invariants (user A never sees user B data across N random tenants) | Security invariants |

### CI Gates

- Coverage >= 80%
- All tests pass
- No new ruff warnings
- Tenant isolation property tests pass
- No security vulnerabilities

---

## OBSERVABILITY_PLAN (Phase 6: MANAGE)

### Metrics

| Name | Unit | Type | Threshold |
|------|------|------|-----------|
| `partner_api_calls_total` | count | counter | — |
| `partner_api_error_rate` | ratio | gauge | < 0.05 |
| `partner_api_latency_p95` | ms | histogram | < 2000 |
| `tenants_active` | count | gauge | — |
| `tenant_members_total` | count | gauge | — |
| `platform_evaluation_score` | score | gauge | — |
| `partner_contacts_documented` | count | gauge | >= 50 |

### Research Tracking

| Metric | Target |
|--------|--------|
| Programs with contacts documented | 50/50 |
| Programs with legal risk assessed | 50/50 |
| Exchange platforms evaluated | 5/5 |
| Financial aggregators tested | 3/3 |
| Platform selection ADR published | 1 |
| Product definition statement | 1 |

---

## LEDGER_APPEND (Phase 6: MANAGE)

```json
{
  "lens_id": "CL-107b6e3b65",
  "conversation_fingerprint": "107b6e3b657940236b5afd6563401fad71593e05718871e779780902eb2b1702",
  "slug": "partner-integration-foundation",
  "work_items": 18,
  "adr_count": 1,
  "sprints": 4,
  "timestamp_utc": "2026-03-12T14:00:00Z",
  "author": "heymumford",
  "status": "planned",
  "sprint_sequence": [
    "partner-research",
    "platform-eval",
    "multi-tenancy",
    "tenant-billing"
  ]
}
```
