#!/usr/bin/env python3
"""
Export a built reactive-presentation project to a screenshot-based .pptx
(one full-bleed image per slide — NOT an editable/native deck; for editable
PPTX use the aws-light-fcd skill).

Renders each slide headlessly (Playwright/Chromium), captures a pixel-exact
screenshot with all fragments revealed and canvas step animations completed,
and assembles a PowerPoint (python-pptx) with speaker notes carried over
from the deck's presenter notes.

This is the reliable, scriptable counterpart to the in-browser
`ExportUtils.exportPPTX()` button (html2canvas): real browser rendering
means fonts, canvas drawings, shadows, and gradients survive intact.

Usage:
    python3 export_pptx.py <project-dir> [-o out.pptx] [--blocks a.html b.html]
                           [--width 1920] [--height 1080] [--scale 2]

    <project-dir>  Built output dir (contains index.html / NN-block.html + common/)

Dependencies:
    pip install playwright python-pptx   (+ `playwright install chromium`,
    or set PLAYWRIGHT_BROWSERS_PATH / CHROMIUM_PATH to an existing Chromium)
"""

import argparse
import functools
import html as html_lib
import http.server
import os
import re
import shutil
import socket
import sys
import tempfile
import threading
from pathlib import Path


def _die(msg: str, code: int = 1):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(code)


def _import_deps():
    try:
        from playwright.sync_api import sync_playwright  # noqa: F401
    except ImportError:
        _die("playwright is not installed. Run: pip install playwright && playwright install chromium")
    try:
        import pptx  # noqa: F401
    except ImportError:
        _die("python-pptx is not installed. Run: pip install python-pptx")


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args, **kwargs):
        pass


def _serve(root: Path):
    """Serve project dir on a free localhost port (file:// breaks fetch/CORS)."""
    handler = functools.partial(_QuietHandler, directory=str(root))

    # Bind port 0 directly on the server socket — no probe/rebind race.
    httpd = http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler)
    port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    return httpd, f"http://127.0.0.1:{port}"


def _discover_blocks(project_dir: Path):
    """Pick HTML files to export: merged index.html if present, else block files."""
    index = project_dir / 'index.html'
    if index.exists() and 'name="generator" content="remarp"' in index.read_text(encoding='utf-8', errors='ignore'):
        return ['index.html']
    blocks = []
    for f in sorted(project_dir.glob('*.html')):
        if f.name in ('toc.html', 'index.html'):
            continue
        text = f.read_text(encoding='utf-8', errors='ignore')
        if 'name="generator" content="remarp"' in text:
            blocks.append(f.name)
    return blocks


# Runs inside the page: freeze motion, reveal fragments, finish canvas steps,
# hide navigation chrome that has no meaning on a static slide.
_PREPARE_JS = """
() => {
  const style = document.createElement('style');
  style.textContent = `
    *, *::before, *::after { transition: none !important; animation: none !important; }
    .progress-bar, .slide-counter, .nav-hint, .canvas-controls { display: none !important; }
  `;
  document.head.appendChild(style);

  document.querySelectorAll('.fragment').forEach(el => el.classList.add('visible'));

  document.querySelectorAll('.slide').forEach(slide => {
    if (typeof slide.__canvasStep === 'function') {
      const parsed = parseInt(slide.dataset.canvasMaxStep || '30', 10);
      const max = Number.isFinite(parsed) ? parsed : 30;
      for (let s = 0; s < max; s++) {
        if (slide.__canvasStep('next') === false) break;
      }
    }
  });

  return document.querySelectorAll('.slide-deck .slide').length;
}
"""

_SHOW_SLIDE_JS = """
(idx) => {
  document.querySelectorAll('.slide-deck .slide').forEach((el, i) => {
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
  const el = document.querySelectorAll('.slide-deck .slide')[idx];
  const h = el ? el.querySelector('h1, h2, h3') : null;
  return h ? h.textContent.trim() : '';
}
"""

# presenterNotes is a top-level `const` in the built HTML; code evaluated in
# the page's global scope (like the DevTools console) can still read it.
_NOTES_JS = """
() => {
  try { return typeof presenterNotes !== 'undefined' ? presenterNotes : {}; }
  catch (e) { return {}; }
}
"""


def _strip_html(text: str) -> str:
    """HTML notes → plain text, preserving block boundaries as newlines."""
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</(?:p|li|div|ul|ol|h[1-6]|tr)>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<[^>]+>', '', text)
    text = html_lib.unescape(text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def export(project_dir: Path, out_path: Path, blocks, width: int, height: int, scale: int):
    from playwright.sync_api import sync_playwright
    from pptx import Presentation
    from pptx.util import Inches

    httpd, base_url = _serve(project_dir)
    tmpdir = Path(tempfile.mkdtemp(prefix='remarp-pptx-'))

    prs = Presentation()
    # Slide size follows the capture viewport's aspect ratio (7.5in height is
    # the PowerPoint constant; 16:9 → 13.333in, 4:3 → 10in).
    prs.slide_height = Inches(7.5)
    prs.slide_width = Inches(round(7.5 * width / height, 3))
    blank = prs.slide_layouts[6]

    total = 0
    try:
        with sync_playwright() as p:
            launch_kwargs = {}
            chromium_path = os.environ.get('CHROMIUM_PATH')
            if chromium_path:
                launch_kwargs['executable_path'] = chromium_path
            browser = p.chromium.launch(**launch_kwargs)
            page = browser.new_page(
                viewport={'width': width, 'height': height},
                device_scale_factor=scale,
            )

            for block in blocks:
                page.goto(f"{base_url}/{block}", wait_until='networkidle')
                page.evaluate("() => document.fonts.ready.then(() => true)")
                page.wait_for_timeout(600)  # let canvas setup scripts settle

                slide_count = page.evaluate(_PREPARE_JS)
                notes = page.evaluate(_NOTES_JS) or {}
                page.wait_for_timeout(300)  # canvas redraw after step advance

                deck = page.locator('.slide-deck')
                for i in range(slide_count):
                    title = page.evaluate(_SHOW_SLIDE_JS, i)
                    page.wait_for_timeout(80)

                    img = tmpdir / f"{Path(block).stem}-{i + 1:03d}.png"
                    deck.screenshot(path=str(img))

                    pptx_slide = prs.slides.add_slide(blank)
                    pptx_slide.shapes.add_picture(
                        str(img), 0, 0, prs.slide_width, prs.slide_height)

                    note = notes.get(str(i + 1)) or notes.get(i + 1) or ''
                    note_text = _strip_html(str(note))
                    if title and note_text:
                        note_text = f"{title}\n\n{note_text}"
                    elif title:
                        note_text = title
                    if note_text:
                        pptx_slide.notes_slide.notes_text_frame.text = note_text

                    total += 1
                    print(f"  [{total}] {block} slide {i + 1}/{slide_count}"
                          + (f" — {title}" if title else ""))

            browser.close()
    finally:
        httpd.shutdown()
        shutil.rmtree(tmpdir, ignore_errors=True)

    prs.save(str(out_path))
    print(f"\nOK: {total} slides → {out_path}")


def main():
    ap = argparse.ArgumentParser(description='Export built reactive-presentation to .pptx')
    ap.add_argument('project_dir', help='Built output dir (contains *.html + common/)')
    ap.add_argument('-o', '--output', help='Output .pptx path (default: <dir-name>.pptx in project dir)')
    ap.add_argument('--blocks', nargs='+', help='Specific block HTML files to export (relative to project dir)')
    ap.add_argument('--width', type=int, default=1920, help='Capture viewport width (default 1920)')
    ap.add_argument('--height', type=int, default=1080, help='Capture viewport height (default 1080)')
    ap.add_argument('--scale', type=int, default=2, choices=(1, 2, 3),
                    help='Device scale factor for crisp captures (default 2)')
    args = ap.parse_args()

    _import_deps()

    project_dir = Path(args.project_dir).resolve()
    if not project_dir.is_dir():
        _die(f"not a directory: {project_dir}")

    blocks = args.blocks or _discover_blocks(project_dir)
    if not blocks:
        _die(f"no remarp HTML files found in {project_dir} (build first: remarp_to_slides.py build)")
    for b in blocks:
        if not (project_dir / b).exists():
            _die(f"block not found: {b}")

    out_path = Path(args.output) if args.output else project_dir / f"{project_dir.name}.pptx"

    print(f"Exporting {len(blocks)} file(s) from {project_dir} → {out_path}")
    export(project_dir, out_path, blocks, args.width, args.height, args.scale)


if __name__ == '__main__':
    main()
