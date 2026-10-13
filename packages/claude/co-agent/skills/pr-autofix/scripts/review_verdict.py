#!/usr/bin/env python3
"""Read the native status line from an already authenticated review comment."""
import json
from pathlib import Path
import re
import sys

STATUS = re.compile(r"^\*\*Status: (PASSED|BLOCKED|ERROR)\*\*(?:\s|$)")
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})")


def verdict(body):
    fence = None
    for line in body.splitlines():
        if fence:
            character, length = fence
            if re.fullmatch(r" {0,3}" + re.escape(character) + "{" + str(length) + r",}[ \t]*", line):
                fence = None
            continue
        opening = FENCE.match(line)
        if opening:
            marker = opening.group(1)
            fence = marker[0], len(marker)
            continue
        match = STATUS.match(line)
        if match:
            return match.group(1)
    return "UNBOUND"


def main():
    if len(sys.argv) != 2:
        print("usage: review_verdict.py <trusted-comment.json>", file=sys.stderr)
        return 2
    try:
        with Path(sys.argv[1]).open(encoding="utf-8") as stream:
            comment = json.load(stream)
    except (OSError, ValueError):
        print("Cannot read review comment JSON", file=sys.stderr)
        return 2
    body = comment.get("body") if isinstance(comment, dict) else None
    print(verdict(body) if isinstance(body, str) else "UNBOUND")
    return 0


if __name__ == "__main__":
    sys.exit(main())
