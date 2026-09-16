"""Shared formatting policy: references are prose, assignments require fences."""

from pathlib import Path
import itertools
import json
import random
import re
import runpy
import subprocess
import sys
import types
import unittest

ROOT = Path(__file__).resolve().parents[2]
FORMAT = runpy.run_path(str(
    ROOT / "plugins/co-agent/skills/pr-autofix/scripts/review_format.py"))
CALLER_KEY = (
    r"(?i:(?<![A-Za-z0-9])[A-Za-z0-9_.:-]*(?:password|passwd|pwd|dsn|api[_-]?key|"
    r"secret|token|credential|passphrase|private[_-]?key|cookie|authorization|"
    r"connection[_-]?string|origin[_-]?verify|AccessKeyId|access[_-]?key[_-]?id)[A-Za-z0-9_.:-]*)"
)
MRA_KEY = CALLER_KEY.replace("authorization|", "authorization|auth(?![A-Za-z])|dockerconfigjson|")
SECURITY_KEY = (
    r"(?i:(?<![A-Za-z0-9])[A-Za-z0-9_.:/()\[\],\t -]*(?:password|passwd|pwd|dsn|api[_\t -]*key|"
    r"secret|token|credential|passphrase|private[_-]?key|cookie|authorization|"
    r"connection[_-]?string|origin[_-]?verify|AccessKeyId|access[_-]?key[_-]?id)[A-Za-z0-9_.:/()\[\],\t -]*)"
)
CALLER_PROFILES = (
    ("Usage", CALLER_KEY, r"[A-Za-z0-9_.:-]+"),
    ("NFM", CALLER_KEY, r"[A-Za-z0-9_.:-]+"),
    ("MRA", MRA_KEY, r"[A-Za-z0-9_.:-]+"),
    ("security", SECURITY_KEY, r"[A-Za-z0-9_.:/()\[\],\t -]+"),
)


class ReviewFormatTests(unittest.TestCase):
    def test_opted_caller_tokens_complete_bounded_operator_free_scans(self):
        script = (
            "import json,re,runpy,sys\n"
            "check=runpy.run_path(sys.argv[1])['format_violation']\n"
            "profile=json.loads(sys.argv[2]);pattern=re.compile(profile[1])\n"
            "tokens=re.compile(profile[2],re.I);value='token-'*6000\n"
            "assert check('The caller was checked.',pattern,key_token_pattern=tokens) is None\n"
            "assert check(value,pattern,key_token_pattern=tokens) is None\n"
            "assert check(value+\"='synthetic'\",pattern,key_token_pattern=tokens) == 'unsupported_review_format'\n"
            "assert check('`'+value+'`',pattern,key_token_pattern=tokens) is None\n"
        )
        for profile in CALLER_PROFILES:
            with self.subTest(caller=profile[0]):
                try:
                    result = subprocess.run(
                        [sys.executable, "-c", script, str(ROOT /
                         "plugins/co-agent/skills/pr-autofix/scripts/review_format.py"),
                         json.dumps(profile)],
                        capture_output=True, text=True, timeout=5,
                    )
                except subprocess.TimeoutExpired:
                    self.fail("Explicit caller token matching stalled on a 36KB input")
                self.assertEqual(result.returncode, 0, result.stderr)

    def matcher_examples(self):
        keys = ("token", "token-token", "authentic", "auth", "password", "plain",
                "config.password", "AWS::SecretsManager::Secret", "apiKey", "paſſword",
                "épassword", "İtoken", "_token", "token:plain", ":token")
        tails = ("", ":42", ":L42-L45", ":42:7", "='x'", ": none.", ": bare",
                 ": checked here", ": [file](auth.ts)", '" : "x"', "\\\"='x'",
                 " :token='x'", "\n===\n", " ordinary: prose")
        corpus = [prefix + key + tail for prefix, key, tail in
                  itertools.product(("", "/", "\\", '"', "a "), keys, tails)]
        randomizer = random.Random(234)
        fragments = ("token", "auth", "plain", "-", "_", ".", ":", "=", " ", "\n", '"', "\\", "é")
        corpus.extend("".join(randomizer.choices(fragments, k=12)) for _ in range(1000))
        corpus.extend((
            "some (token), label : none.",
            "api \t-key = 'x'",
            "token [item], name: value",
            "a token \t: bare",
            "token \t\n= 'x'",
            "token:'x', password = 'y'",
            "See `src/token.py:42` for the caller.",
            "Checked ``src/token.py:42`` for the caller.",
            "password: !!str synthetic",
            "Authorization: [implementation](src/auth.py)",
            "Secrets: none.",
            "```text\npassword='synthetic'\n```",
        ))
        return corpus

    def test_default_scan_matches_legacy_regex_positions_and_classification(self):
        pattern = re.compile(FORMAT["DEFAULT_SENSITIVE_KEY"])
        legacy = re.compile(pattern.pattern + r"""(?:\\?["'])?"""
                            + FORMAT["ASSIGNMENT_TAIL"].pattern, pattern.flags)
        def signature(start, match):
            return (start, match.start("spacing"), match.end(),
                    match["spacing"], match["operator"],
                    FORMAT["is_assignment"](text, match,
                        text[start:match.start("spacing")].endswith(("'", '"'))))
        for text in self.matcher_examples():
            with self.subTest(text=text):
                expected = [signature(match.start(), match) for match in legacy.finditer(text)]
                actual = [signature(start, match)
                          for start, match in FORMAT["assignment_matches"](text, pattern)]
                self.assertEqual(actual, expected)
                self.assertEqual(bool(FORMAT["sensitive_reference"](text, pattern)),
                                 bool(pattern.search(text)))

    def test_opted_patterns_preserve_legacy_matches_and_format_results(self):
        def legacy_matches(text, pattern, _tokens=None):
            combined = re.compile(pattern.pattern + r"""(?:\\?["'])?"""
                                  + FORMAT["ASSIGNMENT_TAIL"].pattern, pattern.flags)
            for match in combined.finditer(text):
                yield match.start(), match
        check = FORMAT["format_violation"]
        original_globals = dict(check.__globals__)
        original_globals.update(
            assignment_matches=legacy_matches,
            sensitive_reference=lambda text, pattern, _tokens=None: pattern.search(text),
        )
        original = types.FunctionType(check.__code__, original_globals,
                                      argdefs=check.__defaults__)
        original.__kwdefaults__ = check.__kwdefaults__.copy()
        for name, expression, alphabet in CALLER_PROFILES:
            pattern, tokens = re.compile(expression), re.compile(alphabet, re.I)
            for text in self.matcher_examples():
                with self.subTest(caller=name, text=text):
                    expected = [(start, match.start("spacing"), match.end(),
                                 match["spacing"], match["operator"])
                                for start, match in legacy_matches(text, pattern)]
                    actual = [(start, match.start("spacing"), match.end(),
                               match["spacing"], match["operator"])
                              for start, match in FORMAT["assignment_matches"](
                                  text, pattern, tokens)]
                    self.assertEqual(actual, expected)
                    self.assertEqual(bool(FORMAT["sensitive_reference"](text, pattern, tokens)),
                                     bool(pattern.search(text)))
                    self.assertEqual(check(text, pattern, key_token_pattern=tokens),
                                     original(text, pattern))

    def test_caller_patterns_keep_their_original_matching_behavior(self):
        for pattern in (re.compile(r"(?i:custom_secret)"),
                        re.compile(r"(?i:[\w -]*(?:token|password)[\w -]*)"),
                        re.compile(FORMAT["DEFAULT_SENSITIVE_KEY"], re.ASCII)):
            legacy = re.compile(pattern.pattern + r"""(?:\\?["'])?"""
                                + FORMAT["ASSIGNMENT_TAIL"].pattern, pattern.flags)
            for text in ("custom_secret='x'", "token='x'", "my token : x", "普通token=x",
                         "Ktoken=x", "path/token.py:42", 'token :password="x"'):
                with self.subTest(pattern=pattern.pattern, flags=pattern.flags, text=text):
                    expected = [(match.start(), match.end(), match["spacing"], match["operator"])
                                for match in legacy.finditer(text)]
                    actual = [(start, match.end(), match["spacing"], match["operator"])
                              for start, match in FORMAT["assignment_matches"](text, pattern)]
                    self.assertEqual(actual, expected)
                    self.assertEqual(bool(FORMAT["sensitive_reference"](text, pattern)),
                                     bool(pattern.search(text)))

    def test_long_default_key_tokens_finish_without_an_assignment_search_stall(self):
        script = (
            "import runpy,sys\n"
            "check=runpy.run_path(sys.argv[1])['format_violation']\n"
            "token='token-'*6000\n"
            "assert check(token) is None\n"
            "assert check(token+' ordinary: prose') is None\n"
            "assert check(token+\"='synthetic'\") == 'unsupported_review_format'\n"
            "assert check('`'+token+'`') is None\n"
        )
        try:
            result = subprocess.run(
                [sys.executable, "-c", script, str(ROOT /
                 "plugins/co-agent/skills/pr-autofix/scripts/review_format.py")],
                capture_output=True, text=True, timeout=5,
            )
        except subprocess.TimeoutExpired:
            self.fail("A 36KB token sequence stalled the default assignment scan")
        self.assertEqual(result.returncode, 0, result.stderr)

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
            "See web/lib/auth.ts:42-45.",
            "See (web/lib/auth.ts:42-45).",
            "See web/lib/auth.ts:L42-L45.",
            "See web/lib/auth.ts:L42.",
            "Secrets: none.",
            "Credentials: unchanged!",
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
            "See auth.ts:L42-L45; token='synthetic'",
            '"config.password": synthetic.',
            "password: !!str synthetic-value.",
            "token: &saved synthetic-value.",
        ):
            with self.subTest(text=text):
                self.assertEqual(FORMAT["format_violation"](text), "unsupported_review_format")


if __name__ == "__main__":
    unittest.main()
