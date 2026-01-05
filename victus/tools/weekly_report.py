"""Generate weekly failure summaries."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Iterable, Tuple

from victus.core.failures import FailureEvent, FailureLogger


def _parse_week(value: str) -> Tuple[datetime, datetime]:
    if value == "current":
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=7)
        return start, end

    try:
        year_str, week_str = value.split("-W")
        year = int(year_str)
        week = int(week_str)
        start = datetime.fromisocalendar(year, week, 1).replace(tzinfo=timezone.utc)
        end = start + timedelta(days=7)
        return start, end
    except Exception as exc:
        raise argparse.ArgumentTypeError(f"Invalid week format: {value}") from exc


def _group_recurring(events: Iterable[FailureEvent]):
    groups: Dict[str, Dict[str, object]] = {}
    for event in events:
        stack_hash = event.failure.get("stack_hash")
        key = stack_hash or f"{event.failure.get('code')}:{event.component}"
        groups.setdefault(key, {"count": 0, "example": event})
        groups[key]["count"] += 1
    return groups


def _format_totals(events: Iterable[FailureEvent]) -> str:
    events = list(events)
    totals = Counter()
    by_domain = Counter()
    by_severity = Counter()
    by_category = Counter()
    for event in events:
        totals["total"] += 1
        by_domain[event.domain] += 1
        by_severity[event.severity] += 1
        by_category[event.category] += 1

    lines = ["## Totals", f"- Total: {totals['total']}"]
    lines.append("- By domain:")
    for domain, count in sorted(by_domain.items()):
        lines.append(f"  - {domain}: {count}")
    lines.append("- By severity:")
    for severity, count in sorted(by_severity.items()):
        lines.append(f"  - {severity}: {count}")
    lines.append("- By category:")
    for category, count in sorted(by_category.items()):
        lines.append(f"  - {category}: {count}")
    return "\n".join(lines)


def _format_recurring(groups: Dict[str, Dict[str, object]]) -> str:
    lines = ["## Top recurring issues"]
    if not groups:
        lines.append("- None recorded")
        return "\n".join(lines)

    sorted_groups = sorted(groups.items(), key=lambda item: item[1]["count"], reverse=True)
    for key, data in sorted_groups:
        example: FailureEvent = data["example"]
        lines.append(
            f"- {data['count']}x — component={example.component}, code={example.failure.get('code')}, key={key}"
        )
    return "\n".join(lines)


def _format_policy(events: Iterable[FailureEvent]) -> str:
    lines = ["## Policy-related failures"]
    filtered = [e for e in events if e.category == "policy_violation"]
    if not filtered:
        lines.append("- None")
        return "\n".join(lines)
    for event in filtered:
        lines.append(
            f"- [{event.component}] {event.failure.get('code')}: {event.failure.get('message')} (request={event.request_id})"
        )
    return "\n".join(lines)


def _format_backlog(groups: Dict[str, Dict[str, object]]) -> str:
    lines = ["## Suggested backlog items"]
    any_items = False
    for key, data in groups.items():
        if data["count"] >= 3:
            any_items = True
            example: FailureEvent = data["example"]
            lines.append(f"- Investigate {key} affecting {example.component} ({data['count']} occurrences)")
    if not any_items:
        lines.append("- None above threshold")
    return "\n".join(lines)


def generate_report(events: Iterable[FailureEvent]) -> str:
    events_list = list(events)
    recurring = _group_recurring(events_list)
    parts = [
        "# Weekly Failure Report",
        _format_totals(events_list),
        _format_recurring(recurring),
        _format_policy(events_list),
        _format_backlog(recurring),
    ]
    return "\n\n".join(parts)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate weekly failure report")
    parser.add_argument("--week", default="current", help='"current" or ISO week like 2026-W02')
    args = parser.parse_args(argv)

    start, end = _parse_week(args.week)
    logger = FailureLogger(Path("victus/data/failures"))
    events = list(logger.iter_events(start, end))

    report_body = generate_report(events)

    report_path = Path("victus/reports/weekly") / f"{start.isocalendar().year:04d}-{start.isocalendar().week:02d}.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report_body, encoding="utf-8")
    print(report_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
