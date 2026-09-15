"""Shared formatting policy: references are prose, assignments require fences."""

from pathlib import Path
import runpy
import unittest

ROOT = Path(__file__).resolve().parents[2]
FORMAT = runpy.run_path(str(
    ROOT / "plugins/co-agent/skills/pr-autofix/scripts/review_format.py"))


class ReviewFormatTests(unittest.TestCase):
    def test_citations_and_sentences_are_not_assignments(self):
        for text in (
            "Authorization: The caller is checked.",
            "**Secrets/credentials:** none introduced.",
            "Token handling: preserved.",
            "See [auth.ts](web/lib/auth.ts:42) for the missing guard.",
            "The guard at auth.ts:42 is missing.",
            "Checked `web/lib/token.ts`: the guard is missing.",
            "Per `docs/decisions/002-auth-and-login.md`: signup is closed.",
            "Authorization: [implementation](web/lib/auth.ts)",
            "Authorization:\nThe caller is checked.",
            "password:",
            "Checked `token`\n===\nThe caller is checked.",
        ):
            with self.subTest(text=text):
                self.assertIsNone(FORMAT["format_violation"](text))

    def test_assignments_remain_blocked_after_prose_or_references(self):
        for text in (
            "password='synthetic'",
            "password=",
            "password\n= 'synthetic'",
            "Set `password` = 'synthetic'.",
            "Set `api_key`: 'synthetic'.",
            'Example: "config.password": "synthetic"',
            "Authorization: Bearer synthetic-example",
            "See auth.ts:42; password='synthetic'",
            "Authorization: caller checked; password='synthetic'",
            "Checked `src/token.ts`: note; token='synthetic'",
            "config.password = 'synthetic'",
            "`config.password`: 'synthetic'",
            "`/config/token` = 'synthetic'",
            "password: !!str synthetic-value",
            "token: &saved synthetic-value",
            "config.password: synthetic-value",
        ):
            with self.subTest(text=text):
                self.assertEqual(FORMAT["format_violation"](text), "unsupported_review_format")


if __name__ == "__main__":
    unittest.main()
