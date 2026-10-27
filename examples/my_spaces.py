#!/usr/bin/env python3
"""The Quora Spaces you follow or help run, with your role and the Space ID the other scripts take.

python my_spaces.py
python my_spaces.py --role admin
"""

import argparse

from quora_api_mcp.scripting import call, run, write_rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--role", help="Only Spaces where you have this role, e.g. admin")
    parser.add_argument("--out", help="Save to .csv or .json instead of printing")
    args = parser.parse_args()

    spaces = call("list_my_spaces")["spaces"]
    write_rows([s for s in spaces if not args.role or s.get("role") == args.role], args.out)


if __name__ == "__main__":
    run(main)
