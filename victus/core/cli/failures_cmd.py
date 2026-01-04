import argparse
import json

from ..failures import service
from ..failures.service import FailureNotFound
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
    failures = service.list_failures(
        status=args.status,
        severity=args.severity,
        since=args.days,
        limit=args.limit,
    )
    if args.json:
        print(json.dumps({"failures": [f.__dict__ for f in failures]}))
    else:
        for f in failures:
            print(f"{f.failure_id} {f.status} {f.context} {f.what_failed}")
    return EXIT_SUCCESS


def set_status(args):
    try:
        service.mark_status(args.failure_id, args.status)
        return EXIT_SUCCESS
    except FailureNotFound:
        return EXIT_NOT_FOUND
    except Exception:
        return EXIT_VALIDATION


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
    list_parser.add_argument("--status")
    list_parser.add_argument("--severity")
    list_parser.add_argument("--days", type=int)
    list_parser.add_argument("--limit", type=int)
    list_parser.add_argument("--json", action="store_true")
    list_parser.set_defaults(handler=list_cmd)

    status_parser = failure_sub.add_parser("set-status")
    status_parser.add_argument("--failure-id", required=True)
    status_parser.add_argument("--status", required=True)
    status_parser.set_defaults(handler=set_status)
