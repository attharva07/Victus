# Victus Local UI Prototype

Local-only FastAPI server that hosts a lightweight HTML/CSS/JS prototype UI for the current Victus pipeline.

## Setup

```bash
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r victus_local/requirements.txt
```

## Run

```bash
uvicorn victus_local.server:app --host 127.0.0.1 --port 8000
```

Open: <http://127.0.0.1:8000>

> **Security note:** keep the bind address at `127.0.0.1` so the server is local-only.

## Victus adapter wiring

The adapter uses the same Victus pipeline as `run_ui_temp.py` by calling `VictusApp.run_request` with an OpenAI/LLM step. Ensure your LLM provider configuration is set (see `victus/config/runtime.py`). If no provider is configured, the adapter will raise a clear error from the server response. If you want a placeholder response instead, adjust `victus_local/victus_adapter.py` accordingly.

## API

- `POST /api/chat` `{ "message": "..." }` -> `{ "reply": "..." }`
- `POST /api/task` `{ "action": "open_app" | "open_youtube", "args": {...} }`
- `WS /ws/logs` for live log events (fallback: `GET /api/logs/stream` for SSE)
