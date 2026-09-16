#!/usr/bin/env python3
"""Preserve semantic chair decisions while withholding unusable review text."""

from pathlib import Path
import runpy
import subprocess
import sys


DIRECTORY = Path(__file__).resolve().parent
GATE = DIRECTORY.parent.parent / "plugins/co-agent/skills/pr-autofix/scripts/review_gate.py"


def withheld(blocked):
    if not blocked:
        return (
            "## Review error\n\nChair output could not be validated for publication. "
            "Required review remains incomplete.\n\nVERDICT: FAIL\n"
        )
    return (
        "## Summary\n\nThe primary chair reported a blocking result. Its details "
        "failed publication validation and were withheld. A valid blocking review "
        "must be resolved; fallback cannot clear this result.\n\n"
        "## Issues\n### CRITICAL\nNone.\n### MAJOR\nNone.\n### MINOR\nNone.\n\n"
        "## Verdict\nVERDICT: FAIL\n"
    )


def publish(text):
    gate = runpy.run_path(str(GATE))
    blocked = gate["_markdown_review"](text)["status"] == "BLOCKED"
    try:
        review = gate["markdown_review"]
        original = review(text)
        if original["status"] == "ERROR" or original.get("publishable") is False:
            return withheld(blocked)
        # Use the existing trusted scrubber, with model text on stdin only. Never
        # persist an unscrubbed review or expose scrubber stderr to public output.
        result = subprocess.run(
            ["bash", "-c", 'source "$1"; scrub_secrets', "chair-scrub", str(DIRECTORY / "lib.sh")],
            input=text, text=True, capture_output=True,
        )
        if result.returncode:
            return withheld(blocked)
        filtered = review(result.stdout)
    except (OSError, UnicodeError, ValueError, KeyError, TypeError):
        return withheld(blocked)
    if filtered["status"] == "BLOCKED":
        return result.stdout if filtered.get("publishable") is not False else withheld(True)
    if blocked:
        return withheld(True)
    return result.stdout if filtered["status"] == "PASSED" else withheld(False)


def main():
    try:
        text = sys.stdin.buffer.read().decode("utf-8")
        output = publish(text)
    except (OSError, UnicodeError, ValueError, KeyError, TypeError):
        output = withheld(False)
    sys.stdout.write(output)


if __name__ == "__main__":
    main()
