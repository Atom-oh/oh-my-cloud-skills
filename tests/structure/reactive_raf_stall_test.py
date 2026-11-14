"""Browser regressions: animation steps still draw while the deck window gets no animation frames.

A window behind the focused one (the deck window while the presenter window has focus) can stop
receiving requestAnimationFrame callbacks. The tests hold the frame callbacks back to model that,
then send the Down key from the presenter window. Skips (exit 0) when Playwright for Python or its
Chromium is unavailable; the TAP wrapper reports that as a SKIP.
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
<html lang="en"><head><meta charset="UTF-8"><title>raf stall fixture</title>
<link rel="stylesheet" href="./common/theme.css"></head>
<body>
<div class="slide-deck">
  <div class="slide"><div class="slide-header"><h2>Intro</h2></div><div class="slide-body"><p>first</p></div></div>
  <div class="slide"><div class="slide-header"><h2>Canvas steps</h2></div>
    <div class="slide-body"><canvas id="c1" width="200" height="100"></canvas></div></div>
</div>
<script src="./common/animation-utils.js"></script>
<script src="./common/slide-framework.js"></script>
<script src="./common/presenter-view.js"></script>
<script>
const deck = new SlideFramework({ sidebar: false });
const state = { step: 0, drawnStep: -1, draws: 0, lastElapsed: 0 };
const tl = new TimelineAnimation(
  [0.2, 0.5, 0.8].map((at, i) => ({ at, action: () => { state.step = i + 1; } })), 5);
const c = document.getElementById('c1'), ctx = c.getContext('2d');
const loop = new AnimationLoop((elapsed) => {
  ctx.fillStyle = 'rgb(' + state.step * 60 + ',0,0)';
  ctx.fillRect(0, 0, c.width, c.height);
  state.drawnStep = state.step; state.draws++; state.lastElapsed = elapsed;
});
loop.start();
deck.registerSlideAction(1, { down: () => tl.nextStep(), up: () => tl.prevStep() });
window.__state = state; window.__loop = loop;
</script></body></html>
"""

HOLD = """() => {
  window.__orig = window.requestAnimationFrame.bind(window);
  window.__held = [];
  window.requestAnimationFrame = (cb) => { window.__held.push(cb); return window.__held.length; };
}"""
RELEASE = """() => {
  const held = window.__held; window.__held = [];
  window.requestAnimationFrame = window.__orig;
  held.forEach(cb => window.__orig(cb));
}"""


def _load_playwright():
    try:
        from playwright.sync_api import sync_playwright
        return sync_playwright
    except Exception:  # pragma: no cover
        return None


class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


class FrameStallTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sync_playwright = _load_playwright()
        if sync_playwright is None:
            raise unittest.SkipTest("playwright for Python is not installed")
        cls.tmp = tempfile.TemporaryDirectory(prefix="rp-raf-stall-")
        root = Path(cls.tmp.name)
        (root / "common").mkdir()
        for f in ASSETS.iterdir():
            if f.suffix in (".js", ".css"):
                shutil.copy(f, root / "common" / f.name)
        (root / "index.html").write_text(DECK, encoding="utf-8")
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
        with self.ctx.expect_page() as info:
            self.page.keyboard.press("n")
        self.pv = info.value
        self.pv.set_viewport_size({"width": 1600, "height": 900})
        self.pv.wait_for_timeout(600)
        self.page.evaluate("() => deck.goTo(1)")
        self.page.wait_for_function("() => !deck.transitioning")
        self.pv.wait_for_timeout(300)
        self.pv.bring_to_front()

    def tearDown(self):
        self.assertEqual(self.errors, [])

    def snap(self):
        return self.page.evaluate("""() => {
          const c = document.getElementById('c1');
          const px = c.getContext('2d').getImageData(10, 10, 1, 1).data;
          return { step: __state.step, drawnStep: __state.drawnStep, draws: __state.draws,
                   red: px[0], fallback: __loop.fallbackDraws || 0,
                   active: AnimationLoop.active ? AnimationLoop.active.size : 0 };
        }""")

    def down(self, wait=250):
        self.pv.keyboard.press("ArrowDown")
        self.pv.wait_for_timeout(wait)

    def test_step_draws_with_running_frames(self):
        self.down()
        s = self.snap()
        self.assertEqual((s["step"], s["red"]), (1, 60))

    def test_step_draws_immediately_while_frames_are_held(self):
        self.page.evaluate(HOLD)
        self.page.wait_for_timeout(100)
        # 60 ms is below the 100 ms fallback tick: only the immediate draw can explain the pixel.
        self.down(wait=60)
        s = self.snap()
        self.assertEqual((s["step"], s["red"]), (1, 60))
        self.down(wait=60)
        s = self.snap()
        self.assertEqual((s["step"], s["red"]), (2, 120))
        self.assertEqual(s["drawnStep"], 2)

    def test_up_key_redraws_while_frames_are_held(self):
        self.down()
        self.down()
        self.page.evaluate(HOLD)
        self.page.wait_for_timeout(100)
        self.pv.keyboard.press("ArrowUp")
        self.pv.wait_for_timeout(60)
        s = self.snap()
        self.assertEqual((s["step"], s["red"]), (1, 60))

    def test_fallback_timer_keeps_drawing_while_frames_are_held(self):
        self.page.evaluate(HOLD)
        before = self.snap()["draws"]
        self.page.wait_for_timeout(700)
        after = self.snap()
        self.assertGreaterEqual(after["draws"] - before, 3)
        self.assertGreater(after["fallback"], 0)

    def test_elapsed_time_is_wall_clock_while_frames_are_held(self):
        self.page.evaluate(HOLD)
        self.page.wait_for_timeout(800)
        elapsed = self.page.evaluate("() => __state.lastElapsed")
        started = self.page.evaluate("() => (performance.now() - __loop.startTime) / 1000")
        self.assertGreater(elapsed, 0.5)
        self.assertLess(abs(started - elapsed), 0.3)

    def test_fallback_is_idle_while_frames_arrive(self):
        self.page.wait_for_timeout(700)
        self.assertEqual(self.snap()["fallback"], 0)

    def test_stop_releases_timer_and_registration(self):
        self.page.evaluate("() => __loop.stop()")
        self.page.evaluate(HOLD)
        before = self.snap()
        self.page.wait_for_timeout(500)
        after = self.snap()
        self.assertEqual(before["draws"], after["draws"])
        self.assertEqual(after["active"], 0)
        self.down(wait=60)
        self.assertEqual(self.snap()["draws"], before["draws"])

    def test_restart_does_not_leak_timers(self):
        self.page.evaluate("() => { __loop.restart(); __loop.restart(); }")
        self.page.evaluate(HOLD)
        before = self.snap()["draws"]
        self.page.wait_for_timeout(1000)
        delta = self.snap()["draws"] - before
        # One 100 ms timer: about 10 draws a second. Leaked timers would multiply that.
        self.assertLessEqual(delta, 12)
        self.assertGreaterEqual(delta, 6)


if __name__ == "__main__":
    result = unittest.main(exit=False, verbosity=2).result
    if result.skipped and result.testsRun <= len(result.skipped):
        print("SKIPPED-ALL")
    sys.exit(0 if result.wasSuccessful() else 1)
