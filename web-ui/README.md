# Victus Phase 4 Web UI (desktop-first)

Lovable-style dashboard UI built with Vite + React + TypeScript + Tailwind.

## Run

```bash
cd web-ui
npm install
npm run dev
```

## API base URL

Set `VITE_API_BASE_URL` in `web-ui/.env`.

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Default when unset: `http://127.0.0.1:8000`.

## Auth model

- Login accepts a bearer token.
- UI verifies login by calling `GET /me`.
- Token is stored **in React memory only** (context state).
- No `localStorage`, `sessionStorage`, or IndexedDB auth persistence.
- Logout clears in-memory token.

## Endpoint assumptions

The UI tries the requested Phase 4 endpoints first and falls back to common `/api/*` variants when available:

- `GET /me`
- Logs: `GET /logs` (fallback `/api/logs`)
- Memories: `GET /memory/search?q=...`, `POST /memory`, `DELETE /memory/{id}`
- Finance: `POST /finance/transaction`, `GET /finance/transactions`, `GET /finance/summary`
- Chat: `POST /chat` (fallback `/api/chat`)
- Files: `GET /files/list?path=...`, `GET /files/read?path=...`
- Camera: `GET /camera/status`, `POST /camera/capture`
- Settings: `GET /settings`, `PATCH /settings`

If a backend endpoint does not exist, the UI shows API errors and/or read-only state (settings tab).

## CORS note

If your backend runs on a separate origin/port and requests fail in browser, allow the web UI origin in backend CORS (for example `http://localhost:5173`).

## Curl parity checklist

- [x] Login flow with `/me` verification.
- [x] Chat request UI (`POST /chat` compatible payload).
- [x] Logs/Audit read-only table + filter + detail view.
- [x] Memory search/add/delete with delete confirmation.
- [x] Finance add/list/summary.
- [x] Files list/read.
- [x] Camera status/manual capture.
- [x] Settings read and conditional patch/write.

