"""Tests for decision-reconcile's verify_quotes.py: quotes must appear in the cited ADR."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "plugins/co-agent/skills/decision-reconcile/scripts/verify_quotes.py"

ADRS = {
    "adrs": [
        {
            "number": 3,
            "file": "ADR-003-auth.md",
            "title": "Adopt JWT auth",
            "status": "Accepted",
            "status_raw": "Accepted",
            "decision": "All services must authenticate with signed JWT tokens.\nSessions are not used.",
            "context": "We need stateless authentication across regions.",
        },
        {
            "number": 9,
            "file": "ADR-009-sessions.md",
            "title": "Adopt server sessions",
            "status": "Accepted",
            "status_raw": "Accepted",
            "decision": "All services shall use server-side sessions stored in Redis.",
            "context": "Revocation must be immediate.",
        },
    ],
    "warnings": [],
    "summary": {},
}


def finding(**over):
    base = {
        "category": "C1",
        "adrs": [3, 9],
        "quotes": [
            {"adr": 3, "text": "All services must authenticate with signed JWT tokens."},
            {"adr": 9, "text": "All services shall use server-side sessions stored in Redis."},
        ],
        "severity": "CRITICAL",
        "why": "Opposite mandates.",
    }
    base.update(over)
    return base


def run(findings, adrs=ADRS):
    with tempfile.TemporaryDirectory() as tmp:
        a = Path(tmp, "adrs.json")
        f = Path(tmp, "findings.json")
        a.write_text(json.dumps(adrs), encoding="utf-8")
        f.write_text(json.dumps(findings), encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, "-I", str(SCRIPT), str(a), str(f)],
            capture_output=True, text=True, check=False,
        )
    return proc


class VerifyQuotes(unittest.TestCase):
    def test_exact_quotes_verify(self):
        out = json.loads(run([finding()]).stdout)
        self.assertEqual(out, {"verified": [0], "dropped": []})

    def test_whitespace_and_line_breaks_are_normalized(self):
        q = {"adr": 3, "text": "All services must authenticate  with signed JWT tokens.\n Sessions are not used."}
        out = json.loads(run([finding(adrs=[3], quotes=[q])]).stdout)
        self.assertEqual(out["verified"], [0])

    def test_ellipsis_splits_into_segments_that_must_each_appear(self):
        ok = {"adr": 3, "text": "All services must authenticate ... Sessions are not used."}
        bad = {"adr": 3, "text": "All services must authenticate ... Sessions are required everywhere."}
        out = json.loads(run([finding(adrs=[3], quotes=[ok]), finding(adrs=[3], quotes=[bad])]).stdout)
        self.assertEqual(out["verified"], [0])
        self.assertEqual([d["index"] for d in out["dropped"]], [1])

    def test_invented_quote_is_dropped(self):
        q = [{"adr": 3, "text": "Tokens expire after fifteen minutes."}]
        out = json.loads(run([finding(adrs=[3], quotes=q)]).stdout)
        self.assertEqual(out["verified"], [])
        self.assertIn("not found in ADR-3", out["dropped"][0]["reason"])

    def test_one_bad_quote_drops_the_finding(self):
        good = {"adr": 3, "text": "All services must authenticate with signed JWT tokens."}
        bad = {"adr": 9, "text": "Sessions live in memcached on every node."}
        out = json.loads(run([finding(quotes=[good, bad])]).stdout)
        self.assertEqual(out["verified"], [])
        self.assertIn("ADR-9", out["dropped"][0]["reason"])

    def test_no_quotes_is_dropped(self):
        out = json.loads(run([finding(quotes=[])]).stdout)
        self.assertEqual(out["dropped"][0]["reason"], "no quotes")

    def test_quote_citing_an_adr_outside_adrs_is_dropped(self):
        q = [{"adr": 9, "text": "All services shall use server-side sessions stored in Redis."}]
        out = json.loads(run([finding(adrs=[3], quotes=q)]).stdout)
        self.assertIn("not listed in adrs", out["dropped"][0]["reason"])

    def test_unknown_adr_number_is_dropped(self):
        q = [{"adr": 42, "text": "All services must authenticate with signed JWT tokens."}]
        out = json.loads(run([finding(adrs=[42], quotes=q)]).stdout)
        self.assertIn("unknown ADR-42", out["dropped"][0]["reason"])

    def test_too_short_a_quote_cannot_verify(self):
        q = [{"adr": 3, "text": "JWT"}]
        out = json.loads(run([finding(adrs=[3], quotes=q)]).stdout)
        self.assertIn("too short", out["dropped"][0]["reason"])

    def test_quote_may_come_from_title_context_or_status(self):
        qs = [
            {"adr": 3, "text": "Adopt JWT auth"},
            {"adr": 3, "text": "We need stateless authentication across regions."},
        ]
        out = json.loads(run([finding(adrs=[3], quotes=qs)]).stdout)
        self.assertEqual(out["verified"], [0])

    def test_quote_text_is_matched_case_sensitively(self):
        q = [{"adr": 3, "text": "all services MUST authenticate with signed jwt tokens."}]
        out = json.loads(run([finding(adrs=[3], quotes=q)]).stdout)
        self.assertEqual(out["verified"], [])

    def test_malformed_input_exits_2_without_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = Path(tmp, "adrs.json")
            f = Path(tmp, "findings.json")
            a.write_text("{not json", encoding="utf-8")
            f.write_text("[]", encoding="utf-8")
            proc = subprocess.run(
                [sys.executable, "-I", str(SCRIPT), str(a), str(f)],
                capture_output=True, text=True, check=False,
            )
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(proc.stdout, "")

    def test_findings_that_are_not_a_list_exit_2(self):
        proc = run({"not": "a list"})
        self.assertEqual(proc.returncode, 2)


COLLECT = ROOT / "plugins/co-agent/skills/decision-reconcile/scripts/collect_adrs.py"
TAIL = "Releases are cut only from tags that the release workflow signed."


def run_with_dir(findings, adrs, decisions_dir):
    with tempfile.TemporaryDirectory() as tmp:
        a = Path(tmp, "adrs.json")
        f = Path(tmp, "findings.json")
        a.write_text(json.dumps(adrs), encoding="utf-8")
        f.write_text(json.dumps(findings), encoding="utf-8")
        cmd = [sys.executable, "-I", str(SCRIPT), str(a), str(f)]
        if decisions_dir is not None:
            cmd += ["--decisions-dir", str(decisions_dir)]
        return subprocess.run(cmd, capture_output=True, text=True, check=False)


class StatusAndFullText(unittest.TestCase):
    def test_an_exact_status_line_verifies_though_it_is_short(self):
        q = [{"adr": 3, "text": "Accepted"}]
        out = json.loads(run([finding(adrs=[3], quotes=q)]).stdout)
        self.assertEqual(out["verified"], [0])

    def test_a_short_quote_that_is_not_the_status_still_fails(self):
        q = [{"adr": 3, "text": "Accept"}]
        out = json.loads(run([finding(adrs=[3], quotes=q)]).stdout)
        self.assertIn("too short", out["dropped"][0]["reason"])

    def test_decisions_dir_adds_the_full_adr_file_to_the_corpus(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp, "decisions")
            d.mkdir()
            (d / "ADR-003-auth.md").write_text("# ADR-3\n\n## Decision\n\nShort. " + TAIL + "\n", encoding="utf-8")
            adrs = {"adrs": [{**ADRS["adrs"][0], "file": "ADR-003-auth.md"}]}
            q = [{"adr": 3, "text": TAIL}]
            without = json.loads(run_with_dir([finding(adrs=[3], quotes=q)], adrs, None).stdout)
            with_dir = json.loads(run_with_dir([finding(adrs=[3], quotes=q)], adrs, d).stdout)
        self.assertEqual(without["verified"], [])
        self.assertEqual(with_dir["verified"], [0])

    def test_the_file_field_cannot_reach_outside_the_decisions_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp, "decisions")
            d.mkdir()
            outside = Path(tmp, "outside")
            outside.mkdir()
            (outside / "secret.md").write_text(TAIL, encoding="utf-8")
            adrs = {"adrs": [{**ADRS["adrs"][0], "file": "../outside/secret.md"}]}
            q = [{"adr": 3, "text": TAIL}]
            out = json.loads(run_with_dir([finding(adrs=[3], quotes=q)], adrs, d).stdout)
        self.assertEqual(out["verified"], [])

    def test_a_quote_past_collect_adrs_clip_verifies_through_the_real_pipeline(self):
        body = " ".join(["Filler sentence number %d keeps the decision long." % i for i in range(40)])
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp, "decisions")
            d.mkdir()
            (d / "ADR-001-long.md").write_text(
                "# ADR-001: Long decision\n\n## Status\n\nAccepted\n\n## Context\n\nShort context.\n\n## Decision\n\n%s %s\n" % (body, TAIL),
                encoding="utf-8",
            )
            collected = subprocess.run([sys.executable, "-I", str(COLLECT), str(d)], capture_output=True, text=True, check=True)
            adrs = json.loads(collected.stdout)
            clipped = adrs["adrs"][0]["decision"]
            self.assertTrue(clipped.endswith("\u2026"), "the fixture decision must exceed the 600 character clip")
            self.assertNotIn(TAIL, clipped)
            f = [{"category": "C3", "adrs": [1], "quotes": [{"adr": 1, "text": TAIL}], "severity": "MAJOR", "why": "x"}]
            out = json.loads(run_with_dir(f, adrs, d).stdout)
            self.assertEqual(out["verified"], [0])
            self.assertEqual(json.loads(run_with_dir(f, adrs, None).stdout)["verified"], [])

    def test_an_option_without_a_value_is_a_usage_error(self):
        proc = subprocess.run([sys.executable, "-I", str(SCRIPT), "a.json", "f.json", "--decisions-dir"], capture_output=True, text=True, check=False)
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(proc.stdout, "")


if __name__ == "__main__":
    unittest.main()
