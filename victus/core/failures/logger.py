"""Append-only JSONL failure logger."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from .schema import FailureEvent, RESOLUTION_STATUSES


class FailureLogger:
    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.last_skipped = 0

    def _file_for_date(self, ts: datetime) -> Path:
        return self.base_dir / f"failures_{ts.year:04d}-{ts.month:02d}.jsonl"

    def append(self, event: FailureEvent) -> None:
        """Append a single failure event to the JSONL log."""

        ts = datetime.fromisoformat(event.ts)
        log_file = self._file_for_date(ts)
        with log_file.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event.to_dict(), ensure_ascii=False))
            fh.write("\n")

    def _iter_file_events(self, file_path: Path) -> Iterable[FailureEvent]:
        if not file_path.exists():
            return
        with file_path.open("r", encoding="utf-8") as fh:
            for line in fh:
                try:
                    data = json.loads(line)
                    yield FailureEvent.from_dict(data)
                except Exception:
                    self.last_skipped += 1
                    continue

    def _iter_all_events(self) -> Iterable[FailureEvent]:
        self.last_skipped = 0
        for file_path in sorted(self.base_dir.glob("failures_*.jsonl")):
            yield from self._iter_file_events(file_path)

    def _month_range(self, start: datetime, end: datetime) -> List[Path]:
        current = datetime(start.year, start.month, 1, tzinfo=start.tzinfo)
        end_month = datetime(end.year, end.month, 1, tzinfo=end.tzinfo)
        files: List[Path] = []
        while current <= end_month:
            files.append(self._file_for_date(current))
            next_month = current + timedelta(days=32)
            current = datetime(next_month.year, next_month.month, 1, tzinfo=current.tzinfo)
        return files

    def iter_events(self, start: datetime, end: datetime) -> Iterable[FailureEvent]:
        """Yield events between ``start`` and ``end`` (inclusive)."""

        self.last_skipped = 0
        for file_path in self._month_range(start, end):
            if not file_path.exists():
                continue
            for event in self._iter_file_events(file_path):
                try:
                    ts = datetime.fromisoformat(event.ts)
                except ValueError:
                    self.last_skipped += 1
                    continue
                if ts < start or ts > end:
                    continue
                yield event

    def get_failure(self, event_id: str) -> Optional[FailureEvent]:
        latest: Optional[FailureEvent] = None
        latest_ts = datetime.min.replace(tzinfo=timezone.utc)
        for event in self._iter_all_events():
            if event.event_id != event_id:
                continue
            try:
                event_ts = datetime.fromisoformat(event.ts)
            except ValueError:
                self.last_skipped += 1
                continue
            if event_ts >= latest_ts:
                latest = event
                latest_ts = event_ts
        return latest

    def list_failures(
        self,
        start: datetime,
        end: datetime,
        filters: Optional[Dict[str, str]] = None,
    ) -> List[FailureEvent]:
        filters = filters or {}
        latest_by_id: Dict[str, FailureEvent] = {}
        for event in self.iter_events(start, end):
            latest_by_id[event.event_id] = event
        filtered: List[FailureEvent] = []
        for event in latest_by_id.values():
            if filters.get("domain") and event.domain != filters["domain"]:
                continue
            if filters.get("severity") and event.severity != filters["severity"]:
                continue
            if filters.get("category") and event.category != filters["category"]:
                continue
            if filters.get("status"):
                status = event.resolution.get("status")
                if status != filters["status"]:
                    continue
            filtered.append(event)
        filtered.sort(key=lambda e: e.ts)
        return filtered

    def update_resolution(self, event_id: str, status: str, note: str | None = None) -> FailureEvent:
        if status not in RESOLUTION_STATUSES:
            raise ValueError("Invalid resolution status")
        existing = self.get_failure(event_id)
        if not existing:
            raise KeyError(event_id)
        resolved_ts = _resolution_ts(status)
        updated = FailureEvent.from_dict(
            {
                **existing.to_dict(),
                "ts": datetime.now(timezone.utc).isoformat(),
                "event_id": event_id,
                "resolution": {
                    "status": status,
                    "resolved_ts": resolved_ts,
                    "notes": note,
                },
            }
        )
        self.append(updated)
        return updated


def _resolution_ts(status: str) -> Optional[str]:
    if status in {"resolved", "wont_fix"}:
        return datetime.now(timezone.utc).isoformat()
    return None
