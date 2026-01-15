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
