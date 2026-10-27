#!/usr/bin/env python3
"""Review what followers submitted to your Quora Space: list it, or approve, queue or pass items.

    python review_submissions.py --space 1234567
    python review_submissions.py --space 1234567 --approve 88412 88413
    python review_submissions.py --space 1234567 --approve-all --dry-run

Space admins and moderators only. Space IDs come from my_spaces.py.
"""

import argparse
import json

from quora_api_mcp.scripting import call, run


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--space", required=True, help="Space ID from my_spaces.py")
    parser.add_argument("--approve", nargs="*", default=[], metavar="ID", help="Submission IDs to approve")
    parser.add_argument("--queue", nargs="*", default=[], metavar="ID", help="Submission IDs to add to the queue")
    parser.add_argument("--pass", dest="passed", nargs="*", default=[], metavar="ID", help="Submission IDs to pass on")
    parser.add_argument("--approve-all", action="store_true", help="Approve every pending submission")
    parser.add_argument("--dry-run", action="store_true", help="Show what would happen, change nothing")
    args = parser.parse_args()

    pending = call("list_space_submissions", {"space_id": args.space, "limit": 50})
    decisions = [(i, "approve") for i in args.approve] + [(i, "queue") for i in args.queue]
    decisions += [(i, "pass") for i in args.passed]
    if args.approve_all:
        decisions += [(s["submission_id"], "approve") for s in pending["submissions"]]
    if not decisions:
        print(json.dumps(pending, indent=2))
        return
    for submission_id, action in decisions:
        if args.dry_run:
            print(f"Would {action} {submission_id}")
            continue
        params = {"space_id": args.space, "submission_id": submission_id, "action": action}
        print(json.dumps(call("review_space_submission", params)))


if __name__ == "__main__":
    run(main)
