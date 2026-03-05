# Cognition v1

Cognition is now a **stateful decision layer** that sits between intent routing and tool orchestration.

## Pipeline
1. **Interpreter (LLM adapter)**
   - `interpret(text, context) -> IntentCandidate`.
   - Normalizes output and validates with strict schema (`extra=forbid`, strict types).
   - Invalid output falls back to noop/clarify path.
2. **Deliberator (deterministic)**
   - Input: `IntentCandidate + session_state + config`.
   - Output: `Decision` with `mode`, `risk`, `action_allowed`, optional clarification.
   - Handles confidence thresholds and ambiguity.
3. **Identity Controller**
   - Input: user text, decision, session state, memory candidates.
   - Output: persona mode, selected memories, state patch.
   - Persona override rules:
     - high/blocked risk -> `crisp_cautious`
     - emotional signals -> `warm`
     - default -> `jarvis_playful`
4. **Policy Gate**
   - Enforces allowlist, blocked actions, and high-risk confirmation handshake.
   - High risk requires `confirmation_token == "CONFIRM"`.
5. **Orchestrator (registry execution)**
   - Executes only through `TOOL_REGISTRY` handlers.
   - Cognition never calls tools directly.

## Intent schema (strict)
`IntentCandidate` fields:
- `action: str`
- `parameters: dict`
- `confidence: float`
- `requested_memory_ops: optional dict`
- `risk: optional enum (low|medium|high|blocked)`

Strict validation prevents unsafe auto-actions when malformed payloads arrive.

## Session state machine
Stored in in-memory `InMemorySessionStateStore`:
- `current_focus`
- `pending_clarification`
- `last_action`
- `last_intent`

Transitions:
- clarify -> sets `pending_clarification=True`
- act/suggest/refuse -> clears `pending_clarification`
- no clarification loops: if already pending and confidence is still low, deliberator emits `suggest` instead of another clarify loop.

## Clarification flow
- If confidence is below threshold, cognition returns `mode=clarify` with question.
- If risk is high without confirmation, policy gate blocks execution and asks for explicit `CONFIRM` handshake.

## Identity + memory selection
- Memories are capped (`memory_cap`, default 3).
- For high/blocked risk, sensitive memories are filtered out.
- Identity controller emits `state_patch` consumed by session store.

## Policy interaction details
`enforce_policy_gate(...)` checks:
- allowlist tool membership
- blocked action list
- risk status
- confirmation requirement for high-risk actions

On policy failure, orchestrator returns clarification instead of execution.
