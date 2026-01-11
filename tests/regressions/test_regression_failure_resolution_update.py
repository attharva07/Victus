from datetime import datetime, timezone

from victus.core.failures import FailureEvent, FailureLogger


def test_regression_failure_resolution_update(tmp_path):
    logger = FailureLogger(tmp_path)
    event = FailureEvent(
        event_id="evt-1",
        ts=datetime.now(timezone.utc).isoformat(),
        stage="2",
        phase="1",
        domain="regression",
        component="executor",
        severity="high",
        category="runtime_error",
        request_id="req-1",
        user_intent="run",
        action={"name": "run", "args_redacted": True},
        failure={
            "code": "boom",
            "message": "fail",
            "exception_type": "Exception",
            "stack_hash": "hash-1",
            "details_redacted": True,
        },
        expected_behavior="work",
        remediation_hint=None,
        resolution={"status": "new", "resolved_ts": None, "notes": None},
        tags=[],
    )

    logger.append(event)
    logger.update_resolution("evt-1", "resolved", note="fixed")

    latest = logger.get_failure("evt-1")
    assert latest is not None
    assert latest.resolution["status"] == "resolved"
    assert latest.resolution["notes"] == "fixed"
    assert latest.resolution["resolved_ts"]
