# Phase 1 Assumptions

- The Phase 1 auth flow uses a single local admin account stored in `auth.json` within the data directory, with the password sourced from `VICTUS_ADMIN_PASSWORD` or defaulting to `admin` if unset.
- Orchestrator intent classification is deterministic first, with an LLM stub returning no intent in Phase 1.
- The vault sandbox provides path safety utilities only; no file IO endpoints are implemented.
