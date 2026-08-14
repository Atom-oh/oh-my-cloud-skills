#!/usr/bin/env python3
"""
measure_deck.py — Tier 2 measured gate for reactive-presentation HTML decks.

Playwright-rendered geometry checks that no static linter can do. This is the
half of the old remarp `validate` promise that never actually existed: the
compiler's CANVAS_OVERLAP only saw DSL-declared coordinates on canvas slides;
this measures every slide's real layout.

Checks per slide (per viewport, per theme, per canvas step):
  OVERFLOW      descendant rect escapes the .slide box / clipped container scrolls
  OVERLAP       painted sibling boxes intersect
  CLIPPED_TEXT  overflow:hidden element whose content exceeds its box
  LOW_CONTRAST  computed text/background contrast < 4.5 (WARN)
  RATIO_DRIFT   content scale does not follow the deck box across aspect ratios
  BROKEN_IMAGE  img.naturalWidth === 0
  CONSOLE       page errors / failed requests

Usage:
    python3 measure_deck.py <deck-dir-or-html> [--json] [--screenshots DIR]
        [--viewports 1920x1080,1280x720,3840x2160] [--themes light,dark]
        [--max-steps 30] [--slides 3,7]

Exit 0 = no FAIL findings, 1 = FAIL findings, 2 = usage error.
Requires: pip install 'playwright>=1.40' && playwright install chromium
"""
import argparse
import json
import sys
import urllib.parse
from pathlib import Path

# --- page-side helpers -------------------------------------------------------

# Freeze motion so rects are stable; reveal all fragments (hidden fragments
# have opacity 0 but still occupy layout in some patterns — measuring the
# fully-revealed state is the presentation-final state).
_PREPARE_JS = """
() => {
  const style = document.createElement('style');
  style.textContent = `
    *, *::before, *::after { transition: none !important; animation: none !important; }
    .progress-bar, .slide-counter, .nav-hint, .slide-sidebar { display: none !important; }
  `;
  document.head.appendChild(style);
  document.body.classList.remove('sidebar-visible');
  document.querySelectorAll('.fragment').forEach(el => el.classList.add('visible'));
  return document.querySelectorAll('.slide-deck .slide').length;
}
"""

_SHOW_SLIDE_JS = """
(idx) => {
  const slides = document.querySelectorAll('.slide-deck .slide');
  slides.forEach((el, i) => {
    el.classList.remove('entering', 'leaving');
    if (i === idx) {
      el.classList.add('active');
      el.style.display = 'flex';
      el.style.opacity = '1';
      el.style.visibility = 'visible';
    } else {
      el.classList.remove('active');
      el.style.display = 'none';
    }
  });
  const h = slides[idx] ? slides[idx].querySelector('h1, h2, h3') : null;
  return h ? h.textContent.trim().slice(0, 60) : '';
}
"""

# One measurement pass over the active slide. Returns a list of finding dicts.
_MEASURE_JS = r"""
() => {
  const slide = document.querySelector('.slide-deck .slide.active');
  if (!slide) return [];
  const findings = [];
  const sRect = slide.getBoundingClientRect();
  const TOL = 2; // px tolerance for AA rounding

  const sel = (el) => {
    let s = el.tagName.toLowerCase();
    if (el.id) return s + '#' + el.id;
    if (el.classList.length) s += '.' + [...el.classList].slice(0, 2).join('.');
    return s;
  };
  const visible = (el) => {
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden' || parseFloat(cs.opacity) === 0) return false;
    const r = el.getBoundingClientRect();
    return r.width > 1 && r.height > 1;
  };

  const els = [...slide.querySelectorAll('*')].filter(el =>
    !(el.tagName === 'TEMPLATE' || el.closest('template')) && visible(el));

  // --- OVERFLOW: descendant escapes the slide box ---
  for (const el of els) {
    const r = el.getBoundingClientRect();
    // position:fixed chrome (framework footer etc.) is deck-level, skip
    if (getComputedStyle(el).position === 'fixed') continue;
    const out = Math.max(sRect.left - r.left, r.right - sRect.right,
                         sRect.top - r.top, r.bottom - sRect.bottom);
    if (out > TOL + 4) {
      findings.push({ rule: 'OVERFLOW', severity: 'FAIL', el: sel(el),
        message: `escapes slide box by ${Math.round(out)}px` });
    }
  }

  // --- OVERFLOW (scroll form): clipped container with more content than box ---
  // --- CLIPPED_TEXT: same, but horizontally on text elements ---
  for (const el of els) {
    const cs = getComputedStyle(el);
    const clipsY = ['hidden', 'clip'].includes(cs.overflowY);
    const clipsX = ['hidden', 'clip'].includes(cs.overflowX);
    const scrollable = ['auto', 'scroll'].includes(cs.overflowY);
    if (clipsY && el.scrollHeight > el.clientHeight + TOL + 6) {
      findings.push({ rule: 'CLIPPED_TEXT', severity: 'FAIL', el: sel(el),
        message: `vertically clipped: content ${el.scrollHeight}px in ${el.clientHeight}px box` });
    }
    if (clipsX && el.scrollWidth > el.clientWidth + TOL + 6) {
      findings.push({ rule: 'CLIPPED_TEXT', severity: 'FAIL', el: sel(el),
        message: `horizontally clipped: content ${el.scrollWidth}px in ${el.clientWidth}px box` });
    }
    // scrollable code blocks are a sanctioned pattern — but a slide body that
    // scrolls means the slide doesn't fit: WARN
    if (scrollable && el.classList.contains('slide-body') &&
        el.scrollHeight > el.clientHeight + TOL) {
      findings.push({ rule: 'OVERFLOW', severity: 'WARN', el: sel(el),
        message: 'slide-body scrolls — content exceeds the slide' });
    }
  }

  // --- OVERLAP: painted siblings intersect ---
  const painted = (el) => {
    const cs = getComputedStyle(el);
    const bg = cs.backgroundColor;
    const hasBg = bg && bg !== 'rgba(0, 0, 0, 0)' && bg !== 'transparent';
    const hasBorder = ['Top','Right','Bottom','Left'].some(
      side => parseFloat(cs['border' + side + 'Width']) > 0 &&
              cs['border' + side + 'Style'] !== 'none');
    return hasBg || hasBorder || cs.boxShadow !== 'none';
  };
  const byParent = new Map();
  for (const el of els) {
    if (!painted(el)) continue;
    const p = el.parentElement;
    if (!byParent.has(p)) byParent.set(p, []);
    byParent.get(p).push(el);
  }
  for (const group of byParent.values()) {
    for (let i = 0; i < group.length; i++) {
      for (let j = i + 1; j < group.length; j++) {
        const a = group[i].getBoundingClientRect();
        const b = group[j].getBoundingClientRect();
        const ix = Math.min(a.right, b.right) - Math.max(a.left, b.left);
        const iy = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
        // require a real 2-D bite, not an edge kiss or an intentional badge
        if (ix > 8 && iy > 8 && !(group[i].contains(group[j]) || group[j].contains(group[i]))) {
          const area = ix * iy;
          const aArea = a.width * a.height, bArea = b.width * b.height;
          if (area > 0.15 * Math.min(aArea, bArea)) {
            findings.push({ rule: 'OVERLAP', severity: 'FAIL',
              el: sel(group[i]) + ' × ' + sel(group[j]),
              message: `painted siblings overlap ${Math.round(ix)}×${Math.round(iy)}px` });
          }
        }
      }
    }
  }

  // --- LOW_CONTRAST ---
  const parseColor = (rgb) => {
    const m = rgb.match(/rgba?\(([\d.]+),\s*([\d.]+),\s*([\d.]+)(?:,\s*([\d.]+))?\)/);
    if (!m) return null;
    return { r: +m[1], g: +m[2], b: +m[3], a: m[4] === undefined ? 1 : +m[4] };
  };
  const lumOf = (c) => {
    const f = (v) => { v /= 255;
      return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
    return 0.2126 * f(c.r) + 0.7152 * f(c.g) + 0.0722 * f(c.b);
  };
  const lum = (rgb) => {
    const c = parseColor(rgb);
    return c && c.a > 0 ? lumOf(c) : null;
  };
  // Effective background: composite semi-transparent layers over ancestors
  // (a 10% tint over a dark surface is dark, not the tint's own hue).
  const effBg = (el) => {
    const layers = [];
    for (let n = el; n; n = n.parentElement) {
      const c = parseColor(getComputedStyle(n).backgroundColor);
      if (c && c.a > 0) {
        layers.push(c);
        if (c.a >= 1) break;
      }
    }
    let base = { r: 255, g: 255, b: 255 }; // page default light
    for (const c of layers.reverse()) {
      base = { r: c.r * c.a + base.r * (1 - c.a),
               g: c.g * c.a + base.g * (1 - c.a),
               b: c.b * c.a + base.b * (1 - c.a) };
    }
    return lumOf(base);
  };
  const seenContrast = new Set();
  for (const el of els) {
    if (!el.childNodes.length) continue;
    const hasText = [...el.childNodes].some(
      n => n.nodeType === 3 && n.textContent.trim().length > 3);
    if (!hasText) continue;
    const cs = getComputedStyle(el);
    const fg = lum(cs.color);
    if (fg === null) continue;
    const bg = effBg(el);
    const ratio = (Math.max(fg, bg) + 0.05) / (Math.min(fg, bg) + 0.05);
    const px = parseFloat(cs.fontSize);
    // WCAG large text: >= 24px, or bold >= 18.66px (14pt)
    const bold = parseInt(cs.fontWeight, 10) >= 600;
    const large = px >= 24 || (bold && px >= 18.66);
    const threshold = large ? 3.0 : 4.5;
    if (ratio < threshold) {
      const key = sel(el) + '|' + Math.round(ratio * 10);
      if (!seenContrast.has(key)) {
        seenContrast.add(key);
        findings.push({ rule: 'LOW_CONTRAST', severity: 'WARN', el: sel(el),
          message: `contrast ${ratio.toFixed(1)} < ${threshold}` });
      }
    }
  }

  // --- BROKEN_IMAGE ---
  for (const img of slide.querySelectorAll('img')) {
    if (img.complete && img.naturalWidth === 0) {
      findings.push({ rule: 'BROKEN_IMAGE', severity: 'FAIL', el: sel(img),
        message: (img.getAttribute('src') || '') + ' failed to load' });
    }
  }

  return findings;
}
"""

# Reference metrics for RATIO_DRIFT: deck box + the rendered size of the first
# heading. If the deck scales as one canvas, headingHeight / deckHeight is
# invariant across viewports; the vh-font bug makes it drift.
_RATIO_PROBE_JS = """
() => {
  const deck = document.querySelector('.slide-deck');
  const h = document.querySelector('.slide-deck .slide.active h1, .slide-deck .slide.active h2');
  if (!deck) return null;
  const d = deck.getBoundingClientRect();
  const r = { deckW: d.width, deckH: d.height, headingH: null };
  if (h) r.headingH = h.getBoundingClientRect().height;
  return r;
}
"""

_STEP_JS = """
(dir) => {
  const slide = document.querySelector('.slide-deck .slide.active');
  if (!slide || typeof slide.__canvasStep !== 'function') return false;
  return slide.__canvasStep(dir) !== false;
}
"""


def discover(target: Path):
    if target.is_file():
        return target.parent, [target.name]
    blocks = []
    for f in sorted(target.glob('*.html')):
        if f.name == 'toc.html':
            continue
        text = f.read_text(encoding='utf-8', errors='ignore')
        if 'new SlideFramework(' in text:
            blocks.append(f.name)
    return target, blocks


def measure(deck_dir: Path, blocks, viewports, themes, max_steps, shots_dir,
            only_slides=None):
    from playwright.sync_api import sync_playwright
    import http.server
    import socketserver
    import threading
    import functools
    import os

    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass

    handler = functools.partial(QuietHandler, directory=str(deck_dir))
    httpd = socketserver.TCPServer(('127.0.0.1', 0), handler)
    httpd.allow_reuse_address = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    base_url = f"http://127.0.0.1:{httpd.server_address[1]}"

    findings = []
    ratio_probes = {}  # (block, slide, theme) -> [(vw, vh, deckW, deckH, headingH)]

    try:
        with sync_playwright() as p:
            kw = {}
            if os.environ.get('CHROMIUM_PATH'):
                kw['executable_path'] = os.environ['CHROMIUM_PATH']
            browser = p.chromium.launch(**kw)
            for vw, vh in viewports:
                page = browser.new_page(viewport={'width': vw, 'height': vh})
                console_errs, failed_reqs = [], []
                page.on('pageerror', lambda e: console_errs.append(str(e)))
                page.on('console',
                        lambda m: console_errs.append(m.text) if m.type == 'error' else None)
                page.on('requestfailed',
                        lambda r: failed_reqs.append(r.url) if not r.url.startswith('data:') else None)

                for block in blocks:
                    for theme in themes:
                        page.goto(f"{base_url}/{urllib.parse.quote(block)}",
                                  wait_until='networkidle')
                        page.evaluate("() => document.fonts.ready.then(() => true)")
                        page.wait_for_timeout(400)
                        if theme == 'dark':
                            page.evaluate(
                                "() => document.querySelector('.slide-deck')"
                                ".classList.add('theme-dark')")
                        n = page.evaluate(_PREPARE_JS)
                        page.wait_for_timeout(200)

                        for i in range(n):
                            if only_slides and (i + 1) not in only_slides:
                                continue
                            title = page.evaluate(_SHOW_SLIDE_JS, i)
                            page.wait_for_timeout(60)

                            probe = page.evaluate(_RATIO_PROBE_JS)
                            if probe:
                                key = (block, i + 1, theme)
                                ratio_probes.setdefault(key, []).append(
                                    (vw, vh, probe['deckW'], probe['deckH'],
                                     probe['headingH']))

                            # step through canvas states, measuring each
                            step = 0
                            while True:
                                for f in page.evaluate(_MEASURE_JS):
                                    f.update(file=block, slide=i + 1, title=title,
                                             viewport=f"{vw}x{vh}", theme=theme,
                                             step=step or None)
                                    findings.append(f)
                                if shots_dir and step == 0:
                                    out = (shots_dir /
                                           f"{Path(block).stem}-s{i+1:02d}-{vw}x{vh}-{theme}.png")
                                    page.locator('.slide-deck').screenshot(path=str(out))
                                step += 1
                                if step > max_steps or not page.evaluate(_STEP_JS, 'next'):
                                    break

                for e in console_errs[:10]:
                    findings.append(dict(rule='CONSOLE', severity='WARN', file=block,
                                         slide=None, el=None, viewport=f"{vw}x{vh}",
                                         theme=None, step=None, message=e[:200]))
                for u in sorted(set(failed_reqs))[:10]:
                    # Local asset failures break the deck; external ones
                    # (analytics, CDNs) are network noise in headless — WARN.
                    local = u.startswith(base_url) or u.startswith('file:')
                    findings.append(dict(rule='FAILED_REQUEST',
                                         severity='FAIL' if local else 'WARN',
                                         file=block, slide=None, el=None,
                                         viewport=f"{vw}x{vh}", theme=None, step=None,
                                         message=u[:200]))
                page.close()
            browser.close()
    finally:
        httpd.shutdown()

    # --- RATIO_DRIFT: content scale must follow the deck box ---
    for (block, slide, theme), rows in ratio_probes.items():
        rows = [r for r in rows if r[4]]  # need a heading
        if len(rows) < 2:
            continue
        fracs = [(hh / dh, f"{vw}x{vh}") for vw, vh, dw, dh, hh in rows]
        base, base_vp = fracs[0]
        for frac, vp in fracs[1:]:
            drift = abs(frac - base) / base if base else 0
            if drift > 0.12:
                findings.append(dict(
                    rule='RATIO_DRIFT', severity='FAIL', file=block, slide=slide,
                    el='h1/h2', viewport=f"{base_vp} vs {vp}", theme=theme, step=None,
                    message=(f"heading/deck height ratio drifts {drift*100:.0f}% "
                             f"between viewports — type does not scale with the deck "
                             f"(vh-font vs letterboxed box)")))
                break
    return findings


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument('target')
    ap.add_argument('--json', action='store_true')
    ap.add_argument('--screenshots', metavar='DIR')
    ap.add_argument('--viewports', default='1920x1080,1280x720,960x1080',
                    help='comma list of WxH; include a width-constrained one '
                         'for ratio checks (default adds 960x1080)')
    ap.add_argument('--themes', default='light,dark')
    ap.add_argument('--max-steps', type=int, default=30)
    ap.add_argument('--slides', help='comma list of 1-based slide numbers to limit to')
    args = ap.parse_args()

    target = Path(args.target)
    if not target.exists():
        print(f"error: {target} not found", file=sys.stderr)
        return 2
    deck_dir, blocks = discover(target)
    if not blocks:
        print(f"error: no SlideFramework decks found in {target}", file=sys.stderr)
        return 2

    viewports = []
    for spec in args.viewports.split(','):
        w, _, h = spec.strip().partition('x')
        viewports.append((int(w), int(h)))
    themes = [t.strip() for t in args.themes.split(',') if t.strip()]
    only_slides = ({int(s) for s in args.slides.split(',')} if args.slides else None)
    shots = None
    if args.screenshots:
        shots = Path(args.screenshots)
        shots.mkdir(parents=True, exist_ok=True)

    findings = measure(deck_dir, blocks, viewports, themes, args.max_steps, shots,
                       only_slides)

    fails = [f for f in findings if f['severity'] == 'FAIL']
    warns = [f for f in findings if f['severity'] == 'WARN']

    if args.json:
        print(json.dumps(findings, ensure_ascii=False, indent=1))
    else:
        for f in findings:
            loc = f"{f['file']}#{f['slide']}" if f.get('slide') else f['file']
            extra = ' '.join(x for x in (f.get('viewport'), f.get('theme'),
                                         f'step{f["step"]}' if f.get('step') else None) if x)
            print(f"{f['severity']:4}  {f['rule']:15} {loc:30} [{extra}] "
                  f"{f.get('el') or ''} — {f['message']}")
        print(f"\n{len(fails)} FAIL, {len(warns)} WARN "
              f"({len(blocks)} file(s), {len(viewports)} viewport(s), "
              f"{len(themes)} theme(s))")
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
