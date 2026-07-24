#!/usr/bin/env python3
"""Delegate a one-shot web search to kiro-cli's native `web_search` tool.

Why this exists: Claude Code on Bedrock has no WebSearch tool. Kiro CLI does — so a
session that needs a web lookup can route it through the already-set-up kiro peer
(`/kiro:setup` writes the `kiro-websearch` agent and asks for the opt-in). The routing
rule lives in `plugins/kiro/CLAUDE.md`; this script is the whole mechanism.

Usage:
  echo "<query>" | kiro_websearch.py --stdin [--root DIR]   # canonical (routing rule)
  kiro_websearch.py "<query>" [--root DIR]                  # direct human use

Exit codes: 0 = results printed to stdout · 2 = feature disabled / not set up /
agent file tampered · 1 = kiro-cli invocation failed (timeout, non-zero exit, empty).

Security notes:
- `--stdin` is the canonical mode for agent-driven calls (the CLAUDE.md routing rule):
  the query never rides the caller's shell command line, so query text derived from
  untrusted context (fetched pages, file content) containing `$(...)`/backticks/quotes
  has no shell to inject into — the same reasoning that moved the delegate pipeline's
  task prompts into a task-prompt FILE (references/kiro-headless.md). The positional
  form remains for direct human use where the human shell-quoted the query themselves.
  Inside this process, both modes are identical: the query is forwarded via subprocess
  list-argv, so no shell parses it downstream either.
- The agent file must match the plugin-generated `_WEBSEARCH_AGENT` exactly (same
  tamper defense as kiro_review.py's `_reviewer_agent_ok`): the search agent's whole
  safety story is "web_search only — no fs_read/fs_write/execute_bash", and a
  hand-edited file that quietly adds tools must not be trusted. Fail-closed: refuse,
  never fall back to an unguarded invocation.
- Env is scrubbed with kiro_review's `_sanitized_env` before the call — same
  credential-name filter, keeps only KIRO_API_KEY of the sensitive set.
"""
import sys
import os
import json
import shutil
import tempfile
import subprocess

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
import kiro_config as kc
from kiro_review import _sanitized_env


def _websearch_agent_ok(path):
    """True iff the on-disk kiro-websearch agent file is exactly the plugin-generated
    shape. Imported lazily so a broken sibling module can't take this path down."""
    if not os.path.isfile(path):
        return False
    try:
        import kiro_setup
        with open(path, encoding="utf-8") as f:
            return json.load(f) == kiro_setup._WEBSEARCH_AGENT
    except Exception:
        return False


def run_search(root, query):
    cfg = kc.effective(root)
    w = cfg.get("websearch") or {}
    # _as_bool, not raw truthiness — kiro_config.py's websearch-enabled subcommand and
    # cmd_show both judge this key via _as_bool, so a hand-edited local JSON holding
    # the STRING "false" reads as disabled everywhere the user can inspect it; raw
    # truthiness here would treat that same value as ON and egress queries from a
    # config the user believes is opted out.
    if not kc._as_bool(w.get("enabled")):
        print("kiro websearch is disabled — enable it with "
              "`kiro_config.py set websearch enabled on` (or re-run /kiro:setup).",
              file=sys.stderr)
        return 2
    # Tamper check BEFORE the kiro-cli presence check: a tampered agent file must be
    # rejected regardless of whether kiro-cli happens to be installed — fail-closed is
    # about the file's trustworthiness, not the CLI's availability (and a PATH check
    # first would mask the tamper refusal on hosts without kiro-cli, e.g. CI).
    agent_file = os.path.join(root, ".kiro", "agents", "kiro-websearch.json")
    if not _websearch_agent_ok(agent_file):
        # Fail-closed, no unguarded fallback: a tampered agent file could have added
        # execute_bash/fs_write, and --trust-tools=web_search as a fallback would still
        # run whatever agent the file declares. Regenerating is cheap; trusting isn't.
        print("❌ .kiro/agents/kiro-websearch.json is missing or not plugin-generated — "
              "refusing to run. Regenerate with `kiro_setup.py write-agents --force` "
              "(or /kiro:setup).", file=sys.stderr)
        return 2
    if not shutil.which("kiro-cli"):
        print("kiro-cli not found on PATH — run /kiro:setup first.", file=sys.stderr)
        return 2

    timeout = kc._as_int(w.get("timeout"), 60, "websearch.timeout")
    model = w.get("model")
    with tempfile.TemporaryDirectory(prefix="kiro-websearch-") as wdir:
        # Copy the agent file into the temp cwd so `--agent kiro-websearch` resolves
        # there — same uncommitted-file gotcha kiro_review.py handles for the reviewer.
        agents_dir = os.path.join(wdir, ".kiro", "agents")
        os.makedirs(agents_dir, exist_ok=True)
        shutil.copy(agent_file, os.path.join(agents_dir, "kiro-websearch.json"))
        argv = ["kiro-cli", "chat",
                f"Search the web to answer this query, then reply with a concise "
                f"summary of findings followed by a list of source URLs:\n\n{query}",
                "--mode", "default", "--no-interactive", "--wrap", "never",
                "--agent", "kiro-websearch"]
        if model:
            argv += ["--model", model]
        # Capture to FILES, not PIPEs — a pipe severs kiro-cli's auth-refresh callback
        # and the call hangs to the full timeout (references/kiro-headless.md).
        outp, errp = os.path.join(wdir, ".out"), os.path.join(wdir, ".err")
        try:
            with open(outp, "w") as of, open(errp, "w") as ef:
                r = subprocess.run(argv, cwd=wdir, env=_sanitized_env(),
                                    stdin=subprocess.DEVNULL, stdout=of, stderr=ef,
                                    timeout=timeout)
            with open(outp, encoding="utf-8", errors="replace") as f:
                out = f.read()
            with open(errp, encoding="utf-8", errors="replace") as f:
                err = f.read()
        except subprocess.TimeoutExpired:
            print(f"❌ kiro websearch timed out after {timeout}s "
                  f"(`kiro_config.py set websearch timeout <s>` to raise).", file=sys.stderr)
            return 1
        except OSError as e:
            print(f"❌ could not run kiro-cli: {e}", file=sys.stderr)
            return 1
    if r.returncode != 0:
        print(f"❌ kiro-cli exited {r.returncode}: "
              f"{(err.strip() or out.strip())[:300]}", file=sys.stderr)
        return 1
    if not out.strip():
        print("❌ kiro websearch returned no output.", file=sys.stderr)
        return 1
    print(out.strip())
    return 0


def main():
    argv = sys.argv[1:]
    root = None
    if "--root" in argv:
        i = argv.index("--root")
        if i + 1 >= len(argv):
            print("--root requires a value", file=sys.stderr)
            return 2
        root = argv[i + 1]
        del argv[i:i + 2]
    if root is None:
        root = kc._default_root()
    # --stdin is the CANONICAL calling mode (what the CLAUDE.md routing rule uses):
    # the query never appears on the caller's shell command line, so a query derived
    # from untrusted context (a fetched page, file content) containing $(...) or
    # backticks has nothing to inject into — the host shell only ever parses the
    # fixed `... kiro_websearch.py --stdin` string. The positional-argv form is kept
    # for direct human use, where the human typed (and shell-quoted) the query
    # themselves. Python-side handling is identical either way — subprocess list-argv
    # means no shell parses the query downstream of this process.
    if argv == ["--stdin"]:
        query = sys.stdin.read()
        if not query.strip():
            print("no query on stdin", file=sys.stderr)
            return 2
        return run_search(root, query.strip())
    if len(argv) != 1 or not argv[0].strip():
        print(__doc__)
        return 2
    return run_search(root, argv[0])


if __name__ == "__main__":
    sys.exit(main())
