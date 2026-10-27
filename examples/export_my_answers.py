#!/usr/bin/env python3
"""Export your Quora answers to CSV or JSON: question, text, URL, views, upvotes, comments, date.

    python export_my_answers.py --out answers.csv
    python export_my_answers.py --max 20

Newest first. Pages are followed automatically.
"""

import argparse

from quora_api_mcp.scripting import paginate, run, write_rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--max", type=int, help="Stop after this many answers")
    parser.add_argument("--out", help="Save to .csv or .json instead of printing")
    args = parser.parse_args()

    write_rows(list(paginate("list_my_answers", {"limit": 50}, "answers", args.max)), args.out)


if __name__ == "__main__":
    run(main)
