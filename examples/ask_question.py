#!/usr/bin/env python3
"""Ask a new public question on Quora, unless Quora already has a similar one.

    python ask_question.py "Which burr grinder holds its grind setting best for espresso?"
    python ask_question.py "<question>?" --anyway

Without --anyway, a question Quora finds similar ones for is not asked: the script prints them instead.
"""

import argparse
import json

from quora_api_mcp.scripting import call, run


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("question", help="Question text, ending with a question mark")
    parser.add_argument("--anyway", action="store_true", help="Ask even when Quora suggests similar questions")
    args = parser.parse_args()

    result = call("ask_question", {"question": args.question, "skip_duplicate_check": args.anyway})
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    run(main)
