#!/usr/bin/env python3
"""Classify each AI review finding against the actual diff — mechanical
"verify, don't vote-count". For every finding citing file:line (optionally a
snippet), decide:

  supported     — file is in the diff AND line is in/adjacent (±3) to a changed
                  hunk AND (no snippet OR snippet matches a nearby added line)
  needs-review  — file is in the diff but the line/snippet doesn't line up
  unsupported   — file is not in the diff at all (likely hallucinated path)

Input findings JSON: a list of objects, each with at least:
  {"ai": "...", "severity": "...", "file": "path", "line": 42,
   "snippet": "optional quoted code", "issue": "..."}
Output: the same list with a "citation" field added, plus a summary line.

Usage:
  python3 check_citations.py <diff_file> <findings_json_file>
  python3 check_citations.py <diff_file> <findings_json_file> --json
Exit 0 always (classifier, not a gate). Exit 2 on usage/parse error.
"""
import sys
import re
import json

ADJACENT = 3  # a cited line within ±3 of a changed line still counts as supported


def parse_diff(text):
    """Return {filepath: {new_lineno: added_line_text}} for added/context lines,
    parsed from a unified diff. Only the NEW-file line numbers are tracked."""
    files = {}
    cur = None
    new_ln = 0
    for line in text.splitlines():
        if line.startswith("+++ "):
            path = line[4:].strip()
            path = re.sub(r"^b/", "", path)
            if path == "/dev/null":
                cur = None
            else:
                cur = files.setdefault(path, {})
            continue
        if line.startswith("@@"):
            m = re.search(r"\+(\d+)", line)
            new_ln = int(m.group(1)) if m else 0
            continue
        if cur is None:
            continue
        if line.startswith("+") and not line.startswith("+++"):
            cur[new_ln] = line[1:]
            new_ln += 1
        elif line.startswith("-") and not line.startswith("---"):
            pass  # removed line: does not advance the new-file counter
        else:
            new_ln += 1  # context line
    return files


def classify(finding, files):
    path = (finding.get("file") or "").strip()
    # match by exact path or basename (AIs sometimes drop the dir prefix)
    hit = None
    if path in files:
        hit = files[path]
    else:
        base = path.rsplit("/", 1)[-1]
        for fp, lines in files.items():
            if fp.rsplit("/", 1)[-1] == base:
                hit = lines
                break
    if hit is None:
        return "unsupported"
    try:
        line = int(finding.get("line"))
    except (TypeError, ValueError):
        return "needs-review"  # file matched but no usable line
    near = [ln for ln in hit if abs(ln - line) <= ADJACENT]
    if not near:
        return "needs-review"
    snippet = (finding.get("snippet") or "").strip()
    if not snippet:
        return "supported"
    if any(snippet in hit[ln] for ln in near):
        return "supported"
    return "needs-review"


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) < 2:
        print(__doc__)
        return 2
    diff_path, findings_path = args[0], args[1]
    as_json = "--json" in sys.argv[1:]
    try:
        with open(diff_path, encoding="utf-8") as f:
            diff = f.read()
        with open(findings_path, encoding="utf-8") as f:
            findings = json.load(f)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as e:
        print(f"❌ cannot read inputs: {e}", file=sys.stderr)
        return 2
    if not isinstance(findings, list):
        print("❌ findings JSON must be a list of objects", file=sys.stderr)
        return 2

    files = parse_diff(diff)
    counts = {"supported": 0, "needs-review": 0, "unsupported": 0}
    for fnd in findings:
        c = classify(fnd, files)
        fnd["citation"] = c
        counts[c] += 1

    if as_json:
        print(json.dumps(findings, ensure_ascii=False, indent=2))
    else:
        for fnd in findings:
            mark = {"supported": "✅", "needs-review": "🟡", "unsupported": "❌"}[fnd["citation"]]
            print(f"{mark} [{fnd.get('severity','?')}] {fnd.get('file','?')}:{fnd.get('line','?')} "
                  f"({fnd.get('ai','?')}) — {fnd.get('issue','')[:80]}")
        print(f"\ncitations: {counts['supported']} supported · "
              f"{counts['needs-review']} needs-review · {counts['unsupported']} unsupported")
        if counts["unsupported"]:
            print("→ Drop unsupported findings (likely hallucinated paths). "
                  "Treat needs-review with caution; verify before reporting.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
