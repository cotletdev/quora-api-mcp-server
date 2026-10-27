#!/usr/bin/env python3
"""A stats report for the Quora Spaces you run: views, new followers, upvotes, comments and new items.

    python space_stats.py
    python space_stats.py --space 1234567 --top 10
    python space_stats.py --out stats.csv

Without --space, every Space where you are an admin or moderator. Quora updates the numbers once a day.
"""

import argparse

from quora_api_mcp.scripting import call, run, write_rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--space", help="One Space ID; default all Spaces you run")
    parser.add_argument("--top", type=int, default=0, help="Top content items per Space, 0 to 20 (default 0)")
    parser.add_argument("--out", help="Save to .csv or .json instead of printing")
    args = parser.parse_args()

    if args.space:
        spaces = [{"space_id": args.space, "name": ""}]
    else:
        spaces = [s for s in call("list_my_spaces")["spaces"] if s.get("role") in ("admin", "moderator")]
    rows = []
    for space in spaces:
        stats = call("get_space_stats", {"space_id": space["space_id"], "top_limit": args.top})
        row = {"space_id": space["space_id"], "name": space.get("name")}
        row.update({f"7d_{k}": v for k, v in stats["last_7_days"].items()})
        row.update({f"all_{k}": v for k, v in stats["all_time"].items()})
        if args.top:
            row["top_content"] = stats.get("top_content")
        rows.append(row)
    write_rows(rows, args.out)


if __name__ == "__main__":
    run(main)
