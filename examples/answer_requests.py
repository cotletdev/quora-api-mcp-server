#!/usr/bin/env python3
"""Questions other people asked you to answer, with who asked and how many answers each has.

    python answer_requests.py
    python answer_requests.py --out requests.csv

Quora shows the top requests first.
"""

import argparse

from quora_api_mcp.scripting import call, run, write_rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--limit", type=int, default=50, help="1 to 50 (default 50)")
    parser.add_argument("--out", help="Save to .csv or .json instead of printing")
    args = parser.parse_args()

    write_rows(call("list_answer_requests", {"limit": args.limit})["requests"], args.out)


if __name__ == "__main__":
    run(main)
