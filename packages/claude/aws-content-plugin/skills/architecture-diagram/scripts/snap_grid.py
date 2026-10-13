#!/usr/bin/env python3
"""Snap every cell's position to the grid — mechanical alignment so the diagram
stops looking 1-5px "off".

The LLM hand-picks coordinates and lands a few pixels off; `lint_layout.py` *detects*
that drift, this script *fixes* it. Run it after writing the .drawio and before export:

    write .drawio → snap_grid.py → validate_drawio.py → lint_layout.py → export

By default it snaps each cell's RELATIVE x/y to the nearest multiple of GRID (10) and
leaves width/height ALONE — icon sizes are fixed by design-tokens.md (78×78, which is
intentionally not a grid multiple), so resizing would break the canon. Pass --size to
also snap width/height (rarely wanted).

Usage:
    python3 snap_grid.py <file.drawio>                 # print snapped XML to stdout
    python3 snap_grid.py <file.drawio> --in-place      # rewrite the file
    python3 snap_grid.py <file.drawio> -o out.drawio   # write to a new file
    python3 snap_grid.py <file.drawio> --grid 20        # custom grid (default 10)
    python3 snap_grid.py <file.drawio> --size           # also snap width/height
    python3 snap_grid.py <file.drawio> --report         # just report how many would move (no write)

Exit 0 on success, 2 on usage/read error.
"""
import sys
import re

GRID = 10

# Only touch attributes inside <mxGeometry ...>. We operate on the raw text (not a
# DOM round-trip) to preserve formatting/ordering exactly — only the numbers change.
_GEOM_RE = re.compile(r"<mxGeometry\b[^>]*>")
_ATTR_RE = re.compile(r'\b(x|y|width|height)="(-?\d+(?:\.\d+)?)"')


def _snap(val, grid):
    return int(round(float(val) / grid) * grid)


def snap_text(text, grid=GRID, size=False):
    """Return (new_text, moved_count). Snaps x/y (and w/h if size=True) in every
    <mxGeometry>. DOCTYPE/ENTITY is rejected (defense-in-depth; a .drawio never has one)."""
    if re.search(r"<!DOCTYPE", text, re.I) or re.search(r"<!ENTITY", text, re.I):
        raise ValueError("Refusing to process: contains <!DOCTYPE>/<!ENTITY> "
                         "(XXE/entity risk). Run validate_drawio.py and remove it.")
    keys = ("x", "y", "width", "height") if size else ("x", "y")
    moved = [0]

    def fix_geom(m):
        tag = m.group(0)

        def fix_attr(a):
            name, num = a.group(1), a.group(2)
            if name not in keys:
                return a.group(0)
            snapped = _snap(num, grid)
            if str(snapped) != num and float(num) != snapped:
                moved[0] += 1
            return f'{name}="{snapped}"'

        return _ATTR_RE.sub(fix_attr, tag)

    new_text = _GEOM_RE.sub(fix_geom, text)
    return new_text, moved[0]


def main():
    args = sys.argv[1:]
    if not args or args[0].startswith("-"):
        print(__doc__)
        return 2
    path = args[0]
    grid = GRID
    if "--grid" in args:
        i = args.index("--grid")
        grid = int(args[i + 1]) if i + 1 < len(args) else GRID
    out = None
    if "-o" in args:
        i = args.index("-o")
        out = args[i + 1] if i + 1 < len(args) else None
    in_place = "--in-place" in args
    size = "--size" in args
    report = "--report" in args

    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except (OSError, UnicodeDecodeError) as e:
        print(f"❌ cannot read {path}: {e}", file=sys.stderr)
        return 2

    try:
        new_text, moved = snap_text(text, grid, size)
    except ValueError as e:
        print(f"❌ {path}: {e}", file=sys.stderr)
        return 2

    if report:
        print(f"{path}: {moved} coordinate(s) not on the {grid}px grid "
              f"({'would snap' if moved else 'already aligned'})")
        return 0

    if in_place:
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_text)
        print(f"✅ snapped {moved} coordinate(s) to the {grid}px grid → {path}", file=sys.stderr)
    elif out:
        with open(out, "w", encoding="utf-8") as f:
            f.write(new_text)
        print(f"✅ snapped {moved} coordinate(s) to the {grid}px grid → {out}", file=sys.stderr)
    else:
        sys.stdout.write(new_text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
