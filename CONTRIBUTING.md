# Contributing to Victus AI 2.0

These rules are mandatory for every change. Behavior changes must also update at least one of: `README.md`, `docs/DEV_GUIDE.md`, `CONTRIBUTING.md`, or `docs/POLICY.md`.

## No Bypass Rule
- Policy is supreme. Never add debug flags, bypasses, or emergency switches that skip policy enforcement.
- Executor must refuse to run without a valid approval token and signature.

## Test Requirements
- All tests must run via `pytest`.
- Add or update unit, integration, security, and regression tests relevant to your change.
- Do not merge if tests are failing.

## Documentation Updates
- Update user-facing docs for any behavior change.
- Keep `docs/DEV_GUIDE.md` aligned with workflows and guardrails.

## Review Checklist
- [ ] Scope restated; confirm what changes and what does not
- [ ] Policy supremacy unchanged; segmentation between System and Productivity intact
- [ ] No raw shell or generic exec wrappers introduced
- [ ] Plan/Approval/Context schemas preserved
- [ ] Plugins enforce approval tokens and validate inputs
- [ ] Audit logging and redaction intact; screenshot capture explicit-only
- [ ] Tests added/updated (unit, integration, security, regression)
- [ ] Relevant docs updated (README, DEV_GUIDE, CONTRIBUTING, POLICY)
