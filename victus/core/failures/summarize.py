from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List

from ..util.time import now_iso
from .store import list_failures

REPORTS_DIR = Path("data/reports/weekly")


def summarize(days: int = 7) -> str:
    failures = list_failures(since=days)
    severity_counts = Counter(f.severity for f in failures)
    status_counts = Counter(f.status for f in failures)
    pattern_counts = Counter(f.what_failed for f in failures)
    unresolved = [f for f in failures if f.status == "unresolved"]

    now = datetime.now(timezone.utc)
    start = now - timedelta(days=days)
    lines = [
        f"# Failure report ({start.date()} to {now.date()})",
        "",
        "## Totals by severity",
    ]
    for severity, count in severity_counts.items():
        lines.append(f"- {severity}: {count}")
    lines.append("")
    lines.append("## Totals by status")
    for status, count in status_counts.items():
        lines.append(f"- {status}: {count}")
    lines.append("")
    lines.append("## Top repeated failure patterns")
    for what, count in pattern_counts.most_common():
        lines.append(f"- {what}: {count}")
    lines.append("")
    lines.append("## Unresolved failures")
    for failure in unresolved:
        lines.append(f"- {failure.failure_id}: {failure.what_failed} ({failure.severity})")
    return "\n".join(lines)


def write_weekly_report(markdown: str) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now(timezone.utc).date().strftime("%Y_%m_%d")
    path = REPORTS_DIR / f"report_{today}.md"
    path.write_text(markdown)
    return path
