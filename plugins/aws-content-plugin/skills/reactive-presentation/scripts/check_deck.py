#!/usr/bin/env python3
"""
check_deck.py — Tier 1 static gate for hand-authored reactive-presentation HTML decks.

The retired Remarp compiler's `validate` no longer sees hand-authored HTML, so the
mistakes it used to catch now ship silently: a missing framework script (deck loads
as a wall of text), a <canvas> nobody wires up (blank slide), a quiz with no correct
answer, presenter notes that don't exist, raw hex colors that bypass the theme, and a
forked common/ copy that drifts from the skill assets. This script is the static half
of the pair — measure_deck.py (Tier 2, same directory) does the Playwright-rendered
geometry checks that need a browser.

Contract/wiring/asset breakage is FAIL; design-system drift is WARN and never blocks.

Usage:
    python3 check_deck.py <deck-dir-or-html> [--json] [--skill-assets DIR]

Exit 0 = no FAIL findings, 1 = FAIL findings, 2 = usage error.
Stdlib only — no browser, no network, no third-party deps.
"""
import argparse
import hashlib
import html as html_mod
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

FRAMEWORK_SCRIPTS = ('animation-utils.js', 'slide-framework.js',
                     'quiz-component.js', 'presenter-view.js')

# Referenced by future tests — keep exactly.
RULE_IDS = ('NO_THEME_CSS', 'MISSING_SCRIPT', 'FRAMEWORK_COUNT', 'MISSING_NOTES',
            'SHORT_NOTES', 'PRESENTER_KEYS', 'QUIZ_NO_ANSWER', 'CANVAS_WIRING',
            'FRAGMENT_GAPS', 'RAW_HEX', 'RAW_RGBA', 'INLINE_STYLE', 'OFF_SCALE',
            'PX_FONT', 'TITLE_LENGTH', 'BROKEN_REF', 'THEME_DUP', 'STALE_COMMON')


def discover(target: Path):
    """Return (deck_dir, [deck filenames], [skipped filenames]).

    Same detection as measure_deck.py's discover(): top-level *.html only, toc.html
    excluded by name, and a file without `new SlideFramework(` is a hub/index page
    rather than a deck. An explicitly named file is always checked so FRAMEWORK_COUNT
    can legitimately fire on it.
    """
    if target.is_file():
        return target.parent, [target.name], []
    blocks, skipped = [], []
    for f in sorted(target.glob('*.html')):
        if f.name == 'toc.html':
            skipped.append(f.name)
            continue
        text = f.read_text(encoding='utf-8', errors='ignore')
        (blocks if 'new SlideFramework(' in text else skipped).append(f.name)
    return target, blocks, skipped


class SlideFinder(HTMLParser):
    """Records (start, end) char offsets of each top-level .slide div inside .slide-deck.

    Depth-tracking rather than regex: slides contain nested <div>s (slide-header,
    slide-body), so the matching </div> cannot be found by pattern alone.
    """

    def __init__(self, text):
        super().__init__(convert_charrefs=False)
        self.text = text
        # line_starts[i] = char offset where line i+1 begins; getpos() is 1-based line
        # plus a 0-based column, so abs = line_starts[lineno - 1] + col.
        self.line_starts = [0]
        for i, ch in enumerate(text):
            if ch == "\n":
                self.line_starts.append(i + 1)
        self.div_depth = 0
        self.deck_depth = None   # div_depth at which .slide-deck opened
        self.open_slide = None   # (start_offset, depth_at_open)
        self.spans = []          # [(start, end)] in document order

    def _abs(self):
        lineno, col = self.getpos()
        return self.line_starts[lineno - 1] + col

    def handle_starttag(self, tag, attrs):
        if tag != "div":
            return
        classes = (dict(attrs).get("class") or "").split()
        start = self._abs()
        self.div_depth += 1
        if "slide-deck" in classes and self.deck_depth is None:
            self.deck_depth = self.div_depth
        elif (self.deck_depth is not None
              and self.div_depth == self.deck_depth + 1
              and self.open_slide is None
              and "slide" in classes):
            self.open_slide = (start, self.div_depth)

    def handle_endtag(self, tag):
        if tag != "div":
            return
        end = self._abs() + len("</div>")
        if self.open_slide is not None and self.div_depth == self.open_slide[1]:
            self.spans.append((self.open_slide[0], end))
            self.open_slide = None
        if self.deck_depth is not None and self.div_depth == self.deck_depth:
            self.deck_depth = None
        self.div_depth = max(0, self.div_depth - 1)


def find_slides(text):
    """Slide spans via SlideFinder; documented regex fallback when it finds none."""
    finder = SlideFinder(text)
    try:
        finder.feed(text)
        finder.close()
    except Exception:
        pass
    spans = finder.spans
    if not spans and re.search(r'<div[^>]*class="[^"]*\bslide\b', text):
        starts = [m.start() for m in
                  re.finditer(r'<div[^>]*class="[^"]*\bslide\b', text)]
        spans = []
        for i, s in enumerate(starts):
            if i + 1 < len(starts):
                e = starts[i + 1]
            else:
                m = re.search(r'</div>\s*<script', text[s:])
                e = s + m.start() + len('</div>') if m else len(text)
            spans.append((s, e))
    return spans


def slide_of(pos, spans):
    """1-based slide number whose span contains char offset pos, else None."""
    for i, (s, e) in enumerate(spans):
        if s <= pos < e:
            return i + 1
    return None


def js_object_end(text, open_idx):
    """Index just past the `}` closing the JS object whose `{` is at open_idx.

    Brace-depth scan that skips string literals ('/"/`, honoring \\ escapes) and
    // line comments — note text contains braces and the reference deck has
    `// ── Block 1` comments inside the object. None if unterminated.
    """
    depth, i, n = 0, open_idx, len(text)
    while i < n:
        ch = text[i]
        if ch in ('"', "'", '`'):
            i += 1
            while i < n:
                if text[i] == '\\':
                    i += 2
                    continue
                if text[i] == ch:
                    break
                i += 1
        elif ch == '/' and i + 1 < n and text[i + 1] == '/':
            while i < n and text[i] != '\n':
                i += 1
            continue
        elif ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    return None


def _collapse(s):
    return ' '.join(html_mod.unescape(s).split())


def check_file(deck_dir, name, skill_selectors, findings):
    """Run every Tier 1 rule over one deck file, appending finding dicts."""
    text = (deck_dir / name).read_text(encoding='utf-8', errors='replace')

    def add(severity, rule, message, slide=None):
        findings.append({'file': name, 'slide': slide, 'severity': severity,
                         'rule': rule, 'message': message})

    spans = find_slides(text)
    n_slides = len(spans)

    # --- CONTRACT wiring: a deck missing these loads but renders broken ---
    if not re.search(r'<link[^>]*href="[^"]*theme\.css"', text):
        add('FAIL', 'NO_THEME_CSS',
            'no <link href="...theme.css"> — the deck renders unstyled')
    for script in FRAMEWORK_SCRIPTS:
        if not re.search(r'<script[^>]*src="[^"]*' + re.escape(script) + '"', text):
            add('FAIL', 'MISSING_SCRIPT',
                f'{script} is not referenced by any <script src=...>')
    n_fw = text.count('new SlideFramework(')
    if n_fw != 1:
        add('FAIL', 'FRAMEWORK_COUNT',
            f'new SlideFramework( appears {n_fw} time(s), expected exactly 1')

    # --- NOTES: <template class="notes"> per slide OR a presenterNotes object.
    # Both real shapes must be accepted: a top-level `const presenterNotes = {` and
    # an inline `presenterNotes: {` inside the SlideFramework options — one form
    # appears in each reference deck, so accepting only one false-positives an
    # entire known-good deck.
    tmpl_notes = {}
    for m in re.finditer(
            r'<template\b[^>]*class="[^"]*\bnotes\b[^"]*"[^>]*>(.*?)</template>',
            text, re.S):
        sl = slide_of(m.start(), spans)
        if sl is not None and sl not in tmpl_notes:
            tmpl_notes[sl] = m.group(1)
    notes_block, note_keys = None, set()
    m = re.search(r'(?:const\s+presenterNotes\s*=\s*|presenterNotes\s*:\s*)\{', text)
    if m:
        end = js_object_end(text, m.end() - 1)
        if end is not None:
            notes_block = text[m.end() - 1:end]
            # Line-anchored: every note value is one physical line (newlines in
            # notes are \n escapes), so digits in prose can't look like keys.
            note_keys = {int(k) for k in
                         re.findall(r'^[ \t]*(\d+)\s*:', notes_block, re.M)}
    missing = []
    for i in range(1, n_slides + 1):
        texts = []
        if i in tmpl_notes:
            texts.append(_collapse(re.sub(r'<[^>]+>', '', tmpl_notes[i])))
        if i in note_keys and notes_block:
            lm = re.search(r'^[ \t]*' + str(i) + r'\s*:\s*(.*)$', notes_block, re.M)
            if lm:
                v = lm.group(1).strip().rstrip(',').strip()
                if len(v) >= 2 and v[0] in '\'"`' and v[-1] == v[0]:
                    v = v[1:-1]
                texts.append(_collapse(v))
        if not texts:
            missing.append(i)
            add('WARN', 'MISSING_NOTES',
                'no <template class="notes"> and no presenterNotes key', slide=i)
        else:
            longest = max(texts, key=len)
            if len(longest) < 150:
                add('WARN', 'SHORT_NOTES',
                    f'notes are {len(longest)} chars (<150)', slide=i)
    if missing:
        shown = ', '.join(str(x) for x in missing[:15]) + \
                ('…' if len(missing) > 15 else '')
        add('WARN', 'PRESENTER_KEYS',
            f'notes cover {n_slides - len(missing)}/{n_slides} slides; '
            f'missing: {shown}')

    # --- QUIZ_NO_ANSWER: a quiz with no data-correct="true" can never grade ---
    quiz_tags = list(re.finditer(r'<[a-zA-Z][^>]*\bdata-quiz\b[^>]*>', text))
    for idx, qm in enumerate(quiz_tags):
        sl = slide_of(qm.start(), spans)
        ends = [len(text)]
        if idx + 1 < len(quiz_tags):
            ends.append(quiz_tags[idx + 1].start())
        if sl is not None:
            ends.append(spans[sl - 1][1])
        if 'data-correct="true"' not in text[qm.start():min(ends)]:
            add('FAIL', 'QUIZ_NO_ANSWER',
                'data-quiz element contains no data-correct="true"', slide=sl)

    # --- CANVAS_WIRING: an unwired canvas renders a blank slide. Three real
    # idioms must all count as a reference — getElementById('X'),
    # querySelector('#X'), and a bare 'X' string arg to a helper like
    # initCanvas('agent-canvas', ...). Strip <canvas> tags first so the id
    # attribute never counts as its own reference.
    stripped = re.sub(r'<canvas\b[^>]*>', '', text)
    for cm in re.finditer(r'<canvas\b[^>]*?\bid="([^"]+)"[^>]*>', text):
        cid = cm.group(1)
        if not (f"'{cid}'" in stripped or f'"{cid}"' in stripped
                or f'#{cid}' in stripped):
            add('FAIL', 'CANVAS_WIRING',
                f'<canvas id="{cid}"> id is never referenced elsewhere in the file',
                slide=slide_of(cm.start(), spans))

    # --- FRAGMENT_GAPS: a gap means a fragment step never advances ---
    for i, (s, e) in enumerate(spans):
        vals = {int(v) for v in
                re.findall(r'data-fragment-index="(\d+)"', text[s:e])}
        if vals and sorted(vals) != list(range(min(vals), min(vals) + len(vals))):
            add('WARN', 'FRAGMENT_GAPS',
                f'fragment indices not contiguous: {sorted(vals)}', slide=i + 1)

    # --- Design lint (WARN) over the deck's own text only, never common/.
    # RAW_HEX/RAW_RGBA/OFF_SCALE/PX_FONT aggregate ONE finding per file with a
    # count + up to 5 samples — a real deck has hundreds of matches and one
    # finding each would bury every FAIL in the report.
    style_blocks = re.findall(r'<style[^>]*>(.*?)</style>', text, re.S)
    style_attrs = re.findall(r'style="([^"]*)"', text)
    hex_n, hex_smp, rgba_n, rgba_smp = 0, [], 0, []
    for surf in style_blocks + style_attrs:
        for decl in re.split(r'[;{}]', surf):
            d = decl.strip()
            if not d:
                continue
            if re.search(r'#[0-9a-fA-F]{3,8}\b', d) and 'var(--pptx-' not in d:
                hex_n += 1
                if len(hex_smp) < 5:
                    hex_smp.append(d[:60])
            n_rgba = len(re.findall(r'rgba?\(', d))
            if n_rgba and 'var(' not in d:
                rgba_n += n_rgba
                if len(rgba_smp) < 5:
                    rgba_smp.append(d[:60])
    if hex_n:
        add('WARN', 'RAW_HEX',
            f'{hex_n} declaration(s) use raw hex outside var(--pptx- fallback; '
            f'e.g. {"; ".join(hex_smp)}')
    if rgba_n:
        add('WARN', 'RAW_RGBA',
            f'{rgba_n} raw rgb()/rgba() outside var(); e.g. {"; ".join(rgba_smp)}')

    per_slide = {}
    for sm in re.finditer(r'style="([^"]*)"', text):
        if re.search(r'\b(?:color|background|padding|margin|font-size)\b',
                     sm.group(1)):
            sl = slide_of(sm.start(), spans)
            per_slide[sl] = per_slide.get(sl, 0) + 1
    for sl in sorted(per_slide, key=lambda x: (x is not None, x or 0)):
        add('WARN', 'INLINE_STYLE',
            f'{per_slide[sl]} inline style attribute(s) set '
            f'color/background/padding/margin/font-size', slide=sl)

    off_n, off_smp, pxf_n, pxf_smp = 0, [], 0, []
    for blk in style_blocks:
        for lm in re.finditer(r'([\d.]+)(px|rem)', blk):
            try:
                v = float(lm.group(1))
            except ValueError:
                continue
            if v == 0 or (lm.group(2) == 'px' and (v <= 3 or v == 9999)):
                continue
            px = v if lm.group(2) == 'px' else v * 16
            r = px % 4
            if min(r, 4 - r) > 0.01:
                off_n += 1
                if len(off_smp) < 5:
                    off_smp.append(lm.group(0))
        for fm in re.finditer(r'font-size\s*:\s*[\d.]+px', blk):
            pxf_n += 1
            if len(pxf_smp) < 5:
                pxf_smp.append(fm.group(0))
    if off_n:
        add('WARN', 'OFF_SCALE',
            f'{off_n} length(s) off the 4px grid; e.g. {", ".join(off_smp)}')
    if pxf_n:
        add('WARN', 'PX_FONT',
            f'{pxf_n} px font-size(s) — the framework scale is rem-based; '
            f'e.g. {", ".join(pxf_smp)}')

    # --- TITLE_LENGTH: long titles wrap and push the slide body off-canvas ---
    for i, (s, e) in enumerate(spans):
        tm = re.search(r'<h2[^>]*>(.*?)</h2>', text[s:e], re.S)
        if tm:
            title = _collapse(re.sub(r'<[^>]+>', '', tm.group(1)))
            if len(title) > 28:
                add('WARN', 'TITLE_LENGTH',
                    f'title is {len(title)} chars (>28): "{title}"', slide=i + 1)

    # --- BROKEN_REF: relative refs must resolve on disk, deduplicated.
    # ../favicon.png resolving above the deck dir is legitimate — resolve it.
    seen_missing = set()
    for rm in re.finditer(r'(?:src|href)="([^"]+)"', text):
        ref = rm.group(1)
        if ref.startswith(('http://', 'https://', '//', 'data:', 'mailto:', '#')):
            continue
        path_part = html_mod.unescape(ref.split('#')[0].split('?')[0])
        if not path_part or path_part in seen_missing:
            continue
        try:
            exists = (deck_dir / path_part).exists()
        except OSError:
            exists = False
        if not exists:
            seen_missing.add(path_part)
            add('FAIL', 'BROKEN_REF', f'referenced path not found: {path_part}')

    # --- THEME_DUP: deck-local shadows of theme.css class rules drift apart ---
    if skill_selectors:
        local = set()
        for blk in style_blocks:
            local |= set(re.findall(r'^\s*\.([A-Za-z0-9_-]+)\s*\{', blk, re.M))
        shadowed = sorted(local & skill_selectors)
        if shadowed:
            names = ', '.join(shadowed[:15]) + ('…' if len(shadowed) > 15 else '')
            add('WARN', 'THEME_DUP',
                f'{len(shadowed)} class selector(s) already defined in the '
                f"skill's theme.css: {names} — generalize the rule into "
                f'theme.css instead of shadowing it locally')


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument('target')
    ap.add_argument('--json', action='store_true')
    ap.add_argument('--skill-assets', metavar='DIR',
                    default=str(Path(__file__).resolve().parent.parent / 'assets'))
    args = ap.parse_args()

    target = Path(args.target)
    if not target.exists():
        print(f"error: {target} not found", file=sys.stderr)
        return 2
    deck_dir, blocks, skipped = discover(target)
    if not blocks:
        print(f"error: no SlideFramework decks found in {target}", file=sys.stderr)
        return 2

    skill_css = Path(args.skill_assets) / 'theme.css'
    skill_selectors = set()
    try:
        skill_selectors = set(re.findall(
            r'^\s*\.([A-Za-z0-9_-]+)\s*\{',
            skill_css.read_text(encoding='utf-8', errors='replace'), re.M))
    except OSError:
        pass  # THEME_DUP skips silently when the assets theme.css is unreadable

    findings = []
    for name in blocks:
        try:
            check_file(deck_dir, name, skill_selectors, findings)
        except Exception as exc:  # a malformed deck degrades, never tracebacks
            findings.append({'file': name, 'slide': None, 'severity': 'FAIL',
                             'rule': 'CHECK_ERROR',
                             'message': f'checker crashed on this file: {exc}'})

    # STALE_COMMON: at most once per deck DIRECTORY, not per html file.
    common_css = deck_dir / 'common' / 'theme.css'
    if common_css.is_file() and skill_css.is_file():
        try:
            if (hashlib.sha256(common_css.read_bytes()).hexdigest()
                    != hashlib.sha256(skill_css.read_bytes()).hexdigest()):
                findings.append({
                    'file': blocks[0], 'slide': None, 'severity': 'WARN',
                    'rule': 'STALE_COMMON',
                    'message': 'common/theme.css differs from the skill assets '
                               'theme.css (sha256) — the deck carries a forked/'
                               'stale framework copy; re-sync from skill assets'})
        except OSError:
            pass

    fails = [f for f in findings if f['severity'] == 'FAIL']
    warns = [f for f in findings if f['severity'] == 'WARN']

    if args.json:
        # Nothing else on stdout so it pipes into `python3 -m json.tool`.
        # ensure_ascii=False matters: deck titles and notes are Korean.
        print(json.dumps(findings, ensure_ascii=False, indent=2))
        return 1 if fails else 0

    for name in blocks:
        rows = [f for f in findings if f['file'] == name]
        present = {f['rule'] for f in rows}
        n_ok = sum(1 for r in RULE_IDS if r not in present)
        n_warn = sum(1 for f in rows if f['severity'] == 'WARN')
        n_fail = len(rows) - n_warn
        print(f"=== {name} ===")
        print(f"  OK {n_ok} | WARN {n_warn} | FAIL {n_fail}")
        rows.sort(key=lambda f: (0 if f['severity'] == 'FAIL' else 1,
                                 f['slide'] is not None, f['slide'] or 0))
        for f in rows:
            loc = f"slide {f['slide']}" if f['slide'] else ""
            print(f"  {f['severity']:4}  {f['rule']:15} {loc:10} {f['message']}")
    tail = f"\n{len(fails)} FAIL, {len(warns)} WARN ({len(blocks)} deck file(s)"
    if skipped:
        tail += f"; skipped: {', '.join(skipped)}"
    print(tail + ")")
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
