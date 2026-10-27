#!/usr/bin/env python3
"""Your Quora profile counts and your latest notifications, unread ones by default.

python notifications.py
python notifications.py --all --limit 50
"""

import argparse
import json

from quora_api_mcp.scripting import call, run


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--limit", type=int, default=20, help="1 to 50 (default 20)")
    parser.add_argument("--all", action="store_true", help="Read notifications too, not only unread ones")
    args = parser.parse_args()

    profile = call("get_my_profile")
    notes = call("list_notifications", {"limit": args.limit})["notifications"]
    keys = ("name", "followers", "answers", "questions", "posts")
    print(json.dumps({k: profile.get(k) for k in keys}, indent=2))
    for note in notes:
        if args.all or not note.get("read"):
            print(f"{note['updated_at']}  {note['title']}  {note.get('url') or ''}")


if __name__ == "__main__":
    run(main)
