"""Browser regressions for the T dark/light toggle; skips without Playwright/Chromium."""
import sys
import unittest

sys.dont_write_bytecode = True

from reactive_overlay_fixture import DeckOverlayFixture

SLIDES = """<div class="slide-deck">
  <div class="slide" data-remarp-id="s1"><div class="slide-header"><h2>One</h2></div><div class="slide-body"><p>a</p></div></div>
  <div class="slide theme-light" data-remarp-id="s2"><div class="slide-header"><h2>Pinned</h2></div><div class="slide-body"><p>b</p></div></div>
</div>
"""


class ThemeToggleTests(DeckOverlayFixture):
    overlay_modules = ()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        (cls.root / "t.html").write_text(
            cls.page_head + SLIDES + cls.page_scripts % "sidebar: true", encoding="utf-8")

    @staticmethod
    def deck_dark(page):
        return page.evaluate("() => document.querySelector('.slide-deck').classList.contains('theme-dark')")

    def test_t_toggles_deck_theme_and_persists(self):
        page = self.open("t.html")
        self.assertFalse(self.deck_dark(page))
        page.keyboard.press("t")
        self.assertTrue(self.deck_dark(page))
        # sidebar thumb of the unpinned slide follows; the pinned one does not
        self.assertTrue(page.evaluate(
            "() => document.querySelector('.sidebar-thumb[data-index=\"0\"] .sidebar-thumb-content').classList.contains('theme-dark')"))
        self.assertFalse(page.evaluate(
            "() => document.querySelector('.sidebar-thumb[data-index=\"1\"] .sidebar-thumb-content').classList.contains('theme-dark')"))
        page.reload(wait_until="networkidle")
        page.wait_for_timeout(300)
        self.assertTrue(self.deck_dark(page))
        page.keyboard.press("T")
        self.assertFalse(self.deck_dark(page))

    def test_pinned_light_slide_keeps_a_light_surface_in_a_dark_deck(self):
        page = self.open("t.html#2")
        page.keyboard.press("t")
        self.assertTrue(self.deck_dark(page))
        bg = page.evaluate("() => getComputedStyle(document.querySelectorAll('.slide-deck .slide')[1]).backgroundColor")
        deck = page.evaluate("() => getComputedStyle(document.querySelector('.slide-deck')).backgroundColor")
        self.assertNotEqual(bg, "rgba(0, 0, 0, 0)", "pinned-light slide has its own surface")
        self.assertNotEqual(bg, deck)

    def test_stored_dark_theme_reaches_sidebar_thumbs_after_reload(self):
        page = self.open("t.html")
        page.keyboard.press("t")
        page.reload(wait_until="networkidle")
        page.wait_for_timeout(300)
        self.assertTrue(page.evaluate(
            "() => document.querySelector('.sidebar-thumb[data-index=\"0\"] .sidebar-thumb-content').classList.contains('theme-dark')"))

    def test_t_refreshes_canvas_colors_and_notifies(self):
        page = self.open("t.html")
        page.evaluate("""() => {
          window.__themeEvents = 0;
          window.refreshThemeColors = function () { window.__themeEvents++; };
        }""")
        page.keyboard.press("t")
        self.assertEqual(page.evaluate("() => window.__themeEvents"), 1)

    def test_t_ignored_while_typing_and_with_modifiers(self):
        page = self.open("t.html")
        page.keyboard.press("Control+t")
        page.keyboard.press("Alt+t")
        self.assertFalse(self.deck_dark(page))
        page.evaluate("() => { const i = document.createElement('input'); document.body.appendChild(i); i.focus(); }")
        page.keyboard.type("t")
        self.assertFalse(self.deck_dark(page))


if __name__ == "__main__":
    result = unittest.main(exit=False, verbosity=2).result
    if result.skipped and result.testsRun <= len(result.skipped):
        print("SKIPPED-ALL")
    sys.exit(0 if result.wasSuccessful() else 1)
