# Victus AI 2.0

Victus AI 2.0 is a local-first FastAPI backend with policy-gated orchestration for memory, finance, filesystem sandboxing, and camera tooling.

## Supported run path

### 1) Backend API (supported)
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn apps.local.main:app --host 127.0.0.1 --port 8000
```

API docs:
- Swagger UI: <http://127.0.0.1:8000/docs>
- OpenAPI JSON: <http://127.0.0.1:8000/openapi.json>

### 2) UI
No production UI is shipped in this repository after cleanup. Legacy UI implementations were removed or quarantined to avoid conflicting startup paths.

## Testing
Run all tests:
```bash
python -m pytest
```

## Project layout
- `apps/local/main.py`: primary FastAPI application entrypoint.
- `core/`: backend services (auth, memory, finance, files, camera, orchestrator).
- `victus/`: policy/planner/executor domain logic used by tests and local flows.
- `victus/core/confidence/`: namespaced confidence subsystem (core, events, store, and legacy compatibility).
- `victus_local/`: compatibility helpers still used by unit tests.
- `docs/`: active documentation.
- `docs/legacy/`: quarantined historical docs.

## Cleanup report
See `CLEANUP_REPORT.md` for full removal and quarantine rationale.
