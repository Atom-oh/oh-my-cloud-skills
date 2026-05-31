#!/usr/bin/env python3
"""Validate a .drawio file BEFORE exporting to PNG.

drawio's CLI exporter fails *silently* (exit 0, truncated PNG) on malformed XML —
the #1 cause of "looks done but 90% of the diagram is missing". This linter turns
those silent failures into loud, specific errors, and reports cell counts so you
can detect truncation.

Usage:
    python3 validate_drawio.py <file.drawio>            # lint + counts
    python3 validate_drawio.py <file.drawio> --coords   # also print absolute x/y/w/h of every cell

Exit code 0 = safe to export. Non-zero = fix before exporting.
"""
import sys
import re

# Prefer defusedxml (immune to XXE / billion-laughs); fall back to stdlib + a
# DOCTYPE/ENTITY reject guard (a .drawio file never legitimately contains these).
try:
    import defusedxml.ElementTree as ET  # type: ignore
    _DEFUSED = True
except ImportError:
    import xml.etree.ElementTree as ET
    _DEFUSED = False


def lint_raw(text: str) -> list[str]:
    """Catch the silent killers that pass `drawio -x` with a truncated render."""
    errors = []

    # 1) Unescaped '&' (must be &amp; &lt; &gt; &quot; &#NN;) in element text or
    #    attribute values. XML comments are SKIPPED — '&' is legal inside
    #    <!-- ... -->, so scanning them produces false positives (the real
    #    comment killer is '--', caught in check 2). Comments are blanked to
    #    spaces (newlines preserved) so reported line numbers stay accurate.
    orig_lines = text.splitlines()
    blanked = re.sub(r"<!--.*?-->",
                     lambda m: re.sub(r"[^\n]", " ", m.group(0)), text, flags=re.S)
    for i, bline in enumerate(blanked.splitlines(), 1):
        for m in re.finditer(r"&(?!amp;|lt;|gt;|quot;|apos;|#\d+;|#x[0-9A-Fa-f]+;)", bline):
            oline = orig_lines[i - 1] if i - 1 < len(orig_lines) else bline
            errors.append(f"L{i}: unescaped '&' (use &amp;) near: …{oline[max(0,m.start()-20):m.start()+10].strip()}…")

    # 2) '--' inside an XML comment is illegal and aborts the parser mid-file.
    for m in re.finditer(r"<!--(.*?)-->", text, re.S):
        if "--" in m.group(1):
            errors.append("XML comment contains '--' (illegal — drawio drops everything after it). "
                          "Remove decorative '-----' separators, or delete the comment.")
    # Unterminated comment
    if text.count("<!--") != text.count("-->"):
        errors.append("Mismatched <!-- / --> comment markers.")

    # 3) Security + validity: .drawio must never carry a DTD or entity definition.
    #    Rejecting these also neutralizes XXE / billion-laughs when the stdlib
    #    parser is the fallback (no defusedxml installed).
    if re.search(r"<!DOCTYPE", text, re.I) or re.search(r"<!ENTITY", text, re.I):
        errors.append("Contains <!DOCTYPE>/<!ENTITY> — not valid in a .drawio file "
                      "(and an XXE/entity-expansion risk). Remove it.")

    return errors


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    path = sys.argv[1]
    show_coords = "--coords" in sys.argv[2:]
    text = open(path, encoding="utf-8").read()

    errors = lint_raw(text)

    # Hard parse check (this is what drawio effectively does) — but ONLY when the
    # lint is clean. If lint already failed (e.g. it found a <!DOCTYPE>/<!ENTITY>),
    # do NOT hand the document to the stdlib XML parser: that is exactly the
    # XXE / billion-laughs vector when defusedxml is not installed. Skipping the
    # parse here keeps the DOCTYPE/ENTITY guard effective on the stdlib fallback.
    root = None
    if not errors:
        try:
            root = ET.fromstring(text)
        except ET.ParseError as e:
            errors.append(f"XML ParseError: {e} — drawio would render a TRUNCATED/empty diagram.")

    if errors:
        print(f"❌ {path}: {len(errors)} issue(s) — DO NOT export until fixed:")
        for e in errors:
            print(f"   • {e}")
        return 1

    # Counts (truncation detector): compare your intended node count to this.
    cells = root.findall(".//mxCell")
    vertices = [c for c in cells if c.get("vertex") == "1"]
    edges = [c for c in cells if c.get("edge") == "1"]
    icons = [c for c in vertices if "resIcon=" in (c.get("style") or "")]
    groups = [c for c in vertices if "shape=mxgraph.aws4.group" in (c.get("style") or "")]
    print(f"✅ {path}: XML valid, no silent-killer patterns.")
    print(f"   cells={len(cells)}  vertices={len(vertices)}  edges={len(edges)}  "
          f"aws4-icons={len(icons)}  group-containers={len(groups)}")
    print("   → Compare these counts to what you intended. A low count after export = truncation.")

    # Optional: resolve absolute coordinates (nested geometry) — removes the
    # manual coordinate-drift errors when computing edge waypoints across edits.
    if show_coords:
        by_id = {c.get("id"): c for c in cells}

        def abs_xy(cid, _seen=None):
            _seen = _seen or set()
            c = by_id.get(cid)
            if c is None or cid in _seen:
                return (0.0, 0.0)
            _seen.add(cid)
            g = c.find("mxGeometry")
            if g is None:
                return (0.0, 0.0)
            x, y = float(g.get("x", 0) or 0), float(g.get("y", 0) or 0)
            px, py = abs_xy(c.get("parent"), _seen) if c.get("parent") not in ("0", "1", None) else (0.0, 0.0)
            return (px + x, py + y)

        print("\n   Absolute coordinates (id: x,y w×h  label):")
        for c in vertices:
            g = c.find("mxGeometry")
            if g is None:
                continue
            ax, ay = abs_xy(c.get("id"))
            w, h = g.get("width", "?"), g.get("height", "?")
            label = (c.get("value") or "").strip()[:30]
            print(f"     {c.get('id')}: {ax:.0f},{ay:.0f} {w}×{h}  {label}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
