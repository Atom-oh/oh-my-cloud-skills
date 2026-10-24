#!/usr/bin/env python3
"""Order a unified diff so the review's line cap trims generated copies, not maintained source.

Usage: order_diff.py < filtered-diff > ordered-diff

The review sees only the first lines of the diff. Git lists files by path, so documentation and the
generated package copies (`packages/`, `plugins/*/.codex-plugin/`) come before `plugins/` and
`tools/`, and a large release can push the maintained source out of the reviewed part. This
stable-partitions the per-file chunks into three classes, keeping the input order inside each class:

  0 maintained source, tests, scripts, configuration (everything else)
  1 documentation: docs/, doc-sites/, results/, CHANGELOG.md, README.md
  2 generated copies: packages/, plugins/<name>/.codex-plugin/

Nothing is dropped or edited. Text before the first `diff --git` line stays first. A file is classified
by its new path. The chunk counts and line counts per class go to stderr. The diff is data: it is read
as bytes and never interpreted.
"""

import re
import sys

# Git quotes a path that has non-ASCII bytes, a quote, a backslash or a control character (both sides,
# C-style escapes), so accept either form. The class prefixes are ASCII and survive the escaping, so
# the escaped text is classified as it stands.
HEADER = re.compile(r'^diff --git (?:"a/(?:[^"\\]|\\.)*"|a/.+?) (?:"b/((?:[^"\\]|\\.)*)"|b/(.+))$')
LINES = re.compile(r"[^\n]*\n|[^\n]+")
DOCS_DIRS = ("docs/", "doc-sites/", "results/")
DOCS_FILES = ("CHANGELOG.md", "README.md")
GENERATED = (re.compile(r"^packages/"), re.compile(r"^plugins/[^/]+/\.codex-plugin/"))
NAMES = ("maintained", "documentation", "generated")


def classify(path):
    if any(pattern.match(path) for pattern in GENERATED):
        return 2
    if path.startswith(DOCS_DIRS) or path in DOCS_FILES:
        return 1
    return 0


def split_chunks(lines):
    preamble, chunks = [], []
    for line in lines:
        match = HEADER.match(line.rstrip("\n"))
        if match:
            chunks.append((match.group(1) or match.group(2), [line]))
        elif chunks:
            chunks[-1][1].append(line)
        else:
            preamble.append(line)
    return preamble, chunks


def main():
    text = sys.stdin.buffer.read().decode("utf-8", "surrogateescape")
    # Only a line feed ends a line: str.splitlines() also breaks on \v \f \x1c-\x1e \x85 \u2028 \u2029 and a
    # bare \r, which would let diff content start a false chunk.
    preamble, chunks = split_chunks(LINES.findall(text))
    classes = [[], [], []]
    for path, body in chunks:
        if not body[-1].endswith("\n"):
            body[-1] += "\n"  # only the last chunk can lack it; keep the next header on its own line
        classes[classify(path)].append(body)
    out = list(preamble) + [line for group in classes for body in group for line in body]
    # The input's own final newline state is kept: a diff that did not end in one still does not.
    result = "".join(out)
    if text and not text.endswith("\n") and result.endswith("\n"):
        result = result[:-1]
    sys.stdout.buffer.write(result.encode("utf-8", "surrogateescape"))
    counts = ", ".join(f"{NAMES[i]} {len(classes[i])} files/{sum(len(b) for b in classes[i])} lines" for i in range(3))
    print(f"order_diff: {counts}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
