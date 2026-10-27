#!/usr/bin/env python3
"""Post in a Quora Space you contribute to, now or into its queue.

    python post_to_space.py --space 1234567 --title "Dialing in a light roast" --body-file post.md
    python post_to_space.py --space 1234567 --body "Tip of the week: ..." --queue

Space IDs come from my_spaces.py. The text goes out as plain paragraphs. As a follower, Quora sends the
post to the Space admins for review instead (status submitted).
"""

import argparse
import json
from pathlib import Path

from quora_api_mcp.scripting import call, run


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--space", required=True, help="Space ID from my_spaces.py")
    parser.add_argument("--title", help="Optional post title")
    body = parser.add_mutually_exclusive_group(required=True)
    body.add_argument("--body", help="Post text")
    body.add_argument("--body-file", help="Read the post text from a file")
    parser.add_argument("--queue", action="store_true", help="Add the post to the Space's queue instead of posting now")
    args = parser.parse_args()

    text = args.body if args.body is not None else Path(args.body_file).read_text(encoding="utf-8")
    params = {
        "space_id": args.space,
        "body_markdown": text,
        "title": args.title,
        "mode": "queue" if args.queue else "post",
    }
    print(json.dumps(call("post_to_space", params), indent=2))


if __name__ == "__main__":
    run(main)
