from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from victus.engines import LogicEngine, PersonalityEngine


def main() -> None:
    prompts_path = Path("prompts/test_prompts.txt")
    prompts = [line.strip() for line in prompts_path.read_text().splitlines() if line.strip()]

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = Path("out/engine_runs") / timestamp
    out_dir.mkdir(parents=True, exist_ok=True)

    logic = LogicEngine()
    personality = PersonalityEngine()

    decisions = Counter()
    reasons = Counter()
    confidences: list[float] = []

    for index, prompt in enumerate(prompts, start=1):
        orchestrator_result = logic.run(prompt, context={})
        rendered_result = personality.render(orchestrator_result, profile={"tone": "neutral", "verbosity": "normal"})
        bundle = {
            "prompt": prompt,
            "orchestrator_result": orchestrator_result.to_dict(),
            "rendered_result": rendered_result.model_dump(),
        }
        (out_dir / f"run_{index:02d}.json").write_text(json.dumps(bundle, indent=2))
        decisions[orchestrator_result.decision] += 1
        reasons[orchestrator_result.policy.reason_code] += 1
        confidences.append(orchestrator_result.confidence)

    summary = {
        "counts": dict(decisions),
        "average_confidence": (sum(confidences) / len(confidences)) if confidences else 0.0,
        "most_common_reason_codes": reasons.most_common(5),
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
