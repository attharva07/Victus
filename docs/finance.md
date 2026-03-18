# Finance Domain Architecture

## Current structure

The active finance subsystem is consolidated around `core/finance` and split into explicit layers:

- `core/finance/schemas.py` — typed request/response contracts, validation, category normalization, and deterministic amount/date handling.
- `core/finance/entities.py` — domain entities for `Account`, `Category`, and `Transaction`.
- `core/finance/repository.py` — SQLite-backed repository and additive schema migration support for ledger data.
- `core/finance/service.py` — ledger core business logic, summaries, account support, and backward-compatible service entry points used by the API and orchestrator.
- `core/finance/policy.py` — finance-scoped fail-closed policy/validation exceptions.
- `core/finance/audit.py` — redaction-safe finance audit hooks.
- `core/finance/intelligence.py` — deterministic finance-only heuristics and rule engines.
- `core/finance/store.py` — persistence for alerts, behavior logs, and configurable finance rules.

## Ledger Core responsibilities

Ledger Core now provides deterministic CRUD and reporting for:

- `Account`
- `Transaction`
- `Category`

Supported capabilities:

- create transaction
- update transaction
- delete transaction
- get transaction by id
- list transactions
- spending summary
- category summary
- account-aware filtering and summaries

## Security and policy posture

The finance domain remains policy-first:

- service actions are allowlisted in `core/finance/policy.py`
- malformed inputs fail closed with explicit errors
- no domain logic is hidden inside transport handlers
- destructive actions are audited
- free-form notes are redacted before audit logging
- orchestrator compatibility is preserved without adding cognition or smart routing into orchestrator

## Compatibility notes

Legacy compatibility surfaces (`apps/local/main.py`, `core/domains/finance/handlers.py`, and `victus/finance/service.py`) now route into the shared ledger core instead of maintaining a separate data model.

## Near-term next steps

1. Budgets: move budget configuration from loose snapshots into first-class stored budget entities and policies.
2. Bills/reminders: attach due dates and reminder workflows to accounts/payees.
3. Recurring expenses: persist confirmed recurring merchants and suppression decisions.
4. Anomaly detection: add deterministic outlier scoring on top of normalized ledger history.
5. Insights/guidance: layer explainable finance guidance on top of summaries and rules without changing orchestrator behavior.
