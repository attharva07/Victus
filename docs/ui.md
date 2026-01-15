# Victus UI

## Layout
- Single chat input with streaming output
- Status pill: Connected / Thinking / Executing / Done / Error
- Right-side panels with tabs:
  - Activity
  - Tools
  - Memory
  - Finance

## Data feeds
- `POST /api/turn` (SSE) for streaming tokens and turn events
- `GET /api/logs/stream` for global event logs
- Finance routes for summaries and exports

## Finance tab
- Add transaction form
- Monthly summary widget
- Markdown export preview
