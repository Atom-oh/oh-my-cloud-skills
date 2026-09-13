"""Exercise the real cell loop and launchers without contacting any provider."""

import os
from pathlib import Path
import re
import shlex
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/pr-review/run-panel.sh"


class PanelTimeBudgetTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="panel budget ")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.diff = self.root / "diff.txt"
        self.diff.write_text("diff --git a/main.py b/main.py\n-old\n+new\n")
        self.lenses = self.root / "lenses"
        self.lenses.mkdir()
        (self.lenses / "FULL.txt").write_text("Review the supplied diff only.\n")
        self.work = self.root / "work"
        self.env = {
            **os.environ,
            "PATH": str(self.bin) + os.pathsep + os.environ["PATH"],
            "PR_REVIEW_CONFIG_ROOT": str(self.root),
            "PYTHONDONTWRITEBYTECODE": "1",
            "DIFF": str(self.diff),
            "SLOT": str(self.root / "cell.md"),
            "ERR": str(self.root / "cell.err"),
            "ATTEMPTS": str(self.root / "attempts.txt"),
            "T": "3", "RETRIES": "3", "CELL_BUDGET": "9",
        }
        for key in ("PANEL_TIMEOUT", "PANEL_RETRIES"):
            self.env.pop(key, None)
        # Both provider names are always intercepted, including invalid-budget cases.
        self.fake("codex", "printf 'codex-complete\\n'\n")
        self.kiro_fake("printf 'kiro-complete\\n'\n")

    def fake(self, name, body):
        path = self.bin / name
        path.write_text("#!/usr/bin/env bash\nset -uo pipefail\n" + body)
        path.chmod(0o755)

    # run-panel.sh logs `kiro-cli --version` first and then sends each model a fixed
    # no-tools canary prompt (preflight) before any PR diff; a fake that models the review
    # cell must answer NO_TOOLS to that prompt or every Kiro cell is withheld by design.
    KIRO_PRELUDE = (
        '[ "${1:-}" = "--version" ] && { printf "kiro-cli fake\\n"; exit 0; }\n'
        'if [[ "${2:-}" == "Kiro startup safety check."* ]]; then printf "NO_TOOLS\\n"; exit 0; fi\n'
    )

    def kiro_fake(self, body):
        self.fake("kiro-cli", self.KIRO_PRELUDE + body)

    def panel(self, **overrides):
        return subprocess.run(
            ["bash", str(SCRIPT), str(self.diff), str(self.lenses), str(self.work)],
            cwd=self.root, env={**self.env, **overrides},
            capture_output=True, text=True, timeout=20,
        )

    def cell(self, body, **overrides):
        function = re.search(r"(?ms)^try_panel\(\) \{\n.*?^\}", SCRIPT.read_text())
        self.assertIsNotNone(function)
        program = (
            function[0] + "\nlauncher() {\n"
            'printf \'%s\\n\' "$1" >> "$ATTEMPTS"\n' + body + "\n}\n"
            'try_panel codex "$SLOT" "$ERR" launcher "literal argument"\n'
        )
        result = subprocess.run(
            ["bash", "-uo", "pipefail", "-c", program], cwd=self.root,
            env={**self.env, **overrides}, capture_output=True, text=True, timeout=15,
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        attempts = (self.root / "attempts.txt").read_text().splitlines()
        return attempts, (self.root / "cell.md.rc").read_text().strip()

    def test_default_first_allowance_and_kiro_environment(self):
        log = self.root / "timeouts.txt"
        self.fake("timeout",
                  f'printf "%s %s %s\\n" "$1" "$2" "${{3:-}}" >> {shlex.quote(str(log))}\n'
                  '[ "$1" = "--kill-after=5s" ] && shift\n'
                  'shift\nexec "$@"\n')
        # The isolation checks run for the preflight canary too (same kiro_env/launch_kiro).
        self.fake("kiro-cli",
                  '[ "$HOME" = "$PWD" ] || exit 21\n'
                  '[ "${KIRO_API_KEY:-}" = "fixture" ] || exit 22\n'
                  '[ -z "${PARENT_ONLY_CREDENTIAL:-}" ] || exit 23\n'
                  + self.KIRO_PRELUDE +
                  'printf "kiro-complete\\n"\n')
        result = self.panel(KIRO_API_KEY="fixture", PARENT_ONLY_CREDENTIAL="not-for-kiro",
                            KIRO_PREFLIGHT_TIMEOUT="7")
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        calls = [line.split() for line in log.read_text().splitlines()]
        # `timeout 10 kiro-cli --version` (first stderr line of run-panel.sh) is not a cell.
        version = [call for call in calls if call[-1] == "--version"]
        self.assertEqual([["10", "kiro-cli", "--version"]], version, calls)
        calls = [call for call in calls if call[-1] != "--version"]
        self.assertTrue(all(call[0] == "--kill-after=5s" for call in calls), calls)
        # Two preflight calls (one per roster model) run under KIRO_PREFLIGHT_TIMEOUT, not the
        # cell budget; the review cells keep the former worst-case first allowance.
        preflight = [call for call in calls if call[1] == "7"]
        self.assertEqual(["kiro-cli", "kiro-cli"], [call[2] for call in preflight], calls)
        cells = [call for call in calls if call[1] != "7"]
        # SECONDS can tick between establishing the deadline and launching.
        self.assertTrue(all(call[1].isdigit() and 300 < int(call[1]) <= 900 for call in cells), calls)
        self.assertEqual({"codex", "kiro-cli"}, {call[2] for call in cells})
        self.assertIn("kiro-opus/FULL", (self.work / "responded.txt").read_text())

    def test_long_first_attempt_can_finish_without_restart(self):
        calls = self.root / "codex-calls.txt"
        self.fake("codex", f'printf "call\\n" >> {shlex.quote(str(calls))}\n'
                          'sleep 2\nprintf "codex-complete\\n"\n')
        result = self.panel(PANEL_TIMEOUT="1", PANEL_RETRIES="3")
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual(["call"], calls.read_text().splitlines())
        self.assertIn("codex/FULL", (self.work / "responded.txt").read_text())

    def test_term_ignoring_cell_is_killed_after_grace(self):
        completed = self.root / "ignored-term-completed"
        # Finite even against the old launcher: the assertion detects whether
        # the five-second kill grace stopped this child before it completed.
        self.fake("codex", "trap '' TERM\nsleep 9\n"
                          f'printf "completed\\n" > {shlex.quote(str(completed))}\n'
                          'printf "late response\\n"\n')
        result = self.panel(PANEL_TIMEOUT="1", PANEL_RETRIES="1")
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertFalse(completed.exists(), "TERM-ignoring child outlived the kill grace")
        self.assertNotIn("codex/FULL", (self.work / "responded.txt").read_text())

    def test_kiro_hard_kill_diagnostics_do_not_expand_its_api_key(self):
        fixture_key = "fixture-" + "private-kiro-value"
        self.kiro_fake(
                  f'[ "${{KIRO_API_KEY:-}}" = {shlex.quote(fixture_key)} ] || exit 31\n'
                  "trap '' TERM\nsleep 9\n"
                  'printf "completed\\n" > "$PWD/ignored-term-completed"\n')
        result = self.panel(PANEL_TIMEOUT="1", PANEL_RETRIES="1", KIRO_API_KEY=fixture_key)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("(exit=137)", result.stderr)
        diagnostics = result.stdout + result.stderr
        for error_file in self.work.glob("slot/kiro-*.err"):
            diagnostics += error_file.read_text()
        self.assertNotIn(fixture_key, diagnostics)
        self.assertFalse(list(self.work.glob("kiro-cwd/*/ignored-term-completed")))
        self.assertNotIn("kiro-", (self.work / "responded.txt").read_text())

    def test_fast_failure_can_retry_to_success(self):
        attempts, rc = self.cell(
            '[ "$(wc -l < "$ATTEMPTS")" -lt 3 ] && return 7\n'
            'printf "finished\\n"\n'
        )
        self.assertEqual(3, len(attempts))
        self.assertTrue(all(value.isdigit() and 0 < int(value) <= 9 for value in attempts), attempts)
        self.assertEqual("0", rc)
        self.assertEqual("finished\n", (self.root / "cell.md").read_text())

    def test_fast_failures_stop_at_retry_limit(self):
        attempts, rc = self.cell("return 7\n")
        self.assertEqual(3, len(attempts))
        self.assertEqual("7", rc)

    def test_retry_allowance_shrinks_instead_of_resetting(self):
        attempts, rc = self.cell("sleep 1.1\nreturn 7\n")
        self.assertTrue(all(value.isdigit() for value in attempts), attempts)
        remaining = list(map(int, attempts))
        self.assertEqual(3, len(remaining))
        self.assertTrue(all(a > b > 0 for a, b in zip(remaining, remaining[1:])), remaining)
        self.assertEqual("7", rc)

    def test_exhausted_budget_does_not_launch_another_attempt(self):
        attempts, rc = self.cell("sleep 1.1\nreturn 124\n", CELL_BUDGET="1")
        self.assertEqual(["1"], attempts)
        self.assertEqual("124", rc)

    def test_invalid_budgets_fail_before_launch_or_arithmetic_injection(self):
        # Prevent the old seq-based loop from allocating billions of words in
        # red/mutation runs. Invalid inputs must still be rejected before slots.
        self.fake("seq", 'printf "1\\n2\\n3\\n"\n')
        sentinel = self.root / "injected"
        invalid = ("0", "-1", "1.5", "08", "2147483648", "1+1",
                   f"x[$(touch {shlex.quote(str(sentinel))})]")
        for field in ("PANEL_TIMEOUT", "PANEL_RETRIES"):
            for value in invalid:
                with self.subTest(field=field, value=value):
                    result = self.panel(**{field: value})
                    self.assertNotEqual(0, result.returncode)
                    self.assertIn("budget", result.stderr.lower())
                    self.assertFalse(sentinel.exists())
                    self.assertFalse(list(self.work.glob("slot/*.rc")))
                    self.assertFalse(list(self.work.glob("slot/*.md")))
        result = self.panel(PANEL_TIMEOUT="2147483647", PANEL_RETRIES="2")
        self.assertNotEqual(0, result.returncode)
        self.assertIn("budget", result.stderr.lower())


if __name__ == "__main__":
    unittest.main()
