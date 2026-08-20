#!/usr/bin/env python3
"""atlas doc model, validator, and INDEX.md generator.

The atlas wiki is a directory of markdown pages, each carrying YAML frontmatter
(title / description / covers / related / code_rev / updated). This module is the
single owner of that model: atlas_drift.py and atlas_sync.py import it and must
never reparse frontmatter themselves.

Usage:
  atlas_index.py --validate [--root DIR]   # print problems; exit 1 if any, 0 if clean
  atlas_index.py --write    [--root DIR]   # regenerate the INDEX block; print what changed
  atlas_index.py --list     [--root DIR]   # one JSON object per doc, one per line

--root DIR targets a repo other than the cwd. `--validate` is the ONE entry point in
this plugin that is NOT fail-open: it exists to be a gate, so problems exit 1.
Everything else here exits 0.
"""
import argparse
import datetime
import json
import os
import re
import subprocess
import sys

# The cross-task contract (design.md §D). Tasks 4 and 5 import these names —
# renaming any of them silently breaks a module that cannot see this code.
REQUIRED_KEYS = ("title", "description", "covers", "code_rev")
OPTIONAL_KEYS = ("related", "updated")
INDEX_NAME = "INDEX.md"
BEGIN_MARKER = "<!-- AUTO-MANAGED:index -->"
END_MARKER = "<!-- /AUTO-MANAGED -->"

# INDEX.md description cells are capped so one long description cannot turn the
# table into a horizontal scroll that buries every other doc's row.
_DESC_MAX = 80


class AtlasDoc(object):
    """One atlas wiki page. `errors` is empty for a schema-clean doc."""

    def __init__(self):
        self.path = ""         # absolute path to the .md file
        self.relpath = ""      # POSIX path relative to the atlas root
        self.title = ""
        self.description = ""
        self.covers = []       # list of glob strings, each repo-root-relative
        self.related = []      # list of sibling relpaths
        self.code_rev = ""     # git rev the doc was last synced to ("" if absent)
        self.updated = ""      # ISO date ("" if absent)
        self.errors = []       # list of human-readable schema problems

    def to_dict(self):
        return {
            "path": self.path,
            "relpath": self.relpath,
            "title": self.title,
            "description": self.description,
            "covers": self.covers,
            "related": self.related,
            "code_rev": self.code_rev,
            "updated": self.updated,
            "errors": self.errors,
        }


def repo_root(start=None):
    """Absolute repo root via `git rev-parse --show-toplevel`; falls back to `start`
    or the cwd outside a git repo. Never raises — a missing/hung git binary must not
    take down a caller that only wanted a base directory."""
    cwd = start or os.getcwd()
    try:
        p = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=cwd, capture_output=True, text=True, timeout=30,
        )
        if p.returncode == 0 and p.stdout.strip():
            return p.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        pass
    return os.path.abspath(cwd)


def atlas_root(root=None):
    """Absolute path of the wiki root: <repo_root>/<config `root`>. Reads the config
    via atlas_config.effective(); falls back to "docs/atlas" if the import or the
    read fails, so this module works standalone (e.g. run from an odd cwd, or before
    atlas_config.py exists on disk)."""
    base = os.path.abspath(root) if root else repo_root()
    rel = "docs/atlas"
    try:
        # Sibling import: when run as a script, sys.path[0] is already this scripts/
        # dir; when imported by atlas_drift/atlas_sync the dir is shared. Guarded all
        # the same — a broken or absent config module must not break the doc model.
        import atlas_config
        v = atlas_config.effective(base).get("root")
        if isinstance(v, str) and v:
            rel = v
    except Exception:
        pass
    return os.path.join(base, rel)


def _strip_quotes(s):
    """Strip ONE layer of matching surrounding single or double quotes. Only a
    matching pair is stripped — `"a` or `'a"` stays as-is, because mangling an
    unbalanced value would be worse than leaving the quote visible."""
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ("'", '"'):
        return s[1:-1]
    return s


def _parse_inline_list(val):
    """`["a", "b"]` or `[a, b]` -> list of quote-stripped items. Comma-split is
    enough for the shapes §I documents (globs and relpaths never contain commas)."""
    inner = val[1:-1].strip()
    if not inner:
        return []
    return [_strip_quotes(part.strip()) for part in inner.split(",") if part.strip()]


# A top-level frontmatter key: starts at column 0 so a block-list item indented
# under a key can never be misread as a new key.
_KEY_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*):\s*(.*)$")


def parse_frontmatter(text):
    """(dict, body) from a markdown string. Stdlib only — no pyyaml, which is not a
    dependency of this repo and would break the plugin on a clean machine. Supports
    exactly the shapes design.md §I documents: `key: scalar`, an inline flow list
    (`["a", "b"]` and `[a, b]`), and a block list of `  - item` lines. Returns
    ({}, text) when the text does not begin with `---` or the frontmatter is never
    closed by a second `---`."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return {}, text
    meta = {}
    block_key = None  # key currently collecting `- item` block-list lines
    for raw in lines[1:end]:
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        m = _KEY_RE.match(raw) if not raw[:1].isspace() else None
        if m:
            key, val = m.group(1), m.group(2).strip()
            if val == "":
                # `covers:` with nothing after it opens a block list; a key that
                # never receives items stays an empty list, which parse_doc flags.
                meta[key] = []
                block_key = key
            elif val.startswith("[") and val.endswith("]"):
                meta[key] = _parse_inline_list(val)
                block_key = None
            else:
                meta[key] = _strip_quotes(val)
                block_key = None
        elif stripped.startswith("- ") or stripped == "-":
            if block_key is not None:
                meta[block_key].append(_strip_quotes(stripped[1:].strip()))
        # Any other line shape is silently skipped: this parser must degrade, not
        # raise, on hand-edited frontmatter it does not understand.
    body = "\n".join(lines[end + 1:])
    return meta, body


def parse_doc(path, root):
    """-> AtlasDoc. Populates `errors` for: missing required key, empty `covers`,
    non-list `covers`/`related`. Never raises on a malformed file — a wiki with one
    broken page must stay usable, so a bad doc is returned WITH its errors rather
    than aborting the whole load."""
    doc = AtlasDoc()
    doc.path = os.path.abspath(path)
    doc.relpath = os.path.relpath(doc.path, os.path.abspath(root)).replace(os.sep, "/")
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            text = f.read()
    except OSError as e:
        doc.errors.append("unreadable file: %s" % e)
        return doc
    meta, _body = parse_frontmatter(text)
    if not meta:
        doc.errors.append("no YAML frontmatter (or frontmatter never closed by a second ---)")
    for key in REQUIRED_KEYS:
        if key not in meta:
            doc.errors.append("missing required key: %s" % key)

    def _scalar(key):
        v = meta.get(key, "")
        return v if isinstance(v, str) else str(v)

    doc.title = _scalar("title")
    doc.description = _scalar("description")
    doc.code_rev = _scalar("code_rev")
    doc.updated = _scalar("updated")

    covers = meta.get("covers")
    if covers is not None:
        if not isinstance(covers, list):
            doc.errors.append("covers is not a list")
        elif not covers:
            doc.errors.append("covers is empty")
        else:
            doc.covers = covers
    related = meta.get("related")
    if related is not None:
        if not isinstance(related, list):
            doc.errors.append("related is not a list")
        else:
            doc.related = related
    return doc


def load_docs(root=None):
    """-> list of AtlasDoc for every `*.md` under the atlas root except INDEX.md,
    sorted by relpath. Recurses into subdirectories. Returns [] if the root is
    absent — a repo that has not adopted atlas yet is not an error."""
    aroot = atlas_root(root)
    if not os.path.isdir(aroot):
        return []
    docs = []
    for dirpath, _dirnames, filenames in os.walk(aroot):
        for fn in sorted(filenames):
            # INDEX.md is the generated artifact, never a doc — excluded by name at
            # any depth so a subdirectory index can't feed back into itself.
            if not fn.endswith(".md") or fn == INDEX_NAME:
                continue
            docs.append(parse_doc(os.path.join(dirpath, fn), aroot))
    docs.sort(key=lambda d: d.relpath)
    return docs


def validate(docs):
    """-> list of problem strings: every doc's own `errors`, plus each `related`
    target that does not resolve to another doc's relpath, plus each doc with no
    inbound `related` edge (an orphan advisory). Hard errors are prefixed `error:`
    and orphans `advisory:` — both make --validate exit 1, and a user reading the
    output needs to tell which kind they are looking at."""
    problems = []
    known = set(d.relpath for d in docs)
    inbound = set()
    for d in docs:
        for e in d.errors:
            problems.append("error: %s: %s" % (d.relpath, e))
    for d in docs:
        for r in d.related:
            if r in known:
                inbound.add(r)
            else:
                problems.append("error: %s: broken related link: %s" % (d.relpath, r))
    for d in docs:
        if d.relpath not in inbound:
            problems.append(
                "advisory: %s: orphan — no other doc lists it in `related`" % d.relpath)
    return problems


def _cell(text):
    """Escape `|` as `\\|` in a table cell. Without this, a description containing a
    pipe splits into phantom columns and corrupts the whole table."""
    return text.replace("|", "\\|")


def render_index(docs):
    """-> the markdown table text that goes BETWEEN the markers (no markers, no
    trailing newline). Columns: Doc | Description | Covers | Related | Synced."""
    lines = [
        "| Doc | Description | Covers | Related | Synced |",
        "|---|---|---|---|---|",
    ]
    for d in docs:
        desc = d.description
        if len(desc) > _DESC_MAX:
            desc = desc[:_DESC_MAX] + "..."
        n = len(d.covers)
        covers = "1 glob" if n == 1 else "%d globs" % n
        related = ", ".join(d.related) if d.related else "—"
        synced = d.code_rev if d.code_rev else "—"
        doc_link = "[%s](%s)" % (d.relpath, d.relpath)
        cells = [doc_link, desc, covers, related, synced]
        lines.append("| " + " | ".join(_cell(c) for c in cells) + " |")
    return "\n".join(lines)


def _fresh_index_content(block):
    """The minimal header + block from design.md §J, used only when INDEX.md does
    not exist yet. The `Last updated` footer lives OUTSIDE the block on purpose:
    everything outside the markers belongs to the user after creation."""
    today = datetime.date.today().isoformat()
    return (
        "# Atlas Index\n"
        "\n"
        "Per-topic documentation for this repository. Pick docs by `description` and `covers`,\n"
        "then read only those bodies.\n"
        "\n"
        + block + "\n"
        "\n"
        "Last updated: %s (managed by /atlas:init, /atlas:add-doc, /atlas:sync)\n" % today
    )


def write_index(root=None, docs=None):
    """Splice render_index() between BEGIN_MARKER/END_MARKER in <root>/INDEX.md,
    preserving everything outside the block byte-for-byte — a user's hand-written
    prose above and below the table must survive every regeneration. Creates
    INDEX.md with a minimal header + block if absent. -> True iff the file's
    content actually changed."""
    aroot = atlas_root(root)
    if docs is None:
        docs = load_docs(root)
    block = BEGIN_MARKER + "\n" + render_index(docs) + "\n" + END_MARKER
    path = os.path.join(aroot, INDEX_NAME)

    if not os.path.exists(path):
        os.makedirs(aroot, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(_fresh_index_content(block))
        return True

    with open(path, encoding="utf-8") as f:
        old = f.read()

    begin = old.find(BEGIN_MARKER)
    end = old.find(END_MARKER, begin + len(BEGIN_MARKER)) if begin != -1 else -1
    if begin != -1 and end != -1:
        new = old[:begin] + block + old[end + len(END_MARKER):]
    else:
        # No markers: this may be a user's hand-written index, so never overwrite
        # it — append a fresh managed block instead and say so.
        print("%s has no AUTO-MANAGED markers; appending a fresh index block" % path)
        sep = "" if old.endswith("\n") else "\n"
        new = old + sep + "\n" + block + "\n"

    if new == old:
        return False
    with open(path, "w", encoding="utf-8") as f:
        f.write(new)
    return True


def main():
    ap = argparse.ArgumentParser(description="atlas doc validator and INDEX generator")
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--validate", action="store_true",
                       help="print problems; exit 1 if any, 0 if clean")
    group.add_argument("--write", action="store_true",
                       help="regenerate the INDEX block; print what changed")
    group.add_argument("--list", action="store_true", dest="list_docs",
                       help="one JSON object per doc, one per line")
    ap.add_argument("--root", default=None, help="repo root (default: git toplevel of cwd)")
    args = ap.parse_args()

    docs = load_docs(args.root)

    if args.validate:
        # The ONE non-fail-open entry point in this plugin: it exists to be a gate,
        # so any problem — hard error or orphan advisory alike — exits 1.
        problems = validate(docs)
        for p in problems:
            print(p)
        return 1 if problems else 0

    if args.write:
        path = os.path.join(atlas_root(args.root), INDEX_NAME)
        if write_index(args.root, docs):
            print("updated %s (%d docs)" % (path, len(docs)))
        else:
            print("no change: %s already current (%d docs)" % (path, len(docs)))
        return 0

    for d in docs:
        print(json.dumps(d.to_dict(), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
