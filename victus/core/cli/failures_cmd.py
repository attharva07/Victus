import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ..failures import FailureLogger
from ..failures.schema import RESOLUTION_STATUSES
from ..failures import service
from .constants import EXIT_NOT_FOUND, EXIT_SUCCESS, EXIT_VALIDATION


def log(args):
    try:
        failure_id = service.log_failure(
            context=args.context,
            what_failed=args.what,
            why_it_failed=args.why,
            expected_behavior=args.expected,
            severity=args.severity,
        )
        if args.json:
            print(json.dumps({"failure_id": failure_id}))
        else:
            print(failure_id)
        return EXIT_SUCCESS
    except Exception:
        return EXIT_VALIDATION


def list_cmd(args):
    days = args.days if args.days is not None else 7
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)
    logger = FailureLogger(Path("victus/data/failures"))
    failures = logger.list_failures(
        start,
        end,
        filters={
            "domain": args.domain,
            "severity": args.severity,
            "status": args.status,
            "category": args.category,
        },
    )
    if args.json:
        print(json.dumps({"failures": [f.to_dict() for f in failures]}))
    else:
        for f in failures:
            status = f.resolution.get("status")
            print(f"{f.event_id} {status} {f.domain} {f.failure.get('code')}")
    return EXIT_SUCCESS


def set_status(args):
    try:
        if args.status not in RESOLUTION_STATUSES:
            return EXIT_VALIDATION
        logger = FailureLogger(Path("victus/data/failures"))
        logger.update_resolution(args.event_id, args.status, args.note)
        return EXIT_SUCCESS
    except KeyError:
        return EXIT_NOT_FOUND
    except Exception:
        return EXIT_VALIDATION


def show_cmd(args):
    logger = FailureLogger(Path("victus/data/failures"))
    event = logger.get_failure(args.event_id)
    if not event:
        return EXIT_NOT_FOUND
    if args.json:
        print(json.dumps({"failure": event.to_dict()}))
    else:
        print(json.dumps(event.to_dict(), indent=2))
    return EXIT_SUCCESS


def register(subparsers: argparse._SubParsersAction):
    failures = subparsers.add_parser("failures")
    failure_sub = failures.add_subparsers(dest="failures_cmd")

    log_parser = failure_sub.add_parser("log")
    log_parser.add_argument("--context", required=True)
    log_parser.add_argument("--what", required=True)
    log_parser.add_argument("--why", required=True)
    log_parser.add_argument("--expected", required=True)
    log_parser.add_argument("--severity", default="medium")
    log_parser.add_argument("--json", action="store_true")
    log_parser.set_defaults(handler=log)

    list_parser = failure_sub.add_parser("list")
    list_parser.add_argument("--domain")
    list_parser.add_argument("--severity")
    list_parser.add_argument("--status")
    list_parser.add_argument("--category")
    list_parser.add_argument("--days", type=int)
    list_parser.add_argument("--json", action="store_true")
    list_parser.set_defaults(handler=list_cmd)

    show_parser = failure_sub.add_parser("show")
    show_parser.add_argument("event_id")
    show_parser.add_argument("--json", action="store_true")
    show_parser.set_defaults(handler=show_cmd)

    status_parser = failure_sub.add_parser("set-status")
    status_parser.add_argument("event_id")
    status_parser.add_argument("status")
    status_parser.add_argument("--note")
    status_parser.set_defaults(handler=set_status)
