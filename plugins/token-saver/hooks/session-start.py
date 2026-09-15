#!/usr/bin/env python3
"""Emit static, bounded session guidance without reading user input or state."""
import json
from pathlib import Path
import sys

POLICY = (Path(__file__).resolve().parents[1] /
          "skills/concise-responses/references/policy.md")
MAX_POLICY_BYTES = 2048


def main():
    try:
        with POLICY.open("rb") as source:
            data = source.read(MAX_POLICY_BYTES + 1)
        if len(data) > MAX_POLICY_BYTES:
            raise ValueError("policy is too large")
        text = data.decode("utf-8").strip()
        if not text:
            raise ValueError("policy is empty")
    except (OSError, UnicodeError, ValueError):
        print("token-saver: policy is unavailable or invalid; no context added.",
              file=sys.stderr)
        return 1
    json.dump({"hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": text,
    }}, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
