"""Browser regressions for the deck-window pen overlay; skips without Playwright/Chromium."""
import sys
import unittest

sys.dont_write_bytecode = True

from reactive_overlay_fixture import DeckOverlayFixture

# A deck may bind plain digits through window.__remarpKeys; the pen must leave them alone.
KEYS = "<script>window.__remarpKeys = { '3': 'last' };</script>\n"

SLIDES_PEN = """<div class="slide-deck">
  <div class="slide"><div class="slide-header"><h2>One</h2></div><div class="slide-body"><p>a</p><input id="pen-input" type="text"></div></div>
  <div class="slide"><div class="slide-header"><h2>Two</h2></div><div class="slide-body"><p>b</p></div></div>
  <div class="slide"><div class="slide-header"><h2>Three</h2></div><div class="slide-body"><p>c</p></div></div>
</div>
"""

CHORD = """([code, key]) => {
  const target = document.activeElement || document.body;
  const ev = new KeyboardEvent('keydown', { code, key, altKey: true, bubbles: true, cancelable: true });
  target.dispatchEvent(ev);
  return ev.defaultPrevented;
}"""

INKED = """() => {
  const c = document.getElementById('rp-pen-canvas');
  if (!c.width || !c.height) return 0;
  const d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data;
  let n = 0;
  for (let i = 3; i < d.length; i += 4) if (d[i] > 0) n++;
  return n;
}"""


class DeckPenTests(DeckOverlayFixture):
    overlay_modules = ("pen",)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        for name, opts in (("pen.html", "sidebar: false, pen: { fadeMs: 300 }"),
                           ("pen-nobadge.html",
                            "sidebar: false, pen: { fadeMs: 300, audienceBadge: false }")):
            (cls.root / name).write_text(
                cls.page_head + KEYS + SLIDES_PEN + cls.page_scripts % opts, encoding="utf-8")

    def open_pen(self, name="pen.html"):
        page = self.open(name)
        self.popups = []
        page.on("popup", lambda popup: self.popups.append(popup))
        return page

    # --- helpers ---------------------------------------------------------
    @staticmethod
    def chord(page, code, key):
        return page.evaluate(CHORD, [code, key])

    @staticmethod
    def state(page):
        return page.evaluate("""() => {
          const c = DeckPen.controller;
          return { active: c.active, mode: c.model.mode, size: c.model.size,
                   colorIndex: c.model.colorIndex };
        }""")

    @staticmethod
    def inked(page):
        return page.evaluate(INKED)

    @staticmethod
    def deck_point(page, fx, fy):
        box = page.evaluate("""() => {
          const r = document.querySelector('.slide-deck').getBoundingClientRect();
          return { x: r.left, y: r.top, w: r.width, h: r.height };
        }""")
        return box["x"] + box["w"] * fx, box["y"] + box["h"] * fy

    def stroke(self, page, points):
        x, y = self.deck_point(page, *points[0])
        page.mouse.move(x, y)
        page.mouse.down()
        for fx, fy in points[1:]:
            x, y = self.deck_point(page, fx, fy)
            page.mouse.move(x, y, steps=5)
        page.mouse.up()

    # --- tests -----------------------------------------------------------
    def test_option_p_toggles_pen_and_does_not_open_presenter(self):
        page = self.open_pen()
        self.assertTrue(self.chord(page, "KeyP", "π"))
        self.assertEqual(self.state(page)["active"], True)
        self.assertEqual(self.state(page)["mode"], "laser")
        self.assertTrue(self.chord(page, "KeyP", "p"))
        self.assertEqual(self.state(page)["active"], False)
        # The real Linux/Windows path: Alt+P reports key 'p'.
        page.keyboard.press("Alt+KeyP")
        self.assertEqual(self.state(page)["active"], True)
        page.keyboard.press("Alt+KeyP")
        self.assertEqual(self.state(page)["active"], False)
        page.wait_for_timeout(300)
        self.assertEqual(self.popups, [])
        self.assertEqual(len(self.ctx.pages), 1)

    def test_option_chords_do_not_trigger_framework_keys(self):
        page = self.open_pen()
        for code, key in (("KeyO", "o"), ("KeyI", "i"), ("KeyU", "u"), ("KeyY", "y"),
                          ("KeyT", "t"), ("Digit1", "1"), ("Digit4", "4"), ("Digit3", "3")):
            self.assertTrue(self.chord(page, code, key), code)
        page.keyboard.press("Alt+KeyO")
        page.wait_for_timeout(300)
        self.assertEqual(self.popups, [])
        self.assertFalse(page.evaluate(
            "() => document.querySelector('.slide-deck').classList.contains('overview-mode')"))
        self.assertEqual(self.active(page), 0)

    def test_plain_keys_keep_working_in_pen_mode(self):
        page = self.open_pen()
        page.keyboard.press("Alt+KeyO")
        self.assertTrue(self.state(page)["active"])
        page.keyboard.press("o")
        self.assertTrue(page.evaluate(
            "() => document.querySelector('.slide-deck').classList.contains('overview-mode')"))
        page.keyboard.press("o")
        self.assertFalse(page.evaluate(
            "() => document.querySelector('.slide-deck').classList.contains('overview-mode')"))
        self.assertTrue(self.state(page)["active"])
        page.keyboard.press("3")
        page.wait_for_timeout(450)
        self.assertEqual(self.active(page), 2)
        page.evaluate("""() => {
          window.__escSeen = 0;
          document.addEventListener('keydown', e => { if (e.key === 'Escape') window.__escSeen++; });
        }""")
        page.keyboard.press("Escape")
        self.assertFalse(self.state(page)["active"])
        self.assertEqual(page.evaluate("() => window.__escSeen"), 0,
                         "Esc that leaves pen mode is consumed")
        page.keyboard.press("Escape")
        self.assertEqual(page.evaluate("() => window.__escSeen"), 1,
                         "Esc while pen mode is off reaches the framework")
        page.keyboard.press("ArrowLeft")
        page.wait_for_timeout(450)
        self.assertEqual(self.active(page), 1)

    def test_drawing_in_pen_mode_paints_the_canvas_and_does_not_navigate(self):
        page = self.open_pen()
        self.assertEqual(self.inked(page), 0)
        page.keyboard.press("Alt+KeyO")
        self.stroke(page, [(0.3, 0.5), (0.5, 0.55), (0.7, 0.5)])
        page.wait_for_timeout(100)
        self.assertGreater(self.inked(page), 0)
        x, y = self.deck_point(page, 0.5, 0.3)
        page.mouse.click(x, y)
        page.wait_for_timeout(450)
        self.assertEqual(self.active(page), 0)
        self.assertEqual(page.evaluate("() => DeckPen.controller.model.visible(0).length"), 2)

    def test_laser_fades_and_pen_persists(self):
        page = self.open_pen()
        page.keyboard.press("Alt+KeyP")
        self.stroke(page, [(0.2, 0.2), (0.4, 0.2)])
        self.assertGreater(self.inked(page), 0)
        page.wait_for_timeout(450)
        self.assertEqual(self.inked(page), 0, "laser ink fades out")
        page.keyboard.press("Alt+KeyO")
        self.stroke(page, [(0.2, 0.6), (0.4, 0.6)])
        page.wait_for_timeout(450)
        pen_pixels = self.inked(page)
        self.assertGreater(pen_pixels, 0, "pen ink persists")
        page.keyboard.press("Alt+KeyP")
        self.stroke(page, [(0.6, 0.3), (0.8, 0.3)])
        page.keyboard.press("ArrowRight")
        page.wait_for_timeout(450)
        self.assertEqual(self.active(page), 1)
        self.assertEqual(self.inked(page), 0)
        page.keyboard.press("ArrowLeft")
        page.wait_for_timeout(450)
        self.assertEqual(self.active(page), 0)
        self.assertEqual(self.inked(page), pen_pixels)
        self.assertEqual(page.evaluate(
            "() => DeckPen.controller.model.visible(0).map(s => s.mode)"), ["pen"])

    def test_mode_size_colour_keys(self):
        page = self.open_pen()
        page.keyboard.press("Alt+KeyO")
        page.keyboard.press("Alt+Digit3")
        page.keyboard.press("Alt+Digit5")
        self.assertEqual(self.state(page),
                         {"active": True, "mode": "pen", "size": 3, "colorIndex": 1})
        page.keyboard.press("Alt+Digit9")
        self.assertEqual(self.state(page)["colorIndex"], 5)
        page.keyboard.press("Alt+Digit1")
        self.assertEqual(self.state(page)["size"], 1)
        page.keyboard.press("Escape")
        self.assertFalse(self.state(page)["active"])
        page.keyboard.press("Alt+KeyI")
        self.assertEqual(self.state(page)["active"], True)
        self.assertEqual(self.state(page)["mode"], "highlighter")
        # Pen was set to black; the Highlighter keeps its own default yellow.
        self.assertEqual(self.state(page)["colorIndex"], 1)
        page.keyboard.press("Alt+KeyO")
        self.assertEqual(self.state(page)["colorIndex"], 5)
        page.keyboard.press("Alt+KeyI")
        page.keyboard.press("Alt+KeyU")
        self.assertEqual(self.state(page)["mode"], "eraser")
        self.assertEqual(page.evaluate(
            "() => document.getElementById('rp-pen-canvas').style.cursor"), "cell")
        page.keyboard.press("Alt+KeyP")
        self.assertEqual(self.state(page)["mode"], "laser")
        self.assertTrue(self.state(page)["active"])

    def test_eraser_removes_one_stroke_and_option_t_clears(self):
        page = self.open_pen()
        page.keyboard.press("Alt+KeyO")
        self.stroke(page, [(0.2, 0.3), (0.6, 0.3)])
        self.stroke(page, [(0.2, 0.7), (0.6, 0.7)])
        visible = "() => DeckPen.controller.model.visible(0).length"
        self.assertEqual(page.evaluate(visible), 2)
        page.keyboard.press("Alt+KeyU")
        self.stroke(page, [(0.4, 0.25), (0.4, 0.35)])
        self.assertEqual(page.evaluate(visible), 1)
        self.assertEqual(page.evaluate(
            "() => DeckPen.controller.model.visible(0)[0].points[0].y"), 0.7)
        page.keyboard.press("Alt+KeyO")
        self.stroke(page, [(0.2, 0.5), (0.6, 0.5)])
        self.assertEqual(page.evaluate(visible), 2)
        page.keyboard.press("Alt+KeyT")
        page.wait_for_timeout(100)
        self.assertEqual(page.evaluate(visible), 0)
        self.assertEqual(self.inked(page), 0)

    def test_clear_moved_to_option_t_and_digits_mean_zoom_in_magnifier(self):
        page = self.open_pen()
        visible = "() => DeckPen.controller.model.visible(0).length"
        zoom = "() => DeckPen.controller.model.zoom"
        page.keyboard.press("Alt+KeyO")
        page.keyboard.press("Alt+Digit3")
        page.keyboard.press("Alt+Digit7")
        self.stroke(page, [(0.2, 0.3), (0.6, 0.3)])
        self.assertEqual(page.evaluate(visible), 1)
        page.keyboard.press("Escape")
        self.assertFalse(self.state(page)["active"])
        # Option+Y selects the Magnifier, turns pen mode on and keeps the ink.
        self.assertTrue(self.chord(page, "KeyY", "y"))
        self.assertEqual(self.state(page)["active"], True)
        self.assertEqual(self.state(page)["mode"], "magnifier")
        page.keyboard.press("Alt+KeyY")
        page.wait_for_timeout(100)
        self.assertEqual(self.state(page)["mode"], "magnifier", "Option+Y is not a toggle")
        self.assertTrue(self.state(page)["active"])
        self.assertEqual(page.evaluate(visible), 1, "Option+Y no longer clears ink")
        self.assertGreater(self.inked(page), 0)
        # Drawing in Magnifier mode creates no stroke.
        self.stroke(page, [(0.2, 0.6), (0.6, 0.6)])
        self.assertEqual(page.evaluate(visible), 1)
        # Digits 1-3 are zoom only; 4-9 are consumed and change nothing.
        self.assertEqual(page.evaluate(zoom), 2)
        self.assertTrue(self.chord(page, "Digit2", "2"))
        self.assertEqual(page.evaluate(zoom), 3)
        self.assertEqual(self.state(page)["size"], 3, "pen size unchanged")
        page.keyboard.press("Alt+Digit1")
        self.assertEqual(page.evaluate(zoom), 2)
        page.keyboard.press("Alt+Digit3")
        self.assertEqual(page.evaluate(zoom), 4)
        page.keyboard.press("Alt+Digit2")
        self.assertEqual(page.evaluate(zoom), 3)
        self.assertTrue(self.chord(page, "Digit5", "5"))
        self.assertEqual(page.evaluate(zoom), 3)
        self.assertEqual(self.state(page)["size"], 3)
        self.assertEqual(self.state(page)["colorIndex"], 3, "Option+5 left the colours alone")
        # Back to Pen: the previous size and colour return.
        page.keyboard.press("Alt+KeyO")
        self.assertEqual(self.state(page),
                         {"active": True, "mode": "pen", "size": 3, "colorIndex": 3})
        # Zoom is remembered across modes.
        page.keyboard.press("Alt+KeyY")
        self.assertEqual(page.evaluate(zoom), 3)
        # Option+T clears all ink on the current slide.
        page.keyboard.press("Alt+KeyT")
        page.wait_for_timeout(100)
        self.assertEqual(page.evaluate(visible), 0)
        self.assertEqual(self.inked(page), 0)
        self.assertEqual(self.state(page)["mode"], "magnifier")

    def test_badge_shows_magnifier_and_zoom(self):
        page = self.open_pen()
        label = "() => document.querySelector('#rp-pen-badge .rp-pen-label').textContent"
        swatch = """() => {
          const s = document.querySelector('#rp-pen-badge .rp-pen-swatch');
          return { hidden: s.hidden, neutral: s.classList.contains('rp-pen-swatch-neutral'),
                   inline: s.style.backgroundColor };
        }"""
        page.keyboard.press("Alt+KeyY")
        self.assertTrue(page.locator("#rp-pen-badge").is_visible())
        self.assertEqual(page.evaluate(label), "Magnifier 2x")
        self.assertEqual(page.evaluate(swatch), {"hidden": False, "neutral": True, "inline": ""})
        page.keyboard.press("Alt+Digit3")
        self.assertEqual(page.evaluate(label), "Magnifier 4x")
        page.keyboard.press("Alt+Digit2")
        self.assertEqual(page.evaluate(label), "Magnifier 3x")
        page.keyboard.press("Alt+KeyO")
        self.assertEqual(page.evaluate(label), "Pen, medium")
        info = page.evaluate(swatch)
        self.assertFalse(info["neutral"])
        self.assertNotEqual(info["inline"], "")
        page.keyboard.press("Alt+KeyY")
        self.assertEqual(page.evaluate(label), "Magnifier 3x")

    def test_changing_mode_hides_the_lens_state(self):
        page = self.open_pen()
        lens = "() => Object.assign({}, DeckPen.controller.lens)"
        self.assertEqual(page.evaluate(lens)["visible"], False)
        page.keyboard.press("Alt+KeyY")
        changes = page.evaluate("""() => {
          window.__changes = 0;
          DeckPen.controller.onChange(() => { window.__changes++; });
          DeckPen.controller.setLens(0.25, 0.75, true);
          return window.__changes;
        }""")
        self.assertEqual(changes, 1, "setLens emits a change")
        self.assertEqual(page.evaluate(lens), {"x": 0.25, "y": 0.75, "visible": True})
        # Option+Y again keeps Magnifier and does not hide the lens.
        page.keyboard.press("Alt+KeyY")
        self.assertTrue(page.evaluate(lens)["visible"])
        # Zoom keys do not hide it either.
        page.keyboard.press("Alt+Digit2")
        self.assertTrue(page.evaluate(lens)["visible"])
        for code in ("KeyP", "KeyO", "KeyI", "KeyU"):
            page.keyboard.press("Alt+KeyY")
            page.evaluate("() => DeckPen.controller.setLens(0.5, 0.5, true)")
            page.keyboard.press("Alt+" + code)
            self.assertFalse(page.evaluate(lens)["visible"], code)
            self.assertTrue(self.state(page)["active"], code)
        page.keyboard.press("Alt+KeyY")
        page.evaluate("() => DeckPen.controller.setLens(0.5, 0.5, true)")
        page.keyboard.press("Escape")
        self.assertFalse(self.state(page)["active"])
        self.assertFalse(page.evaluate(lens)["visible"])
        page.keyboard.press("Alt+KeyY")
        page.evaluate("() => DeckPen.controller.setLens(0.5, 0.5, true)")
        page.evaluate("() => DeckPen.controller.setActive(false)")
        self.assertFalse(page.evaluate(lens)["visible"])

    def test_pen_ignores_typing_targets(self):
        page = self.open_pen()
        page.focus("#pen-input")
        page.keyboard.press("Alt+KeyO")
        page.keyboard.press("Alt+KeyU")
        page.keyboard.press("Alt+KeyP")
        self.assertEqual(self.state(page)["active"], False)
        self.assertEqual(self.state(page)["mode"], "laser")
        page.evaluate("() => document.activeElement.blur()")
        page.keyboard.press("Alt+KeyO")
        self.assertTrue(self.state(page)["active"])
        page.focus("#pen-input")
        page.keyboard.press("Escape")
        self.assertTrue(self.state(page)["active"], "Esc inside an input is left to the input")

    def test_option_chords_work_when_the_browser_reports_dead_key_229(self):
        page = self.open_pen()
        send = """([code, keyCode, key, alt, composing]) => {
          const ev = new KeyboardEvent('keydown', { code, key, altKey: alt, isComposing: composing,
            keyCode, bubbles: true, cancelable: true });
          document.body.dispatchEvent(ev);
          return ev.defaultPrevented;
        }"""
        self.assertTrue(page.evaluate(send, ["KeyU", 229, "Dead", True, False]))
        self.assertEqual(self.state(page)["mode"], "eraser")
        self.assertTrue(self.state(page)["active"])
        self.assertTrue(page.evaluate(send, ["KeyI", 229, "Dead", True, True]))
        self.assertEqual(self.state(page)["mode"], "highlighter")
        # A plain key during IME composition is left alone, Esc included.
        self.assertFalse(page.evaluate(send, ["Escape", 229, "Escape", False, True]))
        self.assertFalse(page.evaluate(send, ["Escape", 229, "Escape", False, False]))
        self.assertTrue(self.state(page)["active"])

    def test_overview_mode_makes_the_canvas_inert(self):
        page = self.open_pen()
        page.keyboard.press("Alt+KeyO")
        page.keyboard.press("o")
        page.wait_for_timeout(200)
        self.assertTrue(self.state(page)["active"])
        thumb = page.evaluate("""() => {
          const r = document.querySelector('.slide-deck > .slide:nth-child(3)').getBoundingClientRect();
          return [r.left + r.width / 2, r.top + r.height / 2];
        }""")
        self.assertNotEqual(page.evaluate(
            "([x, y]) => document.elementFromPoint(x, y).id", thumb), "rp-pen-canvas")
        self.assertEqual(page.evaluate(
            "() => getComputedStyle(document.getElementById('rp-pen-canvas')).pointerEvents"),
            "none")
        page.mouse.move(thumb[0], thumb[1])
        page.mouse.down()
        page.mouse.move(thumb[0] + 40, thumb[1] + 20, steps=5)
        page.mouse.up()
        self.assertEqual(page.evaluate(
            "() => [0, 1, 2].map(i => DeckPen.controller.model.visible(i).length)"), [0, 0, 0])
        # The press reached the thumbnail: its click handler leaves overview mode.
        page.wait_for_timeout(450)
        self.assertFalse(page.evaluate(
            "() => document.querySelector('.slide-deck').classList.contains('overview-mode')"))
        self.assertTrue(self.state(page)["active"])
        self.stroke(page, [(0.3, 0.5), (0.6, 0.5)])
        self.assertEqual(page.evaluate(
            "() => DeckPen.controller.model.visible(deck.currentSlide).length"), 1)
        self.assertGreater(self.inked(page), 0)

    def test_canvas_loop_idle(self):
        page = self.open_pen()
        page.evaluate("""() => {
          window.__raf = 0;
          const orig = window.requestAnimationFrame.bind(window);
          window.requestAnimationFrame = f => { window.__raf++; return orig(f); };
        }""")
        page.keyboard.press("Alt+KeyP")
        self.stroke(page, [(0.2, 0.2), (0.5, 0.4)])
        self.assertGreater(page.evaluate("() => window.__raf"), 0, "the loop runs while drawing")
        page.wait_for_timeout(600)
        self.assertEqual(self.inked(page), 0)
        page.evaluate("() => { window.__raf = 0; }")
        page.wait_for_timeout(200)
        self.assertEqual(page.evaluate("() => window.__raf"), 0, "no frames requested when idle")

    def test_badge_shows_mode_and_hides_for_audience_when_disabled(self):
        page = self.open_pen()
        badge = page.locator("#rp-pen-badge")
        self.assertFalse(badge.is_visible())
        page.keyboard.press("Alt+KeyO")
        self.assertTrue(badge.is_visible())
        self.assertIn("Pen", badge.inner_text())
        page.keyboard.press("Alt+KeyI")
        self.assertIn("Highlighter", badge.inner_text())
        page.keyboard.press("Escape")
        self.assertFalse(badge.is_visible())

        page = self.open_pen("pen-nobadge.html")
        page.keyboard.press("Alt+KeyO")
        self.assertTrue(self.state(page)["active"])
        self.assertFalse(page.locator("#rp-pen-badge").is_visible())

    def test_canvas_and_badge_are_overlay_ui_and_pointer_inert_when_off(self):
        page = self.open_pen()
        info = page.evaluate("""() => ['rp-pen-canvas', 'rp-pen-badge'].map(id => {
          const el = document.getElementById(id);
          return { overlay: el.classList.contains('rp-overlay-ui'),
                   bodyChild: el.parentElement === document.body,
                   inSlide: Boolean(el.closest('.slide')),
                   pointer: getComputedStyle(el).pointerEvents };
        })""")
        for item in info:
            self.assertEqual(item, {"overlay": True, "bodyChild": True,
                                    "inSlide": False, "pointer": "none"})
        page.keyboard.press("Alt+KeyO")
        self.assertEqual(page.evaluate(
            "() => getComputedStyle(document.getElementById('rp-pen-canvas')).pointerEvents"),
            "auto")
        self.assertEqual(page.evaluate(
            "() => getComputedStyle(document.getElementById('rp-pen-badge')).pointerEvents"),
            "none")
        rect = page.evaluate("""() => {
          const a = document.getElementById('rp-pen-canvas').getBoundingClientRect();
          const b = document.querySelector('.slide-deck').getBoundingClientRect();
          return [a.left - b.left, a.top - b.top, a.width - b.width, a.height - b.height]
            .map(v => Math.round(v));
        }""")
        self.assertEqual(rect, [0, 0, 0, 0], "canvas covers the deck box")

    def test_deck_badge_markup_and_single_surface_without_presenter(self):
        page = self.open_pen()
        info = page.evaluate("""() => {
          const b = document.getElementById('rp-pen-badge');
          return { role: b.getAttribute('role'), live: b.getAttribute('aria-live'),
                   classes: ['rp-overlay-ui', 'rp-pen-badge'].every(c => b.classList.contains(c)),
                   parts: Array.from(b.children).map(c => c.className),
                   surfaces: DeckPen.controller.surfaceCount() };
        }""")
        self.assertEqual(info, {"role": "status", "live": "polite", "classes": True,
                                "parts": ["rp-pen-swatch", "rp-pen-label"], "surfaces": 1})
        page.keyboard.press("Alt+KeyU")
        self.assertEqual(page.evaluate(
            "() => document.querySelector('#rp-pen-badge .rp-pen-label').textContent"),
            "Eraser, medium")
        self.assertTrue(page.evaluate(
            "() => document.querySelector('#rp-pen-badge .rp-pen-swatch').hidden"))


if __name__ == "__main__":
    result = unittest.main(exit=False, verbosity=2).result
    if result.skipped and result.testsRun <= len(result.skipped):
        print("SKIPPED-ALL")
    sys.exit(0 if result.wasSuccessful() else 1)
