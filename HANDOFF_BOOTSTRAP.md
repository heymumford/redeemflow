# RedeemFlow — Agent Bootstrap

**Lens ID:** CL-0feb6c6563
**Date:** 2026-03-11
**Status:** 50-sprint implementation complete (PRs #12-#98)
**Tests:** 1730 passing
**Branch:** `main` (clean)

## Current State

All 50 sprints delivered. The platform has 17 modules, 124 source files, 126 API endpoints, and 1730 tests across unit and contract categories.

### Module Inventory

| Module | Purpose | Key Files |
|--------|---------|-----------|
| `admin` | System metrics, audit log, dashboard | `audit.py`, `dashboard.py`, `metrics.py` |
| `billing` | Subscription tiers, Stripe webhooks | `models.py`, `stripe_adapter.py`, `webhook_processor.py` |
| `charity` | Donation flow, 50-state partners, impact | `donation_flow.py`, `seed_data.py`, `impact.py` |
| `community` | Achievements, forum, founders network | `achievements.py`, `forum.py`, `founders_network.py` |
| `identity` | Auth, profiles, API keys, onboarding | `auth.py`, `profile.py`, `api_keys.py`, `onboarding.py` |
| `middleware` | Feature flags, rate limits, security | `feature_flags.py`, `rate_limit.py`, `tier_limits.py` |
| `notifications` | Alerts, preferences, expiration alerts | `alerts.py`, `preferences.py`, `expiration_alerts.py` |
| `optimization` | Graph engine, budget, calculator | `graph.py`, `path_optimizer.py`, `budget_planner.py` |
| `portfolio` | Balances, goals, rebalancing, export | `goals.py`, `rebalance.py`, `export.py` |
| `recommendations` | Card recommender, strategy quiz | `card_recommender.py`, `strategy_quiz.py` |
| `redemptions` | Car rental, retail, exchange | `car_rental.py`, `retail.py`, `exchange.py` |
| `search` | Award search, trips, seasonal, saved | `award_search.py`, `trip_planner.py`, `saved_searches.py` |
| `valuations` | CPP aggregation, comparison, trends | `aggregator.py`, `program_comparison.py`, `trends.py` |

### Architectural Patterns

- **Hexagonal**: Protocol-based ports in each domain module, PortBundle for DI
- **Value objects**: `@dataclass(frozen=True)` for all domain objects
- **Financial math**: `Decimal` everywhere, never float for money
- **Auth**: JWT with test tokens for dev (`test-token-eric`, `test-token-sarah`)
- **In-memory stores**: Singleton pattern with `get_store()`/`reset_store()`
- **OpenAPI contract**: Snapshot locked at `tests/contract/openapi_snapshot.json`

### Test Command

```bash
uv run pytest tests/ --ignore=tests/landing/test_visual.py --cache-clear -q
```

### Quality Gates

```bash
uv run ruff format src/ tests/
uv run ruff check --fix src/ tests/
uv run pytest tests/ --ignore=tests/landing/test_visual.py --cache-clear -q
```

## Sprint History

| Sprint | Feature | PR | Tests |
|--------|---------|-----|-------|
| 1 | Free-tier calculator engine | #12 | 147 |
| 2-6 | Premium accounts, optimization, charity, community, travel | #13-#44 | ~1200 |
| 7-35 | Savings dashboard through achievements | #45-#83 | ~1460 |
| 36 | Budget planner | #84 | 1478 |
| 37 | Trip comparison | #85 | 1498 |
| 38 | Seasonal pricing | #86 | 1519 |
| 39 | API key management | #87 | 1537 |
| 40 | Webhook retry | #88 | 1555 |
| 41 | Trip sharing | #89 | 1574 |
| 42 | Feature flags | #90 | 1591 |
| 43 | Notification preferences | #91 | 1611 |
| 44 | Points calculator | #92 | 1631 |
| 45 | Portfolio rebalancing | #93 | 1643 |
| 46 | Program comparison | #94 | 1656 |
| 47 | Admin dashboard | #95 | 1666 |
| 48 | Saved searches | #96 | 1688 |
| 49 | Expiration alerts | #97 | 1706 |
| 50 | Onboarding flow | #98 | 1730 |
