# Mail Intelligence domain module (read-only)

## 1) Architecture overview

`User -> Policy Gate -> Orchestrator -> Mail Intelligence Domain -> Mail Connector (read-only provider APIs)`

The module is intentionally split into two layers:

1. **Connector layer** (`connector.py`): mailbox API contracts and read-scope enforcement.
2. **Intelligence layer** (`normalization.py`, `intelligence.py`): parsing, summarization, priority classification, action extraction, digest generation.

`MailIntelligenceService` composes both layers and exposes read-only use-cases.

## 2) Folder/module structure

```text
core/mail_intelligence/
  __init__.py
  connector.py        # provider boundary + fail-closed guard
  intents.py          # orchestrator action names
  models.py           # Pydantic contracts
  normalization.py    # parsing + quote/signature cleanup
  intelligence.py     # priority/action/summarization logic
  service.py          # façade consumed by orchestrator
```

## 3) Data models (Pydantic)

Implemented in `core/mail_intelligence/models.py`:

- `EmailMetadata`
- `NormalizedEmail`
- `ThreadSummary`
- `ActionItem`
- `PriorityScore` + `PriorityClassification`
- `DigestResult`

## 4) Proposed Victus action names / intents

`core/mail_intelligence/intents.py` defines:

- `mail.list_unread`
- `mail.summarize_email`
- `mail.summarize_thread`
- `mail.get_digest`
- `mail.extract_actions`
- `mail.classify_priority`

## 5) Policy gate integration notes

- Add mail intents to policy allowlist only when connector read-scope is configured in deployment.
- Explicitly deny any non-read actions (`mail.send`, `mail.reply`, `mail.delete`, `mail.archive`) at policy level.
- Keep fail-closed behavior in module guard even if policy misconfiguration occurs.

## 6) Orchestrator integration notes

- Register handlers that map orchestrator intent parameters to `MailIntelligenceService` methods.
- Return deterministic responses first (rules-based intelligence), then layer optional cognition model later.
- On connector/permission errors, return deterministic safe response (`No action executed`) with redacted audit fields.

## 7) Starter scaffolding in this change

- `ReadOnlyConnectorGuard` enforces `enabled`, credentials present, and read scope granted.
- `EmailNormalizer` performs whitespace normalization and removes quoted reply/signature segments.
- `Summarizer`, `RulesPriorityScorer`, and `ActionExtractor` provide deterministic baseline intelligence.
- `MailIntelligenceService` exposes:
  - `list_unread`
  - `summarize_email`
  - `summarize_thread`
  - `extract_actions`
  - `get_digest`

## 8) Security notes and tradeoffs

- **Read-only by construction**: connector protocol only exposes `list/get` operations.
- **Fail-closed**: missing config/credentials/scope raises `MailConnectorError` before connector calls.
- **Redacted logging**: service audits include hashes for message/thread IDs, not raw body content.
- **Tradeoff**: rules-based extraction is deterministic and safe but less accurate than ML; designed for pluggable future cognition without changing service contract.

## 9) Phased implementation plan

1. **Phase 1 (current scaffold)**
   - Connector boundary, models, deterministic normalization/summarization/extraction/priority, digest.
2. **Phase 2 (provider integration)**
   - Implement Gmail/Graph adapters for `MailConnector`; add pagination and retry strategy.
3. **Phase 3 (policy/orchestrator wiring)**
   - Add intent parsing/routing and API contracts.
4. **Phase 4 (cognition add-on)**
   - Add optional cognition scorer/summarizer behind feature flag, preserving rules-first fallback.
5. **Phase 5 (hardening)**
   - Metrics, red-team prompt tests for leakage, and regression suite for thread cleaning.

---

## Example request/response payloads

### `mail.list_unread`

Request:

```json
{
  "action": "mail.list_unread",
  "parameters": {"limit": 20}
}
```

Response:

```json
{
  "message": "Listed unread emails.",
  "result": {
    "count": 2,
    "emails": [
      {
        "metadata": {
          "message_id": "m_123",
          "thread_id": "t_9",
          "subject": "Q3 launch blockers",
          "sender": "lead@vendor.com",
          "recipients": ["you@company.com"],
          "cc": [],
          "sent_at": "2026-02-12T14:10:00Z",
          "received_at": "2026-02-12T14:10:03Z",
          "labels": ["INBOX", "UNREAD"],
          "is_unread": true,
          "has_attachments": false
        },
        "cleaned_text": "Can you confirm launch readiness by 4pm?"
      }
    ]
  }
}
```

### `mail.summarize_email`

```json
{
  "action": "mail.summarize_email",
  "parameters": {"message_id": "m_123"}
}
```

```json
{
  "message": "Summarized email.",
  "result": {
    "summary": "Can you confirm launch readiness by 4pm?",
    "priority": {
      "classification": "high",
      "score": 0.8,
      "reasons": ["unread", "urgent_keywords", "action_language"]
    }
  }
}
```

### `mail.summarize_thread`

```json
{
  "action": "mail.summarize_thread",
  "parameters": {"thread_id": "t_9"}
}
```

### `mail.extract_actions`

```json
{
  "action": "mail.extract_actions",
  "parameters": {"message_id": "m_123"}
}
```

### `mail.get_digest`

```json
{
  "action": "mail.get_digest",
  "parameters": {"limit": 25}
}
```

## Rules-first priority scoring example

Baseline scoring used by `RulesPriorityScorer`:

- start at `0.2`
- `+0.2` if unread
- `+0.4` if urgent keyword exists (`urgent`, `asap`, `blocking`, `outage`, `sev1`, `p1`)
- `+0.1` for external sender heuristic
- `+0.2` for action language (`please`, `can you`, `need you`, `follow up`)
- clamp to `[0.0, 1.0]`
- map score -> class (`critical`, `high`, `normal`, `low`)

## Thread cleaning approach (quoted replies/signatures)

`EmailNormalizer` cleanup:

- normalize line endings and trailing whitespace
- stop at quoted-history markers:
  - `On ... wrote:`
  - `From:`
  - `Sent:`
  - `>`
- drop signature tails from common markers:
  - `--`
  - `Best,`
  - `Thanks,`
  - `Sent from my ...`

## Boundary: connector vs intelligence

- **Connector layer** is only mailbox transport (`list_unread`, `get_message`, `list_thread`) and permission prechecks.
- **Intelligence layer** never calls provider APIs directly; it only consumes `RawEmail`/`NormalizedEmail`.
- This keeps provider swaps and future cognition upgrades isolated.

## Recommendation: one module with subservices vs many services

- **A. One mail domain module with subservices**
  - pros: cohesive policy surface, shared normalization model, easier digest/thread composition, less duplicated connector logic.
  - cons: larger package ownership.
- **B. Multiple independent services**
  - pros: finer deployment boundaries.
  - cons: duplicated parsing/scoring contracts, more cross-service orchestration overhead.

**Recommendation: A. one mail domain module with subservices.** It best fits current Victus architecture and keeps a single secure read-only boundary while still allowing internal subservice modularity.
