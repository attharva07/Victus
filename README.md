# Victus AI 2.0

Victus AI 2.0 is a local-first FastAPI backend with policy-gated orchestration for memory, finance, filesystem sandboxing, and camera tooling.

## Run modes

### Development (backend + frontend separately)
Terminal 1 (backend):
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn apps.local.main:app --reload --host 127.0.0.1 --port 8000
```

Terminal 2 (frontend):
```bash
cd apps/web
npm install
npm run dev
```

Open <http://localhost:5173>.

### Production prep (Option A: FastAPI serves built UI)
Build the frontend:
```bash
cd apps/web
npm install
npm run build
```

Run backend from repo root:
```bash
python -m uvicorn apps.local.main:app --host 127.0.0.1 --port 8000
```

Open <http://127.0.0.1:8000> (UI is served by FastAPI when `apps/web/dist` exists).

API docs:
- Swagger UI: <http://127.0.0.1:8000/docs>
- OpenAPI JSON: <http://127.0.0.1:8000/openapi.json>

## Environment configuration
Frontend environment example lives at `apps/web/.env.example`.

- Dev default: `VITE_API_URL=http://127.0.0.1:8000`
- If deploying same-host with API namespaced (for example `/api`), `VITE_API_URL` can be set to `/api`.

## Testing
Run backend tests:
```bash
python -m pytest -q
```

Run UI tests:
```bash
cd apps/web
npm test
```

## Project layout
- `apps/local/main.py`: primary FastAPI application entrypoint.
- `apps/web/`: Vite + React Phase 4A UI.
- `core/`: backend services (auth, memory, finance, files, camera, orchestrator).
- `victus/`: policy/planner/executor domain logic used by tests and local flows.
- `victus/core/confidence/`: namespaced confidence subsystem (core, events, store, and legacy compatibility).
- `victus_local/`: compatibility helpers still used by unit tests.
- `docs/`: active documentation.
- `docs/legacy/`: quarantined historical docs.

## Cleanup report
See `CLEANUP_REPORT.md` for full removal and quarantine rationale.
