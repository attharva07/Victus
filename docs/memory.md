# Memory v1

## Overview
Memory v1 is local, append-only, and auditable. Victus stores only explicit or safe, important user-provided memories.

## Storage
- Session memory: in-memory list (cleared on restart)
- Project memory: `victus_data/memory/project.jsonl`
- User memory: `victus_data/memory/user.jsonl`

Each line is a JSON object with the `MemoryRecord` schema:
```
{
  "id": "uuid",
  "ts": "2024-01-01T00:00:00Z",
  "scope": "user|project|session",
  "kind": "fact|decision|preference|todo|context",
  "text": "...",
  "tags": ["..."],
  "source": "user|victus|system",
  "confidence": 0.7,
  "pii_risk": "low|medium|high",
  "ttl_days": null
}
```

## Memory gate
Victus writes memory only when:
- The user explicitly says “remember/save this”, **or**
- A heuristic classifier flags the text as important and safe.

Automatic saving is blocked if:
- API keys, tokens, or passwords are detected.
- Banking credentials or high-risk PII appear.

Medium/high PII requires explicit user intent.

## Events
- `memory_used`: emitted when memory snippets are retrieved for a turn.
- `memory_written`: emitted when a memory record is appended.
