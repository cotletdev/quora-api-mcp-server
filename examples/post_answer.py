#!/usr/bin/env python3
"""Publish an answer under a Quora question, as you, from text or a file.

    python post_answer.py --url https://www.quora.com/<question> --body-file answer.md
    python post_answer.py --url https://www.quora.com/<question> --body "Short answer." --dry-run

The text goes out as plain paragraphs: a blank line starts a new one, no formatting, links or images.
Quora allows one answer per question, so the script checks that first. The answer is public at once.
"""

import argparse
import json
import sys
from pathlib import Path

from quora_api_mcp.scripting import call, run


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--url", required=True, help="Question URL on quora.com")
    body = parser.add_mutually_exclusive_group(required=True)
    body.add_argument("--body", help="Answer text")
    body.add_argument("--body-file", help="Read the answer text from a file")
    parser.add_argument("--dry-run", action="store_true", help="Show the question and the text, post nothing")
    args = parser.parse_args()

    text = args.body if args.body is not None else Path(args.body_file).read_text(encoding="utf-8")
    question = call("get_question", {"question_url": args.url, "answers_limit": 0})
    if question.get("viewer_has_answered"):
        sys.exit(f"You have already answered: {question['question']}")
    if args.dry_run:
        print(f"Would answer: {question['question']}\n\n{text}")
        return
    print(json.dumps(call("post_answer", {"question_url": args.url, "body_markdown": text}), indent=2))


if __name__ == "__main__":
    run(main)
