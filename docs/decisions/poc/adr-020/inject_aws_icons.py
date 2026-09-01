#!/usr/bin/env python3
"""PoC: inject official AWS architecture icons into an Archify-rendered HTML.

Post-processing keeps Archify unmodified (depend, don't fork): each node group in
the output carries id="node-<id>" and its <rect> uses the spec's own coordinates,
so an icon can be placed deterministically without touching the renderer.

Usage: inject_aws_icons.py <archify.html> <mapping.json> <icons-dir> <out.html>
mapping.json: {"<node-id>": "<icon-file.svg>", ...}
"""
import json, re, sys

def load_icon(path: str, uid: str) -> str:
    svg = open(path, encoding="utf-8").read()
    svg = re.sub(r"<\?xml[^>]*\?>", "", svg)
    # Namespace internal ids (gradients etc.) so multiple icons can't collide.
    for m in set(re.findall(r'id="([^"]+)"', svg)):
        svg = svg.replace(f'id="{m}"', f'id="{uid}-{m}"')
        svg = svg.replace(f"url(#{m})", f"url(#{uid}-{m})")
        svg = svg.replace(f'href="#{m}"', f'href="#{uid}-{m}"')
    return svg

def main(html_path, map_path, icons_dir, out_path):
    html = open(html_path, encoding="utf-8").read()
    mapping = json.load(open(map_path, encoding="utf-8"))
    injected = 0
    for node_id, icon_file in mapping.items():
        # Find the node group's first rect to get geometry.
        g = re.search(rf'<g[^>]*id="node-{re.escape(node_id)}"[^>]*>', html)
        if not g:
            print(f"skip: node-{node_id} not found", file=sys.stderr)
            continue
        rect = re.search(
            r'<rect x="([\d.]+)" y="([\d.]+)" width="([\d.]+)" height="([\d.]+)"',
            html[g.end():g.end() + 600])
        if not rect:
            print(f"skip: node-{node_id} rect not found", file=sys.stderr)
            continue
        x, y, w, h = (float(v) for v in rect.groups())
        size = 30
        ix, iy = x + w - size - 6, y + 6  # top-right corner of the node
        icon = load_icon(f"{icons_dir}/{icon_file}", f"awsicon-{node_id}")
        # Strip the <svg> wrapper and place the 80x80 content via a <g transform>:
        # a nested <svg>'s x/y geometry can be overridden by the viewer's CSS,
        # a transform attribute on <g> cannot.
        inner = re.sub(r"^.*?<svg[^>]*>", "", icon, count=1, flags=re.S)
        inner = re.sub(r"</svg>\s*$", "", inner, flags=re.S)
        inner = re.sub(r"<title>.*?</title>", "", inner, count=1, flags=re.S)
        scale = size / 80.0
        # SVG paints in document order: insert AFTER the node's rects (before its
        # first <text>) so the opaque node body doesn't cover the icon.
        anchor = html.find("<text", g.end())
        if anchor == -1:
            print(f"skip: node-{node_id} text anchor not found", file=sys.stderr)
            continue
        icon_g = (f'<g class="aws-official-icon" aria-hidden="true" '
                  f'transform="translate({ix} {iy}) scale({scale})">{inner}</g>')
        html = html[:anchor] + icon_g + html[anchor:]
        injected += 1
    open(out_path, "w", encoding="utf-8").write(html)
    print(f"injected {injected}/{len(mapping)} icons -> {out_path}")

if __name__ == "__main__":
    main(*sys.argv[1:5])
