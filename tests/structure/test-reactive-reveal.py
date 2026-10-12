#!/usr/bin/env python3
"""Compiler regressions for semantic content outside column blocks."""

from html.parser import HTMLParser
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py"
sys.dont_write_bytecode = True
SPEC = importlib.util.spec_from_file_location("remarp_reveal", SCRIPT)
remarp = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = remarp
SPEC.loader.exec_module(remarp)

FRONT = "---\nremarp: true\n---\n@type: content\n## Column fixture\n\n"
COLUMNS = "::::left\nLeft detail\n::::\n\n::::right\nRight detail\n::::\n\n"


class FragmentText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []
        self.fragments = {}
        self.outside = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        classes = attributes.get("class", "").split()
        index = attributes.get("data-fragment-index") if "fragment" in classes else None
        self.stack.append((tag, index))

    def handle_endtag(self, tag):
        if self.stack and self.stack[-1][0] == tag:
            self.stack.pop()

    def handle_data(self, data):
        if not data.strip():
            return
        indices = [index for _, index in self.stack if index is not None]
        if indices:
            self.fragments.setdefault(indices[-1], []).append(data.strip())
        else:
            self.outside.append(data.strip())


class ColumnRevealTests(unittest.TestCase):
    def slide(self, text):
        _, blocks = remarp.RemarpParser(FRONT + text).parse()
        slides = [slide for group in blocks.values() for slide in group]
        self.assertEqual(len(slides), 1)
        return slides[0]

    def test_trailing_click_retains_index_animation_and_closing_boundary(self):
        slide = self.slide(COLUMNS + ":::click animation=fade-right order=5\n"
                           "Conclusion on click\n:::\n\nCaption after group\n")
        rendered = remarp.RemarpHTMLGenerator().slide_to_html(slide)
        self.assertIn('class="fragment fade-right" data-fragment-index="5"', rendered)
        parsed = FragmentText()
        parsed.feed(rendered)
        self.assertEqual(parsed.fragments["5"], ["Conclusion on click"])
        self.assertIn("Caption after group", parsed.outside)
        self.assertIn("Left detail", parsed.outside)
        self.assertIn("Right detail", parsed.outside)

    def test_leading_and_trailing_groups_each_retain_their_own_step(self):
        slide = self.slide(":::click order=2\nLeading reveal\n:::\n\n" + COLUMNS +
                           ":::click animation=zoom-in order=7\nTrailing reveal\n:::\n")
        parsed = FragmentText()
        parsed.feed(remarp.RemarpHTMLGenerator().slide_to_html(slide))
        self.assertEqual(parsed.fragments["2"], ["Leading reveal"])
        self.assertEqual(parsed.fragments["7"], ["Trailing reveal"])

    def test_archify_outside_columns_reaches_the_renderer(self):
        slide = self.slide(COLUMNS + ":::archify\nflowchart LR\n  A --> B\n:::\n")
        generator = remarp.RemarpHTMLGenerator()
        iframe = '<iframe class="archify-diagram" src="archify-fixture.html"></iframe>'
        with mock.patch.object(generator, "_render_archify_block", return_value=iframe) as render:
            rendered = generator.slide_to_html(slide)
        render.assert_called_once_with(slide, 0, slide.archify_blocks[0])
        self.assertIn(iframe, rendered)
        self.assertNotIn("__ARCHIFY_BLOCK_", rendered)
        self.assertLess(rendered.index("Right detail"), rendered.index(iframe))

    def test_html_and_plain_remainder_are_kept_without_column_or_author_markers(self):
        slide = self.slide(COLUMNS + "<!-- ordinary author comment -->\n\n"
                           ":::html\n<div data-reveal=\"static\">A detail card</div>\n:::\n"
                           "\nPlain caption\n")
        rendered = remarp.RemarpHTMLGenerator().slide_to_html(slide)
        self.assertIn('data-reveal="static"', rendered)
        self.assertIn("A detail card", rendered)
        self.assertIn("Plain caption", rendered)
        self.assertNotIn("__BLOCK:left", rendered)
        self.assertNotIn("__BLOCK:right", rendered)
        self.assertNotIn("ordinary author comment", rendered)


if __name__ == "__main__":
    unittest.main(verbosity=2)
