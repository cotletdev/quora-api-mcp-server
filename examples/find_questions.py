#!/usr/bin/env python3
"""Find Quora questions on a topic that are worth answering: few answers, not locked.

    python find_questions.py --query "espresso grinder"
    python find_questions.py --query "home espresso" --max-answers 3 --out questions.csv

Prints each question with its answer and follower counts. Pages are followed automatically.
"""

import argparse

from quora_api_mcp.scripting import paginate, run, write_rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--query", required=True, help="Search words")
    parser.add_argument("--max-answers", type=int, help="Only questions with at most this many answers")
    parser.add_argument("--max", type=int, default=100, help="Stop after this many search results (default 100)")
    parser.add_argument("--out", help="Save to .csv or .json instead of printing")
    args = parser.parse_args()

    rows = [
        q
        for q in paginate("search_questions", {"query": args.query, "limit": 50}, "questions", args.max)
        if not q.get("locked") and (args.max_answers is None or (q.get("answers") or 0) <= args.max_answers)
    ]
    write_rows(rows, args.out)


if __name__ == "__main__":
    run(main)
