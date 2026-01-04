import pytest

from victus.core.failures import service, store
from victus.core.failures.summarize import summarize, write_weekly_report


@pytest.fixture(autouse=True)
def temp_paths(tmp_path, monkeypatch):
    fail_path = tmp_path / "failures.jsonl"
    report_dir = tmp_path / "reports"
    monkeypatch.setattr(store, "FAILURES_PATH", fail_path)
    from victus.core.failures import summarize as summarize_module
    monkeypatch.setattr(summarize_module, "REPORTS_DIR", report_dir)
    yield


def test_failure_log_append_works():
    failure_id = service.log_failure(
        context="memory.propose",
        what_failed="Test failure",
        why_it_failed="Because",
        expected_behavior="Should work",
    )
    failures = store.list_failures()
    assert any(f.failure_id == failure_id for f in failures)


def test_weekly_report_generates(tmp_path):
    service.log_failure(
        context="memory.propose",
        what_failed="Test failure",
        why_it_failed="Because",
        expected_behavior="Should work",
    )
    markdown = summarize()
    path = write_weekly_report(markdown)
    assert path.exists()
    content = path.read_text()
    assert "Failure report" in content
