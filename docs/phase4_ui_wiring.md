# Phase 4 UI Wiring: Web UI → Real FastAPI Backend

## Overview

```
Browser (React/Vite UI in apps/web)
        |
        |  fetch('/...')
        v
Vite dev server proxy (apps/web/vite.config.ts)
        |
        |  forwards API routes
        v
FastAPI app (apps.local.main:app)
```

The UI now defaults to real backend calls. Mock/local response fabrication is no longer the default execution path.

## API Base Rules

- The client reads `import.meta.env.VITE_API_URL` in `apps/web/src/lib/api.ts`.
- If `VITE_API_URL` is empty, client uses relative URLs (`"" + path`) so Vite proxy handles routing.
- If `VITE_API_URL` is set, requests go directly to that base URL.

## Auth + Token Lifecycle

- Login endpoint: `POST /login` with `{ username, password }`.
- Token is read/written via:
  - `getToken()`
  - `setToken()`
- Local storage key: `victus_token`.
- `apiFetch()` injects `Authorization: Bearer <token>` automatically when token exists.

## UI Surface Wiring

### App startup / auth shell
- **Component**: `apps/web/src/App.tsx`
- **Trigger**: initial render
- **Call**: `GET /bootstrap/status`
- **Flow**:
  - If `bootstrapped=false`: show bootstrap init form → `POST /bootstrap/init`.
  - If bootstrapped and no token: show login form → `POST /login`.
  - After login: token persisted and authenticated state enabled.
- **Failure modes**:
  - 4xx/5xx from bootstrap/login shown in status banner with status + excerpt.

### Command Dock → Orchestrate
- **Components**:
  - Input: `apps/web/src/components/CommandDock.tsx`
  - Handler: `apps/web/src/App.tsx` + `apps/web/src/store/uiState.ts`
- **Trigger**: user presses Enter in command dock.
- **Call**: `POST /orchestrate` payload `{ text }` with bearer auth.
- **Response handling**:
  - JSON response pretty-printed into dialogue as system message.
  - Errors include HTTP status and body excerpt.
- **Failure modes**:
  - Not authenticated: user is prompted to login (no mock ack).
  - 401/403/500 responses appended as system error text.

### Dialogue widget
- **Component**: `apps/web/src/components/widgets/FocusWidgets.tsx`
- **Data source**: `useUIState()` dialogue messages in `apps/web/src/store/uiState.ts`
- **Behavior**: displays real orchestrate output and backend UI state dialogue feed.

### Memories tab
- **Component**: `apps/web/src/views/MemoriesScreen.tsx`
- **Trigger**: switch to Memories tab while authenticated.
- **Call**: `GET /memory/list`
- **Behavior**: renders backend payload JSON.
- **Not implemented handling**: 404 shows “Not implemented server-side.”

### Finance tab
- **Component**: `apps/web/src/views/FinanceScreen.tsx`
- **Trigger**: switch to Finance tab while authenticated.
- **Call**: `GET /finance/summary`
- **Behavior**: renders backend payload JSON.
- **Not implemented handling**: 404 shows “Not implemented server-side.”

### Files tab
- **Component**: `apps/web/src/views/FilesScreen.tsx`
- **Trigger**: switch to Files tab while authenticated.
- **Call**: `GET /files/list`
- **Behavior**: renders backend file list.
- **Not implemented handling**: 404 shows “Not implemented server-side.”

### Camera tab
- **Component**: `apps/web/src/views/CameraScreen.tsx`
- **Trigger**: switch to Camera tab while authenticated.
- **Call**: `GET /camera/status`
- **Behavior**: renders backend payload JSON.
- **Not implemented handling**: 404 shows “Not implemented server-side.”

## Request Contracts (UI-side)

- `apiFetch(path, opts)`:
  - Adds JSON `Content-Type` when body exists.
  - Adds bearer token header when available.
  - Throws structured `ApiError` with:
    - `status`
    - `contentType`
    - `bodyExcerpt`
    - `path`
    - `method`

## Wire Test

- File: `apps/web/e2e/ui_backend_wire.spec.ts`
- Validates the browser triggers:
  - `GET /bootstrap/status`
  - `POST /login`
  - `POST /orchestrate`
- Uses pathname-based tracking to work with Vite proxy URL rewriting.
- On failure prints request/response diagnostics including status, headers, and body excerpt.

## Runbook

From repository root:

1. `npm install`
2. `npm run dev`
3. `npm run test:wire`
4. `python scripts/contract_check.py`

## Why We Removed Mocks

- Mock acknowledgements masked missing backend integration (e.g., command responses looked successful without real `/orchestrate` calls).
- Real backend wiring exposes auth/bootstrap issues early and makes e2e wire tests meaningful.
- Explicit 404 “Not implemented server-side” messages prevent silent data fabrication.
