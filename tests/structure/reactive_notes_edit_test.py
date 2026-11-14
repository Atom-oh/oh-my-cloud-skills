"""Browser regressions for editable speaker notes in the presenter view (reactive-presentation).

Skips (exit 0) when Playwright for Python or its Chromium is unavailable; the TAP wrapper
reports that as a SKIP so a missing browser is never mistaken for a pass.
"""
import functools
import http.server
import json
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
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Notes edit fixture</title>
<link rel="stylesheet" href="./common/theme.css">
<link rel="stylesheet" href="./common/deck-pen.css">
</head>
<body>
<div class="slide-deck">
  <div class="slide" data-remarp-id="s1"><div class="slide-header"><h2>One</h2></div>
    <div class="slide-body"><p>first</p></div>
    <template class="notes" data-timing="2 min">Original **one** note</template></div>
  <div class="slide" data-remarp-id="s2"><div class="slide-header"><h2>Two</h2></div>
    <div class="slide-body"><p>second</p></div>
    <template class="notes">Original two note</template></div>
  <div class="slide" data-remarp-id="s3"><div class="slide-header"><h2>Three</h2></div>
    <div class="slide-body"><p>third</p></div></div>
</div>
<script src="./common/animation-utils.js"></script>
<script src="./common/deck-pen.js"></script>
<script src="./common/slide-framework.js"></script>
<script src="./common/presenter-view.js"></script>
<script>const deck = new SlideFramework({ sidebar: false });</script>
</body>
</html>
"""

NO_NOTES = "No notes for this slide."


def _load_playwright():
    try:
        from playwright.sync_api import sync_playwright
        return sync_playwright
    except Exception:  # pragma: no cover
        return None


class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


class EditableNotesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sync_playwright = _load_playwright()
        if sync_playwright is None:
            raise unittest.SkipTest("playwright for Python is not installed")
        cls.tmp = tempfile.TemporaryDirectory(prefix="rp-notes-edit-")
        root = Path(cls.tmp.name)
        common = root / "common"
        common.mkdir()
        for f in ASSETS.iterdir():
            if f.suffix in (".js", ".css"):
                shutil.copy(f, common / f.name)
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
        # A fresh context per test keeps localStorage isolated.
        self.ctx = self.browser.new_context(viewport={"width": 1600, "height": 900})
        self.addCleanup(self.ctx.close)
        self.errors = []
        self.page = self.ctx.new_page()
        self.page.set_default_timeout(5000)
        self.page.on("pageerror", lambda exc: self.errors.append(str(exc)))
        self.open_deck()

    def tearDown(self):
        self.assertEqual(self.errors, [])

    def open_deck(self):
        self.page.goto(self.url, wait_until="networkidle")
        self.page.wait_for_timeout(300)
        self.open_presenter()

    def open_presenter(self):
        with self.ctx.expect_page() as info:
            self.page.keyboard.press("n")
        self.pv = info.value
        self.pv.on("pageerror", lambda exc: self.errors.append(str(exc)))
        self.pv.set_viewport_size({"width": 1600, "height": 900})
        self.pv.wait_for_function(
            "() => document.getElementById('p-counter').textContent.startsWith('1 /')", timeout=5000)

    def notes_html(self):
        return self.pv.evaluate("() => document.getElementById('p-notes').innerHTML")

    def notes_text(self):
        return self.pv.evaluate("() => document.getElementById('p-notes').textContent")

    def stored(self):
        raw = self.page.evaluate("() => localStorage.getItem(deck.noteStorageKey())")
        return None if raw is None else json.loads(raw)

    def editing(self):
        return self.pv.evaluate("() => !!document.querySelector('#p-notes textarea.notes-editor')")

    def begin(self):
        self.pv.click("#p-note-edit")
        self.assertTrue(self.editing())

    def replace_text(self, text):
        self.pv.fill("#p-notes textarea", text)

    def goto(self, index):
        self.page.evaluate(f"() => deck.goTo({index})")
        self.page.wait_for_function("() => !deck.transitioning", timeout=5000)
        self.pv.wait_for_function(
            "i => document.getElementById('p-counter').textContent.startsWith(`${i + 1} /`)",
            arg=index, timeout=5000)

    # --- entering edit mode -------------------------------------------------
    def test_edit_button_opens_textarea_with_original_text(self):
        self.assertFalse(self.editing())
        self.begin()
        self.assertEqual(self.pv.input_value("#p-notes textarea"), "Original **one** note")
        self.assertEqual(self.pv.inner_text("#p-note-edit"), "Save notes")
        self.assertTrue(self.pv.evaluate("() => document.activeElement.classList.contains('notes-editor')"))

    def test_double_click_opens_textarea(self):
        self.pv.dblclick("#p-notes")
        self.assertTrue(self.editing())

    # --- saving -------------------------------------------------------------
    def test_ctrl_enter_saves_and_renders_markup(self):
        self.begin()
        self.replace_text("Softer **wording** with `code`")
        self.pv.keyboard.press("Control+Enter")
        self.assertFalse(self.editing())
        self.assertIn("<strong>wording</strong>", self.notes_html())
        self.assertIn("<code>code</code>", self.notes_html())
        self.assertEqual(self.stored(), {"s1": "Softer **wording** with `code`"})
        self.assertEqual(self.pv.inner_text("#p-note-edit"), "Edit notes")

    def test_blur_saves(self):
        self.begin()
        self.replace_text("Saved by blur")
        self.pv.evaluate("() => document.querySelector('#p-notes textarea').blur()")
        self.assertFalse(self.editing())
        self.assertEqual(self.notes_text(), "Saved by blur")
        self.assertEqual(self.stored(), {"s1": "Saved by blur"})

    def test_save_button_saves_while_editing(self):
        self.begin()
        self.replace_text("Saved by button")
        self.pv.click("#p-note-edit")
        self.assertFalse(self.editing())
        self.assertEqual(self.stored(), {"s1": "Saved by button"})

    def test_escape_cancels_without_saving(self):
        self.begin()
        self.replace_text("Should not stick")
        self.pv.keyboard.press("Escape")
        self.assertFalse(self.editing())
        self.assertEqual(self.notes_text(), "Original one note")
        self.assertIsNone(self.stored())

    def test_html_in_notes_is_escaped(self):
        self.begin()
        self.replace_text("<img src=x onerror=\"window.__xss=1\">")
        self.pv.keyboard.press("Control+Enter")
        self.assertNotIn("<img", self.notes_html())
        self.assertIsNone(self.pv.evaluate("() => window.__xss"))

    # --- persistence --------------------------------------------------------
    def test_override_survives_reload(self):
        self.begin()
        self.replace_text("Persisted note")
        self.pv.keyboard.press("Control+Enter")
        self.pv.close()
        self.page.reload(wait_until="networkidle")
        self.page.wait_for_timeout(300)
        self.open_presenter()
        self.assertEqual(self.notes_text(), "Persisted note")
        self.assertEqual(self.pv.inner_text("#p-note-edited"), "Edited")
        self.assertFalse(self.pv.is_hidden("#p-note-reset"))

    def test_other_slides_keep_authored_notes(self):
        self.begin()
        self.replace_text("Only slide one changes")
        self.pv.keyboard.press("Control+Enter")
        self.goto(1)
        self.assertEqual(self.notes_text(), "Original two note")
        self.assertTrue(self.pv.is_hidden("#p-note-edited"))
        self.assertTrue(self.pv.is_hidden("#p-note-reset"))

    def test_invalid_stored_values_are_ignored(self):
        self.page.evaluate(
            "() => localStorage.setItem(deck.noteStorageKey(), JSON.stringify({s1: 5, s2: 'Stored two'}))")
        self.pv.close()
        self.page.reload(wait_until="networkidle")
        self.page.wait_for_timeout(300)
        self.open_presenter()
        self.assertEqual(self.notes_text(), "Original one note")
        self.goto(1)
        self.assertEqual(self.notes_text(), "Stored two")

    # --- reset / deviation-only storage --------------------------------------
    def test_reset_restores_original_and_clears_storage(self):
        self.begin()
        self.replace_text("Temporary")
        self.pv.keyboard.press("Control+Enter")
        self.assertEqual(self.pv.inner_text("#p-note-edited"), "Edited")
        self.pv.click("#p-note-reset")
        self.assertEqual(self.notes_text(), "Original one note")
        self.assertIsNone(self.stored())
        self.assertTrue(self.pv.is_hidden("#p-note-edited"))
        self.assertTrue(self.pv.is_hidden("#p-note-reset"))

    def test_saving_the_original_text_stores_nothing(self):
        self.begin()
        self.replace_text("Changed")
        self.pv.keyboard.press("Control+Enter")
        self.assertIsNotNone(self.stored())
        self.begin()
        self.replace_text("Original **one** note")
        self.pv.keyboard.press("Control+Enter")
        self.assertIsNone(self.stored())

    def test_empty_save_is_an_empty_override(self):
        self.begin()
        self.replace_text("")
        self.pv.keyboard.press("Control+Enter")
        self.assertEqual(self.notes_text(), NO_NOTES)
        self.assertEqual(self.stored(), {"s1": ""})

    def test_slide_without_authored_note_can_gain_one(self):
        self.goto(2)
        self.assertEqual(self.notes_text(), NO_NOTES)
        self.begin()
        self.assertEqual(self.pv.input_value("#p-notes textarea"), "")
        self.replace_text("Added example")
        self.pv.keyboard.press("Control+Enter")
        self.assertEqual(self.stored(), {"s3": "Added example"})

    def test_timing_is_kept_after_edit(self):
        self.begin()
        self.replace_text("Edited")
        self.pv.keyboard.press("Control+Enter")
        self.assertEqual(self.pv.inner_text("#p-timing-value"), "2 min")

    # --- editing safety -----------------------------------------------------
    def test_shortcuts_do_not_fire_while_typing(self):
        self.begin()
        self.replace_text("")
        self.pv.keyboard.type("nghtcopuiy1 ")
        self.assertEqual(self.pv.input_value("#p-notes textarea"), "nghtcopuiy1 ")
        state = self.page.evaluate("""() => ({
          slide: deck.currentSlide,
          hidden: Object.keys(deck.hiddenOverrides).length,
          penActive: !!(window.DeckPen && DeckPen.controller && DeckPen.controller.active),
          theme: localStorage.getItem(deck.themeStorageKey())
        })""")
        self.assertEqual(state, {"slide": 0, "hidden": 0, "penActive": False, "theme": None})
        self.assertTrue(self.editing())

    def test_arrow_keys_edit_text_instead_of_navigating(self):
        self.begin()
        self.pv.keyboard.press("ArrowRight")
        self.pv.keyboard.press("ArrowLeft")
        self.assertEqual(self.page.evaluate("() => deck.currentSlide"), 0)

    def test_rerender_does_not_clobber_open_editor(self):
        self.begin()
        self.replace_text("Half-typed text")
        self.page.evaluate("() => deck.presenterView.updatePresenterView()")
        self.pv.wait_for_timeout(200)
        self.assertTrue(self.editing())
        self.assertEqual(self.pv.input_value("#p-notes textarea"), "Half-typed text")

    def test_slide_change_commits_edit_to_original_slide(self):
        self.begin()
        self.replace_text("Typed on slide one")
        self.goto(1)
        self.assertFalse(self.editing())
        self.assertEqual(self.notes_text(), "Original two note")
        self.assertEqual(self.stored(), {"s1": "Typed on slide one"})

    def test_closing_presenter_window_commits_edit(self):
        self.begin()
        self.replace_text("Typed before closing")
        self.pv.close()
        self.page.wait_for_timeout(200)
        self.assertEqual(self.stored(), {"s1": "Typed before closing"})

    def test_audience_slide_is_unchanged(self):
        self.begin()
        self.replace_text("Presenter only")
        self.pv.keyboard.press("Control+Enter")
        self.assertNotIn("Presenter only", self.page.evaluate("() => document.body.innerText"))


if __name__ == "__main__":
    result = unittest.main(exit=False, verbosity=2).result
    if result.skipped and result.testsRun <= len(result.skipped):
        print("SKIPPED-ALL")
    sys.exit(0 if result.wasSuccessful() else 1)
