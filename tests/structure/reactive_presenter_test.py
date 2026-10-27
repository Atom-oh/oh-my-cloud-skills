"""Browser regression tests for presenter-view preview fidelity (reactive-presentation).

Skips (exit 0) when Playwright for Python or its Chromium is unavailable; the TAP wrapper
reports that as a SKIP so a missing browser is never mistaken for a pass.
"""
import functools
import http.server
import shutil
import socketserver
import sys
import tempfile
import threading
import unittest
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "plugins/aws-content-plugin/skills/reactive-presentation/assets"

LONG = "온프렘 라우터에 node별 prefix를 수동 등록하고 drift를 추적해야 합니다"
DECK = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Presenter fixture</title>
<link rel="stylesheet" href="./common/theme.css">
<link rel="stylesheet" href="./common/deck-overlay.css">
<link rel="stylesheet" href="./common/deck-detail.css">
<link rel="stylesheet" href="./common/deck-nav.css">
</head>
<body>
<div class="slide-deck preset-paper" data-fit="auto">
  <div class="slide"><div class="slide-header"><h2>First slide</h2></div>
    <div class="slide-body"><p>Intro text for the first slide.</p></div></div>
  <div class="slide theme-dark"><div class="slide-header"><h2>Routing choices</h2></div>
    <div class="slide-body"><table>
      <tr><th>Item</th><th>Static</th><th>BGP</th><th>Gateway</th></tr>
      <tr><td>Pod CIDR 도달 방법</td><td>{LONG}</td><td>{LONG}</td><td>{LONG}</td></tr>
      <tr><td>온프렘 라우터 변경</td><td>{LONG}</td><td>필요</td><td>{LONG}</td></tr>
      <tr><td>HA</td><td>{LONG}</td><td>{LONG}</td><td>짧음</td></tr>
    </table></div></div>
  <div class="slide"><div class="slide-header"><h2>Fragments</h2></div>
    <div class="slide-body"><p class="fragment" data-fragment-index="1">One</p>
      <p class="fragment" data-fragment-index="2">Two</p></div></div>
  <div class="slide"><div class="slide-header"><h2>Detail</h2></div>
    <div class="slide-body"><p>port <span class="rp-detail" tabindex="0" data-detail="d" data-tip="t">UDP 8472</span></p></div>
    <div class="rp-detail-store" hidden><section data-detail-id="d" data-title="T" data-text="x"><p>x</p></section></div></div>
</div>
<script src="./common/animation-utils.js"></script>
<script src="./common/deck-overlay.js"></script>
<script src="./common/deck-detail.js"></script>
<script src="./common/deck-nav.js"></script>
<script src="./common/slide-framework.js"></script>
<script src="./common/presenter-view.js"></script>
<script>const deck = new SlideFramework({{ sidebar: false }});</script>
</body>
</html>
"""


def _pen_deck(opts, extra_head="", css=True):
    deck = DECK.replace(
        '<link rel="stylesheet" href="./common/deck-nav.css">\n',
        '<link rel="stylesheet" href="./common/deck-nav.css">\n'
        + ('<link rel="stylesheet" href="./common/deck-pen.css">\n' if css else "") + extra_head)
    deck = deck.replace(
        '<script src="./common/deck-nav.js"></script>\n',
        '<script src="./common/deck-nav.js"></script>\n<script src="./common/deck-pen.js"></script>\n')
    return deck.replace("new SlideFramework({ sidebar: false })", "new SlideFramework({ %s })" % opts)


RATIO_43 = "<style>:root { --slide-ratio-w: 4; --slide-ratio-h: 3; }</style>\n"

# Slide 0 of the lens decks: a marker square and an SVG whose gradient fill and
# <use> both reference ids (the lens clone has no ids of its own).
LENS_MARKERS = """<div class="slide-body"><p>Intro text for the first slide.</p></div>
    <div id="lens-mark" style="position:absolute;left:1000px;top:500px;width:40px;height:40px;background:rgb(0,170,0)"></div>
    <svg id="lens-svg" width="160" height="60" style="position:absolute;left:200px;top:700px">
      <defs><linearGradient id="lens-grad"><stop offset="0" stop-color="rgb(0,120,255)"/><stop offset="1" stop-color="rgb(0,120,255)"/></linearGradient>
        <symbol id="lens-sym"><rect width="60" height="60" fill="rgb(255,140,0)"/></symbol></defs>
      <rect id="lens-svg-grad" width="60" height="60" fill="url(#lens-grad)"/>
      <use id="lens-svg-use" href="#lens-sym" x="90" y="0" width="60" height="60"/>
    </svg></div>"""


def _lens_deck(extra_head=""):
    deck = _pen_deck("sidebar: false, pen: { fadeMs: 300 }", extra_head)
    return deck.replace('<div class="slide-body"><p>Intro text for the first slide.</p></div></div>',
                        LENS_MARKERS, 1)


# Slide 0 of the boxes deck: three boxes with a delegated live handler on the
# slide root (like the aws-landing-zone handlers: e.target.closest, a class
# toggle and out.innerHTML), plus a link, a disabled button and text targets.
BOX_SLIDE = """<div class="slide-body">
      <div class="boxes"><div class="box" data-t="Alpha detail">Alpha</div>
        <div class="box" data-t="Beta detail"><span class="lbl">Beta</span></div>
        <div class="box" data-t="Gamma detail">Gamma</div></div>
      <div id="out">none</div>
      <a id="link" href="#elsewhere">A link</a>
      <button id="off" disabled>Off</button>
      <button id="go">Next slide</button>
      <p id="txt">idle</p><p id="hid">shown</p></div></div>"""

BOX_SCRIPT = """<script>
window.__docClicks = 0;
document.addEventListener('click', () => { window.__docClicks++; });
const boxRoot = document.querySelector('.slide');
boxRoot.addEventListener('click', e => {
  const b = e.target.closest('.box');
  if (!b) return;
  boxRoot.querySelectorAll('.box').forEach(x => x.classList.toggle('sel', x === b));
  boxRoot.querySelector('#out').innerHTML = '<b>' + b.dataset.t + '</b>';
});
document.getElementById('go').addEventListener('click', () => deck.next());
document.getElementById('off').addEventListener('click', () => { window.__offClicks = (window.__offClicks || 0) + 1; });
</script>
</body>"""


def _box_deck():
    deck = _pen_deck("sidebar: false, pen: { fadeMs: 300 }")
    deck = deck.replace('<div class="slide-body"><p>Intro text for the first slide.</p></div></div>',
                        BOX_SLIDE, 1)
    return deck.replace("</body>", BOX_SCRIPT, 1)


PEN_DECKS = {
    "boxes.html": _box_deck(),
    "pen.html": _pen_deck("sidebar: false, pen: { fadeMs: 300 }"),
    "pen-43.html": _pen_deck("sidebar: false, pen: { fadeMs: 300 }", RATIO_43),
    "pen-nobadge.html": _pen_deck("sidebar: false, pen: { fadeMs: 300, audienceBadge: false }"),
    "pen-nocss.html": _pen_deck("sidebar: false", css=False),
    "lens.html": _lens_deck(),
    "lens-43.html": _lens_deck(RATIO_43),
}

# The lens circle and the slide point shown at its centre, read back from the
# clone transform: translate(tx, ty) scale(s) with the design canvas size.
LENS_INFO = """() => {
  const l = document.querySelector('.rp-lens');
  if (!l) return null;
  const r = l.getBoundingClientRect();
  const v = l.querySelector('.rp-lens-view');
  const m = /translate\\(([-\\d.e]+)px, ([-\\d.e]+)px\\) scale\\(([-\\d.e]+)\\)/.exec(v.style.transform || '');
  const cw = parseFloat(v.style.width), ch = parseFloat(v.style.height);
  const out = { hidden: l.hidden, cx: r.left + r.width / 2, cy: r.top + r.height / 2,
                w: r.width, parent: l.parentElement.id || l.parentElement.tagName };
  if (m) {
    const tx = +m[1], ty = +m[2], s = +m[3];
    out.sx = (r.width / 2 - tx) / (s * cw);
    out.sy = (r.height / 2 - ty) / (s * ch);
  }
  return out;
}"""


def _png_pixel(png):
    """RGB of a 1x1 8-bit PNG (any filter type is a no-op for a single pixel)."""
    pos, idat, depth, ctype = 8, b"", None, None
    while pos < len(png):
        n = int.from_bytes(png[pos:pos + 4], "big")
        kind, data = png[pos + 4:pos + 8], png[pos + 8:pos + 8 + n]
        if kind == b"IHDR":
            depth, ctype = data[8], data[9]
        elif kind == b"IDAT":
            idat += data
        pos += 12 + n
    assert depth == 8 and ctype in (2, 6), (depth, ctype)
    return tuple(zlib.decompress(idat)[1:4])

# Centroid of the inked pixels of #rp-pen-canvas, in CSS px relative to the canvas box.
INK = """() => {
  const c = document.getElementById('rp-pen-canvas');
  if (!c || !c.width || !c.height) return { n: 0 };
  const d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data;
  let n = 0, sx = 0, sy = 0;
  for (let y = 0; y < c.height; y++) {
    for (let x = 0; x < c.width; x++) {
      if (d[(y * c.width + x) * 4 + 3] > 0) { n++; sx += x; sy += y; }
    }
  }
  const r = c.getBoundingClientRect();
  if (!n) return { n: 0 };
  return { n, x: (sx / n + 0.5) * r.width / c.width, y: (sy / n + 0.5) * r.height / c.height };
}"""

BOX = """(sel) => {
  const r = document.querySelector(sel).getBoundingClientRect();
  return { x: r.left, y: r.top, w: r.width, h: r.height };
}"""


def _load_playwright():
    try:
        from playwright.sync_api import sync_playwright  # noqa: F401
        return sync_playwright
    except Exception:  # pragma: no cover - environment dependent
        return None


class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


class _PresenterBase(unittest.TestCase):
    page_name = "index.html"

    @classmethod
    def setUpClass(cls):
        sync_playwright = _load_playwright()
        if sync_playwright is None:
            raise unittest.SkipTest("playwright for Python is not installed")
        cls.tmp = tempfile.TemporaryDirectory(prefix="rp-presenter-")
        root = Path(cls.tmp.name)
        common = root / "common"
        common.mkdir()
        for f in ASSETS.iterdir():
            if f.suffix in (".js", ".css"):
                shutil.copy(f, common / f.name)
        (root / "index.html").write_text(DECK, encoding="utf-8")
        for name, deck in PEN_DECKS.items():
            (root / name).write_text(deck, encoding="utf-8")
        handler = functools.partial(_Quiet, directory=str(root))
        cls.httpd = socketserver.TCPServer(("127.0.0.1", 0), handler)
        threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()
        cls.base = f"http://127.0.0.1:{cls.httpd.server_address[1]}/"
        cls.url = cls.base + "index.html"
        cls.pw = sync_playwright().start()
        try:
            cls.browser = cls.pw.chromium.launch()
        except Exception as exc:  # pragma: no cover
            cls.pw.stop()
            cls.httpd.shutdown()
            raise unittest.SkipTest(f"chromium unavailable: {exc}")

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()
        cls.httpd.shutdown()
        cls.tmp.cleanup()

    def setUp(self):
        self.open_deck(self.page_name)

    def open_deck(self, name):
        if getattr(self, "ctx", None):
            self.ctx.close()
        self.ctx = self.browser.new_context(viewport={"width": 1600, "height": 900})
        self.page = self.ctx.new_page()
        self.page.set_default_timeout(5000)
        self.errors = []
        self.page.on("pageerror", lambda exc: self.errors.append(str(exc)))
        self.page.goto(self.base + name, wait_until="networkidle")
        self.page.wait_for_timeout(300)
        self.open_presenter()

    # The popup helper: plain P in the deck opens the presenter window.
    def open_presenter(self):
        with self.ctx.expect_page() as info:
            self.page.keyboard.press("p")
        self.pv = info.value
        self.pv.on("pageerror", lambda exc: self.errors.append(str(exc)))
        self.pv.set_viewport_size({"width": 1600, "height": 900})
        self.settle()

    def tearDown(self):
        self.ctx.close()
        self.ctx = None

    def settle(self):
        self.pv.wait_for_timeout(500)
        self.page.evaluate("() => window.__pvScaleUpdate && window.__pvScaleUpdate()")
        self.pv.wait_for_timeout(150)

    def goto(self, index):
        self.page.evaluate(f"() => deck.goTo({index})")
        self.settle()

    def assert_slide_sync(self, index):
        self.assertEqual(self.page.evaluate("() => deck.currentSlide"), index)
        self.page.wait_for_function("() => !deck.transitioning", timeout=5000)
        self.pv.wait_for_function(
            "index => document.getElementById('p-counter').textContent === `${index + 1} / 4`",
            arg=index, timeout=5000)

    def assert_fragment_sync(self, count):
        self.assert_slide_sync(2)
        self.assertEqual(self.page.locator(".slide.active .fragment.visible").count(), count)
        self.pv.wait_for_function(
            "count => document.querySelectorAll('#p-current .fragment.visible').length === count",
            arg=count, timeout=5000)



class PresenterPreviewTests(_PresenterBase):
    def test_preview_uses_deck_canvas(self):
        size = self.pv.evaluate(
            "() => { const s = document.querySelector('#p-current .slide-scaler');"
            " return [s.offsetWidth, s.offsetHeight]; }")
        self.assertEqual(size, [1920, 1080])

    def test_preview_root_font_matches_deck(self):
        deck_root = self.page.evaluate("() => getComputedStyle(document.documentElement).fontSize")
        pv_root = self.pv.evaluate("() => getComputedStyle(document.documentElement).fontSize")
        self.assertEqual(deck_root, "24px")
        self.assertEqual(pv_root, deck_root)
        deck_h2 = self.page.evaluate("() => getComputedStyle(document.querySelector('.slide.active h2')).fontSize")
        pv_h2 = self.pv.evaluate("() => getComputedStyle(document.querySelector('#p-current .slide h2')).fontSize")
        self.assertEqual(pv_h2, deck_h2)

    def test_preview_font_family_matches_deck(self):
        deck_ff = self.page.evaluate("() => getComputedStyle(document.querySelector('.slide.active h2')).fontFamily")
        pv_ff = self.pv.evaluate("() => getComputedStyle(document.querySelector('#p-current .slide h2')).fontFamily")
        self.assertEqual(pv_ff, deck_ff)

    def test_preview_keeps_slide_and_deck_classes(self):
        self.goto(1)
        cls = self.pv.evaluate("() => document.querySelector('#p-current .slide').className")
        self.assertIn("theme-dark", cls)
        deck_cls = self.pv.evaluate("() => document.querySelector('#p-current .slide-deck').className")
        self.assertIn("preset-paper", deck_cls)
        fit = self.pv.evaluate("() => document.querySelector('#p-current .slide-deck').getAttribute('data-fit')")
        self.assertEqual(fit, "auto")
        self.assertEqual(self.pv.evaluate("() => document.documentElement.lang"), "en")

    def test_preview_table_layout_matches_deck(self):
        self.goto(1)
        js = ("(sel) => { const t = document.querySelector(sel); const h = t.getBoundingClientRect().height;"
              " return Array.from(t.querySelectorAll('tr')).map(r => r.getBoundingClientRect().height / h); }")
        deck_r = self.page.evaluate(js, ".slide.active table")
        pv_r = self.pv.evaluate(js, "#p-current .slide table")
        self.assertEqual(len(deck_r), len(pv_r))
        for d, p in zip(deck_r, pv_r):
            self.assertAlmostEqual(d, p, delta=0.02)

    def test_next_preview_reveals_fragments(self):
        self.goto(1)
        counts = self.pv.evaluate(
            "() => { const f = document.querySelectorAll('#p-next .fragment');"
            " return [f.length, Array.from(f).filter(e => e.classList.contains('visible')).length]; }")
        self.assertEqual(counts[0], 2)
        self.assertEqual(counts[1], 2)

    def test_current_preview_keeps_reveal_state(self):
        self.goto(2)
        self.page.keyboard.press("ArrowRight")
        self.pv.wait_for_timeout(500)
        shown = self.pv.evaluate("() => document.querySelectorAll('#p-current .fragment.visible').length")
        self.assertEqual(shown, 1)

    def test_presenter_vertical_keys_reveal_reverse_and_leave_at_start(self):
        self.goto(2)
        self.assert_fragment_sync(0)
        for key, count in (("ArrowDown", 1), ("ArrowDown", 2),
                           ("ArrowUp", 1), ("ArrowUp", 0)):
            self.pv.keyboard.press(key)
            self.assert_fragment_sync(count)
        self.pv.keyboard.press("ArrowUp")
        self.assert_slide_sync(1)

    def test_presenter_vertical_keys_leave_only_after_last_fragment(self):
        self.goto(2)
        for count in (1, 2):
            self.pv.keyboard.press("ArrowDown")
            self.assert_fragment_sync(count)
        self.pv.keyboard.press("ArrowDown")
        self.assert_slide_sync(3)

    def test_presenter_vertical_keys_dispatch_canvas_steps(self):
        self.goto(1)
        self.page.evaluate("""() => {
            window.canvasCalls = [];
            window.canvasConsumes = true;
            deck.slides[1].__canvasStep = direction => {
                window.canvasCalls.push(direction);
                return window.canvasConsumes;
            };
        }""")
        for key in ("ArrowDown", "ArrowUp"):
            self.pv.keyboard.press(key)
            self.assert_slide_sync(1)
        self.assertEqual(self.page.evaluate("() => window.canvasCalls"), ["next", "prev"])
        self.page.evaluate("() => { window.canvasConsumes = false; }")
        self.pv.keyboard.press("ArrowDown")
        self.assert_slide_sync(2)
        self.assertEqual(self.page.evaluate("() => window.canvasCalls"), ["next", "prev", "next"])

    def test_presenter_slide_actions_take_precedence_and_allow_fallback(self):
        self.goto(1)
        self.page.evaluate("""() => {
            window.actionCalls = [];
            window.actionConsumes = true;
            deck.slides[1].__canvasStep = () => {
                window.actionCalls.push('canvas');
                return true;
            };
            deck.registerSlideAction(1, {
                down: () => {
                    window.actionCalls.push('down');
                    return window.actionConsumes ? undefined : false;
                },
                up: () => {
                    window.actionCalls.push('up');
                    return window.actionConsumes;
                }
            });
        }""")
        for key in ("ArrowDown", "ArrowUp"):
            self.pv.keyboard.press(key)
            self.assert_slide_sync(1)
        self.assertEqual(self.page.evaluate("() => window.actionCalls"), ["down", "up"])
        self.page.evaluate("() => { window.actionConsumes = false; }")
        self.pv.keyboard.press("ArrowDown")
        self.assert_slide_sync(2)
        self.goto(1)
        self.pv.keyboard.press("ArrowUp")
        self.assert_slide_sync(0)
        self.assertEqual(self.page.evaluate("() => window.actionCalls"), ["down", "up", "down", "up"])

    def test_presenter_vertical_keys_refresh_inline_style_tabs(self):
        self.goto(1)
        self.page.evaluate("""() => {
            const body = deck.slides[1].querySelector('.slide-body');
            body.innerHTML = '<div class="tab-bar"><button class="tab-btn">First</button>'
                + '<button class="tab-btn">Second</button></div>'
                + '<p data-tab-panel="0">First tab content</p>'
                + '<p data-tab-panel="1">Second tab content</p>';
            const buttons = body.querySelectorAll('.tab-btn');
            const panels = body.querySelectorAll('[data-tab-panel]');
            const select = index => {
                buttons.forEach((button, i) => button.style.background = i === index ? 'var(--accent)' : 'transparent');
                panels.forEach((panel, i) => panel.style.display = i === index ? 'block' : 'none');
            };
            buttons.forEach((button, index) => button.onclick = () => select(index));
            select(0);
            deck.presenterView.updatePresenterView();
        }""")
        for key, selected in (("ArrowDown", 1), ("ArrowUp", 0)):
            self.pv.keyboard.press(key)
            self.assert_slide_sync(1)
            for page, root in ((self.page, ".slide.active"), (self.pv, "#p-current")):
                page.wait_for_function("""([root, selected]) => {
                    const panels = document.querySelectorAll(root + ' [data-tab-panel]');
                    return panels.length === 2 && Array.from(panels).every(
                        (panel, i) => panel.style.display === (i === selected ? 'block' : 'none'));
                }""", arg=[root, selected], timeout=5000)

    def test_presenter_vertical_keys_cycle_compare_and_refresh_preview(self):
        self.goto(1)
        self.page.evaluate("""() => {
            const body = deck.slides[1].querySelector('.slide-body');
            body.innerHTML = '<div class="compare-toggle"><button class="compare-btn active">Before</button>'
                + '<button class="compare-btn">After</button></div><p data-compare-content>Before details</p>';
            const buttons = body.querySelectorAll('.compare-btn');
            buttons.forEach(button => button.onclick = () => {
                buttons.forEach(other => other.classList.toggle('active', other === button));
                body.querySelector('[data-compare-content]').textContent = button.textContent + ' details';
            });
            deck.presenterView.updatePresenterView();
        }""")
        for key, label in (("ArrowDown", "After"), ("ArrowUp", "Before")):
            self.pv.keyboard.press(key)
            self.assert_slide_sync(1)
            for page, root in ((self.page, ".slide.active"), (self.pv, "#p-current")):
                page.wait_for_function("""([root, label]) => {
                    const active = document.querySelector(root + ' .compare-btn.active');
                    const details = document.querySelector(root + ' [data-compare-content]');
                    return active.textContent === label && details.textContent === label + ' details';
                }""", arg=[root, label], timeout=5000)

    def test_presenter_respects_remapped_navigation_keys(self):
        self.goto(2)
        self.page.evaluate("() => { deck.keyMappings.j = 'down'; deck.keyMappings.k = 'up'; }")
        self.pv.keyboard.press("j")
        self.assert_fragment_sync(1)
        self.pv.keyboard.press("k")
        self.assert_fragment_sync(0)
        self.page.evaluate("() => { deck.keyMappings.ArrowDown = 'prev'; }")
        self.pv.keyboard.press("ArrowDown")
        self.assert_slide_sync(1)

    def test_presenter_step_closes_main_search_and_reveals_fragment(self):
        self.goto(2)
        self.page.keyboard.press("Control+K")
        self.page.wait_for_function("() => document.body.classList.contains('rp-search-open')")
        self.pv.keyboard.press("ArrowDown")
        self.assert_fragment_sync(1)
        self.assertFalse(self.page.evaluate("() => document.body.classList.contains('rp-search-open')"))

    def test_presenter_step_closes_main_detail_and_runs_slide_action(self):
        self.goto(3)
        self.page.evaluate("""() => {
            deck.registerSlideAction(3, {
                down: () => { deck.slides[3].querySelector('h2').textContent = 'Detail advanced'; }
            });
        }""")
        self.page.click('.slide.active .rp-detail')
        self.page.wait_for_function("() => document.body.classList.contains('rp-detail-open')")
        self.pv.keyboard.press("ArrowDown")
        self.assert_slide_sync(3)
        self.assertFalse(self.page.evaluate("() => document.body.classList.contains('rp-detail-open')"))
        self.assertEqual(self.page.locator('.slide.active h2').text_content(), 'Detail advanced')
        self.pv.wait_for_function(
            "() => document.querySelector('#p-current h2').textContent === 'Detail advanced'", timeout=5000)

    def test_presenter_right_space_and_left_preserve_fragments(self):
        self.goto(2)
        for key, count in (("ArrowRight", 1), ("Space", 2),
                           ("ArrowLeft", 1), ("ArrowLeft", 0)):
            self.pv.keyboard.press(key)
            self.assert_fragment_sync(count)

    def test_presenter_editable_controls_do_not_navigate(self):
        self.goto(2)
        self.pv.evaluate("""() => {
            const controls = document.createElement('div');
            controls.innerHTML = '<input id="keyboard-input">'
                + '<textarea id="keyboard-textarea"></textarea>'
                + '<select id="keyboard-select"><option>One</option><option>Two</option></select>'
                + '<div id="keyboard-editable" contenteditable="true">Editable notes</div>';
            document.body.appendChild(controls);
        }""")
        for selector in ("#keyboard-input", "#keyboard-textarea", "#keyboard-select", "#keyboard-editable"):
            with self.subTest(control=selector):
                self.pv.focus(selector)
                for key in ("ArrowDown", "ArrowUp", "ArrowRight", "ArrowLeft", "Space"):
                    self.pv.keyboard.press(key)
                    self.assert_fragment_sync(0)

    def test_presenter_chrome_size_unchanged(self):
        fs = self.pv.evaluate("() => getComputedStyle(document.querySelector('.presenter-timer')).fontSize")
        self.assertEqual(fs, "24px")

    def test_next_preview_after_going_back_is_visible(self):
        self.goto(1)
        self.page.keyboard.press("ArrowLeft")
        self.settle()
        cls = self.pv.evaluate("() => document.querySelector('#p-next .slide').className")
        for bad in ("leaving", "entering", "transition-"):
            self.assertNotIn(bad, cls)
        self.assertEqual(self.pv.evaluate("() => getComputedStyle(document.querySelector('#p-next .slide')).opacity"), "1")

    def test_preview_hides_detail_affordances(self):
        self.goto(3)
        res = self.pv.evaluate(
            "() => { const t = document.querySelector('#p-current .rp-detail'); const a = getComputedStyle(t, '::after');"
            " return [getComputedStyle(t).textDecorationLine, a.visibility, a.content]; }")
        self.assertEqual(res[0], "none")
        self.assertTrue(res[1] == "hidden" or res[2] in ("none", "normal"), res)



class PresenterPenTests(_PresenterBase):
    page_name = "pen.html"

    # --- helpers ---------------------------------------------------------
    def state(self):
        return self.page.evaluate("() => DeckPen.controller.active")

    def preview_box(self):
        return self.pv.evaluate(BOX, "#p-current .slide-scaler")

    def deck_box(self):
        return self.page.evaluate(BOX, ".slide-deck")

    def stroke(self, page, box, fx, fy, half=0.04):
        y = box["y"] + box["h"] * fy
        page.mouse.move(box["x"] + box["w"] * (fx - half), y)
        page.mouse.down()
        page.mouse.move(box["x"] + box["w"] * (fx + half), y, steps=6)
        page.mouse.up()
        page.wait_for_timeout(120)

    def clear(self):
        self.page.evaluate("() => { DeckPen.controller.model.clear(deck.currentSlide); DeckPen.controller.redraw(); }")

    def assert_ink_at(self, page, box, fx, fy):
        ink = page.evaluate(INK)
        self.assertGreater(ink["n"], 0, "canvas has ink")
        self.assertAlmostEqual(ink["x"], box["w"] * fx, delta=2)
        self.assertAlmostEqual(ink["y"], box["h"] * fy, delta=2)

    def assert_canvas_over_preview(self):
        canvas = self.pv.evaluate(BOX, "#rp-pen-canvas")
        preview = self.preview_box()
        for key in ("x", "y", "w", "h"):
            self.assertAlmostEqual(canvas[key], preview[key], delta=1, msg=key)

    def assert_round_trip(self, points=((0.5, 0.5), (0.25, 0.7))):
        self.assert_canvas_over_preview()
        for fx, fy in points:
            with self.subTest(source="presenter", point=(fx, fy)):
                self.clear()
                self.stroke(self.pv, self.preview_box(), fx, fy)
                self.assert_ink_at(self.page, self.deck_box(), fx, fy)
                self.assert_ink_at(self.pv, self.preview_box(), fx, fy)
            with self.subTest(source="deck", point=(fx, fy)):
                self.clear()
                self.stroke(self.page, self.deck_box(), fx, fy)
                self.assert_ink_at(self.pv, self.preview_box(), fx, fy)
        self.assertEqual(self.errors, [])

    # --- tests -----------------------------------------------------------
    def test_presenter_ink_survives_preview_rerender(self):
        self.goto(2)
        self.pv.keyboard.press("Alt+KeyO")
        self.assertTrue(self.state())
        self.stroke(self.pv, self.preview_box(), 0.4, 0.4)
        self.assertGreater(self.pv.evaluate(INK)["n"], 0)
        self.page.evaluate("() => deck.presenterView.updatePresenterView()")
        self.settle()
        self.page.keyboard.press("ArrowRight")
        self.assert_fragment_sync(1)
        self.pv.wait_for_timeout(300)
        attached = self.pv.evaluate("""() => {
          const c = document.getElementById('rp-pen-canvas');
          return [c.isConnected, c.parentElement.id, Boolean(c.closest('#p-current'))];
        }""")
        self.assertEqual(attached, [True, "p-current-wrap", False])
        self.assert_ink_at(self.pv, self.preview_box(), 0.4, 0.4)
        self.assert_canvas_over_preview()
        # A splitter drag resizes #p-current; the canvas realigns over the preview.
        split = self.pv.evaluate(BOX, "#splitter-v")
        sx, sy = split["x"] + split["w"] / 2, split["y"] + split["h"] / 2
        self.pv.mouse.move(sx, sy)
        self.pv.mouse.down()
        self.pv.mouse.move(sx - 300, sy, steps=5)
        self.pv.mouse.up()
        self.pv.wait_for_timeout(200)
        self.assert_canvas_over_preview()
        self.assert_ink_at(self.pv, self.preview_box(), 0.4, 0.4)
        self.pv.set_viewport_size({"width": 1100, "height": 760})
        self.pv.wait_for_timeout(300)
        self.assert_canvas_over_preview()
        self.assert_ink_at(self.pv, self.preview_box(), 0.4, 0.4)
        self.assertEqual(self.errors, [])

    def test_ink_drawn_in_presenter_appears_in_deck_window_at_same_slide_position(self):
        self.pv.keyboard.press("Alt+KeyO")
        self.stroke(self.pv, self.preview_box(), 0.5, 0.5)
        self.assert_ink_at(self.page, self.deck_box(), 0.5, 0.5)
        pts = self.page.evaluate("() => DeckPen.controller.model.visible(0)[0].points.map(p => [p.x, p.y])")
        box = self.deck_box()
        for x, y in pts:
            self.assertAlmostEqual(y * box["h"], 0.5 * box["h"], delta=2)
        self.assertAlmostEqual((pts[0][0] + pts[-1][0]) / 2 * box["w"], 0.5 * box["w"], delta=2)

    def test_ink_position_matches_across_windows_and_ratios(self):
        self.pv.keyboard.press("Alt+KeyO")
        self.assert_round_trip()
        self.pv.set_viewport_size({"width": 900, "height": 1000})
        self.pv.wait_for_timeout(300)
        self.assert_round_trip()
        self.open_deck("pen-43.html")
        self.assertEqual(self.page.evaluate(
            "() => { const r = document.querySelector('.slide-deck').getBoundingClientRect();"
            " return Math.round(r.width / r.height * 100); }"), 133)
        self.assertEqual(self.pv.evaluate(
            "() => document.querySelector('#p-current .slide-scaler').offsetWidth"), 1440)
        self.pv.keyboard.press("Alt+KeyO")
        self.assert_round_trip()
        self.pv.set_viewport_size({"width": 1500, "height": 600})
        self.pv.wait_for_timeout(300)
        self.assert_round_trip()

    def test_presenter_keys_toggle_pen_and_navigation_still_works(self):
        self.page.evaluate("""() => {
          window.__changes = 0;
          DeckPen.controller.onChange(() => { window.__changes++; });
        }""")
        self.pv.keyboard.press("Alt+KeyP")
        self.assertTrue(self.state())
        self.assertEqual(self.page.evaluate("() => DeckPen.controller.model.mode"), "laser")
        self.assertEqual(self.page.evaluate("() => window.__changes"), 1, "handled exactly once")
        self.pv.keyboard.press("ArrowRight")
        self.assert_slide_sync(1)
        self.assertTrue(self.state())
        self.pv.keyboard.press("Alt+KeyO")
        self.assertEqual(self.page.evaluate("() => DeckPen.controller.model.mode"), "pen")
        self.pv.keyboard.press("Alt+Digit3")
        self.assertEqual(self.page.evaluate("() => DeckPen.controller.model.size"), 3)
        self.pv.keyboard.press("Escape")
        self.assertFalse(self.state())
        self.pv.keyboard.press("Alt+KeyP")
        self.pv.keyboard.press("Alt+KeyP")
        self.assertFalse(self.state())
        self.pv.keyboard.press("ArrowLeft")
        self.assert_slide_sync(0)
        self.pv.keyboard.press("Space")
        self.assert_slide_sync(1)
        self.assertEqual(len(self.ctx.pages), 2, "no extra window opened")
        self.assertEqual(self.errors, [])

    def test_presenter_badge_always_visible_when_pen_on(self):
        for name in ("pen.html", "pen-nobadge.html"):
            with self.subTest(page=name):
                if name != self.page_name:
                    self.open_deck(name)
                badge = self.pv.locator("#rp-pen-badge")
                self.assertFalse(badge.is_visible())
                self.pv.keyboard.press("Alt+KeyI")
                self.assertTrue(badge.is_visible())
                self.assertIn("Highlighter", badge.inner_text())
                self.assertEqual(self.page.locator("#rp-pen-badge").is_visible(),
                                 name == "pen.html")
                info = self.pv.evaluate("""() => {
                  const b = document.getElementById('rp-pen-badge');
                  const r = b.getBoundingClientRect();
                  const p = document.querySelector('#p-current .slide-scaler').getBoundingClientRect();
                  return { overlay: b.classList.contains('rp-overlay-ui'),
                           inside: r.left >= p.left && r.top >= p.top && r.right <= p.right,
                           inPreview: Boolean(b.closest('#p-current')),
                           pointer: getComputedStyle(b).pointerEvents };
                }""")
                self.assertEqual(info, {"overlay": True, "inside": True,
                                        "inPreview": False, "pointer": "none"})
                self.pv.keyboard.press("Escape")
                self.assertFalse(badge.is_visible())

    def test_presenter_canvas_is_overlay_ui_and_pointer_inert_when_off(self):
        info = self.pv.evaluate("""() => {
          const c = document.getElementById('rp-pen-canvas');
          return { overlay: c.classList.contains('rp-overlay-ui'),
                   pen: c.classList.contains('rp-pen-canvas'),
                   parent: c.parentElement.id,
                   position: getComputedStyle(c).position,
                   pointer: getComputedStyle(c).pointerEvents,
                   penLinks: document.querySelectorAll('link[href$="deck-pen.css"]').length };
        }""")
        self.assertEqual(info, {"overlay": True, "pen": True, "parent": "p-current-wrap",
                                "position": "fixed", "pointer": "none", "penLinks": 1})
        self.pv.keyboard.press("Alt+KeyO")
        self.assertEqual(self.pv.evaluate(
            "() => getComputedStyle(document.getElementById('rp-pen-canvas')).pointerEvents"), "auto")
        # Clicking the preview while pen mode is on draws instead of doing anything else.
        self.stroke(self.pv, self.preview_box(), 0.5, 0.3)
        self.assertEqual(self.page.evaluate("() => deck.currentSlide"), 0)

    def test_presenter_gets_pen_styles_when_the_deck_does_not_link_them(self):
        self.open_deck("pen-nocss.html")
        info = self.pv.evaluate("""() => ({
          penLinks: document.querySelectorAll('link[href$="deck-pen.css"]').length,
          position: getComputedStyle(document.getElementById('rp-pen-canvas')).position
        })""")
        self.assertEqual(info, {"penLinks": 1, "position": "fixed"})

    def test_closing_presenter_window_keeps_deck_ink(self):
        self.page.keyboard.press("Alt+KeyO")
        self.stroke(self.page, self.deck_box(), 0.3, 0.3)
        self.stroke(self.pv, self.preview_box(), 0.6, 0.6)
        self.assertEqual(self.page.evaluate("() => DeckPen.controller.model.visible(0).length"), 2)
        self.assertEqual(self.page.evaluate("() => DeckPen.controller.surfaceCount()"), 2)
        before = self.page.evaluate(INK)["n"]
        self.pv.close()
        self.page.wait_for_function("() => deck.presenterView._pen === null", timeout=3000)
        self.assertEqual(self.page.evaluate("() => DeckPen.controller.surfaceCount()"), 1)
        self.assertEqual(self.page.evaluate("() => DeckPen.controller.model.visible(0).length"), 2)
        self.page.evaluate("() => DeckPen.controller.redraw()")
        self.assertEqual(self.page.evaluate(INK)["n"], before)
        self.stroke(self.page, self.deck_box(), 0.5, 0.8)
        self.assertEqual(self.page.evaluate("() => DeckPen.controller.model.visible(0).length"), 3)
        self.assertTrue(self.state(), "pen mode survives the close")
        # Reopening attaches a fresh surface that shows the existing ink.
        self.open_presenter()
        self.assertEqual(self.page.evaluate("() => DeckPen.controller.surfaceCount()"), 2)
        self.assertGreater(self.pv.evaluate(INK)["n"], 0)
        self.assertTrue(self.pv.locator("#rp-pen-badge").is_visible())
        self.assertEqual(self.errors, [])

    def test_presenter_surface_draws_with_its_own_frames_and_idles(self):
        self.pv.evaluate("""() => {
          window.__raf = 0;
          const orig = window.requestAnimationFrame.bind(window);
          window.requestAnimationFrame = f => { window.__raf++; return orig(f); };
        }""")
        self.pv.keyboard.press("Alt+KeyP")
        self.stroke(self.pv, self.preview_box(), 0.5, 0.5)
        self.assertGreater(self.pv.evaluate("() => window.__raf"), 0, "presenter frames while drawing")
        self.pv.wait_for_timeout(700)
        self.assertEqual(self.pv.evaluate(INK)["n"], 0, "laser fades in the presenter too")
        self.pv.evaluate("() => { window.__raf = 0; }")
        self.pv.wait_for_timeout(250)
        self.assertEqual(self.pv.evaluate("() => window.__raf"), 0, "no presenter frames when idle")


class PresenterLensTests(_PresenterBase):
    page_name = "lens.html"
    MARK = (0, 170, 0)

    # --- helpers ---------------------------------------------------------
    def preview_box(self):
        return self.pv.evaluate(BOX, "#p-current .slide-scaler")

    def deck_box(self):
        return self.page.evaluate(BOX, ".slide-deck")

    def frac(self, selector):
        """Centre of a live slide element as 0..1 slide coordinates."""
        return self.page.evaluate("""(sel) => {
          const d = document.querySelector('.slide-deck').getBoundingClientRect();
          const r = document.querySelector('.slide-deck ' + sel).getBoundingClientRect();
          return [(r.left + r.width / 2 - d.left) / d.width, (r.top + r.height / 2 - d.top) / d.height];
        }""", selector)

    def hover(self, page, box, fx, fy):
        x, y = box["x"] + box["w"] * fx, box["y"] + box["h"] * fy
        page.mouse.move(x - 4, y - 4)
        page.mouse.move(x, y, steps=3)
        page.wait_for_timeout(150)

    @staticmethod
    def pixel(page, x, y):
        png = page.screenshot(clip={"x": int(x), "y": int(y), "width": 1, "height": 1})
        return _png_pixel(png)

    def assertColor(self, actual, expected, msg=None, tol=16):
        self.assertTrue(all(abs(a - e) <= tol for a, e in zip(actual, expected)),
                        f"{msg or ''}: {actual} != {expected}")

    def lenses(self):
        return self.page.evaluate(LENS_INFO), self.pv.evaluate(LENS_INFO)

    def assert_lens_at(self, info, box, fx, fy, label, clamped=False):
        """The lens shows slide point (fx, fy): within 2 px in that window's slide pixels."""
        self.assertIsNotNone(info, label + " lens exists")
        self.assertFalse(info["hidden"], label + " lens visible")
        self.assertAlmostEqual(info["sx"] * box["w"], fx * box["w"], delta=2, msg=label + " slide x")
        self.assertAlmostEqual(info["sy"] * box["h"], fy * box["h"], delta=2, msg=label + " slide y")
        if not clamped:
            self.assertAlmostEqual(info["cx"], box["x"] + fx * box["w"], delta=2, msg=label + " centre x")
            self.assertAlmostEqual(info["cy"], box["y"] + fy * box["h"], delta=2, msg=label + " centre y")

    def assert_mirrored(self, label):
        mark = self.frac("#lens-mark")
        for source in ("presenter", "deck"):
            for fx, fy, clamped in ((mark[0], mark[1], False), (0.03, 0.96, True)):
                with self.subTest(ratio=label, source=source, point=(round(fx, 3), round(fy, 3))):
                    page = self.pv if source == "presenter" else self.page
                    box = self.preview_box() if source == "presenter" else self.deck_box()
                    self.hover(page, box, fx, fy)
                    deck_lens, pv_lens = self.lenses()
                    dbox, pbox = self.deck_box(), self.preview_box()
                    self.assert_lens_at(deck_lens, dbox, fx, fy, "deck", clamped)
                    self.assert_lens_at(pv_lens, pbox, fx, fy, "presenter", clamped)
                    # Same slide point in both windows, in deck pixels.
                    self.assertAlmostEqual(deck_lens["sx"] * dbox["w"], pv_lens["sx"] * dbox["w"], delta=2)
                    self.assertAlmostEqual(deck_lens["sy"] * dbox["h"], pv_lens["sy"] * dbox["h"], delta=2)
                    if not clamped:
                        self.assertColor(self.pixel(self.page, deck_lens["cx"], deck_lens["cy"]),
                                         self.MARK, "deck lens shows the marker")
                        self.assertColor(self.pixel(self.pv, pv_lens["cx"], pv_lens["cy"]),
                                         self.MARK, "presenter lens shows the marker")

    # --- tests -----------------------------------------------------------
    def test_lens_mirrors_between_windows(self):
        self.pv.keyboard.press("Alt+KeyY")
        self.assertEqual(self.page.evaluate("() => DeckPen.controller.model.mode"), "magnifier")
        self.assert_mirrored("16:9")
        self.pv.set_viewport_size({"width": 1100, "height": 760})
        self.pv.wait_for_timeout(300)
        self.assert_mirrored("16:9 presenter resized")
        self.open_deck("lens-43.html")
        self.assertEqual(self.pv.evaluate(
            "() => document.querySelector('#p-current .slide-scaler').offsetWidth"), 1440)
        self.page.keyboard.press("Alt+KeyY")
        self.assert_mirrored("4:3")
        self.assertEqual(self.errors, [])

    def test_presenter_lens_survives_preview_rerender(self):
        self.goto(2)
        self.pv.keyboard.press("Alt+KeyY")
        self.hover(self.pv, self.preview_box(), 0.5, 0.5)
        before = self.pv.evaluate(LENS_INFO)
        self.assertFalse(before["hidden"])
        self.assertEqual(before["parent"], "p-current-wrap")
        self.page.evaluate("() => deck.presenterView.updatePresenterView()")
        self.settle()
        self.page.keyboard.press("ArrowRight")
        self.assert_fragment_sync(1)
        self.pv.wait_for_timeout(300)
        after = self.pv.evaluate(LENS_INFO)
        self.assertFalse(after["hidden"], "lens still visible after the re-render")
        self.assertEqual(after["parent"], "p-current-wrap")
        self.assertEqual(self.pv.evaluate("""() => ({
          lenses: document.querySelectorAll('.rp-lens').length,
          inPreview: Boolean(document.querySelector('.rp-lens').closest('#p-current')),
          fragments: document.querySelectorAll('.rp-lens .fragment.visible').length })"""),
            {"lenses": 1, "inPreview": False, "fragments": 1})
        for key in ("cx", "cy", "sx", "sy"):
            self.assertAlmostEqual(after[key], before[key], delta=1, msg=key)
        self.assertEqual(self.errors, [])

    def test_closing_presenter_window_keeps_deck_lens(self):
        self.page.keyboard.press("Alt+KeyY")
        mark = self.frac("#lens-mark")
        self.hover(self.page, self.deck_box(), *mark)
        deck_lens, pv_lens = self.lenses()
        self.assertFalse(deck_lens["hidden"])
        self.assertFalse(pv_lens["hidden"])
        self.assertEqual(self.page.evaluate("() => DeckPen.controller.surfaceCount()"), 2)
        self.pv.close()
        self.page.wait_for_function("() => deck.presenterView._pen === null", timeout=3000)
        self.assertEqual(self.page.evaluate("() => DeckPen.controller.surfaceCount()"), 1)
        self.assertEqual(self.page.evaluate("() => document.querySelectorAll('.rp-lens').length"), 1)
        self.hover(self.page, self.deck_box(), 0.4, 0.4)
        self.assert_lens_at(self.page.evaluate(LENS_INFO), self.deck_box(), 0.4, 0.4, "deck after close")
        self.assertEqual(self.page.evaluate("() => DeckPen.controller.model.mode"), "magnifier")
        # Reopening attaches a fresh surface with its own lens at the shared position.
        self.open_presenter()
        self.assertEqual(self.page.evaluate("() => DeckPen.controller.surfaceCount()"), 2)
        self.hover(self.page, self.deck_box(), *mark)
        pv_lens = self.pv.evaluate(LENS_INFO)
        self.assert_lens_at(pv_lens, self.preview_box(), mark[0], mark[1], "presenter after reopen")
        self.assertEqual(self.pv.evaluate("() => document.querySelectorAll('.rp-lens').length"), 1)
        self.assertColor(self.pixel(self.pv, pv_lens["cx"], pv_lens["cy"]), self.MARK)
        self.assertEqual(self.errors, [])

    def test_lens_svg_id_references_in_both_windows(self):
        """The clone drops ids; url(#id) and <use href> still resolve in both windows."""
        self.pv.keyboard.press("Alt+KeyY")
        for selector, colour in (("#lens-svg-grad", (0, 120, 255)), ("#lens-svg-use", (255, 140, 0))):
            fx, fy = self.frac(selector)
            for source in ("presenter", "deck"):
                with self.subTest(selector=selector, source=source):
                    page = self.pv if source == "presenter" else self.page
                    box = self.preview_box() if source == "presenter" else self.deck_box()
                    self.hover(page, box, fx, fy)
                    deck_lens, pv_lens = self.lenses()
                    self.assertColor(self.pixel(self.page, deck_lens["cx"], deck_lens["cy"]), colour, "deck")
                    self.assertColor(self.pixel(self.pv, pv_lens["cx"], pv_lens["cy"]), colour, "presenter")


class PresenterPreviewMirrorTests(_PresenterBase):
    """Clicks in the current-slide preview reach the live slide; live changes reach the preview."""
    page_name = "boxes.html"

    def live_state(self):
        return self.page.evaluate("""() => ({
          sel: Array.from(document.querySelectorAll('.slide-deck .box')).map(b => b.classList.contains('sel')),
          out: document.querySelector('.slide-deck #out').textContent,
          clicks: window.__docClicks })""")

    def test_clicking_a_box_in_the_presenter_preview_selects_it_in_the_deck_window(self):
        self.pv.locator("#p-current .box .lbl").click()
        self.page.wait_for_function(
            "() => document.querySelector('.slide-deck #out').textContent === 'Beta detail'", timeout=3000)
        state = self.live_state()
        self.assertEqual(state["sel"], [False, True, False])
        self.assertEqual(state["out"], "Beta detail")
        # The preview re-renders to the same state as the live slide.
        self.pv.wait_for_function("""() => {
          const boxes = document.querySelectorAll('#p-current .box');
          return boxes.length === 3 && boxes[1].classList.contains('sel') &&
                 !boxes[0].classList.contains('sel') &&
                 document.querySelector('#p-current #out').innerHTML === '<b>Beta detail</b>';
        }""", timeout=3000)
        # A second click on another box moves the selection.
        self.pv.locator("#p-current .box").nth(2).click()
        self.page.wait_for_function(
            "() => document.querySelector('.slide-deck #out').textContent === 'Gamma detail'", timeout=3000)
        self.assertEqual(self.live_state()["sel"], [False, False, True])
        self.pv.wait_for_function(
            "() => document.querySelectorAll('#p-current .box')[2].classList.contains('sel')", timeout=3000)
        self.assertEqual(self.errors, [])

    def test_clicking_a_link_or_the_next_preview_does_not_forward(self):
        pv_url = self.pv.url
        deck_hash = self.page.evaluate("() => location.hash")
        self.pv.locator("#p-current #link").click()
        self.pv.locator("#p-current #off").dispatch_event("click")
        self.pv.locator("#p-next .slide h2").click()
        self.pv.locator("#p-next .slide td").first.click()
        # A click on the letterbox around the clone is outside the slide.
        self.pv.evaluate("() => document.getElementById('p-current').click()")
        self.pv.wait_for_timeout(300)
        self.assertEqual(self.live_state()["clicks"], 0, "nothing reached the deck window")
        self.assertEqual(self.page.evaluate("() => window.__offClicks || 0"), 0)
        self.assertEqual(self.page.evaluate("() => location.hash"), deck_hash)
        self.assertEqual(self.pv.url, pv_url, "presenter window did not navigate")
        self.assertEqual(self.page.evaluate("() => deck.currentSlide"), 0)
        # A forwardable box click does reach the deck (control for the zero count above).
        self.pv.locator("#p-current .box").first.click()
        self.page.wait_for_function("() => window.__docClicks === 1", timeout=3000)
        self.assertEqual(self.errors, [])

    def test_text_only_changes_in_the_deck_window_reach_the_preview(self):
        self.page.evaluate("() => { document.querySelector('.slide-deck #txt').textContent = 'changed'; }")
        self.pv.wait_for_function(
            "() => document.querySelector('#p-current #txt').textContent === 'changed'", timeout=300)
        self.page.evaluate("() => { document.querySelector('.slide-deck #hid').style.display = 'none'; }")
        self.pv.wait_for_function(
            "() => getComputedStyle(document.querySelector('#p-current #hid')).display === 'none'", timeout=300)
        self.page.evaluate("() => { document.querySelector('.slide-deck #txt').firstChild.data = 'data'; }")
        self.pv.wait_for_function(
            "() => document.querySelector('#p-current #txt').textContent === 'data'", timeout=300)
        self.assertEqual(self.errors, [])

    def test_preview_rerender_rate_is_bounded_under_continuous_mutation(self):
        self.page.evaluate("""() => {
          const pv = deck.presenterView;
          const orig = pv._renderSlidePreview.bind(pv);
          window.__renders = 0;
          pv._renderSlidePreview = (doc, container, slide, revealAll) => {
            if (container.id === 'p-current') window.__renders++;
            return orig(doc, container, slide, revealAll);
          };
          const txt = document.querySelector('.slide-deck #txt');
          let n = 0;
          const timer = setInterval(() => { txt.textContent = 'tick ' + (++n); }, 10);
          setTimeout(() => { clearInterval(timer); window.__last = txt.textContent; }, 600);
        }""")
        self.page.wait_for_timeout(900)
        renders = self.page.evaluate("() => window.__renders")
        self.assertGreaterEqual(renders, 1)
        self.assertLessEqual(renders, 8)
        last = self.page.evaluate("() => window.__last")
        self.pv.wait_for_function(
            "last => document.querySelector('#p-current #txt').textContent === last", arg=last, timeout=1000)
        self.assertEqual(self.errors, [])

    def press_box(self, index):
        box = self.pv.evaluate(BOX, f"#p-current .box:nth-child({index + 1})")
        self.pv.mouse.move(box["x"] + box["w"] / 2, box["y"] + box["h"] / 2)
        self.pv.mouse.down()

    def force_preview_render(self):
        self.page.evaluate("""() => {
          const pv = deck.presenterView;
          const doc = pv.presenterWindow.document;
          pv._renderSlidePreview(doc, doc.getElementById('p-current'), deck.slides[deck.currentSlide], false);
        }""")

    def test_click_forwarding_survives_a_rerender_between_press_and_release(self):
        self.press_box(1)
        old = self.pv.evaluate_handle("() => document.querySelectorAll('#p-current .box')[1]")
        self.force_preview_render()
        self.pv.mouse.up()
        self.page.wait_for_function(
            "() => document.querySelector('.slide-deck #out').textContent === 'Beta detail'", timeout=3000)
        self.pv.wait_for_timeout(300)
        # The render requested during the press ran once after the release.
        self.assertFalse(self.pv.evaluate("el => el.isConnected", old), "the preview re-rendered")
        self.assertTrue(self.pv.evaluate(
            "() => document.querySelectorAll('#p-current .box')[1].classList.contains('sel')"))
        state = self.live_state()
        self.assertEqual(state["sel"], [False, True, False])
        self.assertEqual(state["clicks"], 1, "the live box is clicked exactly once")
        # A later keyboard-style click (no press) still resolves at click time.
        self.pv.evaluate("() => document.querySelectorAll('#p-current .box')[2].click()")
        self.page.wait_for_function(
            "() => document.querySelector('.slide-deck #out').textContent === 'Gamma detail'", timeout=3000)
        self.assertEqual(self.live_state()["clicks"], 2)
        self.assertEqual(self.errors, [])

    def test_deferred_render_does_not_repaint_a_previous_slide_after_a_click_navigates(self):
        # Record the title of every preview render in the presenter window.
        self.pv.evaluate("""() => {
          window.__titles = [];
          const c = document.getElementById('p-current');
          new MutationObserver(() => {
            const h = c.querySelector('.slide h2');
            if (h) window.__titles.push(h.textContent);
          }).observe(c, { childList: true });
        }""")
        box = self.pv.evaluate(BOX, "#p-current #go")
        self.pv.mouse.move(box["x"] + box["w"] / 2, box["y"] + box["h"] / 2)
        self.pv.mouse.down()
        # A live mutation during the press requests a (deferred) preview render.
        self.page.evaluate("() => { document.querySelector('.slide-deck #txt').textContent = 'pressed'; }")
        self.pv.wait_for_timeout(250)
        self.pv.mouse.up()
        self.page.wait_for_function("() => deck.currentSlide === 1 && !deck.transitioning", timeout=5000)
        self.pv.wait_for_timeout(400)
        titles = self.pv.evaluate("() => window.__titles")
        self.assertIn("Routing choices", titles)
        after = titles[titles.index("Routing choices"):]
        self.assertNotIn("First slide", after, f"the previous slide was repainted: {titles}")
        self.assertEqual(self.pv.evaluate(
            "() => document.querySelector('#p-current .slide h2').textContent"), "Routing choices")
        self.assertEqual(self.errors, [])

    def test_press_then_slide_change_then_release_forwards_nothing(self):
        self.press_box(1)
        self.force_preview_render()
        self.page.evaluate("() => deck.goTo(1)")
        self.page.wait_for_function("() => !deck.transitioning", timeout=5000)
        self.pv.wait_for_timeout(300)
        self.pv.mouse.up()
        self.pv.wait_for_function(
            "() => document.querySelector('#p-current .slide h2').textContent === 'Routing choices'",
            timeout=3000)
        self.pv.wait_for_timeout(300)
        self.assertEqual(self.live_state()["clicks"], 0)
        self.page.evaluate("() => deck.goTo(0)")
        self.page.wait_for_function("() => !deck.transitioning", timeout=5000)
        state = self.live_state()
        self.assertEqual(state["sel"], [False, False, False])
        self.assertEqual(state["out"], "none")
        self.assertEqual(state["clicks"], 0)
        self.assertEqual(self.errors, [])

    def test_pen_mode_clicks_do_not_forward(self):
        self.pv.keyboard.press("Alt+KeyO")
        self.assertTrue(self.page.evaluate("() => DeckPen.controller.active"))
        box = self.pv.evaluate(BOX, "#p-current .box:nth-child(2)")
        self.pv.mouse.click(box["x"] + box["w"] / 2, box["y"] + box["h"] / 2)
        # Even a click that reaches the preview element is not forwarded in pen mode.
        self.pv.evaluate("() => document.querySelectorAll('#p-current .box')[1].click()")
        self.pv.wait_for_timeout(300)
        state = self.live_state()
        self.assertEqual(state["sel"], [False, False, False])
        self.assertEqual(state["out"], "none")
        self.assertEqual(state["clicks"], 0)
        # Leaving pen mode restores forwarding.
        self.pv.keyboard.press("Escape")
        self.assertFalse(self.page.evaluate("() => DeckPen.controller.active"))
        self.pv.locator("#p-current .box").nth(1).click()
        self.page.wait_for_function(
            "() => document.querySelector('.slide-deck #out').textContent === 'Beta detail'", timeout=3000)
        self.assertEqual(self.errors, [])


if __name__ == "__main__":
    result = unittest.main(exit=False, verbosity=2).result
    if result.skipped and result.testsRun <= len(result.skipped):
        print("SKIPPED-ALL")
    sys.exit(0 if result.wasSuccessful() else 1)
