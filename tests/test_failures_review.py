from datetime import datetime, timedelta, timezone

from victus.core.failures import FailureEvent, FailureLogger


def _event(event_id: str, domain: str, status: str) -> FailureEvent:
    return FailureEvent(
        event_id=event_id,
        ts=datetime.now(timezone.utc).isoformat(),
        stage="2",
        phase="2",
        domain=domain,
        component="executor",
        severity="high",
        category="runtime_error",
        request_id=f"req-{event_id}",
        user_intent="run",
        action={"name": "step", "args_redacted": True},
        failure={
            "code": "boom",
            "message": "fail",
            "exception_type": "Exception",
            "stack_hash": None,
            "details_redacted": True,
        },
        expected_behavior="work",
        remediation_hint=None,
        resolution={"status": status, "resolved_ts": None, "notes": None},
        tags=[],
    )


def test_failure_review_updates_status_and_latest_view(tmp_path):
    logger = FailureLogger(tmp_path)
    logger.append(_event("evt-1", "core", "new"))

    logger.update_resolution("evt-1", "resolved", note="fixed")
    latest = logger.get_failure("evt-1")

    assert latest is not None
    assert latest.resolution["status"] == "resolved"
    assert latest.resolution["notes"] == "fixed"


def test_failure_review_filters_list(tmp_path):
    logger = FailureLogger(tmp_path)
    logger.append(_event("evt-1", "core", "new"))
    logger.append(_event("evt-2", "memory", "new"))
    logger.update_resolution("evt-2", "in_review", note=None)

    end = datetime.now(timezone.utc)
    start = end - timedelta(days=7)
    failures = logger.list_failures(start, end, filters={"domain": "memory", "status": "in_review"})

    assert len(failures) == 1
    assert failures[0].event_id == "evt-2"
