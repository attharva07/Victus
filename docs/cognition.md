# Cognition Layer (DecisionAdvisor)

The cognition layer is an **advisory-only** module for orchestration. It never executes tools or bypasses policy.

## Flow
1. Existing intent parser resolves a base action.
2. `DecisionAdvisor.evaluate(...)` generates and ranks candidate actions.
3. `PolicyGate` (`evaluate_candidates`) evaluates each candidate (allow/deny + reason).
4. `DecisionAdvisor.rerank_after_policy(...)` reranks only allowed candidates.
5. Orchestrator executes the top allowed candidate (or returns clarify/no-allowed response).
6. Audit logging records cognition plan and selection.

## Objects
- `CandidateAction`
  - `action: str`
  - `parameters: dict`
  - `score_total: float`
  - `score_breakdown: dict[str, float]` with `risk`, `effort`, `utility`, `confidence`, `reversibility`, `time`
  - `rationale: str`
  - `required_permissions: list[str]`
  - `tags: list[str]`
- `DecisionPlan`
  - `candidates: list[CandidateAction]`
  - `selected: CandidateAction | None`
  - `notes: list[str]`
  - `trace_id: str`

## Heuristics (v1)
Deterministic weighted scoring:
- Risk by action namespace and destructive patterns (`admin.*`, `*delete*`, `finance.*`).
- Effort by parameter complexity.
- Utility by intent match + context boosts (e.g., `exam_week`).
- Reversibility (`archive`/`trash`/`draft` higher than hard delete).
- Confidence from context (`intent_confidence`/`confidence`).
- Time approximation derived from effort.

## Audit Events
- `cognition.plan` includes `trace_id`, original candidates, policy decisions, and reranked list.
- `cognition.selection` includes selected action and reason.
