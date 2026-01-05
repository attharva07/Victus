"""Append-only JSONL failure logger."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable, List

from .schema import FailureEvent


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
            with file_path.open("r", encoding="utf-8") as fh:
                for line in fh:
                    try:
                        data = json.loads(line)
                        ts = datetime.fromisoformat(data.get("ts", ""))
                        if ts < start or ts > end:
                            continue
                        yield FailureEvent.from_dict(data)
                    except Exception:
                        self.last_skipped += 1
                        continue
