#!/usr/bin/env python3
"""Compute clean orthogonal edge waypoints for a .drawio file.

Messy, crossing arrows are the #1 reason AWS diagrams look bad. Auto-routing
(`orthogonalEdgeStyle` with no waypoints) cuts straight through sibling icons.
This helper computes explicit, channel-based orthogonal routes so parallel edges
share tidy lanes instead of crossing.

It resolves absolute geometry from the nested mxGraph tree (no manual coordinate
math), picks sensible exit/entry sides, and emits the `<mxPoint>` waypoints plus
the recommended `exitX/exitY/entryX/entryY` style to drop into the edge cell.

Usage:
    # one edge, auto side selection, routed through a vertical channel at x=900
    python3 route_edges.py arch.drawio --from <srcId|label> --to <dstId|label> --via-x 900
    # route through a horizontal channel at y=620 instead
    python3 route_edges.py arch.drawio --from A --to B --via-y 620
    # list cell ids/labels/abs-coords to pick from
    python3 route_edges.py arch.drawio --list

`--from`/`--to` accept an mxCell id or a (case-insensitive) substring of its label.
Coordinates are ABSOLUTE canvas coordinates (what mxPoint waypoints use).
"""
import sys
import re
import argparse

try:
    import defusedxml.ElementTree as ET  # immune to XXE / billion-laughs
except ImportError:
    import xml.etree.ElementTree as ET


def load(path):
    text = open(path, encoding="utf-8").read()
    if re.search(r"<!DOCTYPE|<!ENTITY", text, re.I):
        sys.exit("Refusing to parse: file contains <!DOCTYPE>/<!ENTITY> (invalid in .drawio / XXE risk).")
    root = ET.fromstring(text)
    return {c.get("id"): c for c in root.iter("mxCell")}


def abs_box(cells, cid, _seen=None):
    """Absolute (x, y, w, h) of a cell, summing parent offsets."""
    _seen = _seen or set()
    c = cells.get(cid)
    if c is None or cid in _seen:
        return None
    _seen.add(cid)
    g = c.find("mxGeometry")
    if g is None:
        return None
    x, y = float(g.get("x", 0) or 0), float(g.get("y", 0) or 0)
    w, h = float(g.get("width", 0) or 0), float(g.get("height", 0) or 0)
    p = c.get("parent")
    if p not in ("0", "1", None):
        pb = abs_box(cells, p, _seen)
        if pb:
            x += pb[0]
            y += pb[1]
    return (x, y, w, h)


def resolve(cells, key):
    if key in cells:
        return key
    matches = [cid for cid, c in cells.items()
               if key.lower() in (c.get("value") or "").lower() and c.get("vertex") == "1"]
    if len(matches) == 1:
        return matches[0]
    if not matches:
        sys.exit(f"No cell id/label matches '{key}'.")
    sys.exit(f"Ambiguous '{key}' → {[ (m, (cells[m].get('value') or '')[:30]) for m in matches]}. Use an id.")


def side_points(box):
    x, y, w, h = box
    return {
        "right": (x + w, y + h / 2, 1.0, 0.5),
        "left": (x, y + h / 2, 0.0, 0.5),
        "top": (x + w / 2, y, 0.5, 0.0),
        "bottom": (x + w / 2, y + h, 0.5, 1.0),
    }


def route(src, dst, via_x=None, via_y=None):
    """Return (waypoints, exit_anchor, entry_anchor) for a clean orthogonal path."""
    sp, dp = side_points(src), side_points(dst)
    sx, sy = src[0] + src[2] / 2, src[1] + src[3] / 2
    dx, dy = dst[0] + dst[2] / 2, dst[1] + dst[3] / 2

    if via_x is not None:
        # Vertical channel at via_x: exit horizontally → channel → enter horizontally.
        exit_side = "right" if via_x >= sx else "left"
        entry_side = "left" if via_x <= dx else "right"
        ex, ey, eax, eay = sp[exit_side]
        nx, ny, nax, nay = dp[entry_side]
        wps = [(via_x, ey), (via_x, ny)]
    elif via_y is not None:
        # Horizontal channel at via_y.
        exit_side = "bottom" if via_y >= sy else "top"
        entry_side = "top" if via_y <= dy else "bottom"
        ex, ey, eax, eay = sp[exit_side]
        nx, ny, nax, nay = dp[entry_side]
        wps = [(ex, via_y), (nx, via_y)]
    else:
        # Simple L-route: exit toward the dominant axis, single bend.
        if abs(dx - sx) >= abs(dy - sy):
            exit_side = "right" if dx >= sx else "left"
            entry_side = "top" if dy >= sy else "bottom"
            ex, ey, eax, eay = sp[exit_side]
            nx, ny, nax, nay = dp[entry_side]
            wps = [(nx, ey)]
        else:
            exit_side = "bottom" if dy >= sy else "top"
            entry_side = "left" if dx >= sx else "right"
            ex, ey, eax, eay = sp[exit_side]
            nx, ny, nax, nay = dp[entry_side]
            wps = [(ex, ny)]
    return wps, (eax, eay), (nax, nay)


def main():
    ap = argparse.ArgumentParser(description="Compute orthogonal edge waypoints for .drawio")
    ap.add_argument("file")
    ap.add_argument("--from", dest="src")
    ap.add_argument("--to", dest="dst")
    ap.add_argument("--via-x", type=float)
    ap.add_argument("--via-y", type=float)
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    cells = load(a.file)

    if a.list:
        for cid, c in cells.items():
            if c.get("vertex") == "1":
                b = abs_box(cells, cid)
                if b:
                    print(f"{cid:<28} {b[0]:.0f},{b[1]:.0f} {b[2]:.0f}×{b[3]:.0f}  {(c.get('value') or '')[:34]}")
        return

    if not (a.src and a.dst):
        ap.error("--from and --to required (or use --list)")
    s, d = resolve(cells, a.src), resolve(cells, a.dst)
    sb, db = abs_box(cells, s), abs_box(cells, d)
    wps, (eax, eay), (nax, nay) = route(sb, db, a.via_x, a.via_y)

    print(f"# {a.src} → {a.dst}")
    print(f"# add to edge style: exitX={eax};exitY={eay};exitDx=0;exitDy=0;"
          f"entryX={nax};entryY={nay};entryDx=0;entryDy=0;edgeStyle=orthogonalEdgeStyle;rounded=0;")
    print("# waypoints (paste inside the edge's <mxGeometry>):")
    print('        <Array as="points">')
    for x, y in wps:
        print(f'          <mxPoint x="{x:.0f}" y="{y:.0f}" />')
    print('        </Array>')


if __name__ == "__main__":
    main()
