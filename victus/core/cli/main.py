import argparse
import json
import sys

from . import memory_cmd, failures_cmd, report_cmd
from .constants import (
    EXIT_INTERNAL,
    EXIT_IO,
    EXIT_SUCCESS,
    EXIT_VALIDATION,
)


def build_parser():
    parser = argparse.ArgumentParser(prog="victus")
    subparsers = parser.add_subparsers(dest="command")

    memory_cmd.register(subparsers)
    failures_cmd.register(subparsers)
    report_cmd.register(subparsers)
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "handler", None):
        parser.print_help()
        return EXIT_VALIDATION
    try:
        return args.handler(args)
    except BrokenPipeError:
        return EXIT_IO
    except Exception:
        return EXIT_INTERNAL


if __name__ == "__main__":
    sys.exit(main())
