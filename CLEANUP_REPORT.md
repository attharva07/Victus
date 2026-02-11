# CLEANUP_REPORT

## Scope and approach
Repository was reviewed for duplicated UI stacks, temporary scripts, and conflicting run paths. Cleanup prioritized one supported backend path, removal of clearly legacy artifacts, and documentation consistency.

## Removal and major change log

### 1) Removed temporary desktop popup runner
- **Removed**: `run_ui_temp.py`
- **Why**: Legacy/temporary script (`temp` naming, PySide popup path) outside the maintained API workflow.
- **Status**: Deleted.

### 2) Removed standalone Spotify auth helper
- **Removed**: `spotify_auth.py`
- **Why**: One-off manual helper, not part of current automated backend run path or tests.
- **Status**: Deleted.

### 3) Removed duplicate Vite web UI tree
- **Removed**: `web-ui/` (entire directory)
- **Why**: Unverified and conflicting frontend path; endpoint expectations diverged from primary backend routes, creating ambiguity.
- **Status**: Deleted.

### 4) Removed unused legacy static frontend assets
- **Removed**: `victus_local/static/` (entire directory)
- **Why**: Duplicated/legacy static bundle not used by the active backend entrypoint and overlapping with other frontend assets.
- **Status**: Deleted.

### 5) Quarantined phase/demo docs
- **Moved to quarantine**:
  - `docs/DEMO_PHASE3.md -> docs/legacy/DEMO_PHASE3.md`
  - `docs/DEMO_PHASE4.md -> docs/legacy/DEMO_PHASE4.md`
  - `docs/DEMO_PHASE4_TEMP.md -> docs/legacy/DEMO_PHASE4_TEMP.md`
  - `docs/PHASE_STATUS.md -> docs/legacy/PHASE_STATUS.md`
- **Why**: Historical phase docs were partially outdated and mixed with active documentation.
- **Status**: Quarantined under `docs/legacy/`.

### 6) Documentation rewrite for unambiguous run path
- **Changed**: `README.md`, `docs/ui.md`
- **Why**: Prior docs advertised multiple UI/backend startup paths and outdated UI claims.
- **What changed**: README now documents one supported backend command (`uvicorn apps.local.main:app`) and states no maintained bundled UI.

### 7) Route validation test coverage expansion
- **Added**: `tests/unit/test_api_route_smoke.py`
- **Why**: To enforce that all primary FastAPI routes return valid responses in a bootstrapped/authenticated flow.
- **Tests removed?** No tests were removed.


### 8) Quarantined Spotify setup doc
- **Moved to quarantine**: `docs/spotify_setup.md -> docs/legacy/spotify_setup.md`
- **Why**: Referenced removed helper workflow and no longer matches supported run path.
- **Status**: Quarantined under `docs/legacy/`.

### 9) Updated local compatibility README
- **Changed**: `victus_local/README.md`
- **Why**: Prevent conflicting run instructions and clarify compatibility-only status.

## Final category summary

- **backend endpoints removed**: None (kept existing API surface; added smoke coverage instead).
- **frontend/UI files removed**:
  - `web-ui/`
  - `victus_local/static/`
  - `run_ui_temp.py`
- **tools/scripts removed**:
  - `spotify_auth.py`
- **docs rewritten or deleted**:
  - Rewritten: `README.md`, `docs/ui.md`, `victus_local/README.md`
  - Quarantined: `docs/DEMO_PHASE3.md`, `docs/DEMO_PHASE4.md`, `docs/DEMO_PHASE4_TEMP.md`, `docs/PHASE_STATUS.md`, `docs/spotify_setup.md` -> `docs/legacy/`
