# Victus Architecture (Phase 1 Foundation)

## Locked roadmap note
Victus Local is operating under a locked roadmap. This repository only implements Cleanup + Phase 1 foundations. Phase 2 modules (memory, finance, vault file ops, camera) are **not** implemented beyond scaffolding/interfaces.

## Local-only binding
The Local runtime binds to `127.0.0.1` only. No external network exposure is supported.

## Phase 1 module layout
```
apps/
  local/
    main.py        # FastAPI entry for local runtime
    launcher.py    # process supervisor entry
core/
  orchestrator/
    router.py      # 3-layer skeleton
    schemas.py     # Pydantic intents
    policy.py      # policy gates
  logging/
    audit.py       # audit logger
    logger.py      # unified logger config
  security/
    auth.py        # local auth + roles
    api_keys.py    # api key handling
  vault/
    sandbox.py     # safe path join + allowlist checks
adapters/
  llm/
    provider.py    # wrapper for LLM calls (no side effects)
  runtime/
    ollama.py      # start/stop/check ollama process
    supervisor.py  # spawn/stop child processes safely
```

## Data locations
Data is stored outside the repo in a stable OS path:
- Windows: `%APPDATA%/Victus/`
- Linux/macOS: `~/.victus/`

Logs live under `data_dir/logs/` and the vault sandbox reserves `data_dir/vault/` (no file IO features implemented in Phase 1).
