# Finance Domain Redesign (InvestAssist → Finance Cognition Layer)

## Phase A: Current Architecture Review

### Current state (before this redesign)
- Finance logic was split across two disconnected stacks:
  - `core/finance/*` used by orchestrator/local API.
  - `victus/finance/*` and `victus_local/api_finance.py` with a separate SQLite path.
- Primary supported behaviors were transaction logging, list, and simple period summary.
- No first-class credit-card lifecycle data, savings goals, recurring-expense inference, behavior analysis, or portfolio awareness.
- No structured finance alerts or recommendation objects persisted for review/audit.

### Key weaknesses and gaps
1. **Fragmented finance modules** (duplicated concepts across `core` and `victus_local`).
2. **Insufficient domain schema** (transactions-only emphasis).
3. **No deterministic finance rule engine** for due dates, utilization, budget thresholds, or concentration rules.
4. **No lightweight explainable cognition layer** for pattern drift/habit signals.
5. **No alert lifecycle storage** (`severity`, `reason`, `next_step`, `acked`).
6. **No migration-oriented boundary** for future centralized Victus brain integration.

### Preserve / Refactor / Replace
- **Preserve:** existing transaction APIs (`/finance/add`, `/finance/list`, `/finance/summary`) to avoid breaking clients.
- **Refactor:** finance internals into layered deterministic intelligence (`core/finance/intelligence.py` + enhanced service/store).
- **Replace:** ad hoc “summary-only” model with structured alerts/recommendations/reporting pipeline.
- **Deprioritize:** legacy `victus/finance` path (candidate for consolidation in follow-up migration phase).

---

## Phase B: Target Architecture

### Domain module boundaries
Finance Domain (`core/finance`):
1. **Finance Data Layer** → SQLite schema + typed store functions.
2. **Rule Engine** → deterministic threshold/rule evaluation.
3. **Finance Cognition Layer** → explainable pattern heuristics only (non-general intelligence).
4. **Alert Engine** → normalized alert shape + persistence.
5. **Recommendation Engine** → recommendations linked to rule reasons/patterns.
6. **Reporting Engine** → daily/weekly outputs for orchestrator/UI.
7. **API/Service Layer** → endpoints and orchestration (`apps/local/main.py`, `core/finance/service.py`).
8. **Policy hooks/audit** → existing audit logging retained and extended.

### Control flow
`User/API request → Finance service → Rule engine + Cognition → Alert/Recommendation generation → Reporting → Persist alert/behavior logs → Return structured response`

### Why this is better
- Deterministic-first, inspectable behavior.
- Explicit and auditable outputs with reason fields.
- Supports credit/budget/savings/investment awareness without autonomous action.
- Backward-compatible with existing transaction operations.

---

## Phase C: Schema / Models / Interfaces

Added finance-oriented tables in shared DB (`core/storage/db.py`):
- `finance_accounts`
- `finance_cards`
- `finance_budgets`
- `finance_budget_categories`
- `finance_savings_goals`
- `finance_savings_contributions`
- `finance_holdings`
- `finance_watchlist`
- `finance_recurring_expenses`
- `finance_reminders`
- `finance_alerts`
- `finance_behavior_logs`
- `finance_rules`

Core entity coverage now includes:
- accounts/cards + statement/due/autopay fields
- category/total budgets
- savings goals + contribution pacing
- recurring expenses
- holdings/watchlist awareness
- behavior logs
- configurable deterministic rules
- structured alerts/reminders

---

## Phase D: Implementation Summary

Implemented in `core/finance`:
- `FinanceRuleEngine`: deterministic alerts for credit, budget, savings, and investment-awareness thresholds.
- `FinanceCognition`: lightweight pattern detection:
  - spending drift
  - repeated merchant habit
  - post-payday spike
  - recurring-expense candidate detection
- `FinanceRecommendationEngine`: explainable guidance linked to rule/pattern source.
- `FinanceReportingEngine`: daily brief + weekly summary generation.
- `generate_finance_brief(snapshot)`: end-to-end pipeline and persistence for alerts/behavior logs.
- Rule threshold management APIs (`get_rule_thresholds`, `set_rule_threshold`).

API additions (`apps/local/main.py`):
- `POST /finance/intelligence/brief`
- `GET /finance/alerts`
- `GET /finance/behavior`
- `GET /finance/rules`
- `POST /finance/rules`

Backward compatibility retained:
- `POST /finance/add`
- `GET /finance/list`
- `GET /finance/summary`

---

## Phase E: Verification Coverage

Added tests in `tests/unit/test_finance_intelligence.py` for:
- deterministic credit + budget warning rules
- due-date and pre-statement warning logic
- recurring expense detection
- behavior pattern detection (drift + post-payday spike)
- reporting pipeline output contract

---

## Phase F: Non-goals and Safety Boundary

This finance redesign **does not** implement:
- consciousness or self-awareness
- autonomous investing or trade execution
- unrestricted agentic finance behavior
- cross-domain general brain logic

This is a scoped, deterministic + explainable finance cognition layer with human decision authority.

---

## Phase G: Migration & Implementation Plan

### Practical migration sequence
1. Keep existing finance endpoints alive (done).
2. Introduce new schema and engines in parallel (done).
3. Route UI/orchestrator to `intelligence/brief` and structured alerts progressively.
4. Consolidate or deprecate legacy `victus/finance` module after usage audit.
5. Add import/sync jobs for card statements, recurring detection feedback loops, and saved user preferences.

### MVP delivered in this change
- deterministic rules + configurable thresholds
- cognition heuristics + recurring detection
- alert + behavior log persistence
- recommendation and reporting pipeline
- API surface for intelligence output

### Recommended next tasks
1. Add statement-cycle and reminder scheduler jobs.
2. Add explicit user preference persistence (notification channels, quiet hours, risk profile).
3. Add portfolio valuation feed adapters (read-only).
4. Add recurring-expense suppression/confirm actions to reduce false positives.
5. Merge legacy `victus/finance` stack into `core/finance` and remove duplication.

## Architectural rationale (concise)
The design prioritizes deterministic, explainable, finance-scoped cognition: rules generate auditable alerts; lightweight heuristics add behavior context; recommendations remain advisory; all critical outputs are explicit and human-controlled.

## Assumptions
- Existing DB migration strategy is additive (`CREATE TABLE IF NOT EXISTS`), not destructive.
- External market/card feeds are out-of-scope for this PR and represented as request payload snapshots.
- Existing auth and policy layers continue to gate endpoint/tool access.

## Blocked/Ambiguous Items
- No canonical production feed contracts for card statements/holdings were present.
- Dual finance stack (`core/finance` vs `victus/finance`) requires product decision for final consolidation timeline.
