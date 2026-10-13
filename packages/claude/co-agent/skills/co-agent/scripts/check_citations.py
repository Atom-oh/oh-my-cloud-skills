#!/usr/bin/env python3
"""Classify each AI review finding against the actual diff — mechanical
"verify, don't vote-count". For every finding citing file:line (optionally a
snippet), decide:

  supported     — file is in the diff AND line is in/adjacent (±3) to a changed
                  hunk AND (no snippet OR snippet matches a nearby added line)
  needs-review  — file is in the diff but the line/snippet doesn't line up
  unsupported   — file is not in the diff (chair must still verify the claim)

Input findings JSON: a list of objects, each with at least:
  {"ai": "...", "severity": "...", "file": "path", "line": 42,
   "snippet": "optional quoted code", "issue": "..."}
Output: the same list with a "citation" field added, plus a summary line.

Usage:
  python3 check_citations.py <diff_file> <findings_json_file>
  python3 check_citations.py <diff_file> <findings_json_file> --json
Only unified/git diffs are accepted, including empty and deletion-only diffs.
Plan citations must be checked against the actual plan by the chair.
Exit 0 for classification, never a gate verdict. Exit 2 on usage/parse error;
an error must not discard findings or count as a successful review.
"""
import argparse
import ast
import sys
import re
import json
import shlex

ADJACENT = 3  # a cited line within ±3 of a changed line still counts as supported


def parse_diff(text):
    """Return {filepath: {new_lineno: added_line_text}} for a valid diff.

    Deleted files remain present with no new-side lines, so their citations need
    chair review rather than being mistaken for paths absent from the diff.
    """
    if not text.strip():
        return {}
    files = {}
    cur = None
    old_path = None
    new_ln = 0
    remaining = None
    saw_diff = False
    binary = False
    pending_hunk = False
    section_has_payload = False
    metadata = (
        "index ", "new file mode ", "deleted file mode ", "old mode ", "new mode ",
        "similarity index ", "dissimilarity index ", "rename from ", "rename to ",
        "copy from ", "copy to ",
    )

    def path_from_header(value):
        value = value.split("\t", 1)[0]
        if value.startswith('"'):
            try:
                raw = value
                value = ast.literal_eval(raw)
                # Git quotes UTF-8 bytes as C-style octal escapes.
                if re.search(r"\\[0-7]{3}", raw):
                    value = value.encode("latin-1").decode("utf-8", errors="surrogateescape")
            except (SyntaxError, ValueError, UnicodeEncodeError) as exc:
                raise ValueError("invalid quoted diff path") from exc
        return re.sub(r"^[ab]/", "", value)

    # Git delimits diff records with LF. Other Unicode line separators and CR
    # belong to the source payload, including a CR immediately before that LF.
    lines = text.split("\n")
    if lines[-1] == "":
        lines.pop()
    for line in lines:
        if line == r"\ No newline at end of file":
            if remaining is None:
                raise ValueError("newline marker outside a hunk")
            continue
        if remaining is not None and any(remaining):
            if line.startswith("+"):
                if remaining[1] == 0:
                    raise ValueError("too many added lines in diff hunk")
                cur[new_ln] = line[1:]
                remaining[1] -= 1
                new_ln += 1
            elif line.startswith("-"):
                if remaining[0] == 0:
                    raise ValueError("too many removed lines in diff hunk")
                remaining[0] -= 1
            elif line.startswith(" "):
                if 0 in remaining:
                    raise ValueError("too many context lines in diff hunk")
                remaining[0] -= 1
                remaining[1] -= 1
                new_ln += 1
            else:
                raise ValueError("incomplete or malformed diff hunk")
            continue
        if line.startswith("diff --git "):
            if pending_hunk or (saw_diff and not section_has_payload):
                raise ValueError("incomplete diff file section")
            try:
                fields = shlex.split(line, posix=False)
            except ValueError:
                # Git paths are not shell words: an unquoted filename may have
                # unmatched apostrophes. Use the same Git new-path marker fallback.
                fields = []
            if len(fields) == 4:
                new_path = fields[3]
            else:
                # Git leaves ordinary spaces unquoted in --git headers. File
                # headers below remain authoritative for textual hunks.
                payload = line[len("diff --git "):]
                candidates = [(payload[:match.start()], payload[match.end() - 2:])
                              for match in re.finditer(r" b/", payload)]
                if not candidates:
                    raise ValueError("malformed git diff header")
                same_path = [new for old, new in candidates if old[2:] == new[2:]]
                new_path = same_path[0] if same_path else candidates[0][1]
            cur = files.setdefault(path_from_header(new_path), {})
            old_path = None
            remaining = None
            saw_diff = True
            binary = False
            section_has_payload = False
            continue
        if line.startswith("--- "):
            if old_path is not None or pending_hunk:
                raise ValueError("incomplete diff file headers")
            old_path = path_from_header(line[4:])
            remaining = None
            continue
        if line.startswith("+++ "):
            if old_path is None:
                raise ValueError("new-file header without old-file header")
            path = path_from_header(line[4:])
            if path == "/dev/null":
                path = old_path
            if path == "/dev/null" or not path:
                raise ValueError("diff has no file path")
            cur = files.setdefault(path, {})
            old_path = None
            saw_diff = True
            pending_hunk = True
            continue
        if line.startswith("@@"):
            m = re.fullmatch(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(?: .*)?", line)
            if m is None or cur is None or old_path is not None:
                raise ValueError("malformed diff hunk header")
            new_ln = int(m.group(3))
            remaining = [int(m.group(2) or 1), int(m.group(4) or 1)]
            pending_hunk = False
            section_has_payload = True
            continue
        if cur is not None and line.startswith(metadata):
            section_has_payload = True
            continue
        if cur is not None and (line.startswith("Binary files ") or line == "GIT binary patch"):
            binary = True
            pending_hunk = False
            section_has_payload = True
            continue
        if binary and (not line or re.fullmatch(r"(?:literal|delta) \d+|[A-Za-z][!-~]+", line)):
            continue
        raise ValueError("input is not a unified/git diff; check plan citations manually")
    if (not saw_diff or old_path is not None or pending_hunk or not section_has_payload
            or (remaining is not None and any(remaining))):
        raise ValueError("incomplete or malformed unified/git diff")
    return files


def classify(finding, files):
    path = (finding.get("file") or "").strip()
    # match by exact path or basename (AIs sometimes drop the dir prefix)
    hit = None
    if path in files:
        hit = files[path]
    else:
        base = path.rsplit("/", 1)[-1]
        matches = [lines for fp, lines in files.items() if fp.rsplit("/", 1)[-1] == base]
        if len(matches) > 1:
            return "needs-review"
        if matches:
            hit = matches[0]
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("diff_path")
    parser.add_argument("findings_path")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        with open(args.diff_path, encoding="utf-8", newline="") as f:
            diff = f.read()
        with open(args.findings_path, encoding="utf-8") as f:
            findings = json.load(f)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as e:
        print(f"cannot read inputs: {e}; findings still require chair review", file=sys.stderr)
        return 2
    if (not isinstance(findings, list)
            or any(not isinstance(fnd, dict) for fnd in findings)
            or any(not isinstance(fnd.get(key, ""), str)
                   for fnd in findings for key in ("file", "snippet", "issue"))):
        print("findings JSON must be a list of objects with string file/snippet/issue fields",
              file=sys.stderr)
        return 2
    try:
        files = parse_diff(diff)
    except ValueError as e:
        print(f"cannot classify citations: {e}; findings still require chair review", file=sys.stderr)
        return 2
    counts = {"supported": 0, "needs-review": 0, "unsupported": 0}
    for fnd in findings:
        c = classify(fnd, files)
        fnd["citation"] = c
        counts[c] += 1

    if args.json:
        print(json.dumps(findings, ensure_ascii=False, indent=2))
    else:
        for fnd in findings:
            mark = {"supported": "✅", "needs-review": "🟡", "unsupported": "❌"}[fnd["citation"]]
            print(f"{mark} [{fnd.get('severity','?')}] {fnd.get('file','?')}:{fnd.get('line','?')} "
                  f"({fnd.get('ai','?')}) — {fnd.get('issue','')[:80]}")
        print(f"\ncitations: {counts['supported']} supported · "
              f"{counts['needs-review']} needs-review · {counts['unsupported']} unsupported")
        if counts["unsupported"]:
            print("→ Chair must verify unsupported/needs-review findings against the artifact. "
                  "Citation labels alone must not erase active Critical/Major findings.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
