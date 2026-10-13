#!/usr/bin/env python3
"""Geometric QA for a .drawio diagram — the "is it clean enough to look like PPT?" gate.

`validate_drawio.py` checks that the XML is well-formed (no silent truncation).
This script checks the *layout* — the things a human designer fixes intuitively and
the LLM gets subtly wrong, which is what makes output look amateur. Two families:

  GEOMETRY (is it aligned / non-overlapping?)
  - grid alignment      (coordinates off the 10px grid → 1-5px drift, visible)
  - sibling spacing     (uneven gaps between icons in a row/column)
  - containment         (an icon pokes outside its VPC/subnet box)
  - icon overlap        (two icons' boxes intersect)
  - canvas margin       (elements jammed against the edge / negative coords)
  - edge budget         (too many connectors → spaghetti; use numbered flow)

  DESIGN (does it look finished, like a hand-crafted PPT?)
  - icon-size uniformity (mixing 78 and 48 is the #1 "amateur" tell — design-tokens.md)
  - label readability    (a service icon with no label is unreadable)
  - container breathing  (icons jammed against their VPC/subnet edge — no whitespace)
  - title presence       (a titled diagram reads as finished, not a fragment)
  - font consistency     (Amazon Ember/Helvetica everywhere, per design-tokens.md)

It prints a layout SCORE (0-100, with a geometry/design breakdown) and exits non-zero
below the threshold so it can be used as a hard pre-export gate. Tunables match
references/design-tokens.md.

Usage:
    python3 lint_layout.py <file.drawio>                 # score + findings
    python3 lint_layout.py <file.drawio> --threshold 85  # custom gate (default 80)
    python3 lint_layout.py <file.drawio> --json          # machine-readable

Exit 0 = passes the layout gate. 1 = below threshold (fix before export). 2 = usage/read error.
"""
import sys
import json as _json

try:
    import defusedxml.ElementTree as ET  # type: ignore
    _DEFUSED = True
except ImportError:
    import xml.etree.ElementTree as ET
    _DEFUSED = False


def _xxe_guard(text):
    """On the stdlib fallback, refuse documents with a DTD/entity definition (XXE /
    billion-laughs vector). A .drawio file never legitimately contains these, and
    validate_drawio.py is expected to run first — this is defense in depth."""
    if _DEFUSED:
        return
    import re
    if re.search(r"<!DOCTYPE", text, re.I) or re.search(r"<!ENTITY", text, re.I):
        raise ValueError("Refusing to parse: contains <!DOCTYPE>/<!ENTITY> "
                         "(XXE/entity-expansion risk). Run validate_drawio.py and remove it.")

# --- Tunables (keep in sync with references/design-tokens.md) ---
GRID = 5                # drift threshold; real coords on a 5px grid are fine, odd ones drift
MAX_EDGES = 12          # above this → spaghetti risk, recommend numbered flow
CONTAIN_TOL = 2         # px slack for child-inside-parent
SPACING_CV = 0.5        # allowed coeff. of variation (stdev/mean) for row/col gaps
DEFAULT_THRESHOLD = 80
# design checks
EDGE_PAD = 12           # min px between an icon and its container's edge (breathing room)
TITLE_FONT = 14         # a text cell at >= this font size near the top counts as a title


def _style_val(style, key, default=None):
    """Pull a `key=value;` token out of a drawio style string."""
    s = style or ""
    for part in s.split(";"):
        if part.startswith(key + "="):
            return part[len(key) + 1:]
    return default


def _is_group(style):
    return "mxgraph.aws4.group" in (style or "") or "shape=mxgraph.aws4.group" in (style or "")


def _f(v, d=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return d


def _is_icon(style):
    """A service/resource icon — NOT a group/container. `resIcon=` is the reliable
    marker; group shapes (mxgraph.aws4.group*) are explicitly excluded so big
    container boxes aren't counted as overlapping 'icons'."""
    s = style or ""
    return "resIcon=" in s and "mxgraph.aws4.group" not in s


def analyze(text):
    _xxe_guard(text)
    root = ET.fromstring(text)
    cells = root.findall(".//mxCell")
    by_id = {c.get("id"): c for c in cells}

    def geom(c):
        g = c.find("mxGeometry")
        if g is None:
            return None
        return (_f(g.get("x")), _f(g.get("y")), _f(g.get("width")), _f(g.get("height")))

    def abs_origin(cid, _seen=None):
        """Absolute (x,y) of a cell by summing relative offsets up the parent chain."""
        _seen = _seen or set()
        c = by_id.get(cid)
        if c is None or cid in _seen:
            return (0.0, 0.0)
        _seen.add(cid)
        g = geom(c)
        if g is None:
            return (0.0, 0.0)
        x, y = g[0], g[1]
        p = c.get("parent")
        if p in ("0", "1", None):
            return (x, y)
        px, py = abs_origin(p, _seen)
        return (px + x, py + y)

    vertices = [c for c in cells if c.get("vertex") == "1" and geom(c)]
    edges = [c for c in cells if c.get("edge") == "1"]
    icons = [c for c in vertices if _is_icon(c.get("style"))]

    findings = []  # (severity_weight, message)

    # 1) Grid alignment — abs coords should be multiples of GRID
    off_grid = []
    for c in vertices:
        ax, ay = abs_origin(c.get("id"))
        if (round(ax) % GRID) or (round(ay) % GRID):
            off_grid.append((c.get("id"), ax, ay))
    if off_grid:
        findings.append((min(8, len(off_grid)),
                         f"{len(off_grid)} element(s) off the {GRID}px grid (sub-pixel drift) "
                         f"e.g. id={off_grid[0][0]} at ({off_grid[0][1]:.0f},{off_grid[0][2]:.0f})"))

    # 2) Containment — every child must sit inside its parent's box
    out_of_box = []
    for c in vertices:
        p = c.get("parent")
        if p in ("0", "1", None) or p not in by_id:
            continue
        pg = geom(by_id[p])
        if not pg or (pg[2] <= 0 and pg[3] <= 0):
            continue
        ax, ay, w, h = (*abs_origin(c.get("id")), geom(c)[2], geom(c)[3])
        pax, pay = abs_origin(p)
        pw, ph = pg[2], pg[3]
        if (ax < pax - CONTAIN_TOL or ay < pay - CONTAIN_TOL or
                ax + w > pax + pw + CONTAIN_TOL or ay + h > pay + ph + CONTAIN_TOL):
            out_of_box.append(c.get("id"))
    if out_of_box:
        findings.append((min(30, 8 * len(out_of_box)),
                         f"{len(out_of_box)} element(s) escape their container box "
                         f"(e.g. id={out_of_box[0]}) — icon sticking outside a VPC/subnet"))

    # 3) Icon overlap — sibling icon boxes must not intersect
    overlaps = 0
    boxes = []
    for c in icons:
        ax, ay = abs_origin(c.get("id"))
        g = geom(c)
        boxes.append((ax, ay, g[2], g[3], c.get("parent")))
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            a, b = boxes[i], boxes[j]
            if a[4] != b[4]:
                continue  # only flag overlap among siblings
            if (a[0] < b[0] + b[2] and a[0] + a[2] > b[0] and
                    a[1] < b[1] + b[3] and a[1] + a[3] > b[1]):
                overlaps += 1
    if overlaps:
        findings.append((min(30, 8 * overlaps), f"{overlaps} pair(s) of overlapping icons"))

    # 4) Sibling spacing uniformity — icons in the same row/col should be evenly spaced
    from collections import defaultdict
    rows = defaultdict(list)  # (parent, round(y/20)) -> [x...]
    cols = defaultdict(list)
    for c in icons:
        ax, ay = abs_origin(c.get("id"))
        rows[(c.get("parent"), round(ay / 20))].append(ax)
        cols[(c.get("parent"), round(ax / 20))].append(ay)

    def _cv_bad(positions):
        ps = sorted(positions)
        if len(ps) < 3:
            return False
        gaps = [ps[k + 1] - ps[k] for k in range(len(ps) - 1)]
        mean = sum(gaps) / len(gaps)
        if mean <= 0:
            return False
        var = sum((g - mean) ** 2 for g in gaps) / len(gaps)
        return (var ** 0.5) / mean > SPACING_CV

    uneven = sum(1 for v in rows.values() if _cv_bad(v)) + sum(1 for v in cols.values() if _cv_bad(v))
    if uneven:
        findings.append((min(15, 5 * uneven),
                         f"{uneven} row/column of icons with uneven spacing (gaps vary > {int(SPACING_CV*100)}%)"))

    # 5) Canvas margin — no element at negative coords (jammed past the edge)
    neg = [c.get("id") for c in vertices if min(abs_origin(c.get("id"))) < 0]
    if neg:
        findings.append((min(10, 3 * len(neg)), f"{len(neg)} element(s) at negative coordinates (off-canvas)"))

    # 6) Edge budget
    if len(edges) > MAX_EDGES:
        findings.append((min(10, (len(edges) - MAX_EDGES)),
                         f"{len(edges)} edges (> {MAX_EDGES}) — spaghetti risk; consider the "
                         f"numbered-flow pattern (badges + legend) for secondary connections"))

    # ---- DESIGN checks (the "looks finished like a PPT" layer) ----
    design = []  # (weight, message)

    # D1) Icon-size discipline. The canonical scale is 78 (standard) + 48/52 (nested,
    # dense). A clean 78+48 two-tier is allowed (SKILL.md); the real "amateur" tells are
    # (a) off-scale/retired sizes like 40, 60, 64 and (b) more than two tiers at once.
    ALLOWED = {48, 52, 78}
    sizes = {}
    for c in icons:
        g = geom(c)
        sizes.setdefault((round(g[2]), round(g[3])), []).append(c.get("id"))
    off_scale = {wh: ids for wh, ids in sizes.items() if wh[0] not in ALLOWED}
    allowed_tiers = [wh for wh in sizes if wh[0] in ALLOWED]
    if off_scale:
        n = sum(len(ids) for ids in off_scale.values())
        shown = ", ".join(f"{w}x{h}" for (w, h) in sorted(off_scale))
        design.append((min(20, 5 * len(off_scale) + n),
                       f"{n} icon(s) at off-scale size(s) {shown} — use 78×78 (or 48×48 nested). "
                       f"40/60/64 are retired and read as amateur (design-tokens.md)"))
    elif len(allowed_tiers) > 2:
        shown = ", ".join(f"{w}x{h}" for (w, h) in sorted(allowed_tiers))
        design.append((10, f"icons span {len(allowed_tiers)} size tiers ({shown}) — collapse to "
                           f"one standard (78) plus at most one nested tier (48)"))

    # D2) Label readability — a service icon with no visible label.
    unlabeled = [c.get("id") for c in icons if not (c.get("value") or "").strip()]
    if unlabeled:
        design.append((min(12, 3 * len(unlabeled)),
                       f"{len(unlabeled)} icon(s) have no label — every AWS icon needs a "
                       f"service name below it (e.g. id={unlabeled[0]})"))

    # D3) Container breathing room — icons jammed against their container's edge.
    crowded = 0
    for c in icons:
        p = c.get("parent")
        if p in ("0", "1", None) or p not in by_id:
            continue
        if not _is_group(by_id[p].get("style")):
            continue
        pg = geom(by_id[p])
        if not pg or pg[2] <= 0:
            continue
        ax, ay = abs_origin(c.get("id"))
        g = geom(c)
        pax, pay = abs_origin(p)
        if (ax - pax < EDGE_PAD or ay - pay < EDGE_PAD or
                (pax + pg[2]) - (ax + g[2]) < EDGE_PAD or (pay + pg[3]) - (ay + g[3]) < EDGE_PAD):
            crowded += 1
    if crowded:
        design.append((min(12, 2 * crowded),
                       f"{crowded} icon(s) jammed within {EDGE_PAD}px of their container edge — "
                       f"add breathing room (space.icon-to-edge, design-tokens.md)"))

    # D4) Title presence — a top text cell at a heading font size reads as "finished".
    min_x = min((abs_origin(c.get("id"))[0] for c in vertices), default=0.0)
    min_y = min((abs_origin(c.get("id"))[1] for c in vertices), default=0.0)
    has_title = False
    for c in vertices:
        if _is_icon(c.get("style")) or _is_group(c.get("style")):
            continue
        if not (c.get("value") or "").strip():
            continue
        if _f(_style_val(c.get("style"), "fontSize"), 0) >= TITLE_FONT:
            ax, ay = abs_origin(c.get("id"))
            if ay <= min_y + 120:  # near the top band
                has_title = True
                break
    if not has_title and len(icons) >= 3:
        design.append((5, "no title — add a heading text cell (fontSize ≥ 14) at the top; "
                          "a titled diagram reads as finished, not a fragment"))

    # D5) Font consistency — labeled shapes should all use Amazon Ember / Helvetica.
    bad_font = 0
    for c in vertices:
        if not (c.get("value") or "").strip():
            continue
        fam = (_style_val(c.get("style"), "fontFamily") or "")
        if "Amazon Ember" not in fam and "Helvetica" not in fam:
            bad_font += 1
    if bad_font:
        design.append((min(10, bad_font),
                       f"{bad_font} labeled element(s) not using Amazon Ember/Helvetica "
                       f"(font.* in design-tokens.md) — inconsistent type looks unpolished"))

    geom_loss = sum(w for w, _ in findings)
    design_loss = sum(w for w, _ in design)
    score = max(0, 100 - geom_loss - design_loss)
    return {
        "score": score,
        "subscores": {"geometry": max(0, 100 - geom_loss), "design": max(0, 100 - design_loss)},
        "counts": {"vertices": len(vertices), "icons": len(icons), "edges": len(edges)},
        "findings": [f"[geometry] {m}" for _, m in findings] + [f"[design] {m}" for _, m in design],
    }


def main():
    args = sys.argv[1:]
    if not args or args[0].startswith("--"):
        print(__doc__)
        return 2
    path = args[0]
    threshold = DEFAULT_THRESHOLD
    if "--threshold" in args:
        i = args.index("--threshold")
        threshold = int(args[i + 1]) if i + 1 < len(args) else DEFAULT_THRESHOLD
    as_json = "--json" in args

    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except (OSError, UnicodeDecodeError) as e:
        print(f"❌ cannot read {path}: {e}")
        return 2
    try:
        result = analyze(text)
    except ET.ParseError as e:
        print(f"❌ {path}: XML ParseError ({e}) — run validate_drawio.py first")
        return 2
    except ValueError as e:
        print(f"❌ {path}: {e}")
        return 2

    if as_json:
        result["threshold"] = threshold
        result["pass"] = result["score"] >= threshold
        print(_json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["pass"] else 1

    c = result["counts"]
    sub = result.get("subscores", {})
    ok = result["score"] >= threshold
    mark = "✅" if ok else "❌"
    breakdown = (f" [geometry {sub['geometry']} · design {sub['design']}]"
                 if sub else "")
    print(f"{mark} {path}: layout score {result['score']}/100 (gate {threshold}){breakdown} "
          f"— icons={c['icons']} edges={c['edges']} vertices={c['vertices']}")
    for m in result["findings"]:
        print(f"   • {m}")
    if not ok:
        print("   → Below the layout gate. Fix [geometry] (align to grid, containment/overlap, "
              "spacing, edges) and [design] (one icon size, label every icon, breathing room, "
              "title, fonts) before exporting. See design-tokens.md.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
