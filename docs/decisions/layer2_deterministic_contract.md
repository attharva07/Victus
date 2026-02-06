# Layer 2 Deterministic Contract (Victus Local)

## Scope
Layer 2 handles deterministic intent parsing and routing for local operation only.

## Responsibilities
- Parse user text with strict deterministic patterns.
- Route only supported Phase 2/3 actions:
  - memory: `add`, `search`, `list`, `delete`
  - finance: `add_transaction`, `list_transactions`, `summary` (amount stored as cents)
  - files: `list`, `read`, `write` (sandbox + extension allowlist enforced)
  - camera stub: `status`, `capture`, `recognize` (gated by config)
- Execute actions and return structured results keyed by action list order.

## Non-goals / Must Never Do
- No guessing for unknown requests.
- No unsafe execution outside existing policy/sandbox rules.
- No auth bypass for protected endpoints.
- No automatic dependence on Layer 3 LLM in deterministic tests.

## Response Shapes
### Success
```json
{
  "intent": {
    "action": "memory.add",
    "parameters": {"content": "Remember this"},
    "confidence": 1.0
  },
  "message": "Saved memory ...",
  "actions": [
    {
      "action": "memory.add",
      "parameters": {"content": "Remember this"},
      "result": {"id": "..."}
    }
  ]
}
```

### Clarify
```json
{
  "error": "clarify",
  "message": "Please provide more detail so I can route this deterministically.",
  "fields": {"text": "include an explicit action and target"}
}
```

### Unknown intent
```json
{
  "error": "unknown_intent",
  "message": "I could not deterministically map that request to a supported action.",
  "candidates": ["memory", "finance", "files", "camera"]
}
```

## LLM fallback policy
LLM proposal is disabled by default. If `VICTUS_ENABLE_LLM_FALLBACK=true`, Layer 3 proposal can be considered, but deterministic outcomes remain preferred and unknown input should still return structured `clarify` / `unknown_intent` when no high-confidence deterministic route exists.

## Local bootstrap and auth contract
- `GET /bootstrap/status` exposes bootstrap state.
- `POST /bootstrap/init` initializes admin credentials only if not already bootstrapped.
- `POST /login`, `GET /me`, and `POST /orchestrate` require intended auth behavior (except login itself).
- Exposure is controlled by host binding (for local testing, bind to `127.0.0.1`).
