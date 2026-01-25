# Priority Fixes Changelog

## Priority 1: Open App loop/slot fix
- Added per-session state (pending tool, awaiting slot, pending slots) with deduping to prevent repeated executions and to treat the next user message as the app name when a clarification is active.
- Clarification state is now set both after tool-driven clarify responses and when the system asks “Which app should I open?” due to missing slots.

**Verification**
- Manual: send `open` → assistant asks “Which app should I open?”; reply `calculator` → tool runs once and replies “Opened Calculator.”
- Manual: send `open calculator` → tool runs immediately with no extra clarification.
- Manual: send `open` then rapidly resend the same message → tool runs once (deduped).

## Priority 2: Live dictionary (self-updating app aliases)
- Added persistent `app_dict.json` with canonical app entries, aliases, candidates, usage counts, and timestamps.
- Successful opens update alias stats and candidates; candidates promote to aliases after 3 confirmations, with atomic writes.
- Safety guardrails prevent learning suspicious aliases.

**Verification**
- Manual: open `calculator` → verify `app_dict.json` usage increments.
- Manual: open `calc` three times → candidate promoted to alias in `app_dict.json`.

## Priority 3: UI output cleanup
- Suppressed internal “Executing …” confidence messages from the user-visible chat stream.

**Verification**
- Manual: send `hello` → chat displays only the assistant response (no “Executing openai.generate_text.” prefix).
