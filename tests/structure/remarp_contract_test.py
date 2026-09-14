"""Behavioral regression tests for the Remarp source/build contract."""
import importlib.util
import json
import os
from pathlib import Path
import re
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


if __name__ == "__main__":
    unittest.main()
