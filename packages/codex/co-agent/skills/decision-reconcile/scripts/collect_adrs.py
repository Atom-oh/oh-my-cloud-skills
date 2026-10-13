#!/usr/bin/env python3
"""Collect and structure ADRs for contradiction review.

Parses docs/decisions/ADR-*.md into structured records (number, title, status,
decision, context, cross-references) and runs deterministic pre-checks that need
no LLM (status/supersession link inconsistencies, duplicate numbers, unknown
status). Emits JSON for downstream multi-agent review.

Usage:
    collect_adrs.py [decisions_dir]      # default: docs/decisions
    collect_adrs.py --summary [dir]      # human-readable summary instead of JSON

Output JSON shape:
    {
      "adrs": [ {number, file, title, status, decision, context, references, superseded_by} ],
      "warnings": [ "..." ],            # deterministic inconsistencies found
      "summary": {accepted, superseded, deprecated, proposed, total}
    }
"""
import json
import re
import sys
from pathlib import Path

KNOWN_STATUS = {"proposed", "accepted", "deprecated", "superseded"}
# Korean status -> canonical English (bilingual ADRs use 한국어 status too).
KO_STATUS = {"제안됨": "proposed", "승인됨": "accepted",
             "더 이상 사용되지 않음": "deprecated", "대체됨": "superseded"}


def english_portion(text: str) -> str:
    """Bilingual ADRs duplicate every section in Korean. Parse only the English
    half so a single ADR isn't double-counted. Split on the Korean anchor/heading."""
    for marker in ('<a id="korean">', "\n# 한국어", "\n# Korean"):
        idx = text.find(marker)
        if idx != -1:
            return text[:idx]
    return text


def section(text: str, *headings: str) -> str:
    """Return the body of the first `## <heading>` section (any of the aliases),
    up to the next `## ` heading or end of text."""
    for h in headings:
        m = re.search(rf"^#{{1,3}}\s*{re.escape(h)}\s*$(.*?)(?=^#{{1,3}}\s|\Z)",
                      text, re.MULTILINE | re.DOTALL | re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return ""


def first_line(block: str) -> str:
    for line in block.splitlines():
        line = line.strip()
        if line:
            return line
    return ""


def canonical_status(raw: str) -> str:
    low = raw.lower()
    for ko, en in KO_STATUS.items():
        if ko in raw:
            return en
    for s in KNOWN_STATUS:
        if s in low:
            return s
    return raw.strip() or "(missing)"


def parse_adr(path: Path) -> dict:
    full = path.read_text(encoding="utf-8")
    text = english_portion(full)
    num_m = re.search(r"ADR-(\d+)", path.name)
    number = int(num_m.group(1)) if num_m else None

    title_m = re.search(r"^#\s*ADR-\d+\s*[:\-]\s*(.+)$", text, re.MULTILINE)
    title = title_m.group(1).strip() if title_m else path.stem

    status_block = section(text, "Status", "상태")
    status_raw = first_line(status_block)
    status = canonical_status(status_raw)

    decision = section(text, "Decision", "결정")
    context = section(text, "Context", "배경")

    # Cross-referenced ADRs (exclude self).
    refs = sorted({int(n) for n in re.findall(r"ADR-(\d+)", text)} - {number})

    # Supersession: explicit "Superseded by ADR-N" anywhere, or status==superseded.
    sup_m = re.search(r"supersed\w*\s+by\s+ADR-(\d+)", text, re.IGNORECASE)
    superseded_by = int(sup_m.group(1)) if sup_m else None

    def clip(s: str, n: int = 600) -> str:
        s = re.sub(r"\s+", " ", s).strip()
        return s if len(s) <= n else s[:n].rstrip() + " …"

    return {
        "number": number,
        "file": str(path),
        "title": title,
        "status": status,
        "status_raw": status_raw,
        "decision": clip(decision),
        "context": clip(context),
        "references": refs,
        "superseded_by": superseded_by,
    }


def check(adrs: list) -> list:
    """Deterministic inconsistency pre-checks (no LLM needed)."""
    warnings = []
    by_num = {}
    for a in adrs:
        if a["number"] is None:
            warnings.append(f"{a['file']}: filename has no ADR-NNN number")
            continue
        by_num.setdefault(a["number"], []).append(a)

    for num, group in sorted(by_num.items()):
        if len(group) > 1:
            files = ", ".join(g["file"] for g in group)
            warnings.append(f"ADR-{num:03d}: duplicate number across files ({files})")

    for a in adrs:
        n = a["number"]
        if a["status"] not in KNOWN_STATUS:
            warnings.append(
                f"ADR-{n:03d}: unknown status '{a['status_raw']}' "
                f"(expected one of {sorted(KNOWN_STATUS)})")
        # Status says superseded but no superseding ADR is named anywhere.
        if a["status"] == "superseded" and a["superseded_by"] is None:
            warnings.append(
                f"ADR-{n:03d}: status is Superseded but no 'Superseded by ADR-NNN' link found")
        # Points at a superseding ADR that doesn't exist.
        if a["superseded_by"] is not None and a["superseded_by"] not in by_num:
            warnings.append(
                f"ADR-{n:03d}: marked superseded by ADR-{a['superseded_by']:03d}, "
                f"but that ADR does not exist")
        # The superseding ADR exists but is itself not Accepted — dangling reversal.
        elif a["superseded_by"] is not None:
            target = by_num[a["superseded_by"]][0]
            if target["status"] not in ("accepted", "proposed"):
                warnings.append(
                    f"ADR-{n:03d}: superseded by ADR-{a['superseded_by']:03d}, "
                    f"but that ADR's status is '{target['status']}' (not Accepted)")
    return warnings


def main() -> int:
    args = [a for a in sys.argv[1:] if a != "--summary"]
    summary_mode = "--summary" in sys.argv[1:]
    decisions_dir = Path(args[0]) if args else Path("docs/decisions")

    if not decisions_dir.is_dir():
        print(json.dumps({"adrs": [], "warnings": [
            f"{decisions_dir} does not exist — no ADRs to reconcile"], "summary": {}}))
        return 0

    files = sorted(p for p in decisions_dir.glob("ADR-*.md")
                   if not p.name.endswith(".template.md"))
    adrs = [parse_adr(p) for p in files]
    warnings = check(adrs)

    counts = {}
    for a in adrs:
        counts[a["status"]] = counts.get(a["status"], 0) + 1
    summary = {"total": len(adrs), **counts}

    if summary_mode:
        print(f"ADRs in {decisions_dir}: {len(adrs)}")
        for a in adrs:
            sup = f"  -> superseded by ADR-{a['superseded_by']:03d}" if a["superseded_by"] else ""
            print(f"  ADR-{a['number']:03d} [{a['status']}] {a['title']}{sup}")
        print(f"\nStatus counts: {summary}")
        if warnings:
            print(f"\n{len(warnings)} deterministic inconsistency warning(s):")
            for w in warnings:
                print(f"  ! {w}")
        else:
            print("\nNo deterministic inconsistencies found (LLM review still recommended).")
        return 0

    print(json.dumps({"adrs": adrs, "warnings": warnings, "summary": summary},
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
