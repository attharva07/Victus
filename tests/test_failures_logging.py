import json
from datetime import datetime, timezone

from victus.core.failures import FailureEvent, FailureLogger


def test_failure_event_serialization_has_required_keys():
    event = FailureEvent(
        stage="2",
        phase="1",
        domain="test",
        component="executor",
        severity="critical",
        category="runtime_error",
        request_id="req-1",
        user_intent="do something",
        action={"name": "run", "args_redacted": True},
        failure={
            "code": "boom",
            "message": "It failed",
            "exception_type": "ValueError",
            "stack_hash": "abc123",
            "details_redacted": True,
        },
        expected_behavior="Should work",
        remediation_hint=None,
        resolution={"status": "new", "resolved_ts": None, "notes": None},
        tags=["a"],
    )

    payload = event.to_dict()
    for key in [
        "schema_version",
        "event_id",
        "ts",
        "stage",
        "phase",
        "domain",
        "component",
        "severity",
        "category",
        "request_id",
        "user_intent",
        "action",
        "failure",
        "expected_behavior",
        "remediation_hint",
        "resolution",
        "tags",
    ]:
        assert key in payload


def test_failure_logger_appends_valid_jsonl_line(tmp_path):
    base_dir = tmp_path / "failures"
    logger = FailureLogger(base_dir)
    ts = datetime.now(timezone.utc).isoformat()
    event = FailureEvent(
        ts=ts,
        stage="2",
        phase="1",
        domain="productivity",
        component="executor",
        severity="high",
        category="runtime_error",
        request_id="req-123",
        user_intent="do work",
        action={"name": "step", "args_redacted": True},
        failure={
            "code": "x",
            "message": "oops",
            "exception_type": "Exception",
            "stack_hash": "deadbeef",
            "details_redacted": True,
        },
        expected_behavior="complete",
        remediation_hint=None,
        resolution={"status": "new", "resolved_ts": None, "notes": None},
        tags=[],
    )

    logger.append(event)
    log_file = next(base_dir.glob("failures_*.jsonl"))
    lines = log_file.read_text().strip().splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["action"]["args_redacted"] is True
    assert record["failure"]["code"] == "x"


def test_failure_logger_does_not_store_args(tmp_path):
    base_dir = tmp_path / "failures"
    logger = FailureLogger(base_dir)
    event = FailureEvent(
        stage="2",
        phase="1",
        domain="productivity",
        component="executor",
        severity="high",
        category="runtime_error",
        request_id="req-123",
        user_intent="do work",
        action={"name": "step", "args_redacted": True},
        failure={
            "code": "x",
            "message": "oops",
            "exception_type": "Exception",
            "stack_hash": "deadbeef",
            "details_redacted": True,
        },
        expected_behavior="complete",
        remediation_hint=None,
        resolution={"status": "new", "resolved_ts": None, "notes": None},
        tags=[],
    )

    logger.append(event)
    log_file = next(base_dir.glob("failures_*.jsonl"))
    data = json.loads(log_file.read_text())
    assert data.get("args") is None
    assert "args_redacted" in data["action"]
