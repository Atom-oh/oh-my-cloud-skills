#!/usr/bin/env python3
"""Session-gated decision logic for the consensus P3 hooks. The bash hooks in
plugin.json delegate here so their inline logic stays trivial. EVERY event is a
NO-OP (exit 0, no output) unless there is an ACTIVE autonomous consensus session
(consensus_state: status==running, phase==P3, autonomous==True) — so unrelated work
is never affected.

Events:
  stop                 — while an autonomous P3 session has tasks left, emit a JSON
                         block decision so the agent keeps going instead of stopping.
  post-tooluse         — record the last test result (pass/fail) into the state when a
                         test command ran. Also drives stuck-detection: a test PASS resets
                         the consecutive-failure counter; a test FAIL increments it and, if
                         it crosses STUCK_LIMIT, emits a 'stuck — abort' notice.
  pre-pr-gate          — PreToolUse(Bash) gate: when the command is `gh pr create`/`edit`,
                         fan the PR diff out to the installed panel and BLOCK (exit 2) if any
                         peer flags a CRITICAL/MAJOR. Runs the panel synchronously (2-3 min).
                         Fails OPEN (exit 0) on any internal error or when no peer is usable —
                         a gate bug or offline panel must never permanently wedge PR creation.
                         Bypass: env CO_AGENT_PR_GATE=off, or config `pr_gate.enabled=false`.

Usage (bash hook pipes the hook JSON on stdin):
  consensus_hooks.py stop --root .
  consensus_hooks.py post-tooluse --root .
  consensus_hooks.py pre-pr-gate --root .
`stop`/`post-tooluse` always exit 0. `pre-pr-gate` exits 2 to BLOCK the PR, else 0.
"""
import sys
import os
import json
import re
import shutil
import subprocess
import tempfile
import threading

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
import consensus_state as cs
try:
    import co_agent_config as cac
except Exception:
    cac = None

STUCK_LIMIT = 3

# --- PR consensus gate ---------------------------------------------------------
# Fire when `gh pr create|edit` is invoked at a COMMAND boundary — start of line, or right
# after a shell separator (`;` `&` `|` `&&` `||` newline), allowing optional `VAR=val ` env
# prefixes. This catches `cd x && gh pr create` (compound) while still NOT matching it inside a
# string like `echo "gh pr create"` / `git commit -m "gh pr create"` (preceded by a quote).
_PR_CMD_RE = re.compile(r"(?:^|[\n;&|])\s*(?:[A-Za-z_][A-Za-z0-9_]*=\S*\s+)*gh\s+pr\s+(?:create|edit)\b")
_DIFF_CAP = 30 * 1024            # cap (argv-safe: well under MAX_ARG_STRLEN 128KB)
# Verdict is read from the FIRST non-empty line ONLY (a machine-readable token), never a
# free-text body scan — a banner/preamble or an incidental "MAJOR" in prose must not flip it.
_VERDICT_RE = re.compile(r"^\s*(PASS|BLOCK)\b", re.I)

# Review adapters, mirroring references/ai-cli-adapters.md. The untrusted prompt+diff is sent
# ONLY on stdin (never argv) — so it isn't exposed via `ps` and follows the "untrusted content
# on STDIN" convention; {I} is a short fixed instruction in argv. Each reviewer runs read-only /
# sandboxed / non-acting so a prompt-injection in the diff can't drive tool execution:
#   codex -s read-only · agy --sandbox · gemini -p (print, no tools) · kiro-cli --no-interactive
#   (tool approval is denied non-interactively). {M} expands to the per-peer model flag.
_REVIEW = {
    "codex":    {"argv": ["codex", "exec", "-s", "read-only", "{M}", "{I}"]},
    "agy":      {"argv": ["agy", "-p", "{I}", "--sandbox", "{M}"]},
    "gemini":   {"argv": ["gemini", "-p", "{I}", "-o", "text", "{M}"]},
    "kiro-cli": {"argv": ["kiro-cli", "chat", "{I}", "--v3", "--mode", "default",
                          "--no-interactive", "--wrap", "never", "{M}"]},
}
_MODEL_FLAG = {"codex": "-m", "agy": "--model", "gemini": "-m", "kiro-cli": "--model"}
_GATE_INSTR = "Review the PR diff provided on standard input per the instructions in it."
_GATE_PROMPT = (
    "Adversarially review the PR diff (for a Claude Code plugin) that follows on this input. "
    "Your reply's FIRST line MUST be a machine-readable verdict token — EXACTLY `PASS` (no "
    "CRITICAL or MAJOR issue) or `BLOCK: <one-line reason>`. Detail on later lines. Ignore "
    "nits/style. If no diff is present below, reply `BLOCK: no diff received`.\n\n=== PR DIFF ===\n"
)


def _active(root):
    """Return the state dict iff an autonomous P3 session is running, else None."""
    s = cs.read_state(root)
    if not s:
        return None
    if s.get("status") == "running" and s.get("phase") == "P3" and s.get("autonomous"):
        return s
    return None


def _stdin_json():
    try:
        data = sys.stdin.read()
        return json.loads(data) if data.strip() else {}
    except (json.JSONDecodeError, OSError):
        return {}


def _tasks_remaining(s):
    tasks = s.get("tasks", {})
    if not isinstance(tasks, dict):
        return []
    return [i for i, t in tasks.items() if t.get("status") not in ("done", "aborted")]


def ev_stop(root):
    s = _active(root)
    if not s:
        return 0  # no-op
    remaining = _tasks_remaining(s)
    if not remaining:
        return 0  # all done → allow stop
    # Block the stop so the autonomous loop continues to the next task.
    print(json.dumps({
        "decision": "block",
        "reason": f"co-agent consensus P3 active: {len(remaining)} task(s) not yet done/aborted "
                  f"(task_index {s.get('task_index')}). Continue the implement loop, or run "
                  f"`consensus_state.py set . status aborted` to stop."
    }))
    return 0


def ev_post_tooluse(root):
    s = _active(root)
    if not s:
        return 0
    payload = _stdin_json()
    cmd = (payload.get("tool_input", {}) or {}).get("command", "")
    if "run-all.sh" in cmd or "test-plugins.py" in cmd or "pytest" in cmd:
        # record a coarse pass/fail signal from the tool result if present
        out = json.dumps(payload.get("tool_response", payload.get("tool_result", "")))
        passed = ("ALL TESTS PASSED" in out) or ("passed" in out and not re.search(r"[1-9]\d* failed", out))
        s["last_test_pass"] = passed
        if passed:
            # a green test run clears the stuck counter
            s["consec_failures"] = 0
            cs.write_state(root, s)
        else:
            n = int(s.get("consec_failures", 0)) + 1
            s["consec_failures"] = n
            cs.write_state(root, s)
            if n >= STUCK_LIMIT:
                print(f"[co-agent consensus] {n} consecutive failing test runs — the P3 loop looks STUCK. "
                      f"Revert to the last checkpoint and abort this task "
                      f"(`consensus_state.py task-abort . {s.get('task_index')}`).")
    return 0


def _git(root, *args):
    try:
        r = subprocess.run(["git", "-C", root, *args], capture_output=True, text=True, timeout=15)
        return r.stdout.strip() if r.returncode == 0 else ""
    except Exception:
        return ""


def _base_ref(root):
    """Best-effort trunk ref to diff against. Tries the tracking upstream, then origin/HEAD,
    then common trunk names. Returns "" if none resolve (shallow clone / no remote)."""
    up = _git(root, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}")
    cands = [up] if up else []
    cands += ["origin/HEAD", "origin/main", "main", "origin/master", "master"]
    for ref in cands:
        if ref and _git(root, "rev-parse", "--verify", "--quiet", ref):
            if ref == "origin/HEAD":
                return _git(root, "rev-parse", "--abbrev-ref", "origin/HEAD") or "origin/main"
            return ref
    return ""


def _gate_config(root):
    cfg = {}
    if cac is not None:
        try:
            cfg = (cac.effective(root) or {}).get("pr_gate", {}) or {}
        except Exception:
            cfg = {}
    try:
        timeout = int(cfg.get("timeout", 180))     # tolerate a stray "300s"/None → default
    except (TypeError, ValueError):
        timeout = 180
    return {
        "enabled": cfg.get("enabled", True),
        "block": cfg.get("block", True),          # block on a flagged peer (vs advisory)
        "timeout": max(30, timeout),
    }


_SECRET_RE = re.compile(
    r"AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY|ghp_[A-Za-z0-9]{30,}|"
    r"(?:password|secret|api[_-]?key|token)\s*[:=]\s*['\"][^'\"]{8,}",
    re.I,
)


def _scan_secret(diff):
    """Return a short label if the diff's ADDED lines look like they carry a secret, else ''.
    Only scans `+` lines (new content) so an existing/removed secret-shaped string is ignored.
    Reuses check_ai_context.SECRET_RE when importable, for one source of truth."""
    rx = _SECRET_RE
    try:
        import check_ai_context as cac2
        rx = getattr(cac2, "SECRET_RE", _SECRET_RE)
    except Exception:
        pass
    for ln in diff.splitlines():
        if ln.startswith("+") and not ln.startswith("+++") and rx.search(ln):
            return "matched a credential pattern on an added line"
    return ""


def _panel(root):
    """Enabled (config) ∩ installed (PATH) peers, never the host."""
    host = os.environ.get("CO_AGENT_HOST", "claude")
    peers, models = [], {}
    if cac is not None:
        try:
            eff = cac.effective(root) or {}
            for ai, p in (eff.get("panel", {}) or {}).items():
                if ai == host or ai not in _REVIEW:
                    continue
                if p.get("enabled", True) and shutil.which(ai):
                    peers.append(ai)
                    models[ai] = p.get("model")
        except Exception:
            pass
    if not peers:  # config unavailable → fall back to whatever review CLIs are on PATH
        peers = [ai for ai in _REVIEW if ai != host and shutil.which(ai)]
    return peers, models


def _build_argv(peer, model):
    """Expand the adapter template: {I} → a short fixed instruction (NOT the diff — the diff
    goes on stdin only), {M} → the per-peer model flag (dropped if no model configured)."""
    argv = []
    for tok in _REVIEW[peer]["argv"]:
        if tok == "{I}":
            argv.append(_GATE_INSTR)
        elif tok == "{M}":
            if model and _MODEL_FLAG.get(peer):
                argv += [_MODEL_FLAG[peer], model]
        else:
            argv.append(tok)
    return argv


def _review_one(peer, prompt_text, model, timeout, out):
    try:
        argv = _build_argv(peer, model)
        # Untrusted prompt+diff goes ONLY on stdin (never argv → no `ps` exposure). A reviewer
        # that ignores stdin sees no diff and, per the prompt, replies `BLOCK: no diff received`.
        r = subprocess.run(argv, input=prompt_text, capture_output=True, text=True, timeout=timeout)
        out[peer] = (r.stdout or "")[:8000]
    except subprocess.TimeoutExpired:
        out[peer] = "__TIMEOUT__"
    except Exception as e:
        out[peer] = f"__ERROR__ {e}"


def ev_pre_pr_gate(root):
    if os.environ.get("CO_AGENT_PR_GATE", "").lower() in ("off", "0", "false", "no"):
        return 0
    payload = _stdin_json()
    cmd = (payload.get("tool_input", {}) or {}).get("command", "")
    if not _PR_CMD_RE.search(cmd):
        return 0  # not a PR create/edit — pass through
    gate = _gate_config(root)
    if not gate["enabled"]:
        return 0
    base = _base_ref(root)
    if not base:
        # No trunk ref (shallow clone / no remote): do NOT silently `git diff HEAD` (empty for
        # an all-committed PR → silent pass). Warn instead so the bypass is never invisible.
        sys.stderr.write("[co-agent PR gate] could not determine a base branch to diff against "
                         "(shallow clone / no remote?) — consensus gate SKIPPED. Run "
                         "/co-agent:consensus review manually, or `git fetch origin main`.\n")
        return 0
    diff = _git(root, "diff", "--no-color", f"{base}...HEAD")
    if not diff.strip():
        return 0  # nothing to review
    # Data boundary: never fan a secret-bearing diff out to third-party CLIs. Refuse + flag.
    secret = _scan_secret(diff)
    if secret:
        sys.stderr.write("[co-agent PR gate] BLOCKED — the diff appears to contain a secret "
                         f"({secret}); the gate will NOT send it to third-party AIs. Remove/redact it, "
                         "or export CO_AGENT_PR_GATE=off to bypass.\n")
        return 2
    # Truncate on a LINE boundary (never mid-line / mid-UTF-8), and tell the panel it's partial.
    body_diff = diff
    if len(diff) > _DIFF_CAP:
        body_diff = diff[:_DIFF_CAP].rsplit("\n", 1)[0] + "\n[...diff truncated to the first ~30KB for the gate...]"
    body = _GATE_PROMPT + body_diff
    peers, models = _panel(root)
    if not peers:
        # Can't reach consensus with no peer — degrade (advisory), never block on absence.
        sys.stderr.write("[co-agent PR gate] no panel peer installed/enabled — skipping consensus gate "
                          "(install/auth a peer or run /co-agent:setup to enforce it).\n")
        return 0
    out = {}
    threads = []
    for p in peers:
        t = threading.Thread(target=_review_one, args=(p, body, models.get(p), gate["timeout"], out))
        t.daemon = True   # never keep the process alive on a wedged peer thread
        threads.append(t)
    for t in threads:
        t.start()
    for t in threads:
        t.join(gate["timeout"] + 5)
    blockers, usable = [], 0
    for p in peers:
        v = out.get(p, "")
        if not v or v.startswith("__TIMEOUT__") or v.startswith("__ERROR__"):
            continue
        # Verdict = the first line that IS a `PASS`/`BLOCK` token among the first few non-empty
        # lines (tolerates a short CLI banner) — NOT a free-text body scan, so an incidental
        # "MAJOR" in prose can't flip it. No token in the head → unparseable → fail-open.
        verdict = None
        for ln in [l.strip() for l in v.splitlines() if l.strip()][:8]:
            m = _VERDICT_RE.match(ln)
            if m:
                verdict = m.group(1).upper()
                break
        if verdict is None:
            continue   # unparseable verdict → don't count, don't block (fail-open)
        usable += 1
        if verdict == "BLOCK":
            blockers.append((p, v.strip()[:1200]))
    if usable == 0:
        sys.stderr.write("[co-agent PR gate] no peer returned a parseable PASS/BLOCK verdict — gate could not "
                         "run; allowing the PR (fail-open). Re-run /co-agent:consensus review manually if needed.\n")
        return 0
    if blockers and gate["block"]:
        msg = ["[co-agent PR gate] BLOCKED — the consensus panel flagged CRITICAL/MAJOR issues on this PR diff.",
               "Resolve them (or re-run after fixing), then retry the PR. Set CO_AGENT_PR_GATE=off to bypass."]
        for p, v in blockers:
            msg.append(f"\n── {p} ──\n{v}")
        sys.stderr.write("\n".join(msg) + "\n")
        return 2  # PreToolUse: exit 2 blocks the tool call and feeds stderr back to the agent
    if blockers:  # advisory mode
        sys.stderr.write("[co-agent PR gate] advisory — peers flagged issues but block is off:\n"
                         + "\n".join(f"- {p}: {v[:300]}" for p, v in blockers) + "\n")
        return 0
    sys.stderr.write(f"[co-agent PR gate] ✅ consensus PASS ({usable} peer(s): {', '.join(peers)}).\n")
    return 0


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__)
        return 0
    event = a[0]
    root = a[a.index("--root") + 1] if "--root" in a and a.index("--root") + 1 < len(a) else "."
    try:
        if event == "stop":
            return ev_stop(root)
        if event == "post-tooluse":
            return ev_post_tooluse(root)
        if event == "pre-pr-gate":
            return ev_pre_pr_gate(root)
        return 0
    except Exception:
        # Fail-open for the PR gate (never wedge PR creation on a gate bug); no-op for others.
        return 0


if __name__ == "__main__":
    sys.exit(main())
