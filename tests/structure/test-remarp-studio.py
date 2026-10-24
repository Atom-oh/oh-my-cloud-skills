"""Canonical Studio export and lossless source provenance (no browser required)."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / 'plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py'
spec = importlib.util.spec_from_file_location('studio_compiler_test', SCRIPT)
compiler = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = compiler
spec.loader.exec_module(compiler)
spec = importlib.util.spec_from_file_location('studio_source_test', SCRIPT.with_name('remarp_studio.py'))
editor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(editor)

HEADER = '---\nremarp: true\nratio: "16:9"\nlang: en\ntitle: Studio Test\n---\n'
CARDS = '@type: cards\n## Compare options\n### First option\nFirst body\n### Second option\nSecond body\n'
CANVAS = '@type: canvas\n## Request flow\n:::canvas\nbox a "API" at 80,180 size 120,50 color accent step 1\nbox b "Backend" at 380,180 size 120,50 color blue step 2\narrow a -> b "request" step 3\n:::\n'


def text_at(text, span):
    return text.encode('utf-16-le')[span['start'] * 2:span['end'] * 2].decode('utf-16-le')


class StudioTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.output = self.root / 'compiled'

    def build(self, text, filename='deck.remarp.md'):
        source = self.root / filename
        source.write_bytes(text.encode('utf-8'))
        with contextlib.redirect_stdout(io.StringIO()):
            result = compiler.main(['studio', str(source), '--output', str(self.output)])
        self.assertEqual(result, 0)
        return json.loads((self.output / 'studio.json').read_text()), (self.output / 'studio.html').read_text()

    def test_canonical_html_and_css_target_resolution(self):
        source = HEADER + CARDS + '\n:::css\n<card:0>\n  color: red\n</card:0>\n:::\n'
        manifest, html = self.build(source)
        self.assertIn('[data-remarp-id="s0-card-0"] { color: red }', html)
        self.assertIn('data-remarp-id="s0-card-0"', html)
        self.assertEqual(manifest['version'], 1)
        self.assertEqual(manifest['slides'][0]['nodes'][1]['body']['value'], 'First body')
        prop = manifest['slides'][0]['css']['targets']['card:0']['properties']['color']
        self.assertEqual(text_at(source, prop), 'red')
        self.assertEqual(text_at(source, prop['line']), '  color: red\n')

    def test_crlf_unicode_and_exact_spans(self):
        text = (HEADER + CARDS.replace('Compare options', '한글 😀 comparison').replace('First body', '내용 e\u0301 🚀')).replace('\n', '\r\n')
        manifest, _ = self.build(text)
        slide = manifest['slides'][0]
        self.assertEqual(slide['eol'], '\r\n')
        self.assertEqual(text_at(text, slide['range']), slide['source'])
        for node in slide['nodes']:
            for field in ('text', 'body'):
                if field in node:
                    self.assertEqual(text_at(text, node[field]), node[field]['value'])

    def test_card_body_preserves_comment_and_literal_islands(self):
        source = HEADER + CARDS.replace('First body', 'First body\n<!-- preserve this -->\n```python\nprint("literal")\n```')
        manifest, _ = self.build(source)
        card = next(n for n in manifest['slides'][0]['nodes'] if n['id'] == 's0-card-0')
        self.assertEqual(card['body']['value'], 'First body')
        self.assertNotIn('preserve this', text_at(source, card['body']))

    def test_ambiguous_literal_card_headings_do_not_map_to_wrong_cards(self):
        source = HEADER + CARDS.replace('First body', 'First body\n```md\n### Literal card\n```')
        manifest, html = self.build(source)
        self.assertIn('Literal card', html)
        self.assertFalse(any(n['kind'] == 'card' for n in manifest['slides'][0]['nodes']))

    def test_code_fences_and_nested_blocks_are_not_editable_headings(self):
        source = HEADER + '## Real heading\n````md\n---\n@type: quiz\n## Fake heading\n```\n````\n::::left\n:::click\n## Nested heading\n:::\n::::\n---\n' + CARDS
        manifest, _ = self.build(source)
        self.assertEqual(len(manifest['slides']), 2)
        self.assertEqual(manifest['slides'][0]['title'], 'Real heading')
        self.assertEqual(len(manifest['slides'][0]['nodes']), 1)

    def test_canvas_positions_size_and_step_are_canonical_fields(self):
        text = HEADER + CANVAS
        manifest, html = self.build(text)
        node = next(n for n in manifest['slides'][0]['nodes'] if n['kind'] == 'box')
        self.assertEqual(text_at(text, node['position']), '80,180')
        self.assertEqual(text_at(text, node['size']), '120,50')
        self.assertEqual(text_at(text, node['step']), '1')
        self.assertEqual(node['geometry']['canvasWidth'], 960)
        self.assertIn('drawBox(ctx, 80, 180, 120, 50', html)

    def test_a_label_that_contains_the_word_step_does_not_hijack_the_step_field(self):
        text = HEADER + '@type: canvas\n## Request flow\n:::canvas\nbox a "Run step 1" at 80,180 size 120,50 color accent step 2\nbox b "Wait step 7" at 380,180 size 120,50 color blue\n:::\n'
        manifest, _ = self.build(text)
        a, b = [n for n in manifest['slides'][0]['nodes'] if n['kind'] == 'box']
        self.assertEqual(text_at(text, a['step']), '2')
        self.assertEqual(a['step']['value'], 2)
        self.assertNotIn('step', b)

    def test_slide_spans_never_land_in_the_frontmatter(self):
        # The compiler strips the frontmatter before it splits slides; a one-line slide whose text
        # also appears in a YAML comment must map to the slide, not to the comment.
        front = '---\nremarp: true\nratio: "16:9"\nlang: en\ntitle: Studio Test\n# Agenda\n---\n'
        text = front + '# Agenda\n'
        manifest, _ = self.build(text)
        heading = next(n for n in manifest['slides'][0]['nodes'] if n['kind'] == 'heading')
        self.assertEqual(text_at(text, heading['text']), 'Agenda')
        self.assertGreaterEqual(heading['text']['start'], len(front))

    def test_a_card_without_body_text_has_no_body_span(self):
        # An empty span would sit at the start of the next heading line, or at the end of the last
        # heading, so a plain replacement would glue body text onto a heading.
        text = HEADER + '@type: cards\n## Compare options\n### First option\n### Second option\nSecond body\n### Last option\n'
        manifest, _ = self.build(text)
        cards = [n for n in manifest['slides'][0]['nodes'] if n['kind'] == 'card']
        self.assertEqual(len(cards), 3)
        self.assertNotIn('body', cards[0])
        self.assertEqual(text_at(text, cards[1]['body']), 'Second body')
        self.assertNotIn('body', cards[2])
        self.assertEqual([text_at(text, c['text']) for c in cards], ['First option', 'Second option', 'Last option'])

    def heading_nodes(self, manifest):
        return [n for n in manifest['slides'][0]['nodes'] if n['kind'] == 'heading']

    def test_the_heading_node_follows_the_heading_each_slide_type_renders(self):
        # A tabs slide with parsed :::tab blocks renders its first level-two heading; tabs without blocks
        # and compare render the last one. The node must point at the rendered heading.
        block_tabs = HEADER + '@type: tabs\n## First title\n## Second title\n\n:::tab "A"\nBody A\n:::\n:::tab "B"\nBody B\n:::\n'
        plain_tabs = HEADER + '@type: tabs\n## First title\n## Second title\n### Tab A\nA\n### Tab B\nB\n'
        compare = HEADER + '@type: compare\n## First title\n## Second title\n\n:::left\n### Left\nL\n:::\n:::right\n### Right\nR\n:::\n'
        for text, rendered in ((block_tabs, 'First title'), (plain_tabs, 'Second title'), (compare, 'Second title')):
            manifest, html = self.build(text)
            nodes = self.heading_nodes(manifest)
            self.assertEqual(len(nodes), 1, text)
            self.assertEqual(text_at(text, nodes[0]['text']), rendered, text)
            self.assertIn('<h2>' + rendered + '</h2>', html, text)

    def test_a_heading_inside_a_click_block_that_the_renderer_shows_is_not_mapped_to_the_outer_one(self):
        # The compiler re-injects :::click content into the slide and renders the last heading line,
        # even one inside the block; Studio sees the outer line only, so it must not offer it.
        text = HEADER + '@type: content\n## Outer heading Studio maps\n\n:::click\n## Inner heading the deck actually shows\nBody text\n:::\n'
        manifest, html = self.build(text)
        self.assertIn('<h2>Inner heading the deck actually shows</h2>', html)
        self.assertEqual(self.heading_nodes(manifest), [])

    def test_a_tab_separated_heading_is_not_a_rendered_heading(self):
        # The generators only treat "## " followed by one space as a heading.
        text = HEADER + '@type: content\n## Real heading\n##\tTab separated\nBody\n'
        manifest, html = self.build(text)
        nodes = self.heading_nodes(manifest)
        self.assertEqual([text_at(text, n['text']) for n in nodes], ['Real heading'])
        self.assertIn('<h2>Real heading</h2>', html)

    def test_tabs_and_compare_with_one_heading_stay_editable(self):
        tabs = HEADER + '@type: tabs\n## Only title\n\n:::tab "A"\nBody A\n:::\n:::tab "B"\nBody B\n:::\n'
        manifest, _ = self.build(tabs)
        heading = self.heading_nodes(manifest)
        self.assertEqual(len(heading), 1)
        self.assertEqual(text_at(tabs, heading[0]['text']), 'Only title')

    def test_a_last_slide_that_ends_in_a_code_fence_maps_without_a_trailing_newline(self):
        # The compiler restores a fence with a newline the file may not contain.
        text = HEADER + '@type: content\n## Code sample\n\n```python\nprint(1)\n```'
        manifest, _ = self.build(text)
        slide = manifest['slides'][0]
        self.assertEqual(text_at(text, next(n for n in slide['nodes'] if n['kind'] == 'heading')['text']), 'Code sample')
        self.assertLessEqual(slide['range']['end'], len(text.encode('utf-16-le')) // 2)

    def test_heading_matches_the_generator_not_an_earlier_block_heading(self):
        text = HEADER + '@type: cards\n# Block label\n' + CARDS.replace('@type: cards\n', '')
        manifest, html = self.build(text)
        self.assertEqual(manifest['slides'][0]['title'], 'Compare options')
        self.assertEqual(manifest['slides'][0]['nodes'][0]['text']['value'], 'Compare options')
        self.assertIn('<h2>Compare options</h2>', html)

    def test_duplicate_canvas_ids_are_not_editable(self):
        manifest, _ = self.build(HEADER + CANVAS.replace('box b ', 'box a ').replace('a -> b', 'a -> a'))
        self.assertFalse(any(n['kind'] == 'box' for n in manifest['slides'][0]['nodes']))

    def test_ambiguous_css_is_source_only(self):
        source = HEADER + CARDS + '\n:::css\n<header>\n  color: red\n  color: blue\n</header>\n:::\n'
        manifest, _ = self.build(source)
        self.assertFalse(manifest['slides'][0]['cssEditable'])

    def test_every_css_delimiter_form_is_mapped_or_source_only_never_silently_missing(self):
        body = '<header>\n  padding: 4px\n  color: red\n</header>\n'
        for label, opener, closer in (('spaced', '::: css', ':::'), ('four colons', '::::css', '::::'),
                                      ('spaced four colons', ':::: css', '::::')):
            with self.subTest(form=label):
                manifest, _ = self.build(HEADER + CARDS + f'\n{opener}\n{body}{closer}\n')
                slide = manifest['slides'][0]
                # A mapped block carries its properties; otherwise the slide must be source-only, or a visual
                # edit would append a second css block that replaces the authored one.
                self.assertTrue(slide.get('css') or slide['cssEditable'] is False, slide.get('css'))

    def test_a_spaced_css_delimiter_still_maps_its_properties(self):
        text = HEADER + CARDS + '\n::: css\n<header>\n  color: red\n</header>\n:::\n'
        manifest, _ = self.build(text)
        prop = manifest['slides'][0]['css']['targets']['header']['properties']['color']
        self.assertEqual(text_at(text, prop), 'red')

    def test_nested_css_cannot_receive_visual_inserts(self):
        source = HEADER + CARDS + '\n::::left\n:::css\n<header>\n  color: red\n</header>\n:::\n::::\n'
        manifest, _ = self.build(source)
        self.assertFalse(manifest['slides'][0]['cssEditable'])

    def test_comments_unknown_islands_and_notes_preserved_in_source(self):
        source = HEADER + '## Keep source details\nText\n<!-- author comment -->\n:::notes\nSpeaker context\n:::\n:::html\n<div>Opaque HTML</div>\n:::\n'
        manifest, html = self.build(source)
        self.assertIn('<!-- author comment -->', manifest['slides'][0]['source'])
        self.assertIn(':::notes\nSpeaker context', manifest['slides'][0]['source'])
        self.assertIn('<div>Opaque HTML</div>', html)

    def test_project_merged_handles_have_owning_files(self):
        (self.root / '_presentation.md').write_text(HEADER)
        (self.root / '01.remarp.md').write_text(HEADER + CARDS)
        (self.root / '02.remarp.md').write_text(HEADER + CANVAS)
        with contextlib.redirect_stdout(io.StringIO()):
            result = compiler.main(['studio', str(self.root), '--output', str(self.output)])
        self.assertEqual(result, 0)
        manifest = json.loads((self.output / 'studio.json').read_text())
        self.assertEqual([(s['id'], s['file']) for s in manifest['slides']], [('s0', '01.remarp.md'), ('s1', '02.remarp.md')])
        self.assertTrue(any(n['id'] == 's1-canvas-a' for n in manifest['slides'][1]['nodes']))

    def test_legacy_block_grouping_uses_actual_output_order(self):
        text = HEADER + '<!-- block: alpha -->\n## Alpha initial\nText\n---\n<!-- block: beta -->\n## Beta slide\nText\n---\n<!-- block: alpha -->\n## Alpha later\nText\n'
        manifest, _ = self.build(text)
        self.assertEqual([s['title'] for s in manifest['slides']], ['Alpha initial', 'Alpha later', 'Beta slide'])
        for s in manifest['slides']:
            self.assertEqual(text_at(text, s['range']), s['source'])

    @unittest.skipUnless(compiler.HAS_YAML, 'Nested theme front matter requires optional PyYAML')
    def test_the_studio_page_carries_the_same_theme_settings_as_the_built_deck(self):
        # Only a theme directory's manifest fills in the footer text, the auto logo and the colors, so the
        # raw frontmatter alone would drop all three from the studio page.
        brand = self.root / 'brand'
        brand.mkdir()
        (brand / 'theme-manifest.json').write_text(json.dumps({
            'footer_text': 'Manifest footer text',
            'logos': [{'filename': 'logo_manifest.png'}],
            'colors': {'accent1': '#123456'}}), encoding='utf-8')
        themed = HEADER.replace('title: Studio Test\n', 'title: Studio Test\ntheme:\n  source: ./brand\n')
        _, html = self.build(themed + CARDS)
        built = (self.output / 'default.html').read_text()
        for marker in ('Manifest footer text', 'logo_manifest.png', '#123456'):
            self.assertIn(marker, built)
            self.assertIn(marker, html)

    def test_a_comment_only_segment_that_repeats_a_later_slide_does_not_take_its_span(self):
        later = '## Later slide\nBody text\n'
        text = HEADER + '<!--\n' + later + '-->\n---\n' + later
        manifest, _ = self.build(text)
        self.assertEqual(len(manifest['slides']), 1)
        slide = manifest['slides'][0]
        self.assertEqual(text_at(text, slide['range']), slide['source'])
        self.assertGreater(slide['range']['start'], text.index('-->'))

    def test_critical_validation_does_not_produce_editor_map(self):
        source = self.root / 'invalid.remarp.md'
        source.write_text(HEADER + '@type: canvas\n## Too complex\n:::canvas\n' + '\n'.join(f'box n{i} "Node {i}" at {i*100},100 size 90,40 color accent' for i in range(8)) + '\n:::\n')
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(compiler.main(['studio', str(source), '--output', str(self.output)]), 1)
        self.assertFalse((self.output / 'studio.json').exists())


if __name__ == '__main__':
    unittest.main()
