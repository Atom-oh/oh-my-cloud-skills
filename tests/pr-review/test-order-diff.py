"""The review diff lists maintained source first, so the diff cap trims generated copies, not source."""
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/pr-review/order_diff.py"
WORKFLOW = ROOT / ".github/workflows/pr-review.yml"


def chunk(path, body="+changed\n", old=None):
    return f"diff --git a/{old or path} b/{path}\n--- a/{old or path}\n+++ b/{path}\n@@ -1 +1 @@\n{body}"


def order(text):
    proc = subprocess.run([sys.executable, "-I", str(SCRIPT)], input=text.encode("utf-8", "surrogateescape"),
                          capture_output=True, check=False)
    return proc.returncode, proc.stdout.decode("utf-8", "surrogateescape"), proc.stderr.decode()


def paths(text):
    return re.findall(r"(?m)^diff --git a/.+? b/(.+)$", text)


class OrderDiffTests(unittest.TestCase):
    def test_maintained_source_then_documentation_then_generated_copies(self):
        diff = "".join(chunk(p) for p in [
            "CHANGELOG.md", "docs/guide.md", "packages/claude/x/run.py", "plugins/x/run.py",
            "plugins/x/.codex-plugin/inventory.json", "results/report.md", "tools/ext/src/a.ts",
            "doc-sites/docs/x.md", "tests/structure/test-x.sh", "scripts/pr-review/lib.sh"])
        code, out, _ = order(diff)
        self.assertEqual(code, 0)
        self.assertEqual(paths(out), [
            "plugins/x/run.py", "tools/ext/src/a.ts", "tests/structure/test-x.sh", "scripts/pr-review/lib.sh",
            "CHANGELOG.md", "docs/guide.md", "results/report.md", "doc-sites/docs/x.md",
            "packages/claude/x/run.py", "plugins/x/.codex-plugin/inventory.json"])

    def test_order_inside_a_class_is_the_input_order(self):
        names = ["tools/z.ts", "plugins/b.py", "scripts/a.sh", "plugins/a.py"]
        code, out, _ = order("".join(chunk(p) for p in names))
        self.assertEqual(paths(out), names)

    def test_content_is_preserved_byte_for_byte_and_every_chunk_is_kept(self):
        diff = chunk("packages/a.txt", "+one\n+two\n") + chunk("plugins/a.txt", "-x\n+y\n+z\n")
        _, out, _ = order(diff)
        self.assertEqual(sorted(out.splitlines()), sorted(diff.splitlines()))
        self.assertEqual(len(out), len(diff))

    def test_text_before_the_first_diff_header_stays_first(self):
        diff = "note: a preamble line\n" + chunk("docs/a.md") + chunk("plugins/a.py")
        _, out, _ = order(diff)
        self.assertTrue(out.startswith("note: a preamble line\n"))
        self.assertEqual(paths(out), ["plugins/a.py", "docs/a.md"])

    def test_a_final_chunk_without_a_newline_does_not_merge_into_the_next_header(self):
        diff = chunk("packages/a.txt") + chunk("plugins/a.txt").rstrip("\n")
        _, out, _ = order(diff)
        self.assertEqual(paths(out), ["plugins/a.txt", "packages/a.txt"])
        self.assertNotIn("+changeddiff --git", out)

    def test_a_rename_is_classified_by_its_new_path(self):
        diff = chunk("packages/new.txt", old="plugins/old.txt") + chunk("plugins/keep.txt")
        _, out, _ = order(diff)
        self.assertEqual(paths(out), ["plugins/keep.txt", "packages/new.txt"])

    def test_paths_with_spaces_and_unicode_are_handled(self):
        diff = chunk("docs/a b.md") + chunk("plugins/한글 파일.py")
        _, out, _ = order(diff)
        self.assertEqual(paths(out), ["plugins/한글 파일.py", "docs/a b.md"])

    def test_a_directory_named_like_a_class_deeper_in_the_tree_is_not_that_class(self):
        names = ["plugins/x/docs/internal.py", "plugins/x/packages/lib.py", "tools/results/a.ts"]
        _, out, _ = order("".join(chunk(p) for p in names))
        self.assertEqual(paths(out), names)

    def test_empty_input_and_input_without_headers_pass_through(self):
        self.assertEqual(order("")[:2], (0, ""))
        self.assertEqual(order("just text\nno diff\n")[:2], (0, "just text\nno diff\n"))

    def test_invalid_utf8_bytes_survive(self):
        raw = chunk("plugins/a.bin", "+bad \udcff byte\n")
        _, out, _ = order(raw)
        self.assertIn("\udcff", out)

    def test_a_summary_goes_to_stderr_only(self):
        _, out, err = order(chunk("plugins/a.py") + chunk("packages/a.py") + chunk("docs/a.md"))
        self.assertIn("maintained", err)
        self.assertIn("generated", err)
        self.assertNotIn("maintained", out)


class WorkflowWiringTests(unittest.TestCase):
    def test_the_workflow_orders_the_diff_after_filtering_and_before_counting(self):
        text = WORKFLOW.read_text()
        awk = text.index("!skip")
        order_call = text.index("scripts/pr-review/order_diff.py")
        count = text.index('TOTAL_LINES=$(wc -l < "$pr_work_dir/pr-diff.txt")')
        cap = text.index("MAX_LINES=3000")
        self.assertLess(awk, order_call)
        self.assertLess(order_call, count)
        self.assertLess(count, cap)


if __name__ == "__main__":
    unittest.main()
