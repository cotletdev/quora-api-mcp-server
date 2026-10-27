#!/usr/bin/env python3
"""Read one Quora question with its top answers, and whether you have answered it.

python read_question.py https://www.quora.com/How-do-I-make-a-great-cup-of-espresso
python read_question.py <question URL> --answers 10
"""

import argparse
import json

from quora_api_mcp.scripting import call, run


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("url", help="Question URL on quora.com")
    parser.add_argument("--answers", type=int, default=5, help="Top answers to include, 0 to 20 (default 5)")
    args = parser.parse_args()

    print(json.dumps(call("get_question", {"question_url": args.url, "answers_limit": args.answers}), indent=2))


if __name__ == "__main__":
    run(main)
