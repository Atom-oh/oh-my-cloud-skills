"""Behavioral regression tests for the Remarp source/build contract."""
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py"
sys.dont_write_bytecode = True
SPEC = importlib.util.spec_from_file_location("remarp_contract", SCRIPT)
remarp = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = remarp
SPEC.loader.exec_module(remarp)
FRONT = "---\nremarp: true\n---\n"
CANVAS = '@type: canvas\n## Flow\n\n:::canvas\nbox api "API" at 100,180 size 130,55 color #FF9900 step 1\n:::\n'


class RemarpContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="remarp-contract-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def write(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def cli(self, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *map(str, args)],
            capture_output=True, text=True,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )

    def slides(self, text):
        _, blocks = remarp.RemarpParser(text).parse()
        return [slide for block in blocks.values() for slide in block]

    def test_code_fences_are_literal(self):
        for fence in ("```", "````", "~~~"):
            for newline in ("\n", "\r\n"):
                with self.subTest(fence=fence, newline=repr(newline)):
                    content = (FRONT + "## Configuration\n\n" + fence +
                               "yaml\nkind: Service\n---\n@type: quiz\n"
                               ":::notes\nliteral note {.click}\n:::\n## Literal heading\n<!-- block: literal -->\n" + fence + "\n")
                    slides = self.slides(content.replace("\n", newline))
                    self.assertEqual(1, len(slides))
                    self.assertNotEqual(remarp.SlideType.QUIZ, slides[0].slide_type)
                    self.assertIsNone(slides[0].notes)
                    self.assertIn("@type: quiz", slides[0].content)
                    self.assertIn(":::notes", slides[0].content)
                    rendered = remarp.RemarpHTMLGenerator().slide_to_html(slides[0])
                    self.assertIn("kind: Service", re.sub("<[^>]+>", "", rendered))
                    self.assertNotIn("<p>~~~", rendered)
                    self.assertIn("{.click}", rendered)
                    self.assertIn("## Literal heading", rendered)
                    self.assertIn("&lt;!-- block: literal --&gt;", rendered)

    def test_long_fence_contains_short_fence(self):
        text = FRONT + "## Example\n\n````markdown\n```\n---\n```\n````\n---\n## Next\n"
        self.assertEqual(2, len(self.slides(text)))

    def test_literal_examples_do_not_trigger_validation(self):
        source = self.write("01.md", FRONT + "## Example\n\n```markdown\n" +
                            "\n".join("- item" for _ in range(10)) + "\n```\n")
        result = self.cli("validate", source, "--json")
        findings = json.loads(result.stdout)
        self.assertFalse(any(f["rule"] == "CONTENT_OVERFLOW" for f in findings))
        self.assertEqual(0, result.returncode)

    def test_discovery_deduplicates_and_excludes_readme(self):
        self.write("01.remarp.md", FRONT + "## One\n")
        self.write("README.md", "# README\n" + "- docs\n" * 10)
        builder = remarp.RemarpProjectBuilder(str(self.root))
        self.assertTrue(builder.load_project())
        self.assertEqual(["01"], list(builder.blocks))
        result = self.cli("build", self.root)
        self.assertEqual(0, result.returncode, result.stderr + result.stdout)
        output = (self.root / "index.html").read_text()
        self.assertEqual(1, len(re.findall(r'<div class="slide(?: |")', output)))
        findings = json.loads(self.cli("validate", self.root, "--json").stdout)
        self.assertFalse(any(Path(f["file"]).name == "README.md" for f in findings))

    def test_duplicate_block_names_rejected(self):
        self.write("01.md", FRONT + "## First\n")
        self.write("01.remarp.md", FRONT + "## Second\n")
        self.assertNotEqual(0, self.cli("build", self.root).returncode)

    def test_merged_generated_ids_and_css_are_unique(self):
        for name in ("01", "02"):
            self.write(name + ".md", FRONT + CANVAS +
                       "\n:::css\n<header>\ncolor: red\n</header>\n:::\n")
        result = self.cli("build", self.root)
        self.assertEqual(0, result.returncode, result.stderr + result.stdout)
        output = (self.root / "index.html").read_text()
        ids = re.findall(r'<canvas id="([^"]+)"', output)
        self.assertEqual(2, len(ids))
        self.assertEqual(2, len(set(ids)))
        slide_ids = re.findall(r'<div class="slide" data-remarp-id="([^"]+)"', output)
        self.assertEqual(2, len(set(slide_ids)))
        for slide_id in slide_ids:
            self.assertIn(f'[data-remarp-id="{slide_id}-header"]', output)

    def test_duplicate_explicit_canvas_ids_rejected(self):
        for name in ("01", "02"):
            self.write(name + ".md", FRONT + CANVAS.replace(
                "@type: canvas", "@type: canvas\n@canvas-id: repeated"))
        result = self.cli("build", self.root)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("repeated", result.stdout + result.stderr)

    @unittest.skipUnless(remarp.HAS_YAML, "Example requires optional PyYAML")
    def test_sync_refreshes_global_and_merged_output_without_mtime_dependency(self):
        main = self.write("_presentation.md",
                          '---\nremarp: true\ntitle: Talk\nratio: "16:9"\n'
                          'theme:\n  footer: BeforeFooter\n---\n')
        block = self.write("01.md", FRONT + "## BeforeTitle\n")
        self.assertEqual(0, self.cli("build", self.root).returncode)
        block.write_text(FRONT + "## AfterTitle\n", encoding="utf-8")
        os.utime(block, (1, 1))
        main.write_text(main.read_text().replace("BeforeFooter", "AfterFooter"))
        result = self.cli("sync", self.root)
        self.assertEqual(0, result.returncode, result.stderr + result.stdout)
        for name in ("01.html", "index.html"):
            text = (self.root / name).read_text()
            self.assertIn("AfterTitle", text)
            self.assertIn("AfterFooter", text)
        self.write("02.md", FRONT + "## New block\n")
        self.assertEqual(0, self.cli("sync", self.root).returncode)
        self.assertIn("02.html", (self.root / "toc.html").read_text())
        (self.root / "02.md").unlink()
        self.assertEqual(0, self.cli("sync", self.root).returncode)
        self.assertNotIn("New block", (self.root / "index.html").read_text())

    def test_standalone_build_copies_assets(self):
        source = self.write("talk.md", FRONT + "## Title\n")
        result = self.cli("build", source)
        self.assertEqual(0, result.returncode, result.stderr + result.stdout)
        output = self.root / "slides/default.html"
        for asset in re.findall(r'(?:href|src)="(\./common/[^"]+)"', output.read_text()):
            self.assertTrue((output.parent / asset).is_file(), asset)

    def test_invalid_input_is_json_failure(self):
        for target in (self.root / "missing", self.root):
            with self.subTest(target=target):
                result = self.cli("validate", target, "--json")
                self.assertNotEqual(0, result.returncode)
                self.assertTrue(any(f["severity"] == "CRITICAL"
                                    for f in json.loads(result.stdout)))
        self.assertNotEqual(0, self.cli("build", self.root / "missing").returncode)
        self.write('_presentation.md', '---\nremarp: true\nratio: "16:9"\n---\n')
        for command in ('validate', 'build', 'sync'):
            self.assertNotEqual(0, self.cli(command, self.root).returncode)


    def test_critical_findings_reject_build_and_sync(self):
        self.write("01.md", FRONT + "## Too many\n" + "- item\n" * 8)
        for command in ("validate", "build", "sync"):
            with self.subTest(command=command):
                result = self.cli(command, self.root)
                self.assertNotEqual(0, result.returncode)
        self.assertFalse((self.root / "index.html").exists())

    def test_invalid_yaml_is_not_silently_recovered(self):
        source = self.write("01.md", "---\nremarp: true\ntheme: [\n---\n## Title\n")
        result = self.cli("validate", source, "--json")
        self.assertNotEqual(0, result.returncode)
        self.assertTrue(any(f["severity"] == "CRITICAL" for f in json.loads(result.stdout)))

    @unittest.skipUnless(remarp.HAS_YAML, "Example requires optional PyYAML")
    def test_quickstart_compiles(self):
        guide = SCRIPT.parents[1] / 'REMARP.md'
        example = re.search(r'```markdown\n(.*?)\n```', guide.read_text(), re.DOTALL).group(1)
        source = self.write('quickstart.remarp.md', example)
        result = self.cli('build', source)
        self.assertEqual(0, result.returncode, result.stderr + result.stdout)
        output = (self.root / 'slides/default.html').read_text()
        self.assertIn('<canvas', output)
        self.assertIn('drawIcon(', output)

    @unittest.skipUnless(remarp.HAS_YAML, "Example requires optional PyYAML")
    def test_extension_readme_example_compiles(self):
        example = re.search(r'```markdown\n(.*?)\n```', (ROOT / 'tools/remarp-vscode/README.md').read_text(), re.DOTALL).group(1)
        source = self.write('example.remarp.md', example)
        result = self.cli('build', source)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        output = (self.root / 'slides/default.html').read_text()
        for content in ('<canvas', 'API', 'Service', 'First option', 'Second option',
                        'data-remarp-id="s0-card-0"', 'Presenter guidance.'):
            self.assertIn(content, output)

    def test_language_override_applies_to_each_project_output(self):
        self.write('01.md', FRONT.replace('remarp: true', 'remarp: true\nlang: ko') + '## Title\n')
        result = self.cli('build', self.root, '--lang', 'en')
        self.assertEqual(0, result.returncode)
        for name in ('01.html', 'index.html', 'toc.html'):
            self.assertIn('<html lang="en">', (self.root / name).read_text())

    def test_h1_code_example_is_not_a_title_slide(self):
        slide = self.slides(FRONT + '# Python example\n\n```python\nfirst = 1\nsecond = 2\nprint(first + second)\n```\n')[0]
        self.assertNotEqual(remarp.SlideType.TITLE, slide.slide_type)
        self.assertIn('print', remarp.RemarpHTMLGenerator().slide_to_html(slide))

    def test_partial_build_preserves_other_pages_icons(self):
        for name, icon in (('01', 'EC2'), ('02', 'S3')):
            self.write(name + '.md', FRONT + f'## {icon}\n\n:::canvas\nicon api "{icon}" at 100,180 size 48\n:::\n')
        self.assertEqual(0, self.cli('build', self.root).returncode)
        self.assertEqual(0, self.cli('build', self.root, '--block', '01').returncode)
        self.assertTrue((self.root / 'common/aws-icons/services/Arch_Amazon-Simple-Storage-Service_48.svg').is_file())

    def test_archify_asset_identity_survives_merged_numbering(self):
        self.write('01.md', FRONT + '## Intro\n')
        slides = []
        for title in ('DiagramA', 'DiagramB'):
            spec = json.dumps({'title': title, 'components': [{'id': 'api', 'label': 'API'}]})
            slides.append(f'## {title}\n\n:::archify icons=off\n{spec}\n:::\n')
        self.write('02.md', FRONT + '\n---\n'.join(slides))
        backend = SimpleNamespace(resolve_archify_dir=lambda: self.root,
                                  check_pin=lambda path: (True, 'PIN'),
                                  inject_icons=lambda content, mapping: (content, 0))
        def render(args, **kwargs):
            if args[2] == 'render':
                title = json.loads(Path(args[-2]).read_text())['title']
                Path(args[-1]).write_text(title)
            return subprocess.CompletedProcess(args, 0, '', '')
        with patch.object(remarp, '_load_archify_icons', return_value=backend), patch.object(remarp.subprocess, 'run', side_effect=render):
            builder = remarp.RemarpProjectBuilder(str(self.root))
            builder.load_project()
            builder.build_all()
        for name in ('02.html', 'index.html'):
            refs = re.findall(r'<iframe class="archify-diagram" src="([^"]+)"', (self.root / name).read_text())
            self.assertEqual(['DiagramA', 'DiagramB'], [(self.root / ref).read_text() for ref in refs])

    @unittest.skipUnless(remarp.HAS_YAML, "Example requires optional PyYAML")
    def test_footer_strings_generate_valid_javascript(self):
        footer = "Developer's guide </script>"
        source = self.write('01.md', '---\nremarp: true\ntheme: {footer: ' + json.dumps(footer) + '}\n---\n## Title\n')
        self.assertEqual(0, self.cli('build', source).returncode)
        output = (self.root / 'slides/default.html').read_text()
        for script in re.findall(r'<script>(.*?)</script>', output, re.DOTALL):
            result = subprocess.run(['node', '--check'], input=script, text=True, capture_output=True)
            self.assertEqual(0, result.returncode, result.stderr)

    def test_click_block_preserves_fenced_legacy_directives(self):
        source = FRONT + '## Literal\n\n:::click\n```text\n<!-- type: quiz -->\n```\n:::\n'
        slide = self.slides(source)[0]
        self.assertNotEqual(remarp.SlideType.QUIZ, slide.slide_type)
        self.assertIn('&lt;!-- type: quiz --&gt;', remarp.RemarpHTMLGenerator().slide_to_html(slide))

    def test_flat_frontmatter_blank_lines_without_pyyaml(self):
        with patch.object(remarp, 'HAS_YAML', False):
            config, blocks = remarp.RemarpParser('---\nremarp: true\n\ntitle: Flat\n---\n## Slide\n').parse()
        self.assertEqual('Flat', config['title'])
        self.assertTrue(blocks)

    def test_issues_json_reports_empty_and_invalid_sources(self):
        source = self.write('01.md', FRONT + '## Title\n')
        self.assertEqual([], json.loads(self.cli('issues', self.root, '--json').stdout))
        source.write_text('---\nremarp: true\ntheme: [\n---\n## Title\n')
        result = self.cli('issues', self.root, '--json')
        self.assertNotEqual(0, result.returncode)
        self.assertIn('error', json.loads(result.stdout))

    def test_block_build_has_assets_and_unknown_block_fails(self):
        self.write("01.md", FRONT + "## Title\n")
        result = self.cli("build", self.root, "--block", "01")
        self.assertEqual(0, result.returncode, result.stderr + result.stdout)
        self.assertTrue((self.root / "common/slide-framework.js").is_file())
        self.assertNotEqual(0, self.cli("build", self.root, "--block", "absent").returncode)


EXPORT_SCRIPT = ROOT / "plugins/aws-content-plugin/skills/reactive-presentation/scripts/export_pptx.py"
CHECK_SCRIPT = ROOT / "plugins/aws-content-plugin/skills/reactive-presentation/scripts/check_deck.py"
EXPORT_UTILS = ROOT / "plugins/aws-content-plugin/skills/reactive-presentation/assets/export-utils.js"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


export = _load("remarp_export_pptx", EXPORT_SCRIPT)


class RemarpDetailContractTests(unittest.TestCase):
    """Detail layer, block markers and overlay wiring (reactive-nav-detail Task 2)."""

    setUp = RemarpContractTests.setUp
    write = RemarpContractTests.write
    cli = RemarpContractTests.cli

    def build_one(self, text):
        source = self.write("talk.md", text)
        result = self.cli("build", source)
        self.assertEqual(0, result.returncode, result.stderr + result.stdout)
        return (self.root / "slides/default.html").read_text(encoding="utf-8")

    def validate_text(self, text):
        source = self.write("check.md", FRONT + text)
        with patch("sys.stdout"):
            return remarp.validate_presentation(source)

    @staticmethod
    def rules(findings):
        return {(f["severity"], f["rule"]) for f in findings}

    def test_tip_inline_renders_span(self):
        html = self.build_one(FRONT + '## T\n\n표: [UDP 8472]{tip="Cilium VXLAN 포트"}\n')
        self.assertIn('<span class="rp-detail" tabindex="0" data-tip="Cilium VXLAN 포트">UDP 8472</span>', html)

    def test_tip_attribute_is_escaped(self):
        html = self.build_one(FRONT + '## T\n\n[a]{tip="x \\"q\\" <b> & y"}\n')
        self.assertIn('data-tip="x &quot;q&quot; &lt;b&gt; &amp; y"', html)

    def test_tip_value_not_markdown_converted(self):
        html = self.build_one(FRONT + '## T\n\n[a]{tip="**a** `b`"}\n')
        self.assertIn('data-tip="**a** `b`"', html)

    def test_tip_inside_code_span_is_literal(self):
        html = self.build_one(FRONT + '## T\n\n`[a]{tip="x"}`\n')
        self.assertIn('<code>[a]{tip=', html)
        self.assertNotIn('<span class="rp-detail"', html)

    def test_detail_block_moves_to_store(self):
        src = (FRONT + '## T\n\n[UDP 8472]{detail=vxlan}\n\n'
               ':::detail vxlan "UDP 8472가 필요한 이유"\ntip: hybrid 노드 간 VXLAN\n\n'
               '- direct routing, Gateway 모두 필요\n:::\n')
        html = self.build_one(src)
        self.assertIn('data-detail="vxlan" data-tip="hybrid 노드 간 VXLAN"', html)
        self.assertRegex(html, r'(?s)<div class="rp-detail-store" hidden><section data-detail-id="vxlan" '
                               r'data-title="UDP 8472가 필요한 이유"[^>]*>.*<li>direct routing, Gateway 모두 필요</li>')
        self.assertNotIn(':::detail', html)

    def test_detail_reference_before_definition_gets_title_tip(self):
        src = FRONT + '## T\n\n[x]{detail=d}\n\n:::detail d "제목만"\n본문\n:::\n'
        self.assertIn('data-detail="d" data-tip="제목만"', self.build_one(src))

    def test_detail_in_table_cell(self):
        html = self.build_one(FRONT + '## T\n\n| a | b |\n|---|---|\n| 1 | [x]{tip="t"} |\n')
        self.assertRegex(html, r'<td[^>]*><span class="rp-detail" tabindex="0" data-tip="t">x</span>')

    def test_detail_ref_missing_is_critical(self):
        cases = (
            '## T\n\n[x]{detail=nope}\n',
            '## T\n\n:::html\n<span class="rp-detail" data-detail="nope">x</span>\n:::\n',
            '## T\n\n:::tab "A"\n[x]{detail=nope}\n:::\n',
            '## T\n\n:::left\n[x]{detail=nope}\n:::\n\n:::right\ny\n:::\n',
        )
        for src in cases:
            with self.subTest(src=src):
                self.assertIn(("CRITICAL", "DETAIL_REF"), self.rules(self.validate_text(src)))

    def test_detail_ref_ok_is_clean(self):
        src = '## T\n\n[x]{detail=d}\n\n:::detail d "t"\nbody\n:::\n'
        self.assertNotIn("DETAIL_REF", {r for _, r in self.rules(self.validate_text(src))})

    def test_detail_duplicate_and_nested_are_critical(self):
        dup = '## T\n\n[x]{detail=d}\n\n:::detail d "a"\n1\n:::\n\n:::detail d "b"\n2\n:::\n'
        nested = '## T\n\n[x]{detail=d}\n\n:::tab "A"\n:::detail d "a"\n1\n:::\n:::\n'
        for src in (dup, nested):
            with self.subTest(src=src):
                self.assertIn(("CRITICAL", "DETAIL_REF"), self.rules(self.validate_text(src)))

    def test_detail_title_and_block_title_escaped(self):
        html = self.build_one(FRONT + '## T\n\n[x]{detail=d}\n\n:::detail d "a <b> & \\"c\\""\nbody\n:::\n')
        self.assertIn('data-title="a &lt;b&gt; &amp; &quot;c&quot;"', html)
        self.write("_presentation.md", "---\nremarp: true\ntitle: Deck\n---\n")
        self.write("01-x.md", "---\nremarp: true\ntitle: \"<x>\"\n---\n## S\n")
        result = self.cli("build", self.root)
        self.assertEqual(0, result.returncode, result.stderr + result.stdout)
        self.assertIn('data-block-title="&lt;x&gt;"', (self.root / "index.html").read_text(encoding="utf-8"))

    def test_detail_store_data_text_lines(self):
        html = self.build_one(FRONT + '## T\n\n[x]{detail=d}\n\n:::detail d "t"\n- a\n- b\n:::\n')
        m = re.search(r'data-detail-id="d"[^>]*data-text="([^"]*)"', html)
        self.assertIsNotNone(m, html)
        self.assertIn(m.group(1), ("- a&#10;- b", "- a\n- b"))

    def test_detail_data_text_keeps_code_identifiers(self):
        src = (FRONT + '## T\n\n[x]{detail=d}\n\n:::detail d "t"\n'
               '`SNAT_EXCLUDE_CIDRS` and *em*\n\n```\nfoo_bar_baz = 1\n```\n:::\n')
        html = self.build_one(src)
        m = re.search(r'data-detail-id="d"[^>]*data-text="([^"]*)"', html)
        self.assertIsNotNone(m, html)
        text = m.group(1)
        self.assertIn("SNAT_EXCLUDE_CIDRS", text)
        self.assertIn("foo_bar_baz = 1", text)
        self.assertIn("em", text)
        self.assertNotIn("*", text)

    def test_detail_ref_ignores_urls_and_escaped_tags_in_prose(self):
        src = ('## T\n\nSee https://example.com/?data-detail="u" and '
               '&lt;span data-detail="esc"&gt; in prose.\n')
        self.assertNotIn("DETAIL_REF", {r for _, r in self.rules(self.validate_text(src))})

    def test_detail_ref_url_strip_keeps_code_exclusion_and_adjacent_terms(self):
        in_pre = '## T\n\n:::html\n<pre>data-detail="p" https://example.com/x</pre>\n:::\n'
        self.assertNotIn("DETAIL_REF", {r for _, r in self.rules(self.validate_text(in_pre))})
        for src in ('## T\n\nhttps://example.com/[t]{detail=nope}\n',
                    '## T\n\n&lt;b&gt;[t]{detail=nope}&lt;/b&gt;\n',
                    '## T\n\nUse &lt;span [class]{detail=missing}&gt; in the example.\n',
                    '## T\n\nSee https://example.com/?q=[t]{detail=nope2}\n'):
            with self.subTest(src=src):
                self.assertIn(("CRITICAL", "DETAIL_REF"), self.rules(self.validate_text(src)))

    def test_title_slide_meta_skips_detail_placeholder(self):
        src = (FRONT + '@type: title\n# Deck\n\nPresenter Name\n\n'
               '[x]{detail=d}\n\n:::detail d "t"\nbody\n:::\n')
        html = self.build_one(src)
        self.assertNotIn("__BLOCK:", html)

    def test_detail_plain_text_tracks_opening_fence(self):
        text = remarp._detail_plain_text("````\n```\n*keep_this*\n```\n````\nafter *em*")
        self.assertEqual(text.split("\n"), ["```", "*keep_this*", "```", "after em"])

    def test_merged_index_marks_blocks(self):
        self.write("_presentation.md", "---\nremarp: true\ntitle: 덱\n---\n")
        self.write("01-a.md", "---\nremarp: true\ntitle: 개요\n---\n## S1\n")
        self.write("02-b.md", "---\nremarp: true\n---\n# 2부: 네트워킹\n\n---\n## S2\n")
        self.write("03-c.md", "---\nremarp: true\n---\n## S3\n")
        result = self.cli("build", self.root)
        self.assertEqual(0, result.returncode, result.stderr + result.stdout)
        index = (self.root / "index.html").read_text(encoding="utf-8")
        self.assertIn('data-block="01-a" data-block-title="개요"', index)
        self.assertIn('data-block-title="2부: 네트워킹"', index)
        self.assertIn('data-block-title="03-c"', index)
        self.assertNotIn('data-block-title="덱"', index)

    def test_single_block_build_marks_block(self):
        html = self.build_one("---\nremarp: true\ntitle: 단독\n---\n## S\n")
        self.assertRegex(html, r'class="slide[^"]*"[^>]*data-block="[^"]+"')

    def test_wrap_html_loads_overlay_assets(self):
        html = self.build_one(FRONT + "## Title\n")
        self.assertIn('href="./common/deck-overlay.css"', html)
        self.assertIn('src="./common/deck-overlay.js"', html)
        for name in ("deck-detail", "deck-nav"):
            self.assertIn(f'href="./common/{name}.css"', html)
            self.assertIn(f'src="./common/{name}.js"', html)
        self.assertLess(html.index("deck-overlay.js"), html.index("slide-framework.js"))
        self.assertLess(html.index("theme.css"), html.index("deck-overlay.css"))
        for suffix in ("css", "js"):
            self.assertLess(html.index(f"deck-overlay.{suffix}"), html.index(f"deck-detail.{suffix}"))
            self.assertLess(html.index(f"deck-detail.{suffix}"), html.index(f"deck-nav.{suffix}"))
        self.assertLess(html.index("deck-nav.js"), html.index("slide-framework.js"))
        output = self.root / "slides/default.html"
        for asset in re.findall(r'(?:href|src)="(\./common/[^"]+)"', html):
            self.assertTrue((output.parent / asset).is_file(), asset)

    def test_export_details_to_text(self):
        self.assertEqual(export._details_to_text([{"title": "A", "text": "b"}], "ko"), "[디테일]\n- A: b")
        self.assertEqual(export._details_to_text([{"title": "A", "text": "b"}], "en"), "[Details]\n- A: b")
        self.assertEqual(export._details_to_text([], "en"), "")
        self.assertEqual(export._details_to_text([{"title": "", "text": "b"}], "en"), "[Details]\n- b")

    @unittest.skipUnless(shutil.which("node"), "node not installed")
    def test_browser_export_detail_notes_match_python(self):
        script = (
            "const fs = require('fs');"
            "const src = fs.readFileSync(process.argv[1], 'utf8') + '\\nmodule.exports = ExportUtils;';"
            "const m = { exports: {} }; new Function('module', src)(m);"
            "const sec = (t, x, body = '') => ({ textContent: body, getAttribute: k => (k === 'data-title' ? t : x) });"
            "const slide = { querySelectorAll: () => [sec('A', 'b'), sec('', 'c'), sec('', ''), sec('D', null, 'body only')] };"
            "process.stdout.write(m.exports._detailNotesFromSlide(slide, 'ko-KR'));")
        result = subprocess.run(["node", "-e", script, str(EXPORT_UTILS)], capture_output=True, text=True)
        self.assertEqual(0, result.returncode, result.stderr)
        expected = export._details_to_text([{"title": "A", "text": "b"}, {"title": "", "text": "c"},
                                            {"title": "D", "text": "body only"}], "ko")
        self.assertEqual(expected, result.stdout)

    def test_export_prepare_hides_overlay(self):
        self.assertIn(".rp-overlay-ui", export._PREPARE_JS)
        self.assertIn(".rp-detail::after", export._PREPARE_JS)

    def check_deck_findings(self, html):
        deck = self.root / "deck"
        deck.mkdir(exist_ok=True)
        (deck / "index.html").write_text(html, encoding="utf-8")
        result = subprocess.run([sys.executable, str(CHECK_SCRIPT), str(deck), "--json"],
                                capture_output=True, text=True)
        return json.loads(result.stdout or "[]")

    def test_check_deck_missing_overlay_warns(self):
        base = ('<html><head><link rel="stylesheet" href="./common/theme.css"></head><body>'
                '<div class="slide-deck"><div class="slide"><h2>T</h2><p>{body}</p></div></div>'
                '<script src="./common/animation-utils.js"></script><script src="./common/slide-framework.js"></script>'
                '<script src="./common/quiz-component.js"></script><script src="./common/presenter-view.js"></script>'
                '<script>const deck = new SlideFramework({{}});</script></body></html>')
        with_term = self.check_deck_findings(base.format(body='<span class="rp-detail" data-tip="t">x</span>'))
        findings = with_term if isinstance(with_term, list) else with_term.get("findings", [])
        self.assertIn(("WARN", "MISSING_OVERLAY"),
                      {(f.get("severity"), f.get("rule")) for f in findings})
        self.assertNotIn("deck-detail", {f.get("file") for f in findings})
        plain = self.check_deck_findings(base.format(body="x"))
        findings = plain if isinstance(plain, list) else plain.get("findings", [])
        self.assertNotIn("MISSING_OVERLAY", {f.get("rule") for f in findings})

    def test_malformed_detail_ref_is_critical(self):
        for src in ('## T\n\n[x]{detail=}\n', '## T\n\n[x]{detail=bad id}\n', '## T\n\n[x]{detail=a.b}\n'):
            with self.subTest(src=src):
                self.assertIn(("CRITICAL", "DETAIL_REF"), self.rules(self.validate_text(src)))

    def test_stray_backtick_keeps_detail_ref_check(self):
        src = "## T\n\nan unpaired ` backtick\n\nthen [x]{detail=nope} and `code`\n"
        self.assertIn(("CRITICAL", "DETAIL_REF"), self.rules(self.validate_text(src)))

    def test_detail_ref_ignores_script_and_css_bodies(self):
        src = ('## T\n\nbody\n\n:::script\ndocument.querySelector(\'[data-detail="x"]\');\n:::\n\n'
               ':::css\n[data-detail="y"] { outline: 0; }\n:::\n')
        self.assertNotIn("DETAIL_REF", {r for _, r in self.rules(self.validate_text(src))})

    def test_detail_ref_ignores_html_comments_and_code_examples(self):
        examples = ('<!-- <span data-detail="old">x</span> -->\n'
                    '<code>&lt;span data-detail="ex"&gt;</code>\n'
                    '<pre>data-detail="p"</pre>\n'
                    '<pre>[x]{detail=inpre}</pre>\n'
                    '<script>document.querySelector(\'[data-detail="js"]\')</script>\n'
                    '<style>[data-detail="css"] { color: red; }</style>\n')
        clean = '## T\n\n:::html\n' + examples + ':::\n'
        self.assertNotIn("DETAIL_REF", {r for _, r in self.rules(self.validate_text(clean))})
        real = ('## T\n\n:::html\n' + examples
                + '<span class="rp-detail" data-detail="nope">y</span>\n:::\n')
        self.assertIn(("CRITICAL", "DETAIL_REF"), self.rules(self.validate_text(real)))

    def test_single_file_blocks_get_their_own_titles(self):
        src = ("---\nremarp: true\ntitle: 덱\nblocks:\n  - name: a\n    title: \"A부\"\n  - name: b\n    title: \"B부\"\n---\n"
               "<!-- block: a -->\n## S1\n\n---\n<!-- block: b -->\n## S2\n")
        source = self.write("multi.md", src)
        result = self.cli("build", source)
        self.assertEqual(0, result.returncode, result.stderr + result.stdout)
        titles = set()
        for html_file in self.root.rglob("*.html"):
            titles.update(re.findall(r'data-block-title="([^"]*)"', html_file.read_text(encoding="utf-8")))
        self.assertTrue({"A부", "B부"} <= titles, titles)

    def test_unclosed_script_block_keeps_detail_ref_check(self):
        src = "## T\n\n:::script\nlet a = 1;\n\n[x]{detail=nope}\n"
        self.assertIn(("CRITICAL", "DETAIL_REF"), self.rules(self.validate_text(src)))

    def test_detail_ref_ignores_inline_refs_in_html_comments(self):
        src = "## T\n\n<!-- [x]{detail=old} -->\n\nbody\n"
        self.assertNotIn("DETAIL_REF", {r for _, r in self.rules(self.validate_text(src))})


if __name__ == "__main__":
    unittest.main()
