# RedeemFlow — Agent Bootstrap Prompt (Sprints 2-6)

**Lens ID:** CL-0feb6c6563
**Date:** 2026-03-09
**Last commit on main:** `aa13004` — Sprint 1 merged via PR #12
**Tests:** 147 passing, 0 failing
**Branch:** `main` (clean)

---

## YOUR MISSION

You are the orchestrator agent for RedeemFlow, a women-first travel rewards optimization platform. Sprint 1 (free-tier calculator engine) is complete and merged. You will implement Sprints 2-6, using **parallel sub-agents in isolated git worktrees** to minimize wall clock time.

**TDD discipline (Beck):** Write failing tests first, then implement minimally, then refactor.
**Clean architecture (Fowler):** Domain models first, Protocol interfaces at boundaries, thin routes that delegate to domain objects, frozen dataclasses for value objects, Decimal for all financial math.

---

## WHAT EXISTS (Sprint 1 — Complete)

### Codebase Layout

```
src/redeemflow/
├── __init__.py              # __version__ = "0.1.0"
├── app.py                   # FastAPI factory, includes valuations_router
├── calendar/                # Empty placeholder
├── identity/
│   ├── auth.py              # Test token auth (JWT stub), AuthError, get_current_user
│   └── models.py            # User(id, email, name) frozen dataclass
├── infra/                   # Empty placeholder
├── notifications/           # Empty placeholder
├── optimization/
│   ├── graph.py             # TransferGraph (NetworkX DiGraph, BFS path finding)
│   ├── models.py            # TransferPartner, RedemptionOption, TransferPath
│   └── seed_data.py         # 45+ transfer partnerships, 21 redemption sweet spots
├── portfolio/
│   ├── fake_adapter.py      # FakeBalanceFetcher (hardcoded test data)
│   ├── models.py            # LoyaltyProgram, PointBalance, LoyaltyAccount
│   └── ports.py             # BalanceFetcher Protocol
├── recommendations/
│   ├── engine.py            # RecommendationEngine (graph + fallback)
│   └── models.py            # Recommendation dataclass
├── search/                  # Empty placeholder
└── valuations/
    ├── __init__.py
    ├── models.py            # ProgramValuation, CreditCard, ValuationSource, AnnualValueResult
    ├── routes.py            # 6 free-tier API endpoints (no auth)
    └── seed_data.py         # 23 programs, 9 credit cards, CPP from 4 sources
```

### Live API Endpoints (Sprint 1)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | /health | None | Health check |
| GET | /api/portfolio | Bearer | User balances (test tokens) |
| GET | /api/recommendations | Bearer | Transfer recommendations |
| POST | /api/calculate | None | Points value calculator |
| GET | /api/transfers/{program} | None | Transfer partner explorer |
| GET | /api/programs | None | Program listing with CPP |
| POST | /api/recommend-card | None | Best card by category |
| POST | /api/savings | None | Multi-program savings analysis |
| POST | /api/fee-analysis | None | Annual fee vs value analysis |

### Key Domain Objects

- `ProgramValuation` — frozen dataclass with CPP from 4 sources (TPG, OMAAT, NerdWallet, Upgraded Points), methods: `dollar_value()`, `dollar_value_range()`, `cash_back_value()`, `opportunity_cost()`
- `CreditCard` — frozen dataclass with earn rates, credits, `net_annual_fee`, `annual_value()`
- `TransferGraph` — NetworkX DiGraph with BFS `find_paths()`, `optimize_portfolio()`
- `TransferPartner` — directed edge with `transfer_ratio`, `transfer_bonus`, `effective_ratio`
- `RedemptionOption` — node attribute with `points_required`, `cash_value`, `cpp`
- All financial math uses `Decimal`. No floats for money.

### Dependencies (pyproject.toml)

```
fastapi>=0.115.0, uvicorn, pydantic>=2.10.0, PyJWT[crypto]>=2.8.0,
httpx>=0.28.0, networkx>=3.4.0
Dev: pytest>=8.3.0, pytest-asyncio, pytest-cov, ruff>=0.8.0
```

### Test Command

```bash
uv run pytest tests/ --cache-clear -q
```

### Quality Gates

```bash
uv run ruff format src/ tests/
uv run ruff check --fix src/ tests/
uv run pytest tests/ --cache-clear -q   # must be 0 failures
```

---

## WHAT TO BUILD (Sprints 2-6)

### Sprint Dependency Graph

```
Sprint 1 (DONE) ─┬─→ Sprint 2 (accounts + billing) ──→ Sprint 3 (optimization engine)
                  │                                           │
                  │                                           ├──→ Sprint 4 (charity network)
                  │                                           │         │
                  │                                           │         ├──→ Sprint 5 (community pools)
                  │                                           │         │
                  └───────────────────────────────────────────┴─────────┴──→ Sprint 6 (travel community)
```

### Parallelization Strategy

```
WAVE 1 (parallel):
  ├── Agent A: Sprint 2 — Premium accounts + Stripe billing
  └── Agent B: Sprint 4 partial — Charity data model + 50-state seed data (no billing dependency)

WAVE 2 (parallel, after Wave 1 merges):
  ├── Agent C: Sprint 3 — Optimization engine (depends on Sprint 2 for AwardWallet)
  └── Agent D: Sprint 4 completion — Donation pipeline + Change API (depends on Sprint 2 for billing)

WAVE 3 (parallel, after Wave 2 merges):
  ├── Agent E: Sprint 5 — Community pools + auto-donate (depends on Sprint 3 + 4)
  └── Agent F: Sprint 6 partial — Safety layer + conference planner (standalone)

WAVE 4 (final, after Wave 3):
  └── Agent G: Sprint 6 completion — Forum + founders network (depends on Sprint 2)
```

### Sprint 2: Premium Accounts + Billing

**Branch:** `feature/CL-0feb6c6563-premium-accounts`
**New modules:** `src/redeemflow/billing/`, extend `identity/auth.py`

| Task | What to Build | Files |
|------|---------------|-------|
| E2-T01 | Stripe subscription (Premium $9.99/mo, Pro $24.99/mo), webhook handler | `billing/models.py`, `billing/stripe_adapter.py`, `billing/routes.py` |
| E2-T02 | AwardWallet API adapter (fetch user balances via API) | `portfolio/awardwallet.py`, `portfolio/ports.py` (extend) |
| E2-T07 | Points expiration tracker (policy per program, 90/60/30 day alerts) | `portfolio/expiration.py` |

**Auth upgrade:** Replace test tokens in `identity/auth.py` with real JWT verification (Auth0 RS256). Keep test tokens for dev/test mode.

**Tests:** `tests/unit/test_billing.py`, `tests/unit/test_awardwallet.py`, `tests/unit/test_expiration.py`, `tests/contract/test_stripe_webhook.py`

### Sprint 3: Optimization Engine

**Branch:** `feature/CL-0feb6c6563-optimization-engine`
**New modules:** extend `optimization/`, `notifications/`, `search/`

| Task | What to Build | Files |
|------|---------------|-------|
| E2-T03 | Personalized optimizer (user balances → ranked action items) | `optimization/personal_optimizer.py` |
| E2-T04 | Alert system (devaluation + transfer bonus notifications) | `notifications/alerts.py`, `notifications/models.py` |
| E2-T05 | Bank vs Burn advisor (timing engine using CPP trends + bonuses) | `optimization/timing_advisor.py` |
| E2-T06 | Seats.aero integration (award availability search) | `search/award_search.py` |

**Tests:** `tests/unit/test_personal_optimizer.py`, `tests/unit/test_alerts.py`, `tests/unit/test_timing_advisor.py`, `tests/unit/test_award_search.py`

### Sprint 4: Charity Network

**Branch:** `feature/CL-0feb6c6563-charity-network`
**New modules:** `src/redeemflow/charity/`

| Task | What to Build | Files |
|------|---------------|-------|
| E3-T01 | Charity data model (state, category, org, chapter URL, 501c3 status) | `charity/models.py` |
| E3-T02 | 50-state seed data (10 anchor orgs × 50 states + supplementary) | `charity/seed_data.py` or `data/charity_partners.json` |
| E3-T03 | Charity directory API (browse by state + category) | `charity/routes.py` |
| E3-T04 | Donation pipeline via Change API (points → dollar → charity) | `charity/donation_flow.py` |
| E3-T05 | Impact tracking (per-user + aggregate, micro-impact units) | `charity/impact.py` |

**Anchor orgs (all 50 states):** SBA WBC, Girl Scouts, Girls Who Code, Junior League, League of Women Voters, AAUW, GFWC, National PTA, Best Friends Animal Society, Habitat Women Build.

**Tests:** `tests/unit/test_charity_models.py`, `tests/unit/test_charity_directory.py`, `tests/unit/test_donation_flow.py`, `tests/unit/test_impact.py`

### Sprint 5: Community Pools + Pro

**Branch:** `feature/CL-0feb6c6563-community-pools`
**New modules:** `src/redeemflow/community/`

| Task | What to Build | Files |
|------|---------------|-------|
| E4-T01 | Pool data model (members, target charity, goal, pledges, status) | `community/models.py` |
| E4-T02 | Pool CRUD API (create, pledge, status, complete) | `community/routes.py` |
| E4-T03 | Auto-donate rules engine (if unused N days → donate) | `charity/auto_donate.py` |
| E4-T04 | Business travel optimizer (multi-card stacking) | `optimization/business_optimizer.py` |
| E4-T05 | Team points dashboard (consolidated earning, up to 10 cards) | `portfolio/team_dashboard.py` |
| E4-T06 | Subscription charity alignment (Pro → 5% to chosen charity) | `billing/charity_alignment.py` |

**Tests:** `tests/unit/test_community_pools.py`, `tests/unit/test_auto_donate.py`, `tests/unit/test_business_optimizer.py`, `tests/unit/test_team_dashboard.py`

### Sprint 6: Women's Travel Community

**Branch:** `feature/CL-0feb6c6563-travel-community`

| Task | What to Build | Files |
|------|---------------|-------|
| E5-T01 | Community forum (Pro tier discussions) | `community/forum.py` |
| E5-T02 | Women Founders Network (verified members, private community) | `community/founders_network.py` |
| E5-T03 | Conference travel planner (conference → optimized redemption options) | `search/conference_planner.py` |
| E5-T04 | Multigenerational trip planner (3+ travelers, cross-program optimization) | `optimization/multi_traveler.py` |
| E5-T05 | Safety layer (hotel safety scores, neighborhood ratings, women-recommend badges) | `search/safety_scores.py` |

**Tests:** `tests/unit/test_forum.py`, `tests/unit/test_founders_network.py`, `tests/unit/test_conference_planner.py`, `tests/unit/test_multi_traveler.py`, `tests/unit/test_safety.py`

---

## HOW TO ORCHESTRATE PARALLEL AGENTS

### Option A: Git Worktrees (Recommended)

Each sub-agent gets an isolated worktree. No merge conflicts during development.

```bash
# Create worktrees for Wave 1 (from main, after Sprint 1)
cd /Users/vorthruna/Projects/heymumford/redeemflow
git worktree add ../redeemflow-sprint2 -b feature/CL-0feb6c6563-premium-accounts main
git worktree add ../redeemflow-sprint4-seed -b feature/CL-0feb6c6563-charity-seed main

# Each agent works in its worktree independently
# When done: merge sprint2 → main, rebase sprint4-seed on main, continue
```

### Option B: Claude Code Agent Tool with isolation: "worktree"

```
Use the Agent tool with isolation: "worktree" parameter.
Each agent gets an auto-managed worktree.
Changes are returned on a named branch.
```

### Option C: Tmux + Multiple Claude Sessions

```bash
# Create tmux session with panes per sprint
tmux new-session -d -s redeemflow
tmux split-window -h
tmux split-window -v
# Each pane runs: claude --worktree "implement Sprint N per HANDOFF_BOOTSTRAP.md"
```

### Merge Protocol (Per Wave)

1. Agent completes work → runs `uv run pytest tests/ --cache-clear -q` → all pass
2. Agent runs `uv run ruff format src/ tests/ && uv run ruff check --fix src/ tests/`
3. Agent commits on feature branch, pushes
4. Orchestrator creates PR, waits for CI, merges to main
5. Next wave agents rebase on updated main
6. Repeat

### Conflict Resolution

If two agents touch the same file (e.g., `app.py` for router registration):
- Each agent adds its router independently
- Orchestrator resolves by combining both `include_router()` calls
- `app.py` is the only expected conflict point — each sprint adds one `include_router()` line

---

## CONVENTIONS (NON-NEGOTIABLE)

1. **TDD**: Write failing test → implement → green → refactor. No code without tests.
2. **Frozen dataclasses** for all value objects. Mutable only for state holders.
3. **`from __future__ import annotations`** in every file.
4. **Decimal** for all financial calculations. Never float for money.
5. **Protocol** for interfaces (not ABC).
6. **No AI attribution** in commits, PRs, code, or docs.
7. **Commit messages**: `feat(scope): message` — focus on why, not what.
8. **Branch names**: `feature/CL-0feb6c6563-{slug}`
9. **Test command**: `uv run pytest tests/ --cache-clear -q`
10. **Lint/format**: `uv run ruff format src/ tests/ && uv run ruff check --fix src/ tests/`
11. **Line length**: 120 (ruff enforced).
12. **Python**: 3.12+. Type hints on all public functions.

---

## PRODUCT CONTEXT

RedeemFlow fills the unoccupied "women-focused + points-optimized" market niche. No competitor combines travel points optimization with women-first design, community charity pooling, or state-by-state women-led charity networks.

**Tiers:**
- **Free** ($0): Calculators, transfer explorer, card recommender, savings dashboard — already built in Sprint 1
- **Premium** ($9.99/mo): Personalized optimization, real-time alerts, award search, charity donations
- **Pro** ($24.99/mo): Business optimizer, community pools, auto-donate, founders network, team dashboard

**Full product plan:** `task_plan.md` in repo root (547 lines, complete with research appendices)

---

## QUICK START

```bash
cd /Users/vorthruna/Projects/heymumford/redeemflow
git status                                    # Should be clean, on main
uv run pytest tests/ --cache-clear -q         # Should show 147 passed
cat task_plan.md                              # Full sprint plan with all details
```

Then: create worktrees for Wave 1, spawn sub-agents, begin TDD cycle.
