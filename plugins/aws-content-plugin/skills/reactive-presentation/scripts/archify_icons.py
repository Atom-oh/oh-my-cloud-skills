#!/usr/bin/env python3
"""Inject official AWS architecture icons into an Archify-rendered HTML diagram.

Promotes the PoC at docs/decisions/poc/adr-020/inject_aws_icons.py (ADR-020) —
that script's mechanics ARE the contract; nothing here redesigns them. Archify
itself is kept unmodified ("depend, don't fork"): every node group in Archify's
rendered output carries id="node-<id>" and its <rect> uses the spec's own
coordinates, so an icon can be placed deterministically as a post-processing
step without touching the renderer.

Stdlib only.

CLI:
    archify_icons.py <archify.html> <out.html> --map <mapping.json>
    archify_icons.py <archify.html> <out.html> --spec <spec.json>
"""
import argparse
import importlib.util
import json
import os
import re
import subprocess
import sys

# ---- version pin -----------------------------------------------------------
# This module is the SINGLE HOME of the Archify version pin. remarp_to_slides.py
# imports ARCHIFY_VERSION / ARCHIFY_PIN from here rather than repeating the
# literals, so there is exactly one place to bump on an upgrade.
ARCHIFY_VERSION = "2.16.0"
ARCHIFY_PIN = "199360cc6687a7857b54dd188d4922b09e466a4b"


# ---- 3.1 Archify clone discovery -------------------------------------------
def resolve_archify_dir():
    """Locate the Archify clone and return the dir containing bin/archify.mjs.

    Candidate roots, in order: $ARCHIFY_DIR, then /tmp/archify. The clone has a
    DOUBLED directory: the git repo root is /tmp/archify, but the package
    (bin/, schemas/, SKILL.md) lives one level down at /tmp/archify/archify.
    So both <candidate>/bin/archify.mjs and <candidate>/archify/bin/archify.mjs
    are checked, and the directory that actually CONTAINS bin/archify.mjs is
    returned (not necessarily the candidate itself).

    Returns None when neither shape resolves — a legitimate outcome, not an
    error, e.g. in an environment with no clone.
    """
    candidates = []
    env_dir = os.environ.get("ARCHIFY_DIR")
    if env_dir:
        candidates.append(env_dir)
    candidates.append("/tmp/archify")

    for cand in candidates:
        direct = os.path.join(cand, "bin", "archify.mjs")
        if os.path.isfile(direct):
            return cand
        nested = os.path.join(cand, "archify", "bin", "archify.mjs")
        if os.path.isfile(nested):
            return os.path.join(cand, "archify")
    return None


def check_pin(archify_dir):
    """Check the resolved clone's HEAD commit against ARCHIFY_PIN.

    `git -C <archify_dir> rev-parse HEAD` is used directly: git walks up to the
    repo root by itself, so this does NOT need to compute the clone root even
    though archify_dir is the doubled /tmp/archify/archify subdirectory.

    Returns (matches: bool, actual_sha: str). Any failure (dir is None, git
    missing, not a repo, non-zero exit) returns (False, "") rather than raising.
    """
    if not archify_dir:
        return (False, "")
    try:
        result = subprocess.run(
            ["git", "-C", archify_dir, "rev-parse", "HEAD"],
            capture_output=True, text=True, check=False,
        )
    except OSError:
        return (False, "")
    if result.returncode != 0:
        return (False, "")
    actual = result.stdout.strip()
    if actual != ARCHIFY_PIN:
        return (False, actual)
    # HEAD alone is not the pin promise: a clone checked out at the pinned
    # commit with locally modified files (e.g. a world-writable /tmp/archify
    # on a shared host) would pass the SHA test and still run arbitrary code
    # under `node`. A dirty worktree therefore fails the pin check too.
    try:
        dirty = subprocess.run(
            ["git", "-C", archify_dir, "status", "--porcelain"],
            capture_output=True, text=True, check=False,
        )
    except OSError:
        return (False, actual)
    if dirty.returncode != 0 or dirty.stdout.strip():
        return (False, f"{actual} (dirty worktree)")
    return (True, actual)


# ---- 3.2 Icon vocabulary — import, never copy ------------------------------
_HERE = os.path.dirname(os.path.abspath(__file__))
_LAYOUT_AWS = os.path.normpath(os.path.join(
    _HERE, "..", "..", "architecture-diagram", "scripts", "layout_aws.py"))

_arch_stems_cache = None


def _load_arch_stems():
    """Load ARCH_STEMS from the sibling architecture-diagram skill's
    layout_aws.py by file path (never copy the table — it is the shared
    service-name vocabulary consumed by both diagram paths, ADR-020 §2).

    layout_aws.py imports only stdlib at module scope, so exec'ing it here is
    safe and cheap. Cached in a module global so repeated calls don't re-exec.
    """
    global _arch_stems_cache
    if _arch_stems_cache is not None:
        return _arch_stems_cache
    if not os.path.isfile(_LAYOUT_AWS):
        raise RuntimeError(
            "archify_icons.py could not find layout_aws.py at the computed "
            f"path: {_LAYOUT_AWS!r}. This file must live at "
            "skills/reactive-presentation/scripts/ so that "
            "../../architecture-diagram/scripts/layout_aws.py resolves to the "
            "sibling architecture-diagram skill."
        )
    spec = importlib.util.spec_from_file_location("layout_aws", _LAYOUT_AWS)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _arch_stems_cache = module.ARCH_STEMS
    return _arch_stems_cache


# ---- 3.3 Index + icon-file resolution --------------------------------------
_ICONS_DIR = os.path.normpath(os.path.join(_HERE, "..", "icons"))
_INDEX_PATH = os.path.join(_ICONS_DIR, "index-lite.json")

_icons_index_cache = None


def _load_icons_index():
    """Load index-lite.json's ["icons"] sub-dict.

    index-lite.json is NOT a flat dict of stem -> entry: it is
    {"description": ..., "total": 811, "icons": {"<stem>": {...}, ...}}. Every
    lookup in this module goes through ["icons"] — a `stem in index` test
    against the top-level object is always False.
    """
    global _icons_index_cache
    if _icons_index_cache is not None:
        return _icons_index_cache
    with open(_INDEX_PATH, encoding="utf-8") as fh:
        data = json.load(fh)
    _icons_index_cache = data["icons"]
    return _icons_index_cache


def resolve_stem(node_id):
    """Resolve a diagram node id to an index-lite.json icon stem, or None.

    1. ARCH_STEMS[node_id.lower()] -> stem
    2. node_id itself is an index key -> node_id
    3. otherwise -> None (unresolved ids are reported by the caller, never
       treated as fatal here)
    """
    arch_stems = _load_arch_stems()
    index = _load_icons_index()
    stem = arch_stems.get(node_id.lower())
    if stem is not None:
        return stem
    if node_id in index:
        return node_id
    return None


def icon_path_for_stem(stem):
    """Resolve an icon stem to an absolute SVG file path, preferring 64px.

    index-lite.json's `path` field is relative to this skill's icons/
    directory and points at the 48px variant. The 64px sibling is the size
    the PoC validated (§0.6), so it is preferred when present:
    ".../48/Arch_X_48.svg" -> ".../64/Arch_X_64.svg".

    All 25 distinct service stems needed by this work have a 64px sibling
    (measured: 0 missing) — but fall back to the indexed 48px path if, for
    some other stem, the 64px file happens not to exist.
    """
    index = _load_icons_index()
    entry = index.get(stem)
    if entry is None:
        return None
    rel_path = entry["path"]
    abs_48 = os.path.normpath(os.path.join(_ICONS_DIR, rel_path))
    rel_64 = rel_path.replace("/48/", "/64/").replace("_48.svg", "_64.svg")
    abs_64 = os.path.normpath(os.path.join(_ICONS_DIR, rel_64))
    if os.path.isfile(abs_64):
        return abs_64
    return abs_48


_VIEWBOX_RE = re.compile(
    r'viewBox="[\d.+-]+\s+[\d.+-]+\s+([\d.+-]+)\s+[\d.+-]+"')


def _viewbox_scale_denominator(svg_text):
    """Return the icon's own viewBox width, falling back to 80.0.

    This REPLACES the PoC's hardcoded `/80.0`. The 48px icon files use
    viewBox="0 0 64 64" while the 64px files use viewBox="0 0 80 80" (measured,
    §0.5) — they do NOT share a viewBox. A hardcoded /80.0 denominator renders
    a 48px file 25% too small (30/80 instead of the correct 30/64). Parsing
    the icon's own viewBox width keeps the on-screen icon size correct
    regardless of which size variant was actually resolved.
    """
    m = _VIEWBOX_RE.search(svg_text)
    if m:
        return float(m.group(1))
    return 80.0


# ---- 3.4 Injection mechanics — keep the PoC's behavior exactly ------------
_ID_RE = re.compile(r'id="([^"]+)"')


def _load_icon(path, uid):
    """Read an icon SVG and namespace every internal id with `uid-`.

    Gradient ids (and other internal ids) repeat across icon files and would
    collide once two icons are injected into one document, so every id="X" is
    rewritten to id="<uid>-X", and every reference to it (url(#X), href="#X")
    is rewritten to match.
    """
    with open(path, encoding="utf-8") as fh:
        svg = fh.read()
    for m in set(_ID_RE.findall(svg)):
        svg = svg.replace(f'id="{m}"', f'id="{uid}-{m}"')
        svg = svg.replace(f"url(#{m})", f"url(#{uid}-{m})")
        svg = svg.replace(f'href="#{m}"', f'href="#{uid}-{m}"')
    return svg


_NODE_G_RE_TMPL = r'<g[^>]*id="node-{}"[^>]*>'
_RECT_RE = re.compile(
    r'<rect x="([\d.]+)" y="([\d.]+)" width="([\d.]+)" height="([\d.]+)"')


def inject_icons(html_text, mapping):
    """Inject AWS icons into Archify-rendered HTML at each mapped node.

    `mapping` is node_id -> absolute icon FILE path. Returns (new_html, count)
    where count is the number of icons actually landed (mapping entries that
    could not be placed are skipped with a stderr message, not fatal).

    Mechanics reproduce the PoC step-for-step (docs/decisions/poc/adr-020/
    inject_aws_icons.py) — this function depends on ARCHIFY's OUTPUT MARKUP
    SHAPE (the "id="node-<id>"" hook and the geometry-bearing <rect>), which
    is why ARCHIFY_PIN exists in this same module: an Archify upgrade that
    changes this markup shape must fail loudly via the structure probe test
    rather than silently degrade into a diagram with no icons.
    """
    html = html_text
    injected = 0
    for node_id, icon_path in mapping.items():
        g = re.search(_NODE_G_RE_TMPL.format(re.escape(node_id)), html)
        if not g:
            print(f"skip: node-{node_id} not found", file=sys.stderr)
            continue
        rect = _RECT_RE.search(html[g.end():g.end() + 600])
        if not rect:
            print(f"skip: node-{node_id} rect not found", file=sys.stderr)
            continue
        x, y, w, h = (float(v) for v in rect.groups())
        size = 30
        ix, iy = x + w - size - 6, y + 6  # top-right corner of the node

        icon = _load_icon(icon_path, f"awsicon-{node_id}")

        # Strip, in order: the <?xml ...?> declaration; everything up to and
        # including the first <svg ...> open tag; the trailing </svg>; the
        # first <title>...</title>. What remains is placed via a <g transform>
        # rather than a nested <svg x= y=>: the viewer's stylesheet CAN
        # override a nested-svg's x/y geometry, but it CANNOT override a
        # transform attribute on a <g>.
        icon = re.sub(r"<\?xml[^>]*\?>", "", icon)
        inner = re.sub(r"^.*?<svg[^>]*>", "", icon, count=1, flags=re.S)
        inner = re.sub(r"</svg>\s*$", "", inner, flags=re.S)
        inner = re.sub(r"<title>.*?</title>", "", inner, count=1, flags=re.S)

        scale = size / _viewbox_scale_denominator(icon)

        # SVG paints in document order: insert AFTER the node's rects (i.e.
        # before its first <text>) so an icon inserted as the group's first
        # child is not hidden behind the opaque node body.
        anchor = html.find("<text", g.end())
        if anchor == -1:
            print(f"skip: node-{node_id} text anchor not found", file=sys.stderr)
            continue
        icon_g = (
            f'<g class="aws-official-icon" aria-hidden="true" '
            f'transform="translate({ix} {iy}) scale({scale})">{inner}</g>'
        )
        html = html[:anchor] + icon_g + html[anchor:]
        injected += 1
    return html, injected


# ---- 3.5 auto_mapping -------------------------------------------------------
def _spec_component_ids(spec):
    """Read component/node dicts from an Archify architecture spec.

    Reads spec["components"] — the architecture schema's REQUIRED key (§0.2) —
    with spec["nodes"] accepted only as a cheap forward-compat alias (some
    other Archify diagram type may name it differently in the future; there is
    no "nodes" key in the architecture schema today).
    """
    components = spec.get("components")
    if not components:
        components = spec.get("nodes")
    return components or []


def auto_mapping(spec):
    """Derive a node_id -> absolute icon path mapping from an Archify spec.

    Returns ONLY entries that resolve (both resolve_stem and
    icon_path_for_stem succeed). Unresolved ids are not included — see
    unmapped_ids() for those, so the CLI can report them without re-deriving
    the id list.
    """
    mapping = {}
    for component in _spec_component_ids(spec):
        node_id = component.get("id")
        if not node_id:
            continue
        stem = resolve_stem(node_id)
        if stem is None:
            continue
        icon_path = icon_path_for_stem(stem)
        if icon_path is None:
            continue
        mapping[node_id] = icon_path
    return mapping


def unmapped_ids(spec):
    """Return the list of component ids from `spec` that auto_mapping could
    not resolve, in spec order, so the CLI can print one skip: line each."""
    unmapped = []
    for component in _spec_component_ids(spec):
        node_id = component.get("id")
        if not node_id:
            continue
        stem = resolve_stem(node_id)
        if stem is not None and icon_path_for_stem(stem) is not None:
            continue
        unmapped.append(node_id)
    return unmapped


# ---- 3.6 CLI ----------------------------------------------------------------
_MAP_FILENAME_RE = re.compile(r"^Arch_(.+)_(?:16|32|48|64)\.svg$")


def _resolve_map_value(node_id, value):
    """Resolve one --map value to an absolute icon file path, or None.

    A value may be:
      1. a path to a file INSIDE the bundled icons library (absolute or
         relative to cwd) -> as-is. Paths outside the library are refused:
         _load_icon inlines the file's content into the published artifact,
         so an arbitrary path in an untrusted deck's map would exfiltrate
         builder-local files. The library is the only inline source.
      2. a key of the index (a stem) -> resolved via icon_path_for_stem
      3. a filename shaped Arch_<stem>_<16|32|48|64>.svg -> extract <stem>,
         resolve via the index. This is what makes the PoC's own
         icon-map.json (whose values look like "Arch_Amazon-Route-53_64.svg")
         keep working unchanged through this promoted CLI.
    Unresolvable values are reported by the caller, never raised here.
    """
    if os.path.isfile(value):
        resolved = os.path.realpath(value)
        icons_root = os.path.realpath(_ICONS_DIR) + os.sep
        if resolved.startswith(icons_root):
            return resolved
        print(f"skip: node-{node_id} map path {value!r} is outside the icon "
              "library — only bundled icons can be inlined", file=sys.stderr)
        return None
    index = _load_icons_index()
    if value in index:
        return icon_path_for_stem(value)
    m = _MAP_FILENAME_RE.match(os.path.basename(value))
    if m:
        stem = m.group(1)
        if stem in index:
            return icon_path_for_stem(stem)
    return None


def _mapping_from_map_file(map_path):
    with open(map_path, encoding="utf-8") as fh:
        raw_mapping = json.load(fh)
    mapping = {}
    for node_id, value in raw_mapping.items():
        resolved = _resolve_map_value(node_id, value)
        if resolved is None:
            print(f"skip: node-{node_id} unresolvable icon '{value}'",
                  file=sys.stderr)
            continue
        mapping[node_id] = resolved
    return mapping


def _mapping_from_spec_file(spec_path):
    with open(spec_path, encoding="utf-8") as fh:
        spec = json.load(fh)
    mapping = auto_mapping(spec)
    for node_id in unmapped_ids(spec):
        print(f"skip: node-{node_id} no icon for this id", file=sys.stderr)
    return mapping


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="archify_icons.py",
        description=(
            "Inject official AWS architecture icons into an Archify-rendered "
            "HTML diagram (ADR-020)."
        ),
    )
    parser.add_argument("archify_html", help="Archify-rendered HTML input file")
    parser.add_argument("out_html", help="Path to write the icon-injected HTML")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--map", dest="map_path", metavar="mapping.json",
        help="Explicit node_id -> icon mapping JSON (PoC-compatible form)",
    )
    group.add_argument(
        "--spec", dest="spec_path", metavar="spec.json",
        help="Archify architecture spec JSON to auto-derive the mapping from",
    )
    args = parser.parse_args(argv)

    with open(args.archify_html, encoding="utf-8") as fh:
        html_text = fh.read()

    if args.map_path:
        mapping = _mapping_from_map_file(args.map_path)
    else:
        mapping = _mapping_from_spec_file(args.spec_path)

    new_html, injected = inject_icons(html_text, mapping)

    with open(args.out_html, "w", encoding="utf-8") as fh:
        fh.write(new_html)

    # Exit 0 even when some nodes were skipped — skips are informational
    # (e.g. the PoC spec legitimately yields 5/5 plus two skips, §0.7).
    print(f"injected {injected}/{len(mapping)} icons -> {args.out_html}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
