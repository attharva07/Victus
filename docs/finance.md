# Finance Logbook v1

## Overview
Finance v1 is a local-only SQLite logbook for tracking transactions, paychecks, and budgets. It powers the UI Finance tab and Victus finance tools.

## Database
`victus_data/finance/finance.db`

### Tables
1. `transactions`
2. `paychecks`
3. `budgets`

## Services
- `add_transaction`
- `list_transactions`
- `month_summary`
- `export_logbook_md`
- `paycheck_plan`

## API routes
- `POST /api/finance/transaction`
- `GET /api/finance/summary?month=YYYY-MM`
- `GET /api/finance/export?range=month&month=YYYY-MM`

## Logbook export
Exports a Markdown report with summary totals, transaction table, and category totals for the selected range.


## Deterministic orchestrate formats
The deterministic router supports finance transaction logging from both explicit and natural text forms:
- `finance.add_transaction: 6 Starbucks`
- `finance.add_transaction: $6 Starbucks`
- `add transaction $6 for Starbucks`
- `I spent $6 at Starbucks`
- `log $6 Starbucks`

These inputs map to `finance.add_transaction` with structured parameters (`amount`, `merchant`, `category`) and default `currency=USD` plus current UTC `occurred_at` when omitted.
