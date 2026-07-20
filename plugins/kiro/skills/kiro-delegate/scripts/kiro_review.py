#!/usr/bin/env python3
"""Kiro-run code review — used by the pre-commit hook and `/kiro:review`.

Sends a diff to `kiro-cli` on the plugin's configured review model (meant to be Kiro's
strongest/newest model — see `/kiro:setup`) and asks for severity-tagged findings.
Blocks (exit 2) only on `critical` findings by default (`review.block` in
kiro.defaults.json / .claude/kiro.local.json — kiro_config.py).

Usage:
  kiro_review.py --staged [--root DIR]           # staged changes only (git diff --cached)
  kiro_review.py --diff <file> [--root DIR]      # a pre-computed diff file
  kiro_review.py [<path>...] [--root DIR]        # working-tree changes (staged + unstaged),
                                                  # scoped to the given paths if any
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


def _reviewer_agent_ok(path):
    """True iff the reviewer agent file exists AND matches the plugin-generated shape.
    Same rationale as kiro_setup.verify_agents for the implementer: the agent file's
    preToolUse.runCommand is a host command kiro-cli executes, so a tampered file must
    not be copied into the review cwd and run — fall back to the (announced) ad-hoc
    invocation instead of trusting it. Imported lazily so a broken sibling module can't
    take down the fail-open review path."""
    if not os.path.isfile(path):
        return False
    try:
        import kiro_setup
        with open(path, encoding="utf-8") as f:
            return json.load(f) == kiro_setup._REVIEWER_AGENT
    except Exception:
        return False

SEVERITY_ORDER = {"critical": 3, "warning": 2, "suggestion": 1}
# Only the block level's own tier and above should ever block. "warning" blocks
# warning+critical (there is no lower tier to additionally include — "suggestion"
# never blocks under any level); "none" never blocks (review stays advisory-only).
BLOCK_FLOOR = {"critical": 3, "warning": 2, "none": 99}

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


def _git_env():
    return {**os.environ, "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_ATTR_NOSYSTEM": "1", "GIT_PAGER": "cat"}


def _untracked_files(root, paths):
    """Untracked (never-`git add`ed) files, optionally scoped to `paths`. `git diff HEAD`
    never shows these — HEAD has no entry for them at all — so the working-tree review
    mode must fetch them separately or a brand-new file silently reviews as empty.
    Best-effort: on a git failure/timeout, warn and return [] (the tracked-diff pass has
    already succeeded by the time this runs — a traceback here would kill a review that
    was otherwise fine, violating the fail-open contract)."""
    args = ["git", "-C", root, "ls-files", "--others", "--exclude-standard"]
    if paths:
        args += ["--"] + list(paths)
    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=30, env=_git_env())
    except (subprocess.TimeoutExpired, OSError) as e:
        print(f"⚠️  kiro review: could not list untracked files ({e}) — untracked files "
              f"in this review scope were NOT reviewed", file=sys.stderr)
        return []
    if r.returncode != 0:
        print(f"⚠️  kiro review: git ls-files exited {r.returncode} — untracked files "
              f"in this review scope were NOT reviewed", file=sys.stderr)
        return []
    return [p for p in r.stdout.splitlines() if p]


def _git_diff(root, paths, cached):
    """`cached=True` → staged changes only (`git diff --cached`, what the pre-commit hook
    reviews) — untracked files are never staged, so they're correctly absent here.
    `cached=False` → the full working-tree diff (staged + unstaged) `/kiro:review
    <path>...` uses, PLUS any untracked file among `paths` (or all untracked files when
    `paths` is empty) via `git diff --no-index` against /dev/null — `git diff HEAD` alone
    shows nothing for a file HEAD never had, which would silently review a brand-new
    file as empty/unchanged.

    Returns (diff_text, error|None). A real git failure (bad ref, git missing, timeout)
    returns error set so the caller can distinguish "git broke" (fail-open, don't claim
    a clean review) from "genuinely no changes" (both would otherwise just look like an
    empty diff)."""
    env = _git_env()
    args = ["git", "-C", root, "-c", f"core.attributesFile={os.devnull}",
            "-c", "core.fsmonitor=", "-c", f"core.hooksPath={os.devnull}", "-c", "core.pager=cat",
            "diff"] + (["--cached"] if cached else ["HEAD"]) + ["--no-color", "--no-ext-diff", "--no-textconv"]
    if paths:
        args += ["--"] + list(paths)
    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=30, env=env)
    except subprocess.TimeoutExpired:
        return "", "git diff timed out after 30s"
    except OSError as e:
        return "", f"could not run git: {e}"
    if r.returncode != 0:
        return "", f"git diff exited {r.returncode}: {r.stderr.strip()[:300]}"
    tracked_diff = r.stdout
    if cached:
        return tracked_diff, None
    untracked_diff = ""
    for p in _untracked_files(root, paths):
        # --no-index diffs two paths outside git's index tracking; it EXITS 1 when the
        # files differ (the normal/expected case here, not an error) and only >1 on a
        # real usage error, so don't gate on returncode the way tracked-diff calls do.
        try:
            ur = subprocess.run(
                ["git", "-C", root, "diff", "--no-color", "--no-ext-diff", "--no-textconv",
                 "--no-index", "--", os.devnull, p],
                capture_output=True, text=True, timeout=30, env=env)
        except (subprocess.TimeoutExpired, OSError):
            continue   # best-effort for the untracked-file pass; the tracked diff above already succeeded
        if ur.returncode <= 1:
            untracked_diff += ur.stdout
    return tracked_diff + untracked_diff, None


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
    """Returns (findings|None, error|None, truncated). findings=None + error set means
    the review could not run or its output was unparseable — callers must fail-open.
    truncated=True means the diff exceeded _DIFF_CAP and everything past that point was
    NOT reviewed — the caller must warn about this (this gate is advisory, not a
    guarantee of full coverage; a silent truncation would look like a clean full review
    when part of the diff was never actually seen by the reviewer)."""
    if not shutil.which("kiro-cli"):
        return None, "kiro-cli not found on PATH", False
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
                "--no-interactive", "--wrap", "never"]
        # Prefer the kiro-reviewer custom agent (written by kiro_setup.py write-agents):
        # it carries a preToolUse fs_read guard that confines reads to the launch cwd —
        # and this subprocess's cwd is the isolated temp dir holding ONLY the diff, so
        # the guard is precisely "the reviewer can read the diff and nothing else". That
        # is the tool-layer mitigation for prompt-injection exfiltration (an untrusted
        # diff directing the reviewer to fs_read ~/.aws/credentials); prose cautions
        # alone don't restrain an injected model. Fall back to the unguarded ad-hoc
        # --trust-tools form only when setup hasn't written the agent yet — the review
        # gate is advisory/fail-open by contract, so refusing to run entirely would be
        # worse, but the fallback is announced so it's never a silent downgrade.
        reviewer_agent = os.path.join(root, ".kiro", "agents", "kiro-reviewer.json")
        if _reviewer_agent_ok(reviewer_agent):
            # Copy the agent file into the temp cwd so `--agent kiro-reviewer` resolves
            # there regardless of whether kiro-cli looks in cwd or walks upward — the
            # same uncommitted-file gotcha the delegate pipeline handles for the
            # implementer agent in its worktrees.
            agents_dir = os.path.join(wdir, ".kiro", "agents")
            os.makedirs(agents_dir, exist_ok=True)
            shutil.copy(reviewer_agent, os.path.join(agents_dir, "kiro-reviewer.json"))
            argv += ["--agent", "kiro-reviewer"]
        else:
            print("⚠️  kiro review: .kiro/agents/kiro-reviewer.json missing or not "
                  "plugin-generated — running with ad-hoc --trust-tools=fs_read (NO "
                  "read-scope guard). Run /kiro:setup (write-agents --force if tampered) "
                  "to generate the guarded reviewer agent.", file=sys.stderr)
            argv += ["--trust-tools=fs_read"]
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
            return None, f"kiro-cli review timed out after {timeout}s", truncated
        except OSError as e:
            return None, f"could not run kiro-cli: {e}", truncated
        if r.returncode != 0:
            return None, f"kiro-cli exited {r.returncode}: {err.strip()[:300] or out.strip()[:300]}", truncated
        findings = _extract_json_array(out)
        if findings is None:
            return None, "kiro-cli did not return a parseable JSON findings array", truncated
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
        return clean, None, truncated


def main():
    argv = sys.argv[1:]
    root = "."
    if "--root" in argv:
        i = argv.index("--root")
        if i + 1 >= len(argv):
            print("--root requires a value", file=sys.stderr)
            return 2
        root = argv[i + 1]
        del argv[i:i + 2]
    diff_file = None
    if "--diff" in argv:
        i = argv.index("--diff")
        if i + 1 >= len(argv):
            print("--diff requires a value", file=sys.stderr)
            return 2
        diff_file = argv[i + 1]
        del argv[i:i + 2]
    staged = "--staged" in argv
    if staged:
        argv.remove("--staged")
    # Everything after a `--` separator is a PATH, verbatim — even one that starts with
    # "--" (a file literally named "--notes.md"). A blanket startswith("--") filter over
    # the whole argv silently dropped such a path, making the review fall back to the
    # full staged diff instead of the file the user named.
    if "--" in argv:
        sep = argv.index("--")
        paths = [a for a in argv[:sep] if not a.startswith("--")] + argv[sep + 1:]
    else:
        paths = [a for a in argv if not a.startswith("--")]

    cfg = kc.effective(root)

    if diff_file:
        try:
            with open(diff_file, encoding="utf-8") as f:
                diff = f.read()
        except OSError as e:
            # Fail-open: this gate must never crash a caller (the hook, /kiro:review)
            # just because the diff file it was pointed at doesn't exist / isn't readable.
            print(f"⚠️  kiro review skipped (fail-open): could not read --diff file: {e}",
                  file=sys.stderr)
            return 0
    else:
        # --staged (or no paths at all, e.g. the hook's default call) reviews staged
        # changes only; explicit paths review the full working-tree diff (staged +
        # unstaged) for those paths, so an in-progress unstaged edit is reviewable too.
        diff, diff_err = _git_diff(root, paths, cached=staged or not paths)
        if diff_err is not None:
            print(f"⚠️  kiro review skipped (fail-open): {diff_err}", file=sys.stderr)
            return 0

    if not diff.strip():
        print("kiro review: no changes to review")
        return 0

    rcfg = cfg.get("review") or {}   # `or {}`: a hand-edited config could set this key
                                     # to a non-dict; never let a settings-file typo
                                     # crash the fail-open gate it's supposed to protect
    model = rcfg.get("model")
    try:
        timeout = int(rcfg.get("timeout", 120))
    except (TypeError, ValueError):
        print(f"⚠️  kiro review: review.timeout {rcfg.get('timeout')!r} is not a valid "
              f"integer — using the default (120s)", file=sys.stderr)
        timeout = 120
    block_level = rcfg.get("block") or "critical"

    findings, err, truncated = run_review(root, diff, model, timeout)
    if truncated:
        # This gate is advisory, not a coverage guarantee — a silent truncation would
        # look identical to "the whole diff was reviewed and came back clean/blocked".
        print(f"⚠️  kiro review: diff exceeds {_DIFF_CAP // 1024}KB — only the first "
              f"~{_DIFF_CAP // 1024}KB was sent to the reviewer; the rest of this diff "
              f"was NOT reviewed", file=sys.stderr)
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
