import argparse
import json

from ..failures.summarize import summarize, write_weekly_report
from .constants import EXIT_SUCCESS


def weekly(args):
    markdown = summarize(days=args.days or 7)
    path = write_weekly_report(markdown)
    if args.json:
        print(json.dumps({"path": str(path)}))
    else:
        print(path)
    return EXIT_SUCCESS


def register(subparsers: argparse._SubParsersAction):
    report = subparsers.add_parser("report")
    report_sub = report.add_subparsers(dest="report_cmd")

    weekly_parser = report_sub.add_parser("weekly")
    weekly_parser.add_argument("--days", type=int)
    weekly_parser.add_argument("--json", action="store_true")
    weekly_parser.set_defaults(handler=weekly)
