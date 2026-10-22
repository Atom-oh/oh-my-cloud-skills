#!/usr/bin/env python3
"""Verify that every quote in a panel finding appears in the ADR it cites.

Usage: verify_quotes.py ADRS_JSON FINDINGS_JSON [--decisions-dir DIR]

ADRS_JSON is the output of collect_adrs.py. FINDINGS_JSON is a list of findings
`{category, adrs: [N, ...], quotes: [{adr: N, text}], severity, why}`. Prints
`{"verified": [indexes], "dropped": [{"index": i, "reason": "..."}]}` and exits 0.
A finding is verified only when it has at least one quote, every quote cites an ADR
listed in `adrs`, and every quote's text appears in that ADR's title, status, decision
or context. collect_adrs.py clips decision and context to 600 characters, so with
`--decisions-dir` the ADR file itself (its base name inside DIR) is searched too; without
it a quote from the clipped-off part is dropped. Matching collapses whitespace and
straightens curly quotes; it stays case-sensitive. `...` or an ellipsis inside a quote
splits it into segments that must each appear; a segment shorter than 12 characters
only passes as an exact status line. Unreadable input exits 2 with no output on stdout.
"""

import argparse
import json
import os
import re
import sys

MIN_SEGMENT = 12
ELLIPSIS = re.compile(r"\.\.\.|…")
TRANSLATE = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"'})


def norm(text):
    return re.sub(r"\s+", " ", text.translate(TRANSLATE)).strip()


def full_text(adr, decisions_dir):
    """The ADR file's own text, found by base name inside decisions_dir ('' when unreadable)."""
    if not decisions_dir:
        return ""
    name = os.path.basename(str(adr.get("file") or ""))
    if not name.endswith(".md"):
        return ""
    try:
        with open(os.path.join(decisions_dir, name), encoding="utf-8") as fh:
            return norm(fh.read())
    except OSError:
        return ""


def adr_text(adr, decisions_dir=None):
    parts = [adr.get(k) for k in ("title", "status_raw", "status", "decision", "context")]
    return norm(" ".join([p for p in parts if isinstance(p, str)] + [full_text(adr, decisions_dir)]))


def status_lines(adr):
    return {norm(adr[k]) for k in ("status", "status_raw") if isinstance(adr.get(k), str) and adr[k].strip()}


def reason_for(finding, texts, statuses):
    adrs = finding.get("adrs")
    quotes = finding.get("quotes")
    if not isinstance(adrs, list) or not all(isinstance(n, int) for n in adrs):
        return "malformed adrs"
    if not isinstance(quotes, list) or not quotes:
        return "no quotes"
    for quote in quotes:
        if not isinstance(quote, dict) or not isinstance(quote.get("adr"), int) or not isinstance(quote.get("text"), str):
            return "malformed quote"
        number = quote["adr"]
        if number not in adrs:
            return f"quote cites ADR-{number}, which is not listed in adrs"
        if number not in texts:
            return f"unknown ADR-{number}"
        segments = [norm(s) for s in ELLIPSIS.split(quote["text"])]
        segments = [s for s in segments if s]
        if not segments or any(len(s) < MIN_SEGMENT and s not in statuses[number] for s in segments):
            return f"quote from ADR-{number} is too short to verify"
        for segment in segments:
            if segment not in texts[number]:
                return f"quote not found in ADR-{number}"
    return None


def main(argv):
    parser = argparse.ArgumentParser(prog="verify_quotes.py", add_help=False)
    parser.add_argument("adrs")
    parser.add_argument("findings")
    parser.add_argument("--decisions-dir", default=None)
    try:
        args = parser.parse_args(argv[1:])
    except SystemExit:
        return 2
    try:
        with open(args.adrs, encoding="utf-8") as fh:
            adrs = json.load(fh)
        with open(args.findings, encoding="utf-8") as fh:
            findings = json.load(fh)
    except (OSError, ValueError) as exc:
        print(f"verify_quotes: cannot read input: {exc}", file=sys.stderr)
        return 2
    if not isinstance(adrs, dict) or not isinstance(adrs.get("adrs"), list) or not isinstance(findings, list):
        print("verify_quotes: expected collect_adrs.py output and a list of findings", file=sys.stderr)
        return 2
    known = [a for a in adrs["adrs"] if isinstance(a, dict) and isinstance(a.get("number"), int)]
    texts = {a["number"]: adr_text(a, args.decisions_dir) for a in known}
    statuses = {a["number"]: status_lines(a) for a in known}
    verified, dropped = [], []
    for index, finding in enumerate(findings):
        reason = reason_for(finding, texts, statuses) if isinstance(finding, dict) else "malformed finding"
        if reason is None:
            verified.append(index)
        else:
            dropped.append({"index": index, "reason": reason})
    print(json.dumps({"verified": verified, "dropped": dropped}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
