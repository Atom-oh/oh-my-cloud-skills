#!/usr/bin/env python3
"""Exercise atlas_sync.py's _scan_doc_secrets against a real temp git repo, for
test-push-gate.sh.

Usage:
  _atlas_secret_scan_probe.py <before-content> <after-content>   # raw mode
  _atlas_secret_scan_probe.py --case NAME                          # named fixture

Prints "HIT <line>" or "CLEAN". Raw mode's before/after use "\\n" as a literal line
separator (decoded here) so a caller can stay on one shell line.

Named cases build their secret-shaped fixture text via string concatenation at
runtime, deliberately never as a contiguous literal anywhere in THIS FILE's own
source — this repo's own commit-time `.claude/hooks/secret-scan.sh` would otherwise
flag the very fixtures meant to test atlas's scanner for exactly the shapes it's
designed to catch (the same reason `tests/pr-review/test-lib.sh` needs its own
fixture-stripping allowlist in that hook)."""
import importlib.util
import os
import subprocess
import sys
import tempfile

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_spec = importlib.util.spec_from_file_location(
    "atlas_sync", os.path.join(_ROOT, "plugins", "atlas", "skills", "atlas", "scripts",
                                "atlas_sync.py"))
atlas_sync = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(atlas_sync)


def _case(name):
    """(before, after) for a named fixture. Values assembled from parts so no
    single contiguous secret-shaped literal exists in this file's source text."""
    if name == "header-bypass":
        val = "abc" + "1234567890123"
        return "line1\n", 'line1\n++ token: "%s"\n' % val
    if name == "aws-uppercase":
        key = "AWS_" + "SECRET_ACCESS_KEY"
        val = "abcd1234" + "efgh5678ijkl"
        return "line1\n", "line1\n%s=%s\n" % (key, val)
    if name == "allowlist-no-bypass":
        field = "pass" + "word"
        val = "supersecret" + "value123"
        marker = "pragma: allow" + "list secret"
        return "line1\n", 'line1\n%s: "%s"  # %s\n' % (field, val, marker)
    if name == "benign":
        return "line1\n", "line1\nSome more benign prose text.\n"
    raise SystemExit("unknown case: %s" % name)


def main():
    color_always = sys.argv[1:2] == ["--case"] and sys.argv[2] == "color-ui-always"
    if color_always:
        # Reuses the same fixture content as "aws-uppercase" — this case only
        # adds a git config, not a different secret shape.
        before, after = _case("aws-uppercase")
    elif sys.argv[1:2] == ["--case"]:
        before, after = _case(sys.argv[2])
    else:
        before, after = sys.argv[1], sys.argv[2]
        before, after = before.replace("\\n", "\n"), after.replace("\\n", "\n")
    with tempfile.TemporaryDirectory() as d:
        subprocess.run(["git", "init", "-q"], cwd=d, check=True)
        subprocess.run(["git", "config", "user.email", "t@t.com"], cwd=d, check=True)
        subprocess.run(["git", "config", "user.name", "t"], cwd=d, check=True)
        if color_always:
            # Reproduces the round-4 finding: a user's global `color.ui=always`
            # would prepend ANSI codes to every `git diff` line, breaking every
            # `+`/`@@` prefix check `_scan_doc_secrets` relies on — this repo-local
            # config is the same effect without touching the test runner's own
            # global git config.
            subprocess.run(["git", "config", "color.ui", "always"], cwd=d, check=True)
        doc = os.path.join(d, "foo.md")
        with open(doc, "w") as f:
            f.write(before)
        subprocess.run(["git", "add", "-A"], cwd=d, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=d, check=True)
        with open(doc, "w") as f:
            f.write(after)
        hit, line = atlas_sync._scan_doc_secrets(doc, d)
        print(f"HIT {line}" if hit else "CLEAN")


if __name__ == "__main__":
    main()
