"""Browser regression: Escape is locked while the deck is fullscreen so pen mode and overview see it first.

A real keyboard lock cannot be asserted in headless Chromium, so navigator.keyboard is stubbed with
a recorder and Escape is driven with synthetic keydown events.
"""
import sys
import unittest

sys.dont_write_bytecode = True

from reactive_overlay_fixture import DeckOverlayFixture, SLIDES_B

STUB_OK = """
window.__kb = { locks: [], unlocks: 0 };
Object.defineProperty(navigator, 'keyboard', { configurable: true, value: {
  lock(keys) { window.__kb.locks.push(keys); return Promise.resolve(); },
  unlock() { window.__kb.unlocks++; }
}});
"""
STUB_REJECT = """
window.__kb = { locks: [], unlocks: 0 };
Object.defineProperty(navigator, 'keyboard', { configurable: true, value: {
  lock(keys) { window.__kb.locks.push(keys); return Promise.reject(new Error('denied')); },
  unlock() { window.__kb.unlocks++; throw new Error('unlock failed'); }
}});
"""
STUB_ABSENT = "Object.defineProperty(navigator, 'keyboard', { configurable: true, value: undefined });"

ESC = "() => document.dispatchEvent(new KeyboardEvent('keydown', {key: 'Escape', bubbles: true}))"
ESC_REPEAT = "() => document.dispatchEvent(new KeyboardEvent('keydown', {key: 'Escape', bubbles: true, repeat: true}))"
FS = "() => !!document.fullscreenElement"
KB = "() => window.__kb"


class DeckFullscreenLockTests(DeckOverlayFixture):
    overlay_modules = ("pen",)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        (cls.root / "fs.html").write_text(
            cls.page_head + SLIDES_B + cls.page_scripts % "sidebar: false, pen: { fadeMs: 300 }",
            encoding="utf-8")
        (cls.root / "fs-sidebar.html").write_text(
            cls.page_head + SLIDES_B + cls.page_scripts % "sidebar: true", encoding="utf-8")

    def open_stub(self, stub, name="fs.html"):
        self.ctx = self.browser.new_context(viewport={"width": 1600, "height": 900})
        self.addCleanup(self.ctx.close)
        self.ctx.add_init_script(stub)
        page = self.ctx.new_page()
        page.set_default_timeout(5000)
        self.errors = []
        page.on("pageerror", lambda e: self.errors.append(str(e)))
        page.goto(self.base + name, wait_until="networkidle")
        page.wait_for_timeout(300)
        return page

    def toggle_fs(self, page, want):
        page.keyboard.press("f")
        page.wait_for_function(f"() => !!document.fullscreenElement === {str(want).lower()}")
        page.wait_for_timeout(100)

    def test_escape_lock_follows_fullscreen_state(self):
        for name in ("fs.html", "fs-sidebar.html"):
            page = self.open_stub(STUB_OK, name)
            self.assertEqual(page.evaluate(KB), {"locks": [], "unlocks": 0}, name)
            self.toggle_fs(page, True)
            self.assertEqual(page.evaluate(KB), {"locks": [["Escape"]], "unlocks": 0}, name)
            self.toggle_fs(page, False)
            self.assertEqual(page.evaluate(KB), {"locks": [["Escape"]], "unlocks": 1}, name)
            self.toggle_fs(page, True)
            self.assertEqual(page.evaluate(KB), {"locks": [["Escape"], ["Escape"]], "unlocks": 1}, name)
            self.assertEqual(self.errors, [], name)

    def test_bind_escape_lock_is_idempotent(self):
        page = self.open_stub(STUB_OK)
        page.evaluate("() => { deck.bindEscapeLock(); deck.bindEscapeLock(); }")
        self.toggle_fs(page, True)
        self.assertEqual(page.evaluate(KB)["locks"], [["Escape"]])

    def test_keyboard_lock_absent_or_rejected_is_harmless(self):
        for stub in (STUB_ABSENT, STUB_REJECT):
            page = self.open_stub(stub)
            self.toggle_fs(page, True)
            self.assertTrue(page.evaluate(FS))
            self.toggle_fs(page, False)
            self.assertFalse(page.evaluate(FS))
            page.wait_for_timeout(100)
            self.assertEqual(self.errors, [], stub)

    def test_esc_in_fullscreen_leaves_pen_mode_before_fullscreen(self):
        page = self.open_stub(STUB_OK)
        self.toggle_fs(page, True)
        page.keyboard.press("Alt+KeyO")
        self.assertTrue(page.evaluate("() => DeckPen.controller.active"))
        page.evaluate(ESC)
        self.assertFalse(page.evaluate("() => DeckPen.controller.active"))
        self.assertTrue(page.evaluate(FS))
        page.evaluate(ESC)
        page.wait_for_function("() => !document.fullscreenElement")
        self.assertFalse(page.evaluate(FS))

    def test_held_esc_does_not_exit_fullscreen_after_leaving_pen_mode(self):
        page = self.open_stub(STUB_OK)
        self.toggle_fs(page, True)
        page.keyboard.press("Alt+KeyO")
        self.assertTrue(page.evaluate("() => DeckPen.controller.active"))
        page.evaluate(ESC)
        for _ in range(4):
            page.evaluate(ESC_REPEAT)
        page.wait_for_timeout(100)
        self.assertFalse(page.evaluate("() => DeckPen.controller.active"))
        self.assertTrue(page.evaluate(FS))
        page.evaluate(ESC)
        page.wait_for_function("() => !document.fullscreenElement")

    def test_held_esc_repeats_are_consumed_while_pen_is_on(self):
        page = self.open_stub(STUB_OK)
        self.toggle_fs(page, True)
        page.keyboard.press("Alt+KeyO")
        # A repeat Escape with pen on must not turn pen off or exit fullscreen.
        prevented = page.evaluate("""() => {
          const e = new KeyboardEvent('keydown', {key: 'Escape', bubbles: true, cancelable: true, repeat: true});
          document.dispatchEvent(e);
          return e.defaultPrevented;
        }""")
        self.assertTrue(prevented)
        self.assertTrue(page.evaluate("() => DeckPen.controller.active"))
        self.assertTrue(page.evaluate(FS))

    def test_esc_closes_overview_before_leaving_fullscreen(self):
        page = self.open_stub(STUB_OK)
        self.toggle_fs(page, True)
        overview = "() => document.querySelector('.slide-deck').classList.contains('overview-mode')"
        page.keyboard.press("o")
        self.assertTrue(page.evaluate(overview))
        page.evaluate(ESC)
        self.assertFalse(page.evaluate(overview))
        self.assertTrue(page.evaluate(FS))
        page.evaluate(ESC)
        page.wait_for_function("() => !document.fullscreenElement")


if __name__ == "__main__":
    result = unittest.main(exit=False, verbosity=2).result
    if result.skipped and result.testsRun <= len(result.skipped):
        print("SKIPPED-ALL")
    sys.exit(0 if result.wasSuccessful() else 1)
