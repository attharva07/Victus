# Security hardening (early implementation)

## Why we hardened early
Security controls were introduced now (not deferred) because Victus already handles memory, file access, tool execution, and orchestration decisions. Early hardening reduces architectural debt, enforces boundaries before usage expands, and prevents accidental sensitive-data exposure in logs and API errors.

## Threat model assumptions
This hardening targets pragmatic local/backend threats:
- **Local attacker** with host-level read access to logs or local app data.
- **Malware or rogue local process** attempting to trigger unsafe tool execution paths.
- **Leaked logs** containing credentials, tokens, or sensitive payload fields.
- **Exposed endpoints** returning overly detailed errors in production.

Out of scope for this phase: full identity/authz redesign, encryption-at-rest, and secrets-management backends.

## Sensitivity model and enforcement rules
Memory records now support sensitivity levels:
- `public`
- `internal`
- `sensitive`
- `critical`

Rules:
1. Missing sensitivity defaults to `internal`.
2. Reads are filtered by a caller-provided maximum allowed sensitivity.
3. If allowed sensitivity is omitted, effective maximum is `internal`.
4. Retrieval count is capped by configuration (`MAX_MEMORY_RETRIEVAL`, default 5).

## MemoryService responsibilities and boundaries
`core.memory.service.MemoryService` is now the gateway for memory operations.

Responsibilities:
- Validate memory payload schema constraints relevant to persistence.
- Normalize and validate sensitivity.
- Enforce retrieval cap and sensitivity filtering.
- Persist through a repository adapter (`MemoryRepository`) only.

Boundary:
- Orchestrator/API memory operations call the service gateway functions.
- Database memory access is contained in `core.memory.store` repository methods.

## Logging and redaction strategy
A centralized structured logger wrapper (`log_event`) is used via `audit_event`.

Behavior:
- Emits JSON-like key/value payloads.
- Redacts known sensitive fields by key (`token`, `password`, `api_key`, `secret`, etc.).
- Redacts credential-like string patterns (`sk-*`, bearer tokens, key/value credential forms).
- Redaction is environment-configurable and forced on in production.

## Error handling policy (dev vs prod)
`VictusError` provides safe user-facing messages while preserving debuggability.

Policy:
- **dev**: show detailed message for local debugging.
- **prod**: return safe generic error text; do not leak stack traces/secret details.

FastAPI now includes a global unhandled exception sanitizer that returns controlled responses.

## Tool registry and permission boundaries
Tool execution is enforced by a registry map from action name to callable handler.

Policy boundaries:
- Actions execute only through registered handlers.
- Unknown/unregistered actions are blocked and audited.
- Additional allowlist enforcement is driven by central config `ENABLED_TOOLS`.

## Central config values
Security controls are centralized in `get_security_config()`:
- `ENV` (`dev`/`prod`)
- `MAX_MEMORY_RETRIEVAL` (default `5`)
- `CONFIDENCE_THRESHOLD`
- `LOG_REDACTION_ENABLED`
- `ENABLED_TOOLS`

Production mode hardens defaults by forcing redaction and stricter thresholds.

## Future hardening roadmap
Planned next layers:
1. Encryption at rest for memory and finance datasets.
2. Stronger endpoint authorization and per-tool permissions.
3. Managed key lifecycle/rotation and secure key storage.
4. Structured security telemetry and anomaly detection.
5. Optional tamper-evident audit log chaining.
