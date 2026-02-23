# Phase 4 Frontend ↔ Backend Wiring

## Dev architecture

During development, the UI runs on `http://127.0.0.1:5173` and the API runs on `http://127.0.0.1:8000`.

The FastAPI app enables CORS for `http://127.0.0.1:5173` and `http://localhost:5173` so the dev UI can call backend endpoints on port `8000` directly from the browser.

Frontend requests use **relative paths** and are forwarded through the Vite dev proxy:

`UI (5173) -> Vite proxy -> API (8000)`

## API routes used by the Phase 4 UI

- `GET /bootstrap/status`
- `POST /login`
- `POST /orchestrate`

Additional authenticated UI routes are also proxied under `/api` plus domain endpoints (`/memory`, `/finance`, `/files`, `/camera`, `/me`).

## Token lifecycle

- The access token is stored in `localStorage` under key: `victus_token`.
- `POST /login` returns the token.
- The shared `apiFetch` client automatically adds `Authorization: Bearer <token>` for non-login calls.
- Clearing/invalidating auth removes `victus_token` from storage.

## Why “HTML instead of JSON” happens without proxy

If the frontend sends `/bootstrap/status` to port `5173` without a proxy, Vite handles the request as a frontend route and returns HTML (or 404 page HTML) instead of API JSON.

That HTML response then fails JSON parsing in the UI and appears as fetch/parsing errors.

## Run locally

Backend:

```bash
python -m uvicorn apps.local.main:app --host 127.0.0.1 --port 8000
```

Frontend:

```bash
npm --prefix apps/web install
npm --prefix apps/web run dev -- --host 127.0.0.1 --port 5173
```
