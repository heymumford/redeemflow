# RedeemFlow

Travel rewards optimization platform. Maximizes loyalty point value through transfer graph analysis, seasonal pricing intelligence, portfolio rebalancing, and personalized recommendations.

## Quick Start

```bash
uv sync
uv run uvicorn redeemflow.app:app --reload   # API at http://localhost:8000
uv run pytest tests/ --cache-clear -q          # 1730 tests
```

## Architecture

Hexagonal architecture with Protocol-based ports, frozen dataclasses for value objects, and Decimal for all financial math.

```
src/redeemflow/
├── admin/          # System metrics, audit log, admin dashboard
├── billing/        # Subscription tiers, Stripe webhooks, charity alignment
├── charity/        # Donation flow, impact tracking, 50-state partner network
├── community/      # Achievements, forum, founders network
├── identity/       # Auth (JWT), user profiles, API keys, onboarding
├── infra/          # Database adapters
├── middleware/     # Feature flags, rate limiting, security headers, tier limits
├── notifications/  # Alerts, preferences, expiration alerts, webhook retry
├── optimization/   # Transfer graph, path optimizer, budget planner, points calculator
├── portfolio/      # Balances, goals, expiration tracking, rebalancing, export/import
├── recommendations/# Card recommender, strategy quiz
├── redemptions/    # Car rental, retail, exchange
├── search/         # Award search, sweet spots, trip planner, seasonal pricing, saved searches
└── valuations/     # CPP aggregation, program comparison, trend analytics, program health
```

17 modules | 124 source files | 126 API endpoints | 1730 tests

## API Endpoints

### Public (no auth)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/api/calculate` | Points value calculator |
| GET | `/api/programs` | Program listing with CPP |
| GET | `/api/transfers/{program}` | Transfer partner explorer |
| POST | `/api/recommend-card` | Card recommendation by spend category |
| POST | `/api/savings` | Multi-program savings analysis |
| POST | `/api/fee-analysis` | Annual fee vs value analysis |
| GET | `/api/safety/{city}` | Destination safety scores |
| GET | `/api/safety/hotel/{hotel_name}` | Hotel safety rating |
| GET | `/api/conferences` | Women's conference directory |
| GET | `/api/shared/{token}` | View shared trip (public link) |

### Authenticated (Bearer token)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/portfolio` | User point balances |
| POST | `/api/portfolio/sync` | Sync loyalty accounts |
| GET | `/api/portfolio/calendar` | Expiration calendar |
| GET | `/api/portfolio/export` | Export portfolio (JSON/CSV) |
| POST | `/api/portfolio/import` | Import portfolio data |
| POST | `/api/portfolio/rebalance` | Concentration risk analysis |
| GET | `/api/recommendations` | Transfer recommendations |
| GET | `/api/household` | Household pooled balances |
| POST | `/api/household/member` | Add household member |
| GET | `/api/goals` | Savings goals with progress |
| POST | `/api/goals` | Create savings goal |
| POST | `/api/award-search` | Award availability search |
| POST | `/api/award-search/filtered` | Filtered search with sorting |
| GET | `/api/sweet-spots` | High-value redemption finder |
| POST | `/api/trip-compare` | Side-by-side redemption comparison |
| GET | `/api/seasonal/{route}` | Seasonal pricing intelligence |
| GET | `/api/trips` | List trips |
| POST | `/api/trips` | Create trip with segments |
| POST | `/api/trips/{trip_id}/share` | Share trip via link |
| POST | `/api/saved-searches` | Save search criteria |
| GET | `/api/saved-searches` | List saved searches |
| POST | `/api/conference-plan` | Conference travel optimization |
| POST | `/api/budget-plan` | 12-month earning projections |
| POST | `/api/calculator/earnings` | Points earning projections |
| POST | `/api/calculator/break-even` | Card break-even analysis |
| GET | `/api/programs/compare` | Multi-dimension program comparison |
| GET | `/api/profile` | User profile and preferences |
| PUT | `/api/profile` | Update profile |
| POST | `/api/keys` | Create API key |
| GET | `/api/keys` | List API keys |
| GET | `/api/notifications/preferences` | Notification preferences |
| GET | `/api/notifications/expiration-alerts` | Expiration alerts with actions |
| POST | `/api/onboarding/complete` | Guided onboarding with goal suggestions |
| GET | `/api/admin/metrics` | System-wide metrics |
| GET | `/api/admin/programs` | Per-program metrics |
| GET | `/api/admin/audit` | Audit log query |
| GET | `/api/admin/dashboard` | Full admin dashboard |

## Domain Model

### Transfer Graph Engine

NetworkX-powered directed graph modeling transfer partnerships between 23 loyalty programs. BFS path finding with transfer ratio and bonus optimization.

- 45+ transfer partnerships with real ratios
- 21 redemption sweet spots (flights, hotels, experiences)
- Transfer bonus detection and alerting

### Valuation Engine

CPP (cents per point) aggregation from 4 independent sources (TPG, OMAAT, NerdWallet, Upgraded Points). All calculations use `Decimal`.

- Per-program valuations with min/max/consensus CPP
- Trend analytics with devaluation detection
- Program health scoring across 5 dimensions

### Portfolio Management

- Balance tracking with AwardWallet adapter
- Points expiration monitoring with 90/60/30 day alerts
- Household pooling across family members
- Savings goals with progress tracking
- Portfolio rebalancing with Herfindahl concentration index
- Export/import in JSON and CSV formats

### Search & Planning

- Award availability search with multi-dimension filtering
- Seasonal pricing intelligence for 3 routes (SFO-NRT, JFK-LHR, LAX-CDG)
- Trip planner with multi-segment support
- Side-by-side redemption comparison with weighted ranking
- Conference travel optimizer for women's tech conferences
- Saved searches with alert-on-change support

### Subscription Tiers

| Tier | Price | Capabilities |
|------|-------|-------------|
| Free | $0 | Calculators, transfer explorer, card recommender |
| Premium | $9.99/mo | Personalized optimization, alerts, award search, charity donations |
| Pro | $24.99/mo | Business optimizer, community pools, founders network, team dashboard |

### Charity Network

50-state partner network with 10 anchor organizations (SBA WBC, Girl Scouts, Girls Who Code, Junior League, AAUW, and more). Points-to-dollar donation flow with micro-impact tracking.

## Testing

```bash
uv run pytest tests/ --ignore=tests/landing/test_visual.py --cache-clear -q
```

Test categories: unit (domain logic + API endpoints), contract (OpenAPI snapshot), integration (marked, requires external services).

## Quality Gates

```bash
uv run ruff format src/ tests/
uv run ruff check --fix src/ tests/
uv run pytest tests/ --ignore=tests/landing/test_visual.py --cache-clear -q
```

## Deployment

Fly.io on `ord` region. See `infra/architecture.md` for full deployment architecture, DNS configuration, and scaling plan.

| App | Runtime | Machine |
|-----|---------|---------|
| redeemflow-landing | nginx:alpine | shared-cpu-1x 256MB |
| redeemflow-api | Python 3.12 / FastAPI | shared-cpu-2x 1GB |
| redeemflow-web | Next.js | shared-cpu-1x 512MB |
| redeemflow-db | Postgres 16 | shared-cpu-1x 1GB |

## Dependencies

Python 3.12+, FastAPI, Pydantic, PyJWT, NetworkX, httpx. Dev: pytest, ruff.
