# ADR-001: Partner Platform Selection

**Status:** Accepted
**Date:** 2026-03-12
**Context:** Sprint R2 (CL-107b6e3b65) — evaluate intermediary platforms for T0-T2 integration tiers

## Decision

### T0 (Balance Reads): Keep AwardWallet + Evaluate MX for credit card rewards

**AwardWallet** remains the only viable aggregator for standalone airline/hotel loyalty balances (700+ programs). Neither Yodlee nor MX connect to airline or hotel websites — they aggregate financial institution data only.

**MX Technologies** is selected over Yodlee for credit card reward balances (Chase UR, Amex MR, Capital One, Citi TY) based on:
- Lower cost (~$15K/yr vs $5-15K/mo for Yodlee)
- Free developer sandbox with immediate access
- Dedicated rewards API endpoints (`POST fetch_rewards`, `GET rewards`)
- Complementary coverage: credit card rewards that AwardWallet covers via riskier credential-sharing

**Yodlee** is not selected. More mature reward container but pricing is prohibitive for a startup ($5-15K/mo platform fee + per-user).

**Neither fills the United/Delta/American gap.** These airlines blocked AwardWallet via C&D and no aggregator connects to their sites. Email parsing of monthly statements is the only workaround.

### T1 (Award Search): Keep Seats.aero + Add Duffel for revenue flights

**Duffel** is selected for revenue flight search and booking:
- 300+ airlines (NDC + GDS + LCC), $3/booking + 1% managed content fee
- Free sandbox (Duffel Airways test airline), Bearer token auth
- Enables "points vs. cash" comparison — Seats.aero provides award costs, Duffel provides cash costs
- Amadeus Self-Service (primary competitor) is shutting down July 2025
- Python SDK is archived; integrate via httpx (consistent with existing adapter pattern)
- Revenue opportunity: RedeemFlow can book cash flights and earn $3+ per booking

**Seats.aero** remains for award availability search (no alternative exists).

### T2 (Commerce): Currency Alliance for MVP, Points.com for scale

**Currency Alliance** is selected for MVP:
- Public API docs at `api.currencyalliance.com/api-docs/v3`
- Sandbox at `sandbox.api.currencyalliance.com/public/v3.0`
- ~35 endpoints, HMAC-SHA256 auth, simulate-then-execute pattern
- 2% of loyalty value transacted, no setup costs, no minimums
- 13+ airline programs confirmed (Flying Blue, BA, Qatar, Singapore, Etihad, etc.)
- Free registration, API keys available after commercial engagement
- Contact: Chuck Ehredt (CEO), `currencyalliance.com/contact-us`

**Points.com/Plusgrade** is deferred to scale phase:
- Enterprise-sales-only, no public API, no sandbox, password-protected docs
- 60+ programs (dominant coverage), OAuth 2.0 MAC authentication
- $385M acquisition by Plusgrade (2022), $2B+ valuation (2024)
- Contact: Sacha Diab (SVP Global BD), `partnerships@points.com`
- RedeemFlow should position as a "demand channel" driving buy/exchange transactions
- Enterprise sales cycle expected

**Coverage gap:** Currency Alliance is weak on US carriers and major hotel chains. Points.com covers these but requires enterprise partnership. For MVP, this gap is acceptable — T2 commerce is additive, not core.

## Platform Comparison Matrix

| Dimension | Currency Alliance | Points.com | Duffel | MX | AwardWallet |
|-----------|------------------|------------|--------|-----|-------------|
| **Tier** | T2 Commerce | T2 Commerce | T1 Search | T0 Read | T0 Read |
| **API access** | Public, sandbox | Enterprise-only | Public, sandbox | Free dev account | Partner API key |
| **Auth** | HMAC-SHA256 | OAuth 2.0 MAC | Bearer token | Basic auth | Bearer token |
| **Pricing** | 2% transaction | Revenue share (enterprise) | $3/booking + 1% | ~$15K/yr | $4/user/mo |
| **Coverage** | 13+ airlines, 1 hotel | 60+ programs | 300+ airlines (revenue) | Credit card rewards | 700+ loyalty programs |
| **Startup-friendly** | Yes | No | Yes | Moderate | Yes |
| **Integration effort** | Medium (HMAC auth) | High (enterprise process) | Low (Bearer token) | Medium (widget + API) | Low (existing adapter) |

## Integration Priority

| # | Platform | Action | Timeline |
|---|----------|--------|----------|
| 1 | Duffel | Sign up, build adapter, test sandbox | Sprint R2 (now) |
| 2 | Currency Alliance | Register, contact BD, obtain sandbox keys | Sprint R2 (now) |
| 3 | MX Technologies | Sign up for developer account, test rewards endpoints | Sprint R3 |
| 4 | Points.com | Email `partnerships@points.com`, begin BD conversation | Sprint R3 |

## Consequences

**Positive:**
- Duffel + Seats.aero gives complete flight comparison (points vs. cash)
- Currency Alliance provides T2 commerce without enterprise sales cycle
- MX adds bank-grade credit card reward reads alongside AwardWallet
- All three new platforms have developer sandboxes

**Negative:**
- Currency Alliance has limited US carrier coverage (no United, Delta, American)
- Points.com partnership may take 3-6 months of enterprise sales
- MX rewards endpoints are beta — may change
- Total platform cost at scale: ~$15K/yr (MX) + 2% (CA) + $3/booking (Duffel) + $4/user/mo (AW)

**Risks:**
- CFPB Section 1033 (if implemented) would require banks to share reward data via APIs — could reduce need for MX/Yodlee but only for credit card rewards, not airline/hotel programs
- Air Canada v. Seats.aero lawsuit outcome could affect award search integration
- Currency Alliance is a Barcelona startup (~793 LinkedIn followers) — vendor risk
