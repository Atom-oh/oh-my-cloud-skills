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

    def test_critical_validation_does_not_produce_editor_map(self):
        source = self.root / 'invalid.remarp.md'
        source.write_text(HEADER + '@type: canvas\n## Too complex\n:::canvas\n' + '\n'.join(f'box n{i} "Node {i}" at {i*100},100 size 90,40 color accent' for i in range(8)) + '\n:::\n')
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(compiler.main(['studio', str(source), '--output', str(self.output)]), 1)
        self.assertFalse((self.output / 'studio.json').exists())


if __name__ == '__main__':
    unittest.main()
