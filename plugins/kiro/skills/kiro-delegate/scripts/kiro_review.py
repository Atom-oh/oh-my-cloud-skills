#!/usr/bin/env python3
"""Kiro-run code review — used by the pre-commit hook and `/kiro:review`.

Sends a diff (staged changes by default) to `kiro-cli` on the plugin's configured
review model (meant to be Kiro's strongest/newest model — see `/kiro:setup`) and asks
for severity-tagged findings. Blocks (exit 2) only on `critical` findings by default
(`review.block` in kiro.defaults.json / .claude/kiro.local.json — kiro_config.py).

Usage:
  kiro_review.py [--staged | --diff <file> | <path>...] [--root DIR]
Exit: 0 = clean or fail-open (advisory-only findings printed, if any)
      2 = blocked — findings at/above the configured block level
"""
import sys
import os
import re
import json
import shutil
import subprocess
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
import kiro_config as kc

SEVERITY_ORDER = {"critical": 3, "warning": 2, "suggestion": 1}
# Only the block level's own tier and above should ever block. "any" blocks
# warning+critical; "none" never blocks (review stays advisory-only).
BLOCK_FLOOR = {"critical": 3, "any": 2, "none": 99}

_DIFF_CAP = 60 * 1024   # cap the diff sent to the reviewer (context-window / cost bound)

# Same credential-name pattern family as co-agent's consensus_hooks.py — kiro-cli is the
# only peer here, so the keep-list is just its own auth var.
_SENSITIVE_ENV_RE = re.compile(
    r"TOKEN|SECRET|PASSWORD|PASSWD|CREDENTIAL|PRIVATE_KEY|API_?KEY|"
    r"(?:^|_)KEY(?![A-Za-z])|(?:^|_)PAT(?![A-Za-z])|_PWD(?![A-Za-z])|"
    r"^AWS_|^GOOGLE_|^GCP_|^AZURE_|^GH_|^GITHUB_", re.I)


def _sanitized_env():
    keep = {"KIRO_API_KEY"}
    return {k: v for k, v in os.environ.items()
            if k in keep or not _SENSITIVE_ENV_RE.search(k)}


_PROMPT_INSTR = (
    "Use fs_read to read the diff at {F}, then review it as a strict but fair code "
    "reviewer. Reply with ONLY a JSON array (no prose, no code fences) of findings: "
    '[{{"severity":"critical|warning|suggestion","file":"<path>","line":<int or null>,'
    '"issue":"<one-line description>"}}]. "critical" = bug, security issue, or data '
    "loss risk; \"warning\" = real but non-blocking concern; \"suggestion\" = style/nit. "
    "If there is nothing to flag, reply with an empty array []. If the file is empty "
    "or unreadable, reply with []."
)


def _git_diff_cached(root, paths):
    env = {**os.environ, "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
           "GIT_ATTR_NOSYSTEM": "1", "GIT_PAGER": "cat"}
    args = ["git", "-C", root, "-c", f"core.attributesFile={os.devnull}",
            "-c", "core.fsmonitor=", "-c", f"core.hooksPath={os.devnull}", "-c", "core.pager=cat",
            "diff", "--cached", "--no-color", "--no-ext-diff", "--no-textconv"]
    if paths:
        args += ["--"] + list(paths)
    r = subprocess.run(args, capture_output=True, text=True, timeout=30, env=env)
    return r.stdout if r.returncode == 0 else ""


def _extract_json_array(text):
    """Findings must be a JSON array; tolerate a stray code fence or banner line
    around it (LLM output isn't always exactly the bare array)."""
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1 or end < start:
        return None
    try:
        data = json.loads(text[start:end + 1])
    except (json.JSONDecodeError, ValueError):
        return None
    return data if isinstance(data, list) else None


def run_review(root, diff, model, timeout):
    """Returns (findings|None, error|None). findings=None + error set means the
    review could not run or its output was unparseable — callers must fail-open."""
    if not shutil.which("kiro-cli"):
        return None, "kiro-cli not found on PATH"
    body = diff
    truncated = False
    if len(diff) > _DIFF_CAP:
        body = diff[:_DIFF_CAP].rsplit("\n", 1)[0]
        truncated = True
    with tempfile.TemporaryDirectory(prefix="kiro-review-") as wdir:
        fpath = os.path.join(wdir, "review.diff")
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(body)
            if truncated:
                f.write(f"\n[...diff truncated to the first ~{_DIFF_CAP // 1024}KB for review...]\n")
        argv = ["kiro-cli", "chat", _PROMPT_INSTR.format(F=fpath), "--mode", "default",
                "--no-interactive", "--trust-tools=fs_read", "--wrap", "never"]
        if model:
            argv += ["--model", model]
        else:
            # No specific model configured — --v3 is fine on the CLI default catalog.
            argv.insert(2, "--v3")
        # Capture to FILES, not PIPEs: kiro-cli can refresh auth over the host fds it
        # was launched with (--auth=acp-callback), and a pipe severs that callback,
        # hanging the call to the full timeout (see co-agent's check_panel.py probe()).
        outp, errp = os.path.join(wdir, ".out"), os.path.join(wdir, ".err")
        try:
            with open(outp, "w") as of, open(errp, "w") as ef:
                r = subprocess.run(argv, cwd=wdir, env=_sanitized_env(), stdin=subprocess.DEVNULL,
                                    stdout=of, stderr=ef, timeout=timeout)
            with open(outp, encoding="utf-8", errors="replace") as f:
                out = f.read()
            with open(errp, encoding="utf-8", errors="replace") as f:
                err = f.read()
        except subprocess.TimeoutExpired:
            return None, f"kiro-cli review timed out after {timeout}s"
        except OSError as e:
            return None, f"could not run kiro-cli: {e}"
        if r.returncode != 0:
            return None, f"kiro-cli exited {r.returncode}: {err.strip()[:300] or out.strip()[:300]}"
        findings = _extract_json_array(out)
        if findings is None:
            return None, "kiro-cli did not return a parseable JSON findings array"
        # Defense-in-depth: coerce/validate shape so a malformed entry can't crash a caller.
        clean = []
        for f in findings:
            if not isinstance(f, dict):
                continue
            sev = str(f.get("severity", "")).lower()
            if sev not in SEVERITY_ORDER:
                sev = "suggestion"
            clean.append({"severity": sev, "file": str(f.get("file", "")),
                          "line": f.get("line"), "issue": str(f.get("issue", ""))})
        return clean, None


def main():
    argv = sys.argv[1:]
    root = "."
    if "--root" in argv:
        i = argv.index("--root")
        root = argv[i + 1]
        del argv[i:i + 2]
    diff_file = None
    if "--diff" in argv:
        i = argv.index("--diff")
        diff_file = argv[i + 1]
        del argv[i:i + 2]
    if "--staged" in argv:
        argv.remove("--staged")
    paths = [a for a in argv if not a.startswith("--")]

    cfg = kc.effective(root)

    if diff_file:
        with open(diff_file, encoding="utf-8") as f:
            diff = f.read()
    else:
        diff = _git_diff_cached(root, paths)

    if not diff.strip():
        print("kiro review: no staged changes to review")
        return 0

    rcfg = cfg.get("review", {})
    model = rcfg.get("model")
    timeout = int(rcfg.get("timeout", 120))
    block_level = rcfg.get("block", "critical")

    findings, err = run_review(root, diff, model, timeout)
    if err is not None:
        # Fail-open: a broken/absent/unauthenticated reviewer must never block a commit.
        print(f"⚠️  kiro review skipped (fail-open): {err}", file=sys.stderr)
        return 0

    if not findings:
        print("✅ kiro review: no findings")
        return 0

    floor = BLOCK_FLOOR.get(block_level, BLOCK_FLOOR["critical"])
    blocking = [f for f in findings if SEVERITY_ORDER.get(f["severity"], 0) >= floor]
    advisory = [f for f in findings if f not in blocking]

    def _fmt(f):
        loc = f"{f['file']}:{f['line']}" if f.get("line") else f["file"] or "(unknown location)"
        return f"  [{f['severity'].upper()}] {loc} — {f['issue']}"

    if advisory:
        print(f"kiro review — {len(advisory)} advisory finding(s):", file=sys.stderr)
        for f in advisory:
            print(_fmt(f), file=sys.stderr)

    if blocking:
        print(f"❌ kiro review BLOCKED the commit — {len(blocking)} finding(s) at/above "
              f"'{block_level}':", file=sys.stderr)
        for f in blocking:
            print(_fmt(f), file=sys.stderr)
        print("Fix the finding(s) above, then retry the commit. To bypass this run, "
              "`export KIRO_REVIEW=off`, or turn it off persistently with "
              "`/kiro:configure set review on_commit off`.", file=sys.stderr)
        return 2

    print(f"✅ kiro review: {len(advisory)} advisory finding(s), nothing blocking")
    return 0


if __name__ == "__main__":
    sys.exit(main())
