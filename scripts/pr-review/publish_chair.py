#!/usr/bin/env python3
"""Preserve chair decisions and publish content-free validation diagnostics."""

import json
from pathlib import Path
import re
import runpy
import subprocess
import sys


DIRECTORY = Path(__file__).resolve().parent
GATE = DIRECTORY.parent.parent / "plugins/co-agent/skills/pr-autofix/scripts/review_gate.py"
SEVERITIES = ("CRITICAL", "MAJOR", "MINOR", "INFO")
DECISIONS = {
    "Active CRITICAL finding in final Issues": "active_critical",
    "Active MAJOR finding in final Issues": "active_major",
    "Chair returned VERDICT: FAIL": "explicit_fail",
    "Explicit Issues contain no active CRITICAL or MAJOR findings": "no_blocking_findings",
}


def issue_item_counts(text, gate):
    """Count visible canonical list items, not independently verified defects."""
    unknown = dict.fromkeys(SEVERITIES)
    lines, unclosed = gate["visible_lines"](text)
    if unclosed:
        return unknown
    bodies = {}
    section, category, issues = "", None, 0
    for line in lines:
        heading = re.fullmatch(r"(#{1,6})\s+(.+?)(?:\s+#+)?", line)
        if heading:
            level, title = len(heading[1]), heading[2].strip()
            if level <= 2:
                section, category = title.casefold(), None
                if section == "review error":
                    return unknown
                if section == "issues":
                    issues += 1
                    if level != 2 or issues != 1:
                        return unknown
            elif section == "issues":
                if level != 3 or title.upper() not in SEVERITIES:
                    return unknown
                category = title.upper()
                if category in bodies:
                    return unknown
                bodies[category] = []
            continue
        if section == "issues" and line:
            if category is None:
                return unknown
            bodies[category].append(line)
    if issues != 1:
        return unknown
    counts = dict(unknown)
    for severity, body in bodies.items():
        if len(body) == 1 and body[0] in gate["EMPTY_MARKERS"]:
            counts[severity] = 0
            continue
        items = [re.fullmatch(r"(?:[-+*]|\d+[.)])\s+(\S.*)", line) for line in body]
        if items and items[0] and all(
            item is None or item[1] not in gate["EMPTY_MARKERS"] for item in items
        ):
            counts[severity] = sum(item is not None for item in items)
    return counts


def initial_diagnostics():
    return {
        "schema_version": 1,
        "publication": "withheld",
        "reason": "publisher_error",
        "stage": "publisher",
        "source_status": "ERROR",
        "source_decision": "unavailable",
        "published_status": "ERROR",
        "input_bytes": None,
        "scrubbed_bytes": None,
        "byte_limit": None,
        "issue_item_counts": dict.fromkeys(SEVERITIES),
        "format_diagnostic": None,
    }


def withheld(blocked, diagnostics=None):
    if diagnostics is None:
        diagnostics = initial_diagnostics()
        diagnostics["published_status"] = "BLOCKED" if blocked else "ERROR"
    if blocked:
        heading = "## Summary"
        summary = (
            "The chair's blocking decision is preserved, but its details were withheld. "
            "This diagnostic is not a finding-free review; fallback cannot clear the blocker."
        )
    else:
        heading = "## Review error"
        summary = "Chair output could not be published. Required review remains incomplete."
    return (
        f"{heading}\n\n{summary}\n\n## Publication diagnostics\n\n"
        "Counts describe parsed visible issue list items, not verified defects. "
        "Null means unavailable or ambiguous, not zero. No source text is included.\n\n"
        "```json\n" + json.dumps(diagnostics, indent=2) + "\n```\n\n"
        "## Verdict\nVERDICT: FAIL\n"
    )


def publish_with_diagnostics(text):
    diagnostics = initial_diagnostics()
    blocked = False

    def reject(reason, stage, preserve_blocker=None):
        retained = blocked if preserve_blocker is None else preserve_blocker
        diagnostics.update(
            publication="withheld", reason=reason, stage=stage,
            published_status="BLOCKED" if retained else "ERROR",
        )
        return withheld(retained, diagnostics), diagnostics

    try:
        gate = runpy.run_path(str(GATE))
        cap = gate["MAX_REVIEW_BYTES"]
        diagnostics["byte_limit"] = cap
        source = gate["_markdown_review"](text)
        blocked = source["status"] == "BLOCKED"
        diagnostics["source_status"] = source["status"]
        diagnostics["source_decision"] = DECISIONS.get(source["reason"], "review_incomplete")
        diagnostics["issue_item_counts"] = issue_item_counts(text, gate)
        diagnostics["stage"] = "input"
        diagnostics["input_bytes"] = len(text.encode("utf-8"))
        if diagnostics["input_bytes"] > cap:
            return reject("input_too_large", "input")
        diagnostics["stage"] = "source_validation"
        formatter = runpy.run_path(str(GATE.with_name("review_format.py")))
        review = gate["markdown_review"]
        original = review(text)
        if original.get("publishable") is False:
            diagnostics["format_diagnostic"] = formatter["format_diagnostic"](text)
            return reject("source_format_rejected", "source_validation")
        if original["status"] == "ERROR":
            return reject("source_review_incomplete", "source_validation")
        diagnostics["stage"] = "scrub"
        result = subprocess.run(
            ["bash", "-c", 'source "$1"; scrub_secrets', "chair-scrub", str(DIRECTORY / "lib.sh")],
            input=text, text=True, capture_output=True,
        )
        if result.returncode:
            return reject("scrubber_failed", "scrub")
        diagnostics["stage"] = "scrubbed_validation"
        diagnostics["scrubbed_bytes"] = len(result.stdout.encode("utf-8"))
        if diagnostics["scrubbed_bytes"] > cap:
            filtered_blocked = gate["_markdown_review"](result.stdout)["status"] == "BLOCKED"
            return reject("scrubbed_output_too_large", "scrub", blocked or filtered_blocked)
        filtered = review(result.stdout)
        if filtered.get("publishable") is False:
            diagnostics["format_diagnostic"] = formatter["format_diagnostic"](result.stdout)
            return reject("scrubbed_format_rejected", "scrubbed_validation",
                          blocked or filtered["status"] == "BLOCKED")
        if blocked and filtered["status"] != "BLOCKED":
            return reject("blocking_evidence_removed", "scrubbed_validation")
        if filtered["status"] == "ERROR":
            return reject("scrubbed_review_incomplete", "scrubbed_validation")
        diagnostics.update(
            publication="published", reason="published", stage="complete",
            published_status=filtered["status"],
        )
        return result.stdout, diagnostics
    except (OSError, UnicodeError, ValueError, KeyError, TypeError):
        return reject("publisher_error", diagnostics["stage"])


def publish(text):
    return publish_with_diagnostics(text)[0]


def main():
    diagnostics = initial_diagnostics()
    try:
        data = sys.stdin.buffer.read()
        diagnostics["input_bytes"] = len(data)
        text = data.decode("utf-8")
        output, diagnostics = publish_with_diagnostics(text)
    except UnicodeError:
        diagnostics.update(reason="invalid_utf8", stage="input")
        output = withheld(False, diagnostics)
    except (OSError, ValueError, KeyError, TypeError):
        output = withheld(False, diagnostics)
    print("chair-publication: " + json.dumps(diagnostics, sort_keys=True), file=sys.stderr)
    sys.stdout.write(output)


if __name__ == "__main__":
    main()
