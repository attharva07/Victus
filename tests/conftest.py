from __future__ import annotations

import sys
import threading
import time
import trace
from pathlib import Path
from typing import Iterable, List, Set

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _install_psutil_stub():
    import types

    psutil_stub = types.ModuleType("psutil")

    class AccessDenied(Exception):
        def __init__(self, pid=None, name=None):
            super().__init__("Access denied")
            self.pid = pid
            self.name = name

    class NoSuchProcess(Exception):
        pass

    class ZombieProcess(Exception):
        pass

    class Process:
        def __init__(self, pid=None):
            self.pid = pid

        def name(self):  # pragma: no cover - only used when stub active
            raise AccessDenied(pid=self.pid)

    def net_connections(kind=None):  # pragma: no cover - stub placeholder
        return []

    def disk_partitions(all=True):  # pragma: no cover - stub placeholder
        return []

    def win_service_get(name):  # pragma: no cover - stub placeholder
        raise AccessDenied()

    psutil_stub.AccessDenied = AccessDenied
    psutil_stub.NoSuchProcess = NoSuchProcess
    psutil_stub.ZombieProcess = ZombieProcess
    psutil_stub.Process = Process
    psutil_stub.net_connections = net_connections
    psutil_stub.disk_partitions = disk_partitions
    psutil_stub.win_service_get = win_service_get

    sys.modules["psutil"] = psutil_stub


def pytest_addoption(parser):
    parser.addoption(
        "--cov",
        action="append",
        default=[],
        help="Paths or packages to measure coverage for.",
    )
    parser.addoption(
        "--cov-report",
        action="append",
        default=[],
        help="Coverage report types (e.g., term-missing, xml).",
    )


def pytest_configure(config):
    cov_targets = config.getoption("--cov")
    if not cov_targets:
        return
    reports = config.getoption("--cov-report") or ["term-missing"]
    plugin = TraceCoveragePlugin(config, cov_targets, reports)
    config.pluginmanager.register(plugin, name="trace_cov_plugin")
    config.trace_cov_plugin = plugin


class TraceCoveragePlugin:
    def __init__(self, config, cov_targets: List[str], reports: List[str]):
        self.config = config
        self.cov_targets = [self._resolve_target(target) for target in cov_targets]
        self.reports = reports
        self.tracer = trace.Trace(
            count=True,
            trace=False,
            ignoredirs=[sys.prefix, sys.exec_prefix],
        )
        self.statements: dict[Path, Set[int]] = {}
        self.executed: dict[Path, Set[int]] = {}

    def _resolve_target(self, target: str) -> Path:
        path = Path(target)
        if not path.is_absolute():
            path = (ROOT / target).resolve()
        return path

    def pytest_sessionstart(self, session):
        self._collect_files()
        self._start_trace()

    def pytest_sessionfinish(self, session, exitstatus):
        self._stop_trace()
        self._gather_results()
        entries, totals = self._build_summary()
        if any(report.startswith("term") for report in self.reports):
            self._write_term_report(entries, totals)
        if any(report.startswith("xml") for report in self.reports):
            self._write_xml_report(entries, totals)

    def _start_trace(self) -> None:
        tracer = self.tracer.globaltrace
        sys.settrace(tracer)
        threading.settrace(tracer)

    def _stop_trace(self) -> None:
        sys.settrace(None)
        threading.settrace(None)

    def _collect_files(self) -> None:
        for target in self.cov_targets:
            if target.is_file() and target.suffix == ".py":
                self.statements[target.resolve()] = _statement_lines(target)
                continue
            if target.is_dir():
                for py_file in target.rglob("*.py"):
                    self.statements[py_file.resolve()] = _statement_lines(py_file)

    def _gather_results(self) -> None:
        results = self.tracer.results()
        for (filename, lineno), hits in results.counts.items():
            if not hits:
                continue
            path = Path(filename).resolve()
            if path in self.statements:
                self.executed.setdefault(path, set()).add(lineno)

    def _build_summary(self):
        entries = []
        total_statements = 0
        total_executed = 0
        for path in sorted(self.statements):
            statement_lines = self.statements[path]
            executed = self.executed.get(path, set())
            executed_lines = {ln for ln in statement_lines if ln in executed}
            missing = sorted(statement_lines - executed_lines)
            stmt_count = len(statement_lines)
            total_statements += stmt_count
            total_executed += len(executed_lines)
            percent = 100.0 if stmt_count == 0 else (len(executed_lines) / stmt_count * 100.0)
            entries.append(
                {
                    "path": path,
                    "name": path.stem,
                    "statements": statement_lines,
                    "executed": executed_lines,
                    "missing": missing,
                    "percent": percent,
                }
            )
        total_percent = 100.0 if total_statements == 0 else (total_executed / total_statements * 100.0)
        totals = {
            "statements": total_statements,
            "executed": total_executed,
            "percent": total_percent,
        }
        return entries, totals

    def _write_term_report(self, entries, totals) -> None:
        lines = ["Name Stmts Miss Cover Missing", "-" * 60]
        for entry in entries:
            rel = entry["path"].relative_to(ROOT)
            missing_repr = _format_missing(entry["missing"])
            lines.append(
                f"{str(rel):<40} {len(entry['statements']):>5} {len(entry['missing']):>5} "
                f"{entry['percent']:>5.0f}%   {missing_repr}"
            )
        lines.append("-" * 60)
        total_missing = totals["statements"] - totals["executed"]
        lines.append(
            f"TOTAL {totals['statements']:>43} {total_missing:>5} {totals['percent']:>5.0f}%"
        )
        output = "\n".join(lines)
        terminal = self.config.pluginmanager.get_plugin("terminalreporter")
        if terminal:
            terminal.write_line(output)
        else:
            print(output)

    def _write_xml_report(self, entries, totals) -> None:
        coverage_rate = 1.0 if totals["statements"] == 0 else totals["percent"] / 100.0
        lines = [
            "<?xml version=\"1.0\" ?>",
            f"<coverage line-rate=\"{coverage_rate:.4f}\" branch-rate=\"0\" timestamp=\"{int(time.time())}\" version=\"trace\">",
            "  <packages>",
            f"    <package name=\"victus\" line-rate=\"{coverage_rate:.4f}\" branch-rate=\"0\">",
            "      <classes>",
        ]
        for entry in entries:
            line_rate = 1.0 if not entry["statements"] else entry["percent"] / 100.0
            rel = entry["path"].relative_to(ROOT)
            lines.append(
                f"        <class name=\"{entry['name']}\" filename=\"{rel.as_posix()}\" line-rate=\"{line_rate:.4f}\" branch-rate=\"0\">"
            )
            lines.append("          <lines>")
            for line_no in sorted(entry["statements"]):
                hits = 1 if line_no in entry["executed"] else 0
                lines.append(f"            <line number=\"{line_no}\" hits=\"{hits}\"/>")
            lines.append("          </lines>")
            lines.append("        </class>")
        lines.extend([
            "      </classes>",
            "    </package>",
            "  </packages>",
            "</coverage>",
        ])
        Path("coverage.xml").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _statement_lines(path: Path) -> Set[int]:
    statements: Set[int] = set()
    for lineno, line in enumerate(path.read_text().splitlines(), start=1):
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            statements.add(lineno)
    return statements


def _format_missing(missing: Iterable[int]) -> str:
    if not missing:
        return ""
    ranges = []
    start = end = None
    for number in missing:
        if start is None:
            start = end = number
            continue
        if number == end + 1:
            end = number
            continue
        ranges.append(_range_text(start, end))
        start = end = number
    if start is not None:
        ranges.append(_range_text(start, end))
    return ",".join(ranges)


def _range_text(start: int, end: int) -> str:
    if start == end:
        return str(start)
    return f"{start}-{end}"


def _ensure_psutil():
    try:
        import psutil  # noqa: F401
    except ImportError:  # pragma: no cover - fallback when dependency missing locally
        _install_psutil_stub()


_ensure_psutil()
