# RedeemFlow Partner Integration — Product Definition

## What We Do

RedeemFlow optimizes loyalty point redemptions for travelers. We read balances, search award availability, calculate optimal transfer paths, and facilitate donations — all through intermediary platforms, never directly with loyalty programs.

## Why Intermediaries

No loyalty program exposes a public API for balance reads, point transfers, or award booking. The industry operates through licensed intermediary platforms that hold bilateral contracts with programs. Direct scraping invites legal action (see: Air Canada v. Seats.aero, 2023).

RedeemFlow is an **optimization advisor**, not a point broker. We never hold, transfer, or liquidate points. We advise users on the best use of points they already own.

## Integration Tiers

| Tier | Function | Current Platform | Status | Coverage |
|------|----------|-----------------|--------|----------|
| **T0: Read** | Balance aggregation | AwardWallet | Live | 700+ programs (3 blocked: UA, AA, DL) |
| **T1: Search** | Award availability | Seats.aero | Live | Major airline alliances |
| **T2: Commerce** | Buy/sell/transfer | Points.com, Currency Alliance | Not started | 60+ programs (Points.com) |
| **T3: Donate** | Point-to-charity | Change API | Live | 1.5M+ nonprofits |

**Platform services** (cross-cutting, not part of partner data tiers):

| Service | Function | Platform | Status |
|---------|----------|----------|--------|
| Billing | Subscription management | Stripe | Live |

### Planned Evaluations

- **Duffel** (T1): NDC flight booking, 300+ airlines. Complements Seats.aero (search → booking).
- **Yodlee / MX** (T0): OAuth-based balance reads. Alternative to AwardWallet's scraping model. Reduces legal exposure.
- **Currency Alliance** (T2): Startup-friendly, ~30 API endpoints, free brand integration. Faster onboarding than Points.com.

## Protocol Boundaries

Every external integration implements a `Protocol` interface in `src/redeemflow/{domain}/ports.py`. Real adapters are env-var toggled. Tests use fakes with zero I/O. This table reflects current code — update if ports.py or auth schemes change.

| Port | Protocol | Env Var Toggle | Auth Method |
|------|----------|---------------|-------------|
| Portfolio | `PortfolioPort` | `AWARDWALLET_API_KEY` | Bearer token |
| Search | `AwardSearchPort` | `SEATS_AERO_API_KEY` | Partner-Authorization header |
| Donation | `DonationPort` | `CHANGE_API_KEY` | Bearer token |
| Billing | `BillingPort` | `STRIPE_SECRET_KEY` | API key (via SDK) |

New integrations follow this pattern: define Protocol → implement fake → implement real adapter → toggle via env var.

## Partner Contact Protocol

### Outreach Tiers

1. **Self-service** — Sign up for developer portal, get API key, integrate. (Duffel, Currency Alliance)
2. **BD outreach** — Email partnership team, schedule call, negotiate terms. (Points.com, Yodlee, MX)
3. **Affiliate** — Apply through affiliate network, no direct contact needed. (AwardWallet, Seats.aero)

### Contact Channels (by priority)

1. Developer portal / API docs (self-service signup)
2. Partnership email (partnerships@, developers@, api-support@)
3. Named BD contact (LinkedIn, press releases, conference attendees)
4. Affiliate network application (CJ, Impact, direct program)

### Engagement Sequence

```
1. Research    → Document program, API, contacts in partner Excel
2. Evaluate    → Sign up for sandbox / request demo
3. Test        → Build adapter against sandbox, verify data quality
4. Negotiate   → Terms: revenue share, volume minimums, SLA, data rights
5. Contract    → MSA + DPA (data processing agreement)
6. Integrate   → Real adapter behind env-var toggle
7. Monitor     → Error rates, latency, coverage gaps
```

## Contract Framework

### What We Need From Partners

| Term | Requirement | Negotiable? |
|------|------------|-------------|
| API access | REST or GraphQL, documented endpoints | No |
| Sandbox | Test environment with synthetic data | Preferred |
| Authentication | API key or OAuth 2.0 | No |
| Rate limits | >= 10 req/sec per tenant | Negotiable |
| Data rights | Display balance/availability to authenticated user | No |
| Revenue model | Revenue share, per-transaction, or flat fee | Yes |
| SLA | 99.5% uptime, < 2s p95 latency | Preferred |
| Data retention | We don't store raw partner data beyond cache TTL | No |

### What Partners Need From Us

| Term | Our Commitment |
|------|---------------|
| User consent | Explicit opt-in before accessing any program data |
| Data handling | No resale, no scraping, encrypted at rest and in transit |
| Attribution | Program name and branding per partner guidelines |
| Compliance | SOC 2 Type II (planned, pending counsel), GDPR/CCPA data subject rights |
| Volume reporting | Monthly transaction counts, error rates |

## Legal Risk Matrix (Provisional — Pending Counsel Review)

| Risk Level | Programs | Constraint |
|------------|----------|-----------|
| **HIGH** | United MileagePlus, American AAdvantage, Delta SkyMiles | Actively block third-party access. C&D history against AwardWallet. |
| **HIGH** | Air Canada Aeroplan | Active CFAA + trademark lawsuit against Seats.aero ($2M+ per claim). |
| **MEDIUM** | Southwest Rapid Rewards, JetBlue TrueBlue | TOS prohibit automated access. No known enforcement. |
| **LOW** | Most hotel programs, smaller airlines | No known restrictions on intermediary access. |

### Mitigations

- Route all data access through licensed intermediaries (never scrape directly)
- Maintain clear "optimization advisor" positioning (we don't hold or transfer points)
- Engage fintech attorney for: money transmitter analysis, CFAA exposure, terms of service review
- Monitor Air Canada v. Seats.aero outcome for precedent

## Open Questions (Requiring External Input)

| # | Question | Owner | Blocking? |
|---|----------|-------|-----------|
| 1 | Points.com partnership terms (revenue share, minimums, timeline) | BD outreach | Yes (T2) |
| 2 | Currency Alliance startup pricing and sandbox access | BD outreach | Yes (T2) |
| 3 | Yodlee reward container: which programs are actually supported? | Sandbox test | No |
| 4 | Legal classification: optimization advisor vs. point broker | Attorney | Yes |
| 5 | Money transmitter licensing for point-to-dollar donation flows | Attorney | Yes |
| 6 | SOC 2 Type II timeline and cost | Compliance | No |

## Multi-Tenancy (Prerequisite for Commercial Partners)

Commercial accounts require tenant isolation before partner APIs serve multiple organizations.

```
Individual Tenant (shared)     Commercial Tenant (isolated)
├── Free users                 ├── Team members (up to 10)
├── Premium ($9.99/mo)         ├── Admin dashboard
└── Pro ($24.99/mo)            ├── Consolidated billing
                               ├── Separate point pools
                               └── Tenant-scoped API calls
```

Implementation: Auth0 Organizations, tenant_id in JWT claims, row-level database isolation, per-tenant rate limiting on partner APIs.
