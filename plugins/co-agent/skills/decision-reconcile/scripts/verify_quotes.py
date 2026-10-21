#!/usr/bin/env python3
"""Verify that every quote in a panel finding appears in the ADR it cites.

Usage: verify_quotes.py ADRS_JSON FINDINGS_JSON

ADRS_JSON is the output of collect_adrs.py. FINDINGS_JSON is a list of findings
`{category, adrs: [N, ...], quotes: [{adr: N, text}], severity, why}`. Prints
`{"verified": [indexes], "dropped": [{"index": i, "reason": "..."}]}` and exits 0.
A finding is verified only when it has at least one quote, every quote cites an ADR
listed in `adrs`, and every quote's text appears in that ADR's title, status, decision
or context. Matching collapses whitespace and straightens curly quotes; it stays
case-sensitive. `...` or an ellipsis inside a quote splits it into segments that must
each appear. Unreadable input exits 2 with no output on stdout.
"""

import json
import re
import sys

MIN_SEGMENT = 12
ELLIPSIS = re.compile(r"\.\.\.|…")
TRANSLATE = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"'})


def norm(text):
    return re.sub(r"\s+", " ", text.translate(TRANSLATE)).strip()


def adr_text(adr):
    parts = [adr.get(k) for k in ("title", "status_raw", "status", "decision", "context")]
    return norm(" ".join(p for p in parts if isinstance(p, str)))


def reason_for(finding, texts):
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
        if not segments or any(len(s) < MIN_SEGMENT for s in segments):
            return f"quote from ADR-{number} is too short to verify"
        for segment in segments:
            if segment not in texts[number]:
                return f"quote not found in ADR-{number}"
    return None


def main(argv):
    if len(argv) != 3:
        print("usage: verify_quotes.py ADRS_JSON FINDINGS_JSON", file=sys.stderr)
        return 2
    try:
        with open(argv[1], encoding="utf-8") as fh:
            adrs = json.load(fh)
        with open(argv[2], encoding="utf-8") as fh:
            findings = json.load(fh)
    except (OSError, ValueError) as exc:
        print(f"verify_quotes: cannot read input: {exc}", file=sys.stderr)
        return 2
    if not isinstance(adrs, dict) or not isinstance(adrs.get("adrs"), list) or not isinstance(findings, list):
        print("verify_quotes: expected collect_adrs.py output and a list of findings", file=sys.stderr)
        return 2
    texts = {a["number"]: adr_text(a) for a in adrs["adrs"] if isinstance(a, dict) and isinstance(a.get("number"), int)}
    verified, dropped = [], []
    for index, finding in enumerate(findings):
        reason = reason_for(finding, texts) if isinstance(finding, dict) else "malformed finding"
        if reason is None:
            verified.append(index)
        else:
            dropped.append({"index": index, "reason": reason})
    print(json.dumps({"verified": verified, "dropped": dropped}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
