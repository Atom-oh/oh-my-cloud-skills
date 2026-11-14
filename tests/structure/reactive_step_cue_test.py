"""Browser regressions for the presenter step cue (reactive-presentation).

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
from pathlib import Path

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "plugins/aws-content-plugin/skills/reactive-presentation/assets"

DECK = """<!DOCTYPE html>
<html lang="%(lang)s">
<head>
<meta charset="UTF-8">
<title>Step cue fixture</title>
<link rel="stylesheet" href="./common/theme.css">
<link rel="stylesheet" href="./common/deck-pen.css">
</head>
<body>
<div class="slide-deck">
  <div class="slide" data-remarp-id="s1"><div class="slide-header"><h2>Action</h2></div>
    <div class="slide-body"><p>action</p></div></div>
  <div class="slide" data-remarp-id="s2"><div class="slide-header"><h2>Plain</h2></div>
    <div class="slide-body"><p>plain</p></div></div>
  <div class="slide" data-remarp-id="s3"><div class="slide-header"><h2>Fragments</h2></div>
    <div class="slide-body"><p class="fragment" data-fragment-index="1">a</p><p class="fragment" data-fragment-index="2">b</p><p class="fragment" data-fragment-index="3">c</p></div></div>
  <div class="slide" data-remarp-id="s4"><div class="slide-header"><h2>Stateless</h2></div>
    <div class="slide-body"><p>stateless</p></div></div>
</div>
<script src="./common/animation-utils.js"></script>
<script src="./common/deck-pen.js"></script>
<script src="./common/slide-framework.js"></script>
<script src="./common/presenter-view.js"></script>
<script>
const deck = new SlideFramework({ sidebar: false });
let n = 0;
deck.registerSlideAction(0, {
  down: () => (n < 2 ? (n++, true) : false),
  up: () => (n > 0 ? (n--, true) : false),
  state: () => ({ cur: n, total: 2 }),
});
deck.registerSlideAction(3, { down: () => true, up: () => true });
</script>
</body>
</html>
"""


def _load_playwright():
    try:
        from playwright.sync_api import sync_playwright
        return sync_playwright
    except Exception:  # pragma: no cover
        return None


class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


class _Base(unittest.TestCase):
    LANG = "ko"

    @classmethod
    def setUpClass(cls):
        sync_playwright = _load_playwright()
        if sync_playwright is None:
            raise unittest.SkipTest("playwright for Python is not installed")
        cls.tmp = tempfile.TemporaryDirectory(prefix="rp-step-cue-")
        root = Path(cls.tmp.name)
        common = root / "common"
        common.mkdir()
        for f in ASSETS.iterdir():
            if f.suffix in (".js", ".css"):
                shutil.copy(f, common / f.name)
        (root / "index.html").write_text(DECK % {"lang": cls.LANG}, encoding="utf-8")
        handler = functools.partial(_Quiet, directory=str(root))
        cls.httpd = socketserver.TCPServer(("127.0.0.1", 0), handler)
        threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()
        cls.url = f"http://127.0.0.1:{cls.httpd.server_address[1]}/index.html"
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
        self.ctx = self.browser.new_context(viewport={"width": 1600, "height": 900})
        self.addCleanup(self.ctx.close)
        self.errors = []
        self.page = self.ctx.new_page()
        self.page.set_default_timeout(5000)
        self.page.on("pageerror", lambda exc: self.errors.append(str(exc)))
        self.page.goto(self.url, wait_until="networkidle")
        self.page.wait_for_timeout(300)
        self.open_presenter()

    def tearDown(self):
        self.assertEqual(self.errors, [])

    def open_presenter(self):
        with self.ctx.expect_page() as info:
            self.page.keyboard.press("n")
        self.pv = info.value
        self.pv.on("pageerror", lambda exc: self.errors.append(str(exc)))
        self.pv.set_viewport_size({"width": 1600, "height": 900})
        self.pv.wait_for_function(
            "() => document.getElementById('p-counter').textContent.startsWith('1 /')", timeout=5000)

    def goto(self, index):
        self.page.evaluate(f"() => deck.goTo({index})")
        self.page.wait_for_function("() => !deck.transitioning", timeout=5000)
        self.pv.wait_for_function(
            "i => document.getElementById('p-counter').textContent.startsWith(`${i + 1} /`)",
            arg=index, timeout=5000)

    def cue(self):
        return self.pv.evaluate("() => document.getElementById('p-step-cue').textContent")

    def wait_cue(self, text):
        self.pv.wait_for_function(
            "t => document.getElementById('p-step-cue') && document.getElementById('p-step-cue').textContent === t",
            arg=text, timeout=5000)


# WCAG contrast of an element's computed text color against the first opaque
# background up its ancestor chain (its own background for a filled badge).
CONTRAST_JS = """sel => {
  const el = document.querySelector(sel);
  const rgb = c => (c.match(/[\\d.]+/g) || []).map(Number);
  const lum = ([r, g, b]) => {
    const f = v => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b);
  };
  let bgEl = el, bg = null;
  while (bgEl) {
    const c = rgb(getComputedStyle(bgEl).backgroundColor);
    if (c.length >= 3 && (c.length < 4 || c[3] === 1)) { bg = c; break; }
    bgEl = bgEl.parentElement;
  }
  const fg = rgb(getComputedStyle(el).color);
  const [a, b] = [lum(fg), lum(bg)].sort((x, y) => y - x);
  return { ratio: (a + 0.05) / (b + 0.05), fg: getComputedStyle(el).color, bg: String(bg) };
}"""


class StepCueKoTests(_Base):
    def contrast(self, sel):
        return self.pv.evaluate(CONTRAST_JS, sel)

    def test_cue_contrast_default_theme(self):
        self.wait_cue("↓ 다음 단계 있음 (지금 0/2)")
        more = self.contrast("#p-step-cue")
        self.assertGreaterEqual(more["ratio"], 4.5, more)
        self.goto(1)
        self.wait_cue("✓ 단계 없음, 누르면 다음 슬라이드")
        plain = self.contrast("#p-step-cue")
        self.assertGreaterEqual(plain["ratio"], 4.5, plain)


    def test_cue_for_action_slide_updates_on_down(self):
        self.wait_cue("↓ 다음 단계 있음 (지금 0/2)")
        self.assertEqual(self.pv.get_attribute("#p-step-cue", "data-more"), "1")
        self.assertEqual(self.pv.get_attribute("#p-step-cue", "role"), "status")
        self.page.keyboard.press("ArrowDown")
        self.wait_cue("↓ 다음 단계 있음 (지금 1/2)")
        self.page.keyboard.press("ArrowDown")
        self.wait_cue("✓ 마지막 단계 (2/2), 누르면 다음 슬라이드")
        self.assertEqual(self.pv.get_attribute("#p-step-cue", "data-more"), "0")

    def test_cue_none(self):
        self.goto(1)
        self.wait_cue("✓ 단계 없음, 누르면 다음 슬라이드")
        self.assertEqual(self.pv.get_attribute("#p-step-cue", "data-more"), "0")

    def test_cue_fragment_variant(self):
        self.goto(2)
        self.wait_cue("→ 다음 항목 있음 (0/3)")
        self.page.keyboard.press("ArrowDown")
        self.wait_cue("→ 다음 항목 있음 (1/3)")
        self.page.keyboard.press("ArrowDown")
        self.page.keyboard.press("ArrowDown")
        self.wait_cue("✓ 마지막 단계 (3/3), 누르면 다음 슬라이드")

    def test_cue_action_without_state(self):
        self.goto(3)
        self.wait_cue("↓ 이 장에 단계가 있음")

    def test_cue_updates_when_main_window_pressed(self):
        self.page.bring_to_front()
        self.page.keyboard.press("ArrowDown")
        self.wait_cue("↓ 다음 단계 있음 (지금 1/2)")

    def test_cue_survives_state_throwing(self):
        self.page.evaluate("() => deck.registerSlideAction(0, {down: () => true, up: () => true, state: () => { throw new Error('x'); }})")
        self.page.evaluate("() => deck.presenterView.updatePresenterView()")
        self.wait_cue("↓ 이 장에 단계가 있음")

    def test_no_duplicate_box_after_reopen(self):
        self.pv.close()
        self.page.wait_for_timeout(200)
        self.open_presenter()
        self.assertEqual(self.pv.evaluate("() => document.querySelectorAll('#p-step-cue').length"), 1)
        self.page.keyboard.press("ArrowDown")
        self.wait_cue("↓ 다음 단계 있음 (지금 1/2)")

    def test_no_errors_after_close(self):
        self.pv.close()
        self.page.wait_for_timeout(200)
        self.page.keyboard.press("ArrowDown")
        self.page.keyboard.press("ArrowDown")
        self.page.wait_for_timeout(500)
        self.assertEqual(self.errors, [])


class StepCueEnTests(_Base):
    LANG = "en"

    def test_cue_english_when_lang_en(self):
        self.wait_cue("↓ more steps (now 0/2)")
        self.page.keyboard.press("ArrowDown")
        self.page.keyboard.press("ArrowDown")
        self.wait_cue("✓ last step (2/2), the next press moves on")
        self.goto(1)
        self.wait_cue("✓ no steps, the next press moves on")
        self.goto(2)
        self.wait_cue("→ more items (0/3)")
        self.goto(3)
        self.wait_cue("↓ this slide has steps")


class StepMarkBadgeTests(_Base):
    def set_note(self, text):
        self.page.evaluate("t => { deck.presenterNotes[1] = t; }", text)
        self.page.evaluate("() => deck.presenterView.updatePresenterView()")
        self.pv.wait_for_function("t => document.getElementById('p-notes').textContent.length > 0", arg=text)

    def marks(self):
        return self.pv.evaluate("() => document.querySelectorAll('#p-notes .rp-step-mark').length")

    def test_marks_become_badges(self):
        self.set_note("A↓ B↓")
        self.assertEqual(self.marks(), 2)
        self.assertEqual(self.pv.get_attribute("#p-notes .rp-step-mark", "title"), "여기서 ↓")

    def test_marks_in_meta_lines_stay_plain(self):
        self.set_note("[요약] 한 줄↓")
        self.assertEqual(self.marks(), 0)
        self.assertIn("↓", self.pv.inner_text("#p-notes"))
        self.set_note("대본↓\n[출처] x↓\n[약어] y↓\n끝 {여기↓} 다시↓")
        self.assertEqual(self.marks(), 2)

    def test_block_form_meta_layer_stays_plain(self):
        self.set_note("[요약]\n• 요점↓\n- 둘째↓\n\n대본↓")
        self.assertEqual(self.marks(), 1)
        self.set_note("[출처]\n  * 문서↓\n대본입니다.↓ 다음↓")
        self.assertEqual(self.marks(), 2)
        self.set_note("[요약]\n• 요점\n\n• 대본 줄↓")
        self.assertEqual(self.marks(), 1)

    def test_mark_after_closing_brace_is_badge(self):
        self.set_note("{timing: 2}↓\n앞 {cue: 여기↓} 뒤")
        self.assertEqual(self.marks(), 1)

    def test_badge_contrast(self):
        self.set_note("A↓")
        got = self.pv.evaluate(CONTRAST_JS, "#p-notes .rp-step-mark")
        self.assertGreaterEqual(got["ratio"], 4.5, got)

    def test_html_still_escaped(self):
        self.set_note("<b>↓</b>")
        self.assertEqual(self.marks(), 1)
        self.assertEqual(self.pv.evaluate("() => document.querySelectorAll('#p-notes b').length"), 0)
        self.assertIn("<b>", self.pv.inner_text("#p-notes"))

    def test_note_edit_still_works(self):
        self.set_note("A↓ B")
        self.pv.click("#p-note-edit")
        self.assertEqual(self.pv.input_value("#p-notes textarea"), "A↓ B")
        self.pv.fill("#p-notes textarea", "C↓ D↓")
        self.pv.click("#p-note-edit")
        self.assertEqual(self.marks(), 2)


class StepMarkBadgeEnTests(_Base):
    LANG = "en"

    def test_english_title(self):
        self.page.evaluate("() => { deck.presenterNotes[1] = 'A↓'; deck.presenterView.updatePresenterView(); }")
        self.pv.wait_for_selector("#p-notes .rp-step-mark")
        self.assertEqual(self.pv.get_attribute("#p-notes .rp-step-mark", "title"), "press ↓ here")


if __name__ == "__main__":
    result = unittest.main(exit=False, verbosity=2).result
    if result.skipped and result.testsRun <= len(result.skipped):
        print("SKIPPED-ALL")
    sys.exit(0 if result.wasSuccessful() else 1)
