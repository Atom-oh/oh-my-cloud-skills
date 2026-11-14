#!/usr/bin/env python3
"""Check bilingual (English/Korean) Markdown documents for layout drift.

Usage: python3 check-bilingual.py FILE...

Prints one issue per line as ``FILE:LINE: message`` on stdout.
Exit status: 0 no issues, 1 issues found, 2 usage or read error.

The rules come from the project-init writing-style-guide
(skills/project-scaffolder/references/writing-style-guide.md) and
ADR-001 (identical structure), ADR-002 (HTML badges, ASCII anchors),
and ADR-007 (Mermaid diagrams):

1. The language badges are HTML ``<a href="#english"><img ... alt="English"></a>``
   and ``<a href="#korean"><img ... alt="Korean"></a>`` above the English half;
   Markdown badges that link to #english, #korean, or #한국어 are not used.
2. ``<a id="english"></a>`` sits directly above ``# English``, ``<a id="korean"></a>``
   directly above ``# 한국어`` (both h1, once each), English comes first, and a
   ``---`` line precedes each anchor.
3. Both halves have the same heading-level sequence (headings inside code
   blocks and HTML comments do not count). A paragraph line directly above
   a ``===`` or ``---`` line is a setext h1 or h2, as GitHub renders it, so
   that ``---`` is not a horizontal rule.
4. Both halves have the same fenced blocks (count and language tags), the same
   tables (count and rows per table), and byte-identical Mermaid blocks.
   Other code blocks and table cells are compared by count only, because
   comments and descriptive cells are translated.
5. Every opening code fence has a language tag and a closing fence.
6. No emoji anywhere, code blocks included. Text symbols such as the check
   mark U+2713, arrows, and box drawing characters are not emoji.
7. CHANGELOG files (name starts with "changelog", any case): release headings
   are ``## [Unreleased]`` or ``## [x.y.z] - YYYY-MM-DD`` with a real date, and
   both halves list the same releases in the same order.

A file with none of the bilingual markers gets one issue saying so.

It checks layout only. Whether each Korean paragraph says what its English
counterpart says still needs a reader.

Standard library only; Python 3.8+.
"""

import datetime
import os
import re
import sys

FENCE_RE = re.compile(r"^(\s*)(`{3,}|~{3,})(.*)$")
HEADING_RE = re.compile(r"^ {0,3}(#{1,6})(?:[ \t]+(.*?))?(?:[ \t]+#+)?[ \t]*$")
HR_RE = re.compile(r"^ {0,3}(?:-[ \t]*){3,}$")
SETEXT_RE = re.compile(r"^ {0,3}(=+|-+)[ \t]*$")
# Lines that start a block other than a paragraph; a --- below them is a rule, not a setext underline
NON_PARAGRAPH_RE = re.compile(r"^(?: {0,3}(?:[-+*]|\d{1,9}[.)])(?:[ \t]|$)| {0,3}>| {0,3}<|    |\t)")
ANCHOR_RE = {
    "english": re.compile(r'^\s*<a\s+id="english"\s*>\s*</a>\s*$'),
    "korean": re.compile(r'^\s*<a\s+id="korean"\s*>\s*</a>\s*$'),
}
BADGE_RE = {
    "english": re.compile(r'<a\s+href="#english"\s*>\s*<img\b[^>]*\balt="English"[^>]*>\s*</a>'),
    "korean": re.compile(r'<a\s+href="#korean"\s*>\s*<img\b[^>]*\balt="Korean"[^>]*>\s*</a>'),
}
BADGE_HTML = {
    "english": '<a href="#english"><img src="https://img.shields.io/badge/lang-English-blue.svg" alt="English"></a>',
    "korean": '<a href="#korean"><img src="https://img.shields.io/badge/lang-한국어-red.svg" alt="Korean"></a>',
}
LANG_HEADING = {"english": "English", "korean": "한국어"}
MD_BADGE_RE = re.compile(r"\[!\[[^\]]*\]\([^)]*\)\]\(#(english|korean|한국어)\)")
UNICODE_ANCHOR_RE = re.compile(r'href="#(한국어|%ED%95%9C%EA%B5%AD%EC%96%B4)"', re.IGNORECASE)
INLINE_CODE_RE = re.compile(r"(`+)(.+?)\1")
RELEASE_RE = re.compile(
    r"^\[(\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?)\] - (\d{4}-\d{2}-\d{2})(?: \[YANKED\])?$"
)

# Emoji: characters whose default presentation is emoji, the pictograph
# blocks of plane 1, and status symbols models often emit without U+FE0F.
# Text symbols such as the check mark U+2713, arrows, and box drawing are allowed.
EMOJI_RANGES = (
    (0x231A, 0x231B), (0x23E9, 0x23EC), (0x23F0, 0x23F0), (0x23F3, 0x23F3),
    (0x25FD, 0x25FE), (0x2614, 0x2615), (0x2648, 0x2653), (0x267F, 0x267F),
    (0x2693, 0x2693), (0x26A1, 0x26A1), (0x26AA, 0x26AB), (0x26BD, 0x26BE),
    (0x26C4, 0x26C5), (0x26CE, 0x26CE), (0x26D4, 0x26D4), (0x26EA, 0x26EA),
    (0x26F2, 0x26F3), (0x26F5, 0x26F5), (0x26FA, 0x26FA), (0x26FD, 0x26FD),
    (0x2705, 0x2705), (0x270A, 0x270B), (0x2728, 0x2728), (0x274C, 0x274C),
    (0x274E, 0x274E), (0x2753, 0x2755), (0x2757, 0x2757), (0x2795, 0x2797),
    (0x27B0, 0x27B0), (0x27BF, 0x27BF), (0x2B1B, 0x2B1C), (0x2B50, 0x2B50),
    (0x2B55, 0x2B55),
    # status symbols with text default presentation
    (0x203C, 0x203C), (0x2049, 0x2049), (0x2139, 0x2139), (0x2611, 0x2611),
    (0x26A0, 0x26A0), (0x2714, 0x2714), (0x2716, 0x2716), (0x2764, 0x2764),
    # plane 1 pictographs
    (0x1F004, 0x1F004), (0x1F0CF, 0x1F0CF), (0x1F170, 0x1F2FF),
    (0x1F300, 0x1F6FF), (0x1F7E0, 0x1F7FF), (0x1F900, 0x1FAFF),
)
EMOJI_MODIFIERS = (0xFE0F, 0x20E3)  # emoji presentation selector, keycap


def is_emoji(cp):
    for lo, hi in EMOJI_RANGES:
        if lo <= cp <= hi:
            return True
    return False


class Fence:
    def __init__(self, line, char, length, info):
        self.line = line  # 0-based index of the opening fence
        self.char = char
        self.length = length
        self.info = info
        self.lang = info.split()[0].lower() if info else ""
        self.body = []
        self.closed = False


class Document:
    """Line-level view of a Markdown file: fences, headings, tables."""

    def __init__(self, text):
        self.lines = [line.rstrip("\r") for line in text.split("\n")]
        if len(self.lines) > 1 and self.lines[-1] == "":
            self.lines.pop()  # the final newline does not start a line
        self.fences = []
        self.headings = []  # (index, level, text)
        self.tables = []  # (start index, row count)
        self.prose = []  # True where a line is outside code and HTML comments
        self.setext = set()  # indexes of setext underlines, which are not horizontal rules
        self._scan()

    def is_rule(self, idx):
        return idx not in self.setext and bool(HR_RE.match(self.lines[idx]))

    def _scan(self):
        fence = None
        in_comment = False
        table_start = None
        table_rows = 0
        para = None  # (start index, lines) of the open paragraph, a setext heading candidate
        other_block = False  # the current run of lines belongs to a list, quote, HTML, or code block

        def end_table():
            nonlocal table_start, table_rows
            if table_start is not None:
                self.tables.append((table_start, table_rows))
            table_start, table_rows = None, 0

        for idx, line in enumerate(self.lines):
            if fence is not None or in_comment or not line.strip():
                para, other_block = None, False  # a blank line, code, or a comment ends the block
            if fence is not None:
                m = FENCE_RE.match(line)
                if (m and m.group(2)[0] == fence.char and len(m.group(2)) >= fence.length
                        and not m.group(3).strip()):
                    fence.closed = True
                    fence = None
                else:
                    fence.body.append(line)
                self.prose.append(False)
                continue
            if in_comment:
                if "-->" in line:
                    in_comment = False
                self.prose.append(False)
                continue
            m = FENCE_RE.match(line)
            if m and not (m.group(2)[0] == "`" and "`" in m.group(3)):
                end_table()
                para, other_block = None, False
                fence = Fence(idx, m.group(2)[0], len(m.group(2)), m.group(3).strip())
                self.fences.append(fence)
                self.prose.append(False)
                continue
            self.prose.append(True)
            bare = INLINE_CODE_RE.sub("", line)
            opened = bare.rfind("<!--")
            if opened != -1 and "-->" not in bare[opened:]:
                in_comment = True
            if line.lstrip().startswith("|"):
                if table_start is None:
                    table_start = idx
                table_rows += 1
                para = None
                continue
            end_table()
            if not line.strip():
                continue
            s = SETEXT_RE.match(line)
            if s and para is not None:
                level = 1 if s.group(1)[0] == "=" else 2
                self.headings.append((para[0], level, " ".join(para[1])))
                self.setext.add(idx)
                para = None
                continue
            h = HEADING_RE.match(line)
            if h:
                self.headings.append((idx, len(h.group(1)), (h.group(2) or "").strip()))
                para, other_block = None, False
            elif HR_RE.match(line):
                para, other_block = None, False
            elif para is not None:
                para[1].append(line.strip())
            elif other_block or NON_PARAGRAPH_RE.match(line):
                other_block = True
            else:
                para = (idx, [line.strip()])
        end_table()


def prev_nonblank(lines, idx):
    idx -= 1
    while idx >= 0 and not lines[idx].strip():
        idx -= 1
    return idx


def show(text, limit=60):
    return text if len(text) <= limit else text[: limit - 3] + "..."


def first_divergence(en, ko):
    """Compare two key sequences and describe the first place they diverge.

    Returns None when equal, otherwise (kind, pos, count) where kind is
    "missing" (English items en[pos:pos+count] have no Korean counterpart),
    "extra" (Korean items ko[pos:pos+count] have no English counterpart),
    or "mismatch" (en[pos] and ko[pos] differ and no skip realigns them).
    """
    pos = 0
    while pos < len(en) and pos < len(ko) and en[pos] == ko[pos]:
        pos += 1
    if pos == len(en) and pos == len(ko):
        return None
    for count in range(1, max(len(en), len(ko)) - pos + 1):
        if en[pos + count:] == ko[pos:]:
            return ("missing", pos, count)
        if en[pos:] == ko[pos + count:]:
            return ("extra", pos, count)
    return ("mismatch", pos, 1)


class Checker:
    def __init__(self, path, text):
        self.path = path
        self.doc = Document(text)
        self.issues = []  # (1-based line, message)
        self.is_changelog = os.path.basename(path).lower().startswith("changelog")

    def add(self, idx, message):
        self.issues.append((idx + 1, message))

    def run(self):
        halves = self.check_layout()
        if halves:
            self.check_headings(*halves)
            self.check_blocks(*halves)
        self.check_fences()
        self.check_emoji()
        if self.is_changelog:
            self.check_changelog(halves)
        self.issues.sort(key=lambda issue: issue[0])
        return self.issues

    # Rules 1 and 2: badges, anchors, language headings, separators.
    def check_layout(self):
        doc = self.doc
        lines = doc.lines
        markers = any(
            doc.prose[i] and (ANCHOR_RE[lang].match(l) or BADGE_RE[lang].search(l))
            for i, l in enumerate(lines) for lang in ("english", "korean")
        ) or any(h[1] == 1 and h[2] in LANG_HEADING.values() for h in doc.headings)
        if not markers:
            self.add(0, 'no bilingual layout: add the language badges, then <a id="english"></a> + "# English" and <a id="korean"></a> + "# 한국어" halves with the same sections (writing-style-guide Bilingual Structure)')
            return None
        found = {}
        for lang in ("english", "korean"):
            anchors = [i for i, l in enumerate(lines) if doc.prose[i] and ANCHOR_RE[lang].match(l)]
            heads = [h for h in doc.headings if h[1] == 1 and h[2] == LANG_HEADING[lang]]
            heading = "# " + LANG_HEADING[lang]
            anchor = '<a id="%s"></a>' % lang
            if not heads:
                wrong = [h for h in doc.headings if h[2] == LANG_HEADING[lang]]
                if wrong:
                    self.add(wrong[0][0], '"%s %s" is h%d; the language heading is "%s" (h1)'
                             % ("#" * wrong[0][1], wrong[0][2], wrong[0][1], heading))
                else:
                    self.add(0, 'no "%s" heading; each half starts with %s, a blank line, and "%s"'
                             % (heading, anchor, heading))
            elif len(heads) > 1:
                for h in heads[1:]:
                    self.add(h[0], 'second "%s" heading (first at line %d); a document has one %s half'
                             % (heading, heads[0][0] + 1, "English" if lang == "english" else "Korean"))
            if not anchors:
                where = heads[0][0] if heads else 0
                self.add(where, 'no %s line; put it on its own line directly above "%s" (ADR-002)'
                         % (anchor, heading))
            elif len(anchors) > 1:
                for a in anchors[1:]:
                    self.add(a, "duplicate %s (first at line %d); keep one, directly above \"%s\""
                             % (anchor, anchors[0] + 1, heading))
            if heads and anchors:
                above = prev_nonblank(lines, heads[0][0])
                if above not in anchors:
                    self.add(heads[0][0], '"%s" is not directly preceded by %s; put the anchor on its own line just above the heading (ADR-002)'
                             % (heading, anchor))
            top = anchors[0] if anchors else (heads[0][0] if heads else None)
            if top is not None:
                above = prev_nonblank(lines, top)
                if above < 0 or not doc.is_rule(above):
                    self.add(top, 'no "---" line above %s; a horizontal rule separates %s (writing-style-guide Bilingual Structure)'
                             % (anchor, "the badges from the English half" if lang == "english"
                                else "the English half from the Korean half"))
            found[lang] = (heads[0][0] if heads else None, top)

        en_head, en_top = found["english"]
        ko_head, ko_top = found["korean"]
        preamble_end = en_top if en_top is not None else len(lines)
        self.check_badges(preamble_end)

        if en_head is None or ko_head is None:
            return None
        if ko_head < en_head:
            self.add(ko_head, 'the Korean half (line %d) comes before the English half (line %d); English comes first (ADR-001)'
                     % (ko_head + 1, en_head + 1))
            return None
        korean_start = ko_top if ko_top is not None and ko_top > en_head else ko_head
        return (en_head + 1, korean_start), (ko_head + 1, len(lines))

    def check_badges(self, preamble_end):
        doc = self.doc
        for lang in ("english", "korean"):
            if not any(doc.prose[i] and BADGE_RE[lang].search(doc.lines[i]) for i in range(preamble_end)):
                self.add(0, "no %s language badge between the title and the English half; add %s (ADR-002)"
                         % ("English" if lang == "english" else "Korean", BADGE_HTML[lang]))
        for i, line in enumerate(doc.lines):
            if not doc.prose[i]:
                continue
            bare = INLINE_CODE_RE.sub("", line)
            for m in MD_BADGE_RE.finditer(bare):
                target = "english" if m.group(1) == "english" else "korean"
                self.add(i, "Markdown badge linking to #%s; GitHub can drop the link and open the image instead, so use %s (ADR-002)"
                         % (m.group(1), BADGE_HTML[target]))
            if UNICODE_ANCHOR_RE.search(bare):
                self.add(i, 'link to the Korean auto-anchor "#한국어"; use the ASCII anchor "#korean" (ADR-002)')

    # Rule 3: same heading-level sequence.
    def check_headings(self, en, ko):
        en_heads = [h for h in self.doc.headings if en[0] <= h[0] < en[1]]
        ko_heads = [h for h in self.doc.headings if ko[0] <= h[0] < ko[1]]
        diff = first_divergence([h[1] for h in en_heads], [h[1] for h in ko_heads])
        if diff is None:
            return
        kind, pos, count = diff

        def label(h):
            return '"%s %s"' % ("#" * h[1], show(h[2]))

        # Only the first divergence is reported; later headings would repeat it.
        if kind == "missing":
            e = en_heads[pos]
            anchor = ko_heads[pos][0] if pos < len(ko_heads) else ko[1] - 1
            self.add(anchor, "heading structure diverges here: the English half has %d more heading(s), first unmatched around %s (line %d); add the missing Korean section so both halves have the same headings (ADR-001)"
                     % (count, label(e), e[0] + 1))
        elif kind == "extra":
            k = ko_heads[pos]
            self.add(k[0], "heading structure diverges here: the Korean half has %d extra heading(s), first unmatched around %s; add the section to the English half or remove it here (ADR-001)"
                     % (count, label(k)))
        elif pos < len(ko_heads) and pos < len(en_heads):
            e, k = en_heads[pos], ko_heads[pos]
            self.add(k[0], "heading %s is h%d but its English counterpart %s (line %d) is h%d; both halves need the same headings at the same levels in the same order (ADR-001)"
                     % (label(k), k[1], label(e), e[0] + 1, e[1]))

    # Rule 4: fenced blocks, Mermaid blocks, tables.
    def check_blocks(self, en, ko):
        doc = self.doc
        en_fences = [f for f in doc.fences if en[0] <= f.line < en[1]]
        ko_fences = [f for f in doc.fences if ko[0] <= f.line < ko[1]]
        diff = first_divergence([f.lang for f in en_fences], [f.lang for f in ko_fences])
        if diff:
            kind, pos, count = diff
            if kind == "missing":
                where = ko_fences[pos].line if pos < len(ko_fences) else ko[1] - 1
                self.add(where, "the Korean half lacks %d code block(s) from the English half, first the %s block at line %d; copy every code block into both halves, translating only comments (ADR-001)"
                         % (count, en_fences[pos].lang or "untagged", en_fences[pos].line + 1))
            elif kind == "extra":
                self.add(ko_fences[pos].line, "this %s code block has no English counterpart; the same code blocks appear in both halves (ADR-001)"
                         % (ko_fences[pos].lang or "untagged"))
            else:
                e, k = en_fences[pos], ko_fences[pos]
                self.add(k.line, 'code block %d is "%s" here but "%s" in the English half (line %d); the same code blocks appear in both halves in the same order (ADR-001)'
                         % (pos + 1, k.lang or "untagged", e.lang or "untagged", e.line + 1))

        en_mermaid = [f for f in en_fences if f.lang == "mermaid"]
        ko_mermaid = [f for f in ko_fences if f.lang == "mermaid"]
        if len(en_mermaid) != len(ko_mermaid):
            self.add(ko[0] - 1, "the English half has %d mermaid blocks and the Korean half has %d; every diagram appears in both halves (writing-style-guide Diagram Rules)"
                     % (len(en_mermaid), len(ko_mermaid)))
        for n, (e, k) in enumerate(zip(en_mermaid, ko_mermaid), 1):
            if e.body == k.body:
                continue
            offset = next((i for i, (a, b) in enumerate(zip(e.body, k.body)) if a != b),
                          min(len(e.body), len(k.body)))
            self.add(k.line + 1 + offset, "mermaid block %d differs from the English copy (line %d); diagrams are byte-identical in both halves with English labels (writing-style-guide Diagram Rules)"
                     % (n, e.line + 1 + offset + 1))

        en_tables = [t for t in doc.tables if en[0] <= t[0] < en[1]]
        ko_tables = [t for t in doc.tables if ko[0] <= t[0] < ko[1]]
        if len(en_tables) == len(ko_tables):
            for n, (e, k) in enumerate(zip(en_tables, ko_tables), 1):
                if e[1] != k[1]:
                    self.add(k[0], "table %d has %d rows here but %d in the English half (line %d); both halves carry the same rows (ADR-001)"
                             % (n, k[1], e[1], e[0] + 1))
            return
        kind, pos, count = first_divergence([t[1] for t in en_tables], [t[1] for t in ko_tables])
        if kind == "extra":
            self.add(ko_tables[pos][0], "this table has no English counterpart; the same tables appear in both halves (ADR-001)")
        else:
            where = ko_tables[pos][0] if pos < len(ko_tables) else ko[1] - 1
            self.add(where, "the English half has %d tables and the Korean half has %d; the first one without a Korean counterpart is probably the table at English line %d (ADR-001)"
                     % (len(en_tables), len(ko_tables), en_tables[pos][0] + 1))

    # Rule 5: every opening fence has a language tag; every fence closes.
    def check_fences(self):
        for f in self.doc.fences:
            if not f.lang:
                self.add(f.line, "code fence has no language tag; add one (bash, json, markdown, or text for plain output and directory trees)")
            if not f.closed:
                self.add(f.line, "code fence is never closed, so the rest of the file renders as code; add the closing %s"
                         % (f.char * f.length))

    # Rule 6: no emoji.
    def check_emoji(self):
        for i, line in enumerate(self.doc.lines):
            found = []
            for pos, ch in enumerate(line):
                cp = ord(ch)
                if cp in EMOJI_MODIFIERS and pos > 0:
                    ch, cp = line[pos - 1], ord(line[pos - 1])
                elif not is_emoji(cp):
                    continue
                label = "%s (U+%04X)" % (ch, cp)
                if label not in found:
                    found.append(label)
            if found:
                self.add(i, "emoji %s; the writing-style-guide allows no emoji anywhere, so use words instead"
                         % ", ".join(found))

    # Rule 7: CHANGELOG release headings.
    def check_changelog(self, halves):
        doc = self.doc
        if halves:
            ranges = list(halves)
        else:
            ranges = [(1, len(doc.lines))]
        releases = []
        for lo, hi in ranges:
            found = []
            for idx, level, text in doc.headings:
                if level != 2 or not lo <= idx < hi:
                    continue
                found.append((idx, text))
                if text == "[Unreleased]":
                    continue
                m = RELEASE_RE.match(text)
                if not m:
                    self.add(idx, 'release heading "## %s" does not match "## [x.y.z] - YYYY-MM-DD" or "## [Unreleased]" (Keep a Changelog)'
                             % show(text))
                    continue
                try:
                    datetime.date(*map(int, m.group(2).split("-")))
                except ValueError:
                    self.add(idx, 'release date %s is not a valid YYYY-MM-DD date' % m.group(2))
            releases.append(found)
        if len(releases) != 2:
            return
        en, ko = releases
        diff = first_divergence([r[1] for r in en], [r[1] for r in ko])
        if diff is None:
            return
        kind, pos, count = diff
        if kind == "missing":
            anchor = ko[pos][0] if pos < len(ko) else halves[1][1] - 1
            self.add(anchor, 'the Korean half is missing release "## %s" (English line %d)%s; add it with the same version and date'
                     % (show(en[pos][1]), en[pos][0] + 1, " and %d more" % (count - 1) if count > 1 else ""))
        elif kind == "extra":
            self.add(ko[pos][0], 'release "## %s" is not in the English half; both halves list the same releases in the same order'
                     % show(ko[pos][1]))
        else:
            self.add(ko[pos][0], 'release heading "## %s" differs from the English half, which has "## %s" (line %d) here; both halves list the same releases with the same dates in the same order'
                     % (show(ko[pos][1]), show(en[pos][1]), en[pos][0] + 1))


def main(argv):
    args = argv[1:]
    if args and args[0] in ("-h", "--help"):
        sys.stdout.write(__doc__)
        return 0
    if not args:
        sys.stderr.write("usage: python3 check-bilingual.py FILE...\n")
        return 2
    status = 0
    for path in args:
        try:
            with open(path, encoding="utf-8-sig") as handle:  # -sig drops a BOM
                text = handle.read()
        except (OSError, UnicodeDecodeError) as exc:
            sys.stderr.write("%s: cannot read: %s\n" % (path, exc))
            status = 2
            continue
        issues = Checker(path, text).run()
        for line, message in issues:
            sys.stdout.write("%s:%d: %s\n" % (path, line, message))
        if issues and status == 0:
            status = 1
    return status


if __name__ == "__main__":
    sys.exit(main(sys.argv))
