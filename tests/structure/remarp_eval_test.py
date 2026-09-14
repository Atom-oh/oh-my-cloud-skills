"""Remarp eval regressions; Claude and setup commands are never executed."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "remarp_eval", ROOT / "scripts/eval-skill-behavior.py")
EVAL = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = EVAL
SPEC.loader.exec_module(EVAL)
SOURCE = "---\nremarp: true\n---\n# A source slide\n\nUseful content.\n"
SLIDE = '<section class="slide active"><h1>Fresh slide</h1></section>'


class RemarpEvalTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="remarp eval ")
        self.addCleanup(temporary.cleanup)
        self.work = Path(temporary.name)
        self.project = self.work / "output"
        self.project.mkdir()

    def write(self, name, content):
        path = self.project / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def case(self, **kwargs):
        values = dict(name="regression", description="", skill="reactive-presentation",
                      plugin="aws-content-plugin", timeout=30, prompt="unused",
                      scorers=[], source_path=self.work / "case.yaml")
        values.update(kwargs)
        return EVAL.EvalCase(**values)

    def build(self):
        return EVAL.BuildScorer().run(self.work, {"project_dir": "output/"})

    def compiler(self, html=SLIDE, returncode=0, stderr=""):
        def run(cmd, **kwargs):
            self.assertEqual("build", cmd[2])
            self.assertEqual(self.project, Path(cmd[3]))
            output = Path(cmd[cmd.index("--output") + 1]) if "--output" in cmd else self.project
            output.mkdir(parents=True, exist_ok=True)
            (output / "index.html").write_text(html, encoding="utf-8")
            return subprocess.CompletedProcess(cmd, returncode, "", stderr)
        return run

    def test_setup_uses_disposable_workspace_and_dry_run_skips_it(self):
        # Deliberately destructive-looking input must reach only the subprocess mock.
        case = self.case(setup=["rm -rf relative-fixture"])
        for dry_run in (False, True):
            with self.subTest(dry_run=dry_run):
                runner = EVAL.EvalRunner(ROOT, dry_run=dry_run)
                with patch.object(EVAL.subprocess, "run") as command, \
                     patch.object(runner, "run_claude_print", return_value={"success": True}), \
                     contextlib.redirect_stderr(io.StringIO()):
                    result = runner.run_case(case)
                if dry_run:
                    command.assert_not_called()
                else:
                    command.assert_called_once_with(
                        case.setup[0], shell=True, cwd=result["work_dir"], timeout=30)
                self.assertNotEqual(str(ROOT), result["work_dir"])
                self.assertFalse(Path(result["work_dir"]).exists())

    def test_missing_or_unrecognized_source_cannot_pass_with_existing_output(self):
        self.write("index.html", "<!-- " + SLIDE + " SlideFramework -->")
        self.write("common/theme.css", "")
        for source in (None, "# README\n", "---\ntitle: Notes\n---\nremarp: true\n"):
            with self.subTest(source=source):
                if source is not None:
                    self.write("README.md", source)
                result = self.build()
                self.assertEqual(0, result.score, result.details)

    def test_recognized_source_builds_with_real_compiler(self):
        for name, source in (("deck.md", SOURCE), ("deck.remarp.md", "# Legacy slide\n"),
                             ("quoted.md", SOURCE.replace("remarp: true", 'remarp: "true"')),
                             ("single.md", SOURCE.replace("remarp: true", "remarp: 'true'"))):
            with self.subTest(name=name):
                path = self.write(name, source)
                result = self.build()
                self.assertEqual(100, result.score, result.details)
                path.unlink()

    def test_successful_noop_compiler_cannot_reuse_stale_output(self):
        self.write("deck.md", SOURCE)
        stale = self.write("index.html", SLIDE)
        with patch.object(EVAL.subprocess, "run", return_value=
                          subprocess.CompletedProcess([], 0, "", "")):
            result = self.build()
        self.assertEqual(0, result.score, result.details)
        self.assertEqual(SLIDE, stale.read_text(encoding="utf-8"))

    def test_fresh_output_requires_real_slide_class_element(self):
        self.write("deck.md", SOURCE)
        for html, expected in (
            ("<!-- " + SLIDE + " -->", 0),
            ("<script>const sample = '" + SLIDE + "';</script>", 0),
            ("<textarea>" + SLIDE + "</textarea>", 0),
            ("<template>" + SLIDE + "</template>", 0),
            ("<p>&lt;section class='slide'&gt;</p>", 0),
            ('<section class="slide-deck">No slide</section>', 0),
            ('<html><body></body></html>', 0),
            (SLIDE, 100),
            ("<DIV CLASS='active slide'><h1>Slide</h1></DIV>", 100),
            ("<template><template>" + SLIDE + "</template></template>" + SLIDE, 100),
        ):
            with self.subTest(html=html), \
                 patch.object(EVAL.subprocess, "run", side_effect=self.compiler(html)):
                result = self.build()
                self.assertEqual(expected, result.score, result.details)

    def test_build_errors_are_fatal_and_warnings_keep_existing_penalty(self):
        self.write("deck.md", SOURCE)
        for returncode, stderr, expected in (
            (1, "invalid source", 0), (0, "warning: advisory\n", 90),
            (0, "warning: advisory\n" * 6, 50),
        ):
            with self.subTest(returncode=returncode, stderr=stderr), \
                 patch.object(EVAL.subprocess, "run", side_effect=
                              self.compiler(returncode=returncode, stderr=stderr)):
                self.assertEqual(expected, self.build().score)
        for error in (subprocess.TimeoutExpired("build", 60), OSError("unavailable")):
            with self.subTest(error=error), \
                 patch.object(EVAL.subprocess, "run", side_effect=error):
                self.assertEqual(0, self.build().score)

    def test_build_failure_overrides_average_in_report_json_and_exit_code(self):
        for build_score, expected_total, expected_status in ((0, 0, "FAIL"), (90, 1020, "PASS")):
            with self.subTest(build_score=build_score):
                scores = [EVAL.ScorerResult("html_check", 100, 100)] * 9
                scores += [EVAL.ScorerResult("llm_judge", 30, 30),
                           EVAL.ScorerResult("build_check", build_score, 100)]
                runner = EVAL.EvalRunner(ROOT)
                with patch.object(runner, "run_claude_print", return_value={"success": True}), \
                     patch.object(runner, "run_scorers", return_value=scores):
                    result = runner.run_case(self.case())
                self.assertEqual(expected_total, result["total_score"])
                self.assertEqual(1030, result["max_score"])
                for threshold in (0, 85):
                    self.assertIn("| " + expected_status,
                                  EVAL.format_report([result], threshold))
                    output = io.StringIO()
                    with patch.object(sys, "argv", ["eval", "--skill", "reactive-presentation",
                                                   "--json", "--threshold", str(threshold)]), \
                         patch.object(EVAL.EvalRunner, "run_case", return_value=result), \
                         contextlib.redirect_stdout(output), \
                         self.assertRaises(SystemExit) as exited:
                        EVAL.main()
                    self.assertEqual(1 if build_score == 0 else 0, exited.exception.code)
                    data = json.loads(output.getvalue())[0]
                    self.assertEqual(expected_total, data["total_score"])
                    self.assertEqual(1030, data["max_score"])
                    self.assertEqual(30, data["scorer_results"][-2]["max_score"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
