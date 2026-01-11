import argparse
import json

from ..memory import service
from ..memory.proposals import ProposalNotFound
from ..memory.service import MemoryServiceError
from ..util.validate import parse_tags
from .constants import EXIT_NOT_FOUND, EXIT_STATE_CONFLICT, EXIT_SUCCESS, EXIT_VALIDATION


def _output(result, json_mode: bool):
    if json_mode:
        print(json.dumps(result))
    else:
        if "proposal_id" in result:
            print(f"PROPOSED {result['proposal_id']}")
        elif "memory_id" in result:
            print(result["memory_id"])
        elif "proposals" in result:
            for p in result["proposals"]:
                print(f"{p.proposal_id} {p.status} {p.memory_type} {p.content}")


def propose(args):
    tags = parse_tags(args.tags)
    try:
        proposal_id = service.propose_memory(args.category, args.content, True, tags)
        _output({"ok": True, "proposal_id": proposal_id}, args.json)
        return EXIT_SUCCESS
    except MemoryServiceError:
        return EXIT_VALIDATION


def approve(args):
    try:
        memory_id = service.approve_memory(args.proposal_id)
        _output({"memory_id": memory_id}, args.json)
        return EXIT_SUCCESS
    except ProposalNotFound:
        return EXIT_NOT_FOUND
    except MemoryServiceError:
        return EXIT_STATE_CONFLICT


def reject(args):
    try:
        service.reject_memory(args.proposal_id, args.reason)
        return EXIT_SUCCESS
    except ProposalNotFound:
        return EXIT_NOT_FOUND
    except MemoryServiceError:
        return EXIT_STATE_CONFLICT


def revise(args):
    try:
        service.revise_memory(args.proposal_id, args.content)
        return EXIT_SUCCESS
    except ProposalNotFound:
        return EXIT_NOT_FOUND
    except MemoryServiceError:
        return EXIT_STATE_CONFLICT


def list_cmd(args):
    proposals = service.list_memory_proposals(status=args.status, domain=args.domain, limit=args.limit)
    if args.json:
        _output({"proposals": [p.__dict__ for p in proposals]}, True)
    else:
        _output({"proposals": proposals}, False)
    return EXIT_SUCCESS


def show_cmd(args):
    try:
        proposal = service.show_memory_proposal(args.proposal_id)
    except ProposalNotFound:
        return EXIT_NOT_FOUND
    if args.json:
        _output({"proposal": proposal.__dict__}, True)
    else:
        print(json.dumps(proposal.__dict__, indent=2))
    return EXIT_SUCCESS


def register(subparsers: argparse._SubParsersAction):
    memory = subparsers.add_parser("memory")
    memory_sub = memory.add_subparsers(dest="memory_cmd")
    proposals = memory_sub.add_parser("proposals")
    proposals_sub = proposals.add_subparsers(dest="memory_proposals_cmd")

    propose_parser = memory_sub.add_parser("propose")
    propose_parser.add_argument("--category", required=True)
    propose_parser.add_argument("--content", required=True)
    propose_parser.add_argument("--confidence", default="medium")
    propose_parser.add_argument("--tags")
    propose_parser.add_argument("--json", action="store_true")
    propose_parser.set_defaults(handler=propose)

    approve_parser = memory_sub.add_parser("approve")
    approve_parser.add_argument("--proposal-id", required=True)
    approve_parser.add_argument("--json", action="store_true")
    approve_parser.set_defaults(handler=approve)

    reject_parser = memory_sub.add_parser("reject")
    reject_parser.add_argument("--proposal-id", required=True)
    reject_parser.add_argument("--reason", required=True)
    reject_parser.set_defaults(handler=reject)

    revise_parser = memory_sub.add_parser("revise")
    revise_parser.add_argument("--proposal-id", required=True)
    revise_parser.add_argument("--content", required=True)
    revise_parser.set_defaults(handler=revise)

    list_parser = memory_sub.add_parser("list")
    list_parser.add_argument("--status")
    list_parser.add_argument("--limit", type=int)
    list_parser.add_argument("--domain")
    list_parser.add_argument("--json", action="store_true")
    list_parser.set_defaults(handler=list_cmd)

    proposals_list = proposals_sub.add_parser("list")
    proposals_list.add_argument("--domain")
    proposals_list.add_argument("--status")
    proposals_list.add_argument("--limit", type=int)
    proposals_list.add_argument("--json", action="store_true")
    proposals_list.set_defaults(handler=list_cmd)

    proposals_show = proposals_sub.add_parser("show")
    proposals_show.add_argument("proposal_id")
    proposals_show.add_argument("--json", action="store_true")
    proposals_show.set_defaults(handler=show_cmd)

    proposals_approve = proposals_sub.add_parser("approve")
    proposals_approve.add_argument("proposal_id")
    proposals_approve.add_argument("--json", action="store_true")
    proposals_approve.set_defaults(handler=approve)

    proposals_reject = proposals_sub.add_parser("reject")
    proposals_reject.add_argument("proposal_id")
    proposals_reject.add_argument("--reason", required=True)
    proposals_reject.set_defaults(handler=reject)
