#!/usr/bin/env python3
"""atlas drift detection — range resolution, covers matching, work packets.

A doc is stale iff a file matching one of its `covers` globs changed between its
OWN frontmatter `code_rev` and the effective "now" ref (`head_ref`, "HEAD" unless
overridden). Detection is O(changed files x docs) with no LLM call: this script
only runs git and matches globs. atlas_sync.py imports resolve_range / range_head /
changed_files / stale_docs and feeds the resulting work packets to the headless
fixer, so their names and the packet JSON shape are a cross-module contract with
atlas_sync.py — do not rename them.

Usage:
  atlas_drift.py [--range A..B] [--root DIR] [--json]

--range A..B  override which ref counts as "now" for every doc's staleness check —
              only the RIGHT-hand side (B) is used; the left-hand side is
              informational only (each doc always uses its own code_rev as the
              left bound, never a caller-supplied one — see stale_docs' docstring
              for why: gating on a shared range used to let real drift go
              permanently unreviewed). Omit to use literal HEAD.
--root DIR    target a repo other than the cwd
--json        one work packet (see stale_docs' docstring for the exact shape) per
              line instead of human-readable text

Always exits 0 (fail-open): this script runs from a PreToolUse push hook, and an
uncaught exception or non-zero exit there is a traceback on a developer's push. An
unresolvable auto-range is no longer fatal to the check (see main()) — it only
means no explicit override; every doc still gets checked against literal HEAD.
"""
import argparse
import json
import os
import re
import subprocess
import sys

# Sibling import: when run as a script, sys.path[0] is already this scripts/ dir,
# but atlas_sync.py (and test harnesses) load this module by file path, where the
# dir is NOT implicitly importable — insert it so `import atlas_index` resolves in
# both cases. atlas_index owns the doc model and frontmatter parsing; reparsing
# frontmatter here would fork the schema in two places.
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
from atlas_index import load_docs, atlas_root, repo_root  # noqa: E402

# Trunk fallbacks for resolve_range, tried in order, when the branch has no
# configured upstream (e.g. the first push of a brand-new branch).
TRUNK_CANDIDATES = ("origin/main", "main", "origin/master", "master")


def _git(args, cwd=None):
    """Run one git command; -> (stripped stdout, ok). The single funnel for every
    git invocation in this file: it returns the ("", False) sentinel on OSError,
    TimeoutExpired, UnicodeDecodeError, or a non-zero exit instead of raising,
    because this script is called from a push hook and an uncaught exception there
    is a traceback on a developer's push — the one outcome this plugin must never
    produce.

    UnicodeDecodeError is caught alongside the other two for a concrete reason, not
    defensively: `text=True` makes subprocess.run() decode stdout as UTF-8 (the
    platform default) internally, BEFORE this function ever sees it. A filename can
    be an arbitrary byte sequence on Linux — not every byte sequence is valid
    UTF-8 — and `changed_files()` runs with `core.quotePath=false` specifically so
    non-ASCII-but-valid-UTF-8 names come back unquoted (see that function's
    docstring); the tradeoff is that a name which ISN'T valid UTF-8 at all now
    raises during decoding instead of coming back safely quoted. Failing this
    single call closed (treated as a git error, same as any other) is correct: one
    unusual filename must not crash the whole push."""
    try:
        p = subprocess.run(
            ["git"] + list(args),
            cwd=cwd, capture_output=True, text=True, timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired, UnicodeDecodeError):
        return "", False
    if p.returncode != 0:
        return "", False
    return p.stdout.strip(), True


def resolve_range(rng=None, root=None):
    """-> "A..B" string, or "" when it cannot be resolved (fail-open).
    Precedence: explicit `rng` wins; else `@{upstream}...HEAD`; else the merge-base
    against the first resolvable TRUNK_CANDIDATES entry; else "" with a stderr
    advisory — a guessed range could silently diff the wrong (or an empty) span,
    so no range at all is the safer failure."""
    if rng:
        return rng
    base = repo_root(root)
    # Three dots for the upstream form: `A..B` would show every commit that exists
    # only on the upstream side as a DELETION in the diff, so a branch merely behind
    # its upstream would look like it removed unrelated code. `A...B` diffs against
    # the merge base, which reflects exactly what this push actually changes.
    _out, ok = _git(["rev-parse", "--verify", "--quiet", "@{upstream}"], cwd=base)
    if ok:
        return "@{upstream}...HEAD"
    for trunk in TRUNK_CANDIDATES:
        _out, ok = _git(["rev-parse", "--verify", "--quiet", trunk], cwd=base)
        if not ok:
            continue
        mb, ok = _git(["merge-base", trunk, "HEAD"], cwd=base)
        if ok and mb:
            return "%s..HEAD" % mb
    print("atlas drift: could not auto-resolve a push range (no explicit --range, "
          "no @{upstream}, and none of %s resolve) — no explicit override; every "
          "doc is still checked against literal HEAD"
          % ", ".join(TRUNK_CANDIDATES), file=sys.stderr)
    return ""


def changed_files(rng, root=None):
    """-> sorted list of repo-relative POSIX paths changed in `rng`
    (`git diff --name-only <rng>`). [] on any git error — an empty change set
    yields zero packets, which is the fail-open direction.

    `-c core.quotePath=false` + `-z`, not a bare `--name-only`: git's default
    `core.quotePath=true` octal-escapes and double-quotes any path byte outside
    printable ASCII, so a file with a non-ASCII name (this plugin is "installable
    in any repo" — plenty have them) comes back as e.g. `"plugins/\\355\\225\\234/x.py"`
    instead of the literal path. `glob_match`'s matcher escapes every character of a
    `covers` glob literally, so that quoted form can never match — the changed path
    is simply missing from the returned list, which reads as "not stale" (silent
    drift, the exact failure this plugin exists to prevent). `-z` NUL-terminates
    each entry unambiguously regardless of quoting, sidestepping the escaping
    entirely rather than trying to un-escape it."""
    if not rng:
        return []
    base = repo_root(root)
    out, ok = _git(["-c", "core.quotePath=false", "diff", "-z", "--name-only", rng],
                    cwd=base)
    if not ok:
        # An advisory, not silence: a range git rejects (typo'd ref, shallow clone)
        # would otherwise be indistinguishable from a genuinely empty change set,
        # and "no drift found" would be claimed for a diff that never ran.
        print("atlas drift: git diff --name-only %s failed — treating as no "
              "changes (no drift check performed for this range)" % rng,
              file=sys.stderr)
        return []
    if not out:
        return []
    return sorted(set(p for p in out.split("\0") if p))


def range_head(rng):
    """Extract the right-hand ref from an "A..B" or "A...B" range string ("..."
    checked first — it's a superset of ".."). "" when `rng` is empty or has no
    recognizable separator; callers then fall back to the literal "HEAD".

    Used to let an explicit `--range` override which ref counts as "now" for
    staleness (see `stale_docs`'s `head_ref`) — the left-hand side is no longer
    used for anything (see `stale_docs` for why: it used to gate which changes were
    even visible, which was the bug)."""
    if not rng:
        return ""
    for sep in ("...", ".."):
        idx = rng.find(sep)
        if idx != -1:
            right = rng[idx + len(sep):].strip()
            return right or "HEAD"
    return ""


def head_ref_for(explicit_rng, resolved_rng):
    """-> the ref `stale_docs` should treat as "now". Shared by atlas_drift.py's and
    atlas_sync.py's CLIs so the "explicit override that couldn't be parsed" warning
    below is written once, not duplicated (and possibly drifting) in both.

    `range_head(resolved_rng) or "HEAD"` alone would silently swap in the default
    the moment a user's EXPLICIT `--range` has no recognizable separator (a typo'd
    ref, a bare sha with no "..") — the caller asked for an override, got the
    default instead, and nothing on stderr says so. That is a real footgun: a typo
    silently checked against (and, from atlas_sync.py, could sync + commit against)
    an unintended revision with no sign anything went wrong. So an EXPLICIT
    `explicit_rng` that fails to parse gets its own advisory; an unresolved AUTO
    range (no explicit override given at all) stays silent, by design — that path's
    own advisory already printed inside `resolve_range`."""
    head_ref = range_head(resolved_rng) or "HEAD"
    if explicit_rng and not range_head(explicit_rng):
        print("atlas drift: --range %r has no recognizable right-hand ref (expected "
              "\"A..B\" or \"A...B\") — ignoring it and using literal HEAD instead"
              % explicit_rng, file=sys.stderr)
    return head_ref


_GLOB_CACHE = {}


def _glob_to_regex(pat):
    """Translate a repo-root-relative `covers` glob into an anchored regex.

    Deliberately NOT fnmatch: fnmatch's `*` matches `/` too, so `docs/atlas/*.md`
    would match `docs/atlas/sub/deep.md` and a doc would claim territory it does
    not cover. Hand-rolled so `*` stops at a path separator and `**` spans them.

      `**/`  -> `(?:.*/)?`   (zero or more leading dirs — so `a/**/b` matches `a/b`)
      `**`   -> `.*`         (any depth, trailing form: `plugins/atlas/**`)
      `*`    -> `[^/]*`      (one path segment only)
      `?`    -> `[^/]`
    Every other character is escaped literally.
    """
    out = []
    i = 0
    n = len(pat)
    while i < n:
        c = pat[i]
        if c == "*":
            if i + 1 < n and pat[i + 1] == "*":
                # `**/` consumes the slash so it can also match zero directories.
                if i + 2 < n and pat[i + 2] == "/":
                    out.append("(?:.*/)?")
                    i += 3
                    continue
                out.append(".*")
                i += 2
                continue
            out.append("[^/]*")
            i += 1
            continue
        if c == "?":
            out.append("[^/]")
            i += 1
            continue
        out.append(re.escape(c))
        i += 1
    return re.compile("^" + "".join(out) + "$")


def glob_match(pat, path):
    """True iff repo-relative POSIX `path` matches `covers` glob `pat`."""
    rx = _GLOB_CACHE.get(pat)
    if rx is None:
        rx = _GLOB_CACHE[pat] = _glob_to_regex(pat)
    return bool(rx.match(path))


def _skip(doc, reason):
    """The one-line stderr advisory for a doc that CANNOT be drift-checked
    (stale_docs' conditions 1-3). Load-bearing, not cosmetic: staying silent here would let a
    doc with a broken schema or an unresolvable code_rev look permanently fresh —
    the exact failure this plugin exists to prevent. A doc that merely is not
    stale (conditions 4-5) gets no advisory."""
    print("atlas drift: skipping %s — %s" % (doc.relpath, reason), file=sys.stderr)


def stale_docs(docs, root=None, head_ref="HEAD"):
    """-> list of work packets, one per stale doc, ordered by doc relpath. Each
    packet: {"doc", "doc_path", "code_rev", "head", "matched", "range"} (see the
    packet built at the bottom of this function for the exact shape — atlas_sync.py
    consumes it as-is). A doc yields a packet iff ALL of (in this order):
      1. doc.errors is empty, and
      2. doc.covers is non-empty, and
      3. doc.code_rev is non-empty and resolves to a commit, and
      4. the resolved code_rev sha != the resolved head_ref sha, and
      5. at least one path changed between the doc's OWN code_rev and head_ref
         matches at least one covers glob.
    Failing (1), (2) or (3) produces a stderr advisory naming the doc and the
    reason; failing (4) or (5) is silent — the doc simply is not stale.

    Condition 5 used to be gated on a single CALLER-SUPPLIED `changed` list (the
    push-range's changed files) shared across every doc. That was a real bug, not
    a cosmetic one: a covered file that changed during an earlier push the hook
    never saw (hook was off, or the push went straight from a terminal — this
    PreToolUse hook only fires on Bash calls Claude itself makes) would not appear
    in THIS push's range, so `matched` came back empty and the doc was silently
    treated as not stale — and if the SAME doc later got a packet for some OTHER
    covered file, anchor advancement moved `code_rev` straight to head_ref, marking
    the never-reviewed earlier change as synced forever. Computing `matched` from
    each doc's OWN `code_rev..head_ref` (below) closes both holes: it can never
    miss a change, and it always exactly matches the range whose end becomes the
    new anchor."""
    base = repo_root(root)
    head_sha, head_ok = _git(["rev-parse", "--verify", "%s^{commit}" % head_ref], cwd=base)
    # An UNRESOLVABLE head_ref (a typo'd explicit --range's right-hand side, e.g.
    # "main..typoo") must not fail silently: every doc's condition (4) below reads
    # `not head_ok` as "not stale" and `continue`s with NO advisory of its own, which
    # would make an entire repo report "nothing stale" with no sign anything is
    # wrong. head_ref_for() only catches a right-hand side with no separator at all
    # (a string with no ".." in it); a syntactically-fine but non-existent ref still
    # reaches here.
    if not head_ok:
        print("atlas drift: --range's right-hand ref %r does not resolve to a "
              "commit — no doc can be checked against it" % head_ref,
              file=sys.stderr)
    # Short form for the packet's `head` / `range` fields (matches this function's
    # own packet shape below); the full sha above is what the freshness comparison
    # uses.
    head_short, ok = _git(["rev-parse", "--short", head_ref], cwd=base)
    if not ok or not head_short:
        head_short = head_sha[:7] if head_sha else ""

    packets = []
    for doc in sorted(docs, key=lambda d: d.relpath):
        # (1) A schema-broken doc must never reach the fixer unanchored.
        if doc.errors:
            _skip(doc, "schema errors: %s" % "; ".join(doc.errors))
            continue
        # (2) No covers globs means no territory — nothing can ever mark it stale.
        if not doc.covers:
            _skip(doc, "covers is empty")
            continue
        # (3) code_rev is the drift anchor; without a resolvable one there is no
        # "since" side of the diff and staleness is undecidable.
        if not doc.code_rev:
            _skip(doc, "code_rev is empty")
            continue
        rev_sha, ok = _git(
            ["rev-parse", "--verify", "%s^{commit}" % doc.code_rev], cwd=base)
        if not ok or not rev_sha:
            _skip(doc, "code_rev %r does not resolve to a commit" % doc.code_rev)
            continue
        # (4) Already synced to head_ref: fresh, silent.
        if not head_ok or rev_sha == head_sha:
            continue
        # (5) The doc's OWN full history since its OWN code_rev — never a shared,
        # possibly-narrower push-range change set (see the docstring above for why
        # that was wrong). `matched` is what scopes the diff the fixer later sees,
        # and it is exactly the same range `range`/anchor-advancement below uses.
        doc_changed = changed_files("%s..%s" % (doc.code_rev, head_ref), root)
        matched = [p for p in doc_changed
                   if any(glob_match(g, p) for g in doc.covers)]
        if not matched:
            continue
        packets.append({
            "doc": doc.relpath,
            "doc_path": doc.path,
            "code_rev": doc.code_rev,
            "head": head_short,
            "matched": matched,
            "range": "%s..%s" % (doc.code_rev, head_short),
        })
    return packets


def main():
    ap = argparse.ArgumentParser(
        description="detect atlas docs whose covered code changed since their code_rev")
    ap.add_argument("--range", dest="rng", default=None, metavar="A..B",
                    help="explicit diff range (default: auto-resolve)")
    ap.add_argument("--root", default=None,
                    help="repo root (default: git toplevel of cwd)")
    ap.add_argument("--json", action="store_true", dest="as_json",
                    help="one work packet per line instead of human-readable text")
    args = ap.parse_args()

    # `--range` only ever supplies which ref counts as "now" (its right-hand side);
    # resolve_range's auto-detected forms (`@{upstream}...HEAD`, `<merge-base>..HEAD`)
    # always end in literal HEAD anyway. An unresolvable auto-range used to mean "no
    # drift check at all" — that was itself part of the anchor-skipping bug this
    # rewrite fixes, so it no longer short-circuits anything; it only means no
    # explicit override, and stale_docs() still checks every doc against true HEAD.
    rng = resolve_range(args.rng, args.root)
    head_ref = head_ref_for(args.rng, rng)
    docs = load_docs(args.root)
    packets = stale_docs(docs, args.root, head_ref=head_ref)

    for pkt in packets:
        if args.as_json:
            print(json.dumps(pkt, ensure_ascii=False))
        else:
            n = len(pkt["matched"])
            print("stale: %s — %d matched file%s, range %s"
                  % (pkt["doc"], n, "" if n == 1 else "s", pkt["range"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
