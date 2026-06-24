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
  pre-pr-gate          — PreToolUse(Bash) gate: when the command is `gh pr create`, fan the PR
                         diff out to the installed panel and BLOCK (exit 2) when a QUORUM of
                         peers (default majority) flags CRITICAL/MAJOR. Runs synchronously (2-3 min).
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
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
import consensus_state as cs
try:
    import co_agent_config as cac
except Exception as _e:   # missing OR a SyntaxError/etc. in the module — degrade, but don't hide it
    cac = None
    sys.stderr.write(f"[co-agent] could not import co_agent_config (panel config disabled): {_e!r}\n")

STUCK_LIMIT = 3

# --- PR consensus gate ---------------------------------------------------------
# Fire only on `gh pr create` (the PR-raise event) at a COMMAND boundary — start of line, or
# right after a shell separator (`;` `&` `|` `&&` `||` newline), allowing optional `VAR=val ` env
# prefixes. Catches `cd x && gh pr create` (compound) but NOT a string like `echo "gh pr create"`
# / `git commit -m "gh pr create"` (preceded by a quote). `gh pr edit` is intentionally NOT
# gated — a metadata edit needn't re-run a 2-3 min panel, and `edit <n>` would diff a possibly
# unrelated local `base...HEAD`. Code updates land via push (not `gh pr edit`), at PR-raise time.
_PR_CMD_RE = re.compile(r"(?:^|[\n;&|])\s*(?:[A-Za-z_][A-Za-z0-9_]*=\S*\s+)*gh\s+pr\s+create\b")
_DIFF_CAP = 30 * 1024            # cap the diff sent to each peer (context-window / cost bound)
# Verdict is read from the FIRST non-empty line ONLY (a machine-readable token), never a
# free-text body scan — a banner/preamble or an incidental "MAJOR" in prose must not flip it.
_VERDICT_RE = re.compile(r"^\s*(PASS|BLOCK)\b", re.I)

# Review adapters, mirroring references/ai-cli-adapters.md. Delivery is per the channel each
# CLI actually consumes (untrusted content is NEVER put in argv → no `ps` exposure):
#   channel "stdin" — prompt+diff piped on stdin (codex/agy/gemini).
#   channel "file"  — written to a temp file; argv tells the CLI to fs_read it. Kiro `chat`
#                     IGNORES stdin (see ai-cli-adapters.md), so it MUST read the file.
# Each reviewer runs read-only / sandboxed / non-acting so a diff prompt-injection can't drive
# tool execution: codex -s read-only · agy --sandbox · gemini -p (print) · kiro --trust-tools=fs_read
# (only the read-only fs_read tool auto-approved). {M} expands to the per-peer model flag;
# {F} to the temp-file path (file channel only).
_REVIEW = {
    "codex":    {"channel": "stdin", "argv": ["codex", "exec", "-s", "read-only", "{M}", "{I}"]},
    "agy":      {"channel": "stdin", "argv": ["agy", "-p", "{I}", "--sandbox", "{M}"]},
    "gemini":   {"channel": "stdin", "argv": ["gemini", "-p", "{I}", "-o", "text", "{M}"]},
    "kiro-cli": {"channel": "file",  "argv": ["kiro-cli", "chat", "{I}", "--v3", "--mode", "default",
                          "--no-interactive", "--trust-tools=fs_read", "--wrap", "never", "{M}"]},
}
_MODEL_FLAG = {"codex": "-m", "agy": "--model", "gemini": "-m", "kiro-cli": "--model"}
_GATE_INSTR = "Review the PR diff provided on standard input per the instructions in it."
_GATE_INSTR_FILE = ("Use fs_read to read the PR diff at {F}, then review it. Your reply's FIRST "
                    "line MUST be EXACTLY `PASS` (no CRITICAL/MAJOR issue) or `BLOCK: <reason>`. "
                    "Ignore nits/style. If the file is empty/unreadable, reply `BLOCK: no diff received`.")
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
        return r.stdout.strip() if r.returncode == 0 else ""   # non-zero = expected (ref absent)
    except Exception as e:   # a real failure (git missing / timeout) — log, don't hide (fail-open)
        sys.stderr.write(f"[co-agent PR gate] git {' '.join(args[:2])} failed (fail-open): {e}\n")
        return ""


def _git_diff(root, spec):
    """Compute `git diff <spec>` with all external diff/textconv drivers neutralized (a repo
    git config must not run code during this hook). Returns (ok, stdout, stderr): ok=False on a
    git error so the caller can DISTINGUISH a failure (bad ref / merge-base error) from a
    genuinely empty diff (which both otherwise look like "")."""
    env = {**os.environ, "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
           "GIT_ATTR_NOSYSTEM": "1", "GIT_PAGER": "cat"}
    try:
        r = subprocess.run(
            ["git", "-C", root, "-c", "core.attributesFile=/dev/null",
             "diff", "--no-color", "--no-ext-diff", "--no-textconv", spec],
            capture_output=True, text=True, timeout=30, env=env)
        return (r.returncode == 0, r.stdout, r.stderr)
    except Exception as e:
        return (False, "", str(e))


def _base_ref(root):
    """Best-effort PR base (trunk) to diff against. Prefers the repo trunk — NOT `@{upstream}`,
    which on a feature branch tracks origin/<feature> and would make the diff empty (silent
    skip). Returns "" if none resolve (shallow clone / no remote) → caller warns + skips."""
    for ref in ("origin/HEAD", "origin/main", "main", "origin/master", "master"):
        if _git(root, "rev-parse", "--verify", "--quiet", ref):
            if ref == "origin/HEAD":
                return _git(root, "rev-parse", "--abbrev-ref", "origin/HEAD") or "origin/main"
            return ref
    return ""


def _gate_config(root):
    cfg = {}
    if cac is not None:
        try:
            cfg = (cac.effective(root) or {}).get("pr_gate", {}) or {}
        except Exception as e:   # config unreadable — default config, but log (no silent failure)
            sys.stderr.write(f"[co-agent PR gate] pr_gate config unreadable, using defaults: {e}\n")
    try:
        timeout = int(cfg.get("timeout", 180))     # tolerate a stray "300s"/None → default
    except (TypeError, ValueError):
        timeout = 180
    quorum = cfg.get("quorum", "majority")
    if quorum not in ("majority", "any"):          # validate, don't silently accept a typo
        sys.stderr.write(f"[co-agent PR gate] invalid pr_gate.quorum '{quorum}' — using 'majority'.\n")
        quorum = "majority"
    return {
        "enabled": cfg.get("enabled", False),     # opt-in: enabling = consent to external fan-out
        "block": cfg.get("block", True),          # hard-block (vs advisory-only) on a quorum BLOCK
        "quorum": quorum,                         # "majority" (default) | "any"
        "timeout": max(30, timeout),
    }


# Strong, broad credential patterns — this gate is the LAST line of defense before an external
# fan-out, so the set must be comprehensive (not a weaker canonical fallback).
_SECRET_RE = re.compile(
    r"AKIA[0-9A-Z]{16}"                                  # AWS access key id
    r"|aws_secret_access_key\s*[:=]\s*\S{16,}"           # AWS secret access key
    r"|-----BEGIN [A-Z ]*PRIVATE KEY"                    # PEM private key
    r"|gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}"  # GitHub PAT/OAuth/app tokens
    r"|xox[abprs]-[A-Za-z0-9-]{10,}"                     # Slack tokens
    r"|sk-[A-Za-z0-9]{20,}|sk-ant-[A-Za-z0-9-]{20,}"     # OpenAI / Anthropic keys
    r"|AIza[0-9A-Za-z_\-]{30,}"                          # Google API key
    # generic keyword=value — require a QUOTED literal value so a code assignment like
    # `secret = _scan_secret(diff)` (an identifier/call, not a credential) is NOT a false match;
    # unquoted real secrets are covered by the dedicated high-entropy patterns above.
    r"|(?:password|passwd|secret|api[_-]?key|token|client[_-]?secret)['\"]?\s*[:=]\s*['\"][^'\"]{8,}",
    re.I,
)


_DIFF_META = ("diff --git", "index ", "--- ", "+++ ", "@@", "new file", "deleted file",
              "old mode", "new mode", "similarity ", "rename ", "copy ", "Binary files")


def _scan_secret(diff):
    """Return a short label if the fanned-out diff carries a secret, else ''. Scans EVERY line
    that will be sent — added (`+`), removed (`-`), AND context (unchanged) lines — skipping only
    diff metadata headers. The payload is the whole diff, so a credential in a context line near
    a change would otherwise leak unscanned. Uses the UNION of the strong local pattern and
    check_ai_context.SECRET_RE (never a weaker-only fallback)."""
    extra = None
    try:
        import check_ai_context as cac2
        extra = getattr(cac2, "SECRET_RE", None)
    except ImportError:
        pass
    for ln in diff.splitlines():
        if ln.startswith(_DIFF_META):
            continue   # diff metadata, not content
        if _SECRET_RE.search(ln) or (extra is not None and extra.search(ln)):
            kind = "an added" if ln.startswith("+") else ("a removed" if ln.startswith("-") else "a context")
            return f"matched a credential pattern on {kind} line"
    return ""


def _path_panel(host):
    """Degraded fallback when the config module is unavailable: review CLIs on PATH. Keeps only
    ONE of the Gemini family (agy preferred over gemini) so it isn't double-counted in quorum."""
    peers = [ai for ai in _REVIEW if ai != host and shutil.which(ai)]
    if "agy" in peers and "gemini" in peers:
        peers.remove("gemini")     # agy supersedes gemini — never count both
    return peers, {}


def _panel(root):
    """The canonical panel (`panel_ais`: kiro-cli + cross-provider peer + agy|gemini fallback —
    so agy and gemini are never BOTH counted), filtered by config `enabled` and PATH. Never the
    host. An explicit "all disabled" yields [] (no PATH override). Only a missing/failed config
    module degrades to a best-effort PATH scan."""
    host = os.environ.get("CO_AGENT_HOST", "claude")
    if cac is None:
        return _path_panel(host)
    try:
        ais = cac.panel_ais(host)
        panelcfg = (cac.effective(root) or {}).get("panel", {}) or {}
    except Exception as e:   # config/panel resolution failed — log, then PATH fallback (no hide)
        sys.stderr.write(f"[co-agent PR gate] panel resolution failed (fail-open, PATH fallback): {e}\n")
        return _path_panel(host)
    peers, models = [], {}
    for ai in ais:
        if ai == host or ai not in _REVIEW or not shutil.which(ai):
            continue
        if not panelcfg.get(ai, {}).get("enabled", True):
            continue   # respect an explicit disable (do NOT PATH-override it)
        peers.append(ai)
        models[ai] = panelcfg.get(ai, {}).get("model")
    return peers, models


def _build_argv(peer, model, fpath):
    """Expand the adapter template. {I} → the fixed instruction (stdin-channel: references
    stdin; file-channel: tells the CLI to fs_read {F}). {M} → the per-peer model flag. The
    untrusted diff is NEVER placed in argv."""
    file_ch = _REVIEW[peer]["channel"] == "file"
    instr = _GATE_INSTR_FILE.replace("{F}", fpath) if file_ch else _GATE_INSTR
    argv = []
    for tok in _REVIEW[peer]["argv"]:
        if tok == "{I}":
            argv.append(instr)
        elif tok == "{M}":
            if model and _MODEL_FLAG.get(peer):
                argv += [_MODEL_FLAG[peer], model]
        else:
            argv.append(tok)
    return argv


def _review_one(peer, prompt_text, model, fpath, timeout, out):
    try:
        argv = _build_argv(peer, model, fpath)
        if _REVIEW[peer]["channel"] == "file":
            # Kiro ignores stdin in `chat` — it reads the diff from the temp file via fs_read.
            r = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
        else:
            # stdin channel: pipe prompt+diff (never argv → no `ps` exposure). A CLI that
            # ignores stdin sees no diff → replies `BLOCK: no diff received` per the prompt.
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
        return 0  # not a `gh pr create` — pass through
    gate = _gate_config(root)
    if not gate["enabled"]:
        return 0
    # Prefer the PR's explicit base (`gh pr create --base <ref>`) over the repo trunk, so we
    # gate the same diff the PR will show; fall back to the detected trunk.
    mbase = re.search(r"(?:--base|-B)[= ]+(\S+)", cmd)
    base = ""
    if mbase:   # honor the PR's explicit base; try the local ref AND its remote-tracking form
        cand = mbase.group(1)
        for ref in (cand, f"origin/{cand}"):
            if _git(root, "rev-parse", "--verify", "--quiet", ref):
                base = ref
                break
        if not base:
            # An explicit --base that doesn't resolve must NOT silently fall back to trunk (that
            # would review a different scope than the PR). Warn + skip instead.
            sys.stderr.write(f"[co-agent PR gate] --base '{cand}' does not resolve (locally or "
                             "origin/) — consensus gate SKIPPED rather than review a different "
                             "scope. `git fetch origin` or check the base name.\n")
            return 0
    base = base or _base_ref(root)
    if not base:
        # No base ref (shallow clone / no remote): do NOT silently `git diff HEAD` (empty for an
        # all-committed PR → silent pass). Warn instead so the bypass is never invisible.
        sys.stderr.write("[co-agent PR gate] could not determine a base branch to diff against "
                         "(shallow clone / no remote?) — consensus gate SKIPPED. Run "
                         "/co-agent:consensus review manually, or `git fetch origin main`.\n")
        return 0
    ok, diff, derr = _git_diff(root, f"{base}...HEAD")
    if not ok:
        # git ERROR (bad ref / merge-base failure) — distinguish from an empty diff; warn, don't
        # silently pass (empty "" alone would look like "nothing to review").
        sys.stderr.write(f"[co-agent PR gate] `git diff {base}...HEAD` failed — gate SKIPPED "
                         f"(fail-open): {derr.strip()[:200]}\n")
        return 0
    if not diff.strip():
        return 0  # genuinely nothing to review
    # Data boundary: secret-scan the FULL diff's added lines (catch a credential ANYWHERE in the
    # PR, even past the cap) and refuse to fan out if any is found — before truncating the payload.
    secret = _scan_secret(diff)
    if secret:
        # ALWAYS refuse to fan a secret-bearing diff to third-party AIs. Whether that also HARD-
        # BLOCKS the PR follows the same block/advisory mode as a panel verdict: block→exit 2,
        # advisory→exit 0 with a loud warning (the diff is still never sent either way).
        if gate["block"]:
            sys.stderr.write("[co-agent PR gate] BLOCKED — the diff appears to contain a secret "
                             f"({secret}); it was NOT sent to third-party AIs. **Remove/redact the "
                             "secret from the diff, then retry the PR.** (CO_AGENT_PR_GATE=off would "
                             "disable the whole gate, NOT a safe fix for a leak.)\n")
            return 2
        sys.stderr.write("[co-agent PR gate] ADVISORY — the diff appears to contain a secret "
                         f"({secret}); it was NOT sent to third-party AIs and the consensus gate was "
                         "SKIPPED (block is off). Remove/redact the secret before relying on the gate.\n")
        return 0
    # Truncate the SENT payload on a line boundary (never mid-line / mid-UTF-8); tell the panel.
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
    fpath = None
    try:
        # File-channel peers (kiro) fs_read the diff from here; deadline shared by all threads.
        with tempfile.NamedTemporaryFile("w", suffix=".diff", delete=False, encoding="utf-8") as f:
            f.write(body)
            fpath = f.name
        threads = []
        for p in peers:
            t = threading.Thread(target=_review_one, args=(p, body, models.get(p), fpath, gate["timeout"], out))
            t.daemon = True   # never keep the process alive on a wedged peer thread
            threads.append(t)
        for t in threads:
            t.start()
        # Shared ABSOLUTE deadline: total wait is bounded to ~timeout+5, not timeout*N, even if
        # several peer threads wedge (join takes a remaining-time duration, recomputed per call).
        end = time.monotonic() + gate["timeout"] + 5
        for t in threads:
            t.join(max(0, end - time.monotonic()))
    finally:
        if fpath:
            try:
                os.unlink(fpath)
            except OSError:
                pass
    blockers, voted = [], []
    for p in peers:
        v = out.get(p, "")
        if not v or v.startswith("__TIMEOUT__") or v.startswith("__ERROR__"):
            continue
        # Verdict = the first line that IS a `PASS`/`BLOCK` token among the first few non-empty
        # lines (tolerates a short CLI banner) — NOT a free-text body scan, so an incidental
        # "MAJOR" in prose can't flip it. No token in the head → unparseable → fail-open.
        verdict = vline = None
        for ln in [l.rstrip().strip() for l in v.splitlines() if l.strip()][:8]:  # rstrip → CRLF-safe
            m = _VERDICT_RE.match(ln)
            if m:
                verdict, vline = m.group(1).upper(), ln
                break
        if verdict is None:
            continue   # unparseable verdict → don't count, don't block (fail-open)
        # A peer that didn't receive the diff (delivery glitch, not a content problem) is told to
        # reply `BLOCK: no diff received`. Treat that as a NON-vote (fail-open), never a real BLOCK.
        if verdict == "BLOCK" and re.search(r"no diff received|empty/unreadable", vline, re.I):
            sys.stderr.write(f"[co-agent PR gate] {p}: 'no diff received' → treated as non-vote (delivery issue, not content).\n")
            continue
        voted.append(p)   # peers that returned a parseable verdict (the actual voters)
        if verdict == "BLOCK":
            blockers.append((p, v.strip()[:1200]))
    usable = len(voted)
    if usable == 0:
        sys.stderr.write("[co-agent PR gate] no peer returned a parseable PASS/BLOCK verdict — gate could not "
                         "run; allowing the PR (fail-open). Re-run /co-agent:consensus review manually if needed.\n")
        return 0
    # Chair Principle — never let ONE AI's verdict decide. Hard-block only on a QUORUM:
    # "majority" (default) needs >half of voters AND ≥2 blockers; "any" needs ≥1. Below quorum,
    # a BLOCK is surfaced as ADVISORY (the host decides), not an automatic veto.
    n_block = len(blockers)
    if gate["quorum"] == "any":
        quorum_met = n_block >= 1
    else:  # majority
        quorum_met = n_block >= 2 and n_block * 2 > usable
    if blockers and gate["block"] and quorum_met:
        msg = [f"[co-agent PR gate] BLOCKED — {n_block}/{usable} panel peers flagged CRITICAL/MAJOR "
               "issues on this PR diff (quorum reached).",
               "Resolve them (or re-run after fixing), then retry the PR. To bypass, "
               "`export CO_AGENT_PR_GATE=off` (disables the gate)."]
        for p, v in blockers:
            msg.append(f"\n── {p} ──\n{v}")
        sys.stderr.write("\n".join(msg) + "\n")
        return 2  # PreToolUse: exit 2 blocks the tool call and feeds stderr back to the agent
    if blockers:  # below quorum (or block off) → advisory; the host weighs it, gate does not veto
        sys.stderr.write(f"[co-agent PR gate] ADVISORY — {n_block}/{usable} peer(s) flagged issues "
                         "(below block quorum; not vetoing — review and decide):\n"
                         + "\n".join(f"- {p}: {v[:300]}" for p, v in blockers) + "\n")
        return 0
    sys.stderr.write(f"[co-agent PR gate] [PASS] consensus PASS ({usable} voting peer(s): {', '.join(voted)}).\n")
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
    except Exception as e:
        # Fail-open (never wedge PR creation on a gate bug) but NOT silent — surface the error
        # to stderr with a traceback so a swallowed bug is debuggable, then allow the action.
        import traceback
        sys.stderr.write(f"[co-agent {event}] internal error (fail-open): {e}\n")
        traceback.print_exc(file=sys.stderr)
        return 0


if __name__ == "__main__":
    sys.exit(main())
