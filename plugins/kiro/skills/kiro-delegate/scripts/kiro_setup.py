#!/usr/bin/env python3
"""kiro plugin setup helpers: probe kiro-cli usability, list its models, and write the
two `.kiro/agents/*.json` custom agents the delegate/review paths invoke headlessly.

Usage:
  kiro_setup.py probe [--timeout N]                  # READY | AUTH | NO_INGEST | TIMEOUT | ERROR | ABSENT
  kiro_setup.py list-models                          # one model id per line (best-effort)
  kiro_setup.py write-agents [--root DIR] [--force] [--enable-bash]
                                                      # write .kiro/agents/kiro-{implementer,reviewer,websearch}.json
                                                      # --enable-bash grants the implementer execute_bash
                                                      # (off by default — see _implementer_agent's docstring);
                                                      # an unedited plugin-generated V2 implementer/reviewer
                                                      # file is upgraded without --force
  kiro_setup.py verify-agents [--root DIR]            # confirm kiro-implementer.json is plugin-generated
                                                      # (not tampered) before the pipeline runs its hook;
                                                      # exit 0 ok · 1 mismatch/tampered · 2 missing

probe() statuses:
  READY      — kiro-cli echoed the sentinel; usable headlessly.
  AUTH       — an auth-required message was detected; run `kiro-cli` interactively to
               log in, or set KIRO_API_KEY, then re-probe.
  NO_INGEST  — kiro-cli exited 0 but did NOT echo the sentinel back (it ran, but its
               input channel wasn't actually consumed the way the probe expects — e.g.
               a CLI build/flag combination that silently drops the argv prompt). Treat
               the same as not-yet-usable; report it to the user rather than assuming
               READY from a zero exit code alone.
  TIMEOUT    — the probe exceeded its timeout (cold-start CLIs can be slow on first call
               — retrying once is reasonable before treating this as a real failure).
  ERROR      — kiro-cli exited non-zero for a reason other than AUTH.
  ABSENT     — kiro-cli is not on PATH.
"""
import sys
import os
import re
import json
import errno
import hashlib
import shutil
import subprocess
import tempfile

_VALIDATE_TIMEOUT = 20  # seconds — `kiro-cli agent validate` on a small local JSON file
                        # should be near-instant; not exposed as a user setting (unlike
                        # delegate/review timeouts) since this is a write-time sanity
                        # check, not a long-running headless invocation.

_AUTH_RE = re.compile(
    r"not logged in|unauthenticated|invalid credentials|access denied|"
    r"token expired|expired token|please (log|sign) in|run .*login|\b401\b|\b403\b|"
    r"unauthorized|forbidden", re.I)

# The fs_read/fs_write preToolUse guard, realpath-based. Resolves the candidate path
# against the hook's cwd (the worktree — kiro-cli runs the hook where the agent runs),
# follows symlinks via os.path.realpath, and refuses (exit 2) any read/write whose
# RESOLVED location falls outside the resolved cwd. This closes the two bypasses a naive
# startswith('/')/'..'-in-parts string check leaves open: a symlink inside the worktree
# that points outside it (the path string looks relative and clean, the read/write lands
# elsewhere), and Windows drive/UNC absolute paths (no leading '/'). For a not-yet-
# existing file, realpath resolves the existing ancestry, so a write THROUGH an
# out-pointing symlinked directory is still caught. Kept as a single -c one-liner because
# it's embedded in the generated .kiro/agents JSON. Shared verbatim across both tool
# types and both agents (implementer, reviewer) — one path-confinement guard, three call
# sites.
#
# Every path in the payload is checked, and the call is refused unless at least one path
# was found and all of them resolve inside the cwd. fs_write carries `tool_input.path`,
# but the V2 engine's fs_read (kiro-cli 2.29.1) carries `tool_input.operations[]`, each
# with its own `path` (or `image_paths` in Image mode) and no top-level path. The earlier
# guard read only `tool_input.path`, saw "", resolved it to the cwd and allowed every
# read, including absolute paths outside the worktree. An operation with no path, a
# non-list `operations`, or a non-string path is refused rather than guessed at.
#
# kiro-cli expands `~` and environment variables in tool paths before opening them, so
# `~/.aws/credentials` and `$HOME/.aws/credentials` reached the home directory while this
# guard resolved them as relative names inside the cwd (measured on 2.29.1, reads and
# writes alike). Rather than reimplement the CLI's expansion rules (`~user`, unset
# variables), any path that starts with `~` or contains `$` is refused.
# A path-like key the guard does not read (`file_path`, `paths`, ...) is refused too, so
# a CLI field alias cannot carry a path past the check.
#
# A refusal writes its reason to stderr. The V3 engine ignores exit 2 when stderr is
# empty and runs the tool anyway (measured on 2.29.1); V2 blocks either way.
#
# The V3 engine's payloads (measured on 2.29.1): `read_file` {path, offset, limit},
# `list_directory` {path, ...}, `fs_write` {path, text} and `str_replace` {path, ...}
# carry a top-level `path`, which the same check covers. The universal-format `read`
# matcher also routes V3's search tools here, and those carry no path at all:
# `grep_search` {query, includePattern, excludePattern, ...} and `file_search`
# {query, excludePattern, ...}. V3 itself already confines both to the workspace (an
# outside includePattern finds nothing, and symlinks are not followed), so allowing
# them here is defense in depth on top of that confinement, not a replacement for it.
# Only those two tool names may pass without a path, and both of their checks are
# allowlists: the glob engine interprets the patterns, so an earlier literal denylist
# let brace expansion (`{/etc,src}/*`), escapes (`.\./x`) and character classes
# (`[.][.]/x`) through, as well as unknown keys such as `directory`.
# (1) Keys: every tool_input key must be in the measured set for that tool —
# grep_search {query, caseSensitive, excludePattern, explanation, includePattern},
# file_search {query, explanation, excludePattern, includeIgnoredFiles}. Any other key
# (`path`, `directory`, a field a later kiro-cli adds) is refused, not guessed at.
# (2) Patterns: includePattern/excludePattern must be None or a string that fully
# matches [A-Za-z0-9_.*?/!-]* (no braces, brackets, backslash, comma, `$`, `~`, colon,
# whitespace or NUL), does not start with `/`, is not os.path.isabs, and contains no
# `..`. Anything else is refused. Every other path-less payload (`introspect`,
# `tool_search`, ...) is still refused. The `!` is written as chr(33) so no shell can
# history-expand it inside the double-quoted one-liner.
#
# `python3 -I` (isolated mode), NOT bare `python3 -c`: this guard RUNS with cwd = the
# worktree — a checkout of HEAD in a repo this plugin's own threat model treats as
# untrusted (that's the whole reason capture-diff/scope_guard/these guards exist).
# Bare `python3 -c` puts cwd at sys.path[0], so a malicious `json.py` or `os.py`
# committed at the worktree root would be imported INSTEAD OF the real stdlib module by
# this guard's own `import json,sys,os,re` — arbitrary code execution as the host user,
# from the very mechanism meant to confine what Kiro can touch. `-I` drops cwd/the
# script's directory from sys.path (and ignores PYTHONPATH/PYTHONSTARTUP), closing that
# import-hijack path entirely; it changes nothing else about this one-liner's behavior.
_GUARD_CMD = (
    "python3 -I -c \"import json,sys,os,re; d=json.load(sys.stdin); "
    "i=d.get('tool_input'); i=i if isinstance(i,dict) else {}; "
    "o=i.get('operations',[]); o=o if isinstance(o,list) else [None]; "
    "g=lambda v: v if isinstance(v,list) else [None]; "
    "f=lambda e: (([e['path']] if 'path' in e else []) + g(e.get('image_paths',[]))) "
    "if isinstance(e,dict) else [None]; "
    "z=lambda e: [None] if any('path' in str(k).lower() and k not in ('path','image_paths') "
    "for k in e) else []; "
    "ps=f(i) + z(i) "
    "+ [p for e in o for p in ((f(e) + (z(e) if isinstance(e,dict) else [])) or [None])]; "
    "a={'grep_search':('query','caseSensitive','excludePattern','explanation','includePattern'), "
    "'file_search':('query','explanation','excludePattern','includeIgnoredFiles')}; "
    "n=d.get('tool_name'); t=isinstance(d.get('tool_input'),dict) and n in tuple(a); "
    "q=lambda v: v is None or (isinstance(v,str) "
    "and re.fullmatch('[A-Za-z0-9_.*?/'+chr(33)+'-]*',v) is not None "
    "and v[:1]!='/' and not os.path.isabs(v) and '..' not in v); "
    "wt=os.path.realpath(os.getcwd()); "
    "r=lambda p: os.path.realpath(p if os.path.isabs(p) else os.path.join(wt,p)); "
    "ok=(all(k in a[n] for k in i) and all(q(i.get(k)) for k in ('includePattern','excludePattern'))) "
    "if t else (bool(ps) and all(isinstance(p,str) and p and p[0]!='~' and '$' not in p "
    "and chr(0) not in p and (r(p)==wt or r(p).startswith(wt+os.sep)) for p in ps)); "
    "ok or sys.stderr.write('kiro guard: refused a path outside the working directory, "
    "or a payload without a checkable path'+chr(10)); "
    "sys.exit(0 if ok else 2)\""
)

# The guard embedded in the last plugin-generated V2 agent files (df79bad0, before the
# V3 search-tool rule above). Kept verbatim for _legacy_v2_*_agent, which tests use to
# build legacy fixtures; it is never written to a new file. write_agents recognizes
# legacy files through _LEGACY_V2_DIGESTS below, which covers every earlier guard too.
_LEGACY_V2_GUARD_CMD = (
    "python3 -I -c \"import json,sys,os; d=json.load(sys.stdin); "
    "i=d.get('tool_input'); i=i if isinstance(i,dict) else {}; "
    "o=i.get('operations',[]); o=o if isinstance(o,list) else [None]; "
    "g=lambda v: v if isinstance(v,list) else [None]; "
    "f=lambda e: (([e['path']] if 'path' in e else []) + g(e.get('image_paths',[]))) "
    "if isinstance(e,dict) else [None]; "
    "z=lambda e: [None] if any('path' in str(k).lower() and k not in ('path','image_paths') "
    "for k in e) else []; "
    "ps=f(i) + z(i) "
    "+ [p for e in o for p in ((f(e) + (z(e) if isinstance(e,dict) else [])) or [None])]; "
    "wt=os.path.realpath(os.getcwd()); "
    "r=lambda p: os.path.realpath(p if os.path.isabs(p) else os.path.join(wt,p)); "
    "ok=bool(ps) and all(isinstance(p,str) and p and p[0]!='~' and '$' not in p "
    "and chr(0) not in p and (r(p)==wt or r(p).startswith(wt+os.sep)) for p in ps); "
    "ok or sys.stderr.write('kiro guard: refused a path outside the working directory, "
    "or a payload without a checkable path'+chr(10)); "
    "sys.exit(0 if ok else 2)\""
)

# SHA-256 of every V2-format agent file a released or main-branch `write-agents` ever
# produced, over the canonical JSON (`_agent_digest`). Generated by running the
# kiro_setup.py of each main commit that changed it (588075a9, a0feab66, 844aca50,
# d6913752, 6195f7c9, 9729180e, df79bad0; v3.0.0 matches a0feab66's output) with and
# without --enable-bash. The guard string changed across those commits, so a single
# builder like _legacy_v2_implementer_agent (df79bad0's shape) would miss files written
# by the 3.0.0 release. A digest match proves the file holds no user edits, so
# write_agents may upgrade it without --force. Implementer digests map to the file's
# own execute_bash choice, which the upgrade keeps.
_LEGACY_V2_DIGESTS = {
    "kiro-implementer.json": {
        "06ff16838d272c1eec9e4410c796044332b22eafe56fef256a8e63f1e1a41b9e": False,
        "7b2f60f47f48defb4f2a0ceeff49406188154cacf37853f2e64c88b6330a1e10": False,
        "edc7065b3757ed9cd6cea0ab6274126eeb22e8e64b0a000e85422d6ee9b538fd": False,
        "7e9ef528aaa24d7be433dcabc9e327855a8b46590df20bad86f631dc9e9f75ae": True,
        "990c2af03a4ea7e17607abf49d9faf055e7b8053babb97f19f632b1477cadb50": True,
        "d5da9686e834e2029e5cd336edb0a0cd2e2463e8d86d9704400e7bebe17ba7cc": True,
    },
    "kiro-reviewer.json": {
        "26e88fd97debe06bac167256e013348b9fd914cacbf3375fc425b35f870e9e9c": None,
        "336bb727be6d0c78e7127b7a096b7e9c41c482f368279c6b97766f537ca78eb1": None,
        "d4e479059665a8619a575bfbe05dd77ad16df1f0647d7e3c599d95e5e2027850": None,
    },
}


def _agent_digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False).encode("utf-8")).hexdigest()


def _legacy_v2_match(name, obj):
    """(True, execute_bash) when `obj` is a V2 agent file this plugin generated earlier,
    else (False, None). execute_bash is None for the reviewer."""
    table = _LEGACY_V2_DIGESTS.get(name, {})
    try:
        d = _agent_digest(obj)
    except (TypeError, ValueError):
        return False, None
    return (True, table[d]) if d in table else (False, None)


_IMPLEMENTER_DESCRIPTION = ("Implements tasks handed off by the /kiro:delegate pipeline, inside a "
                            "throwaway git worktree the host controls.")
_IMPLEMENTER_PROMPT = ("You implement exactly the task described in the prompt you're given, using "
                       "the requirements/design/tasks spec files as context (read them with "
                       "fs_read). Make the minimal change that satisfies the task. Do not touch "
                       "files outside the task's declared file set. Do not run git commit — the "
                       "host commits after review.")
_REVIEWER_DESCRIPTION = ("Reviews a diff for the /kiro:review command and the pre-commit hook. "
                         "Read-only — never writes; reads only within its launch directory "
                         "(the isolated temp dir holding the diff).")
_REVIEWER_PROMPT = ("You are a strict but fair code reviewer. Read the diff you're pointed to "
                    "with fs_read and report findings as instructed in the prompt. Never modify "
                    "any file. You can only read files inside your working directory.")


def _guard_hook(index, matcher):
    """One preToolUse entry in kiro-cli's universal agent format (2.29.1), exactly as
    `kiro-cli agent upgrade` emits it, so the upgrade reports the generated files as
    already universal. The V3 engine refuses the older V2 format (exit 4); the V2 engine
    loads this format too."""
    return {"name": f"preToolUse-{index}", "trigger": "preToolUse", "matcher": matcher,
            "action": {"type": "command", "command": _GUARD_CMD}, "timeout": 10}


def _implementer_agent(enable_bash):
    """`enable_bash` grants execute_bash — OFF by default. worktree/capture-diff/
    scope_guard only guarantee what reaches the main git tree; they do nothing about a
    shell command's host-side side effects (reading credentials, deleting files outside
    the worktree, network calls) while it runs. Granting execute_bash is a separate trust
    decision about kiro-cli itself, made explicitly via `/kiro:setup`'s AskUserQuestion —
    never silently defaulted on.

    Universal agent format, the shape `kiro-cli agent upgrade` produces from the V2
    file: `tools` uses the universal names (`read`, `shell`, `write`, in that order),
    `allowedTools` keeps the V2 names, and `permissions.rules` allows the same
    capabilities."""
    return {
        "name": "kiro-implementer",
        "description": _IMPLEMENTER_DESCRIPTION,
        "prompt": _IMPLEMENTER_PROMPT,
        "tools": ["read"] + (["shell"] if enable_bash else []) + ["write"],
        "allowedTools": ["fs_read", "fs_write"] + (["execute_bash"] if enable_bash else []),
        "hooks": [
            # `write` covers fs_write/str_replace and V3's `code` tool. Defense-in-depth
            # on top of the host's worktree.py capture-diff + scope_guard.py (the
            # load-bearing guarantee — see references/kiro-headless.md): refuse a write
            # that RESOLVES outside the cwd the implementer was launched in (the
            # worktree). realpath-based, not string-based: a plain startswith('/')/'..'
            # check misses (a) a symlink inside the worktree pointing out of it — the
            # write path LOOKS relative but lands outside — and (b) Windows drive/UNC
            # absolute paths, which isabs() catches but a '/'-prefix check doesn't.
            # Escapes that slip past this still can't reach the main tree (the host
            # only ever applies the CAPTURED, scope-guarded diff) — this hook just
            # narrows the blast radius earlier.
            _guard_hook(0, "write"),
            # `read` covers fs_read/read_file/list_directory and V3's grep, glob, code,
            # introspect and tool_search tools. Same realpath containment, applied to
            # reads. Without this, a prompt-injection payload reachable from the task
            # prompt or spec content could direct the implementer to read an absolute
            # path outside the worktree (credentials, SSH keys) and have its contents
            # surface in Kiro's response — a confidentiality leak that execute_bash-off
            # does nothing to prevent. The pipeline copies spec files INTO the worktree
            # specifically so the implementer never needs an out-of-worktree read.
            _guard_hook(1, "read"),
        ],
        "permissions": {"rules": [{"capability": "fs_read", "effect": "allow"},
                                  {"capability": "fs_write", "effect": "allow"}]
                                 + ([{"capability": "shell", "effect": "allow"}]
                                    if enable_bash else [])},
    }


# Reviewer's read guard: the same _GUARD_CMD above, applied to reads. kiro_review.py
# runs the reviewer with cwd = an isolated temp dir containing ONLY the diff file, so
# confining reads to the resolved cwd is exactly the "expose only the diff" allowlist:
# a prompt-injection payload in an untrusted diff that tells the reviewer to read
# ~/.aws/credentials (or any absolute path / ../ escape / symlink out) gets exit 2 at the
# TOOL layer instead of relying on prose cautions. This is the technical mitigation for
# the standing /kiro:review path, which review.on_commit=false never protected. Same
# universal format as _implementer_agent.
_REVIEWER_AGENT = {
    "name": "kiro-reviewer",
    "description": _REVIEWER_DESCRIPTION,
    "prompt": _REVIEWER_PROMPT,
    "tools": ["read"],
    "allowedTools": ["fs_read"],
    "hooks": [_guard_hook(0, "read")],
    "permissions": {"rules": [{"capability": "fs_read", "effect": "allow"}]},
}


def _legacy_v2_implementer_agent(enable_bash):
    """The kiro-implementer file the plugin wrote before the universal format: V2 tool
    names, the flat V2 hook map ({"preToolUse": [{"matcher", "command"}]}) and
    _LEGACY_V2_GUARD_CMD — df79bad0's output, one of the _LEGACY_V2_DIGESTS entries.
    Used to build test fixtures. Never written."""
    tools = ["fs_read", "fs_write"] + (["execute_bash"] if enable_bash else [])
    return {
        "name": "kiro-implementer",
        "description": _IMPLEMENTER_DESCRIPTION,
        "prompt": _IMPLEMENTER_PROMPT,
        "tools": tools,
        "allowedTools": tools,
        "hooks": {"preToolUse": [{"matcher": "fs_write", "command": _LEGACY_V2_GUARD_CMD},
                                 {"matcher": "fs_read", "command": _LEGACY_V2_GUARD_CMD}]},
    }


def _legacy_v2_reviewer_agent():
    """The kiro-reviewer file the plugin wrote before the universal format. See
    _legacy_v2_implementer_agent."""
    return {
        "name": "kiro-reviewer",
        "description": _REVIEWER_DESCRIPTION,
        "prompt": _REVIEWER_PROMPT,
        "tools": ["fs_read"],
        "allowedTools": ["fs_read"],
        "hooks": {"preToolUse": [{"matcher": "fs_read", "command": _LEGACY_V2_GUARD_CMD}]},
    }


# Web-search delegation agent: lets a Claude Code session WITHOUT the WebSearch tool
# (e.g. Claude Code on Bedrock) route one-shot web searches through kiro-cli's native
# web_search tool. Search-only — no fs_read/fs_write/execute_bash, so unlike the two
# agents above there is nothing to path-confine and no preToolUse guard is needed; the
# entire risk surface is "the query text goes to Kiro's backend", which is the point
# of the feature and is consented to via /kiro:setup's websearch question. The file is
# always written by write_agents (harmless when the feature is off — routing is gated
# by kiro_config.py's websearch.enabled, not by this file's existence), and
# kiro_websearch.py refuses to run unless the on-disk file matches this dict exactly
# (same tamper defense as kiro_review.py's _reviewer_agent_ok — a hand-edited file
# that quietly adds execute_bash must not be trusted).
#
# Unlike the two agents above, this one stays in the V2 format: kiro_websearch.py runs
# on the default V2 engine, and `kiro-cli agent upgrade` would add a `web` (fetch URL)
# tool next to `web_search`, widening the agent's tool list.
_WEBSEARCH_AGENT = {
    "name": "kiro-websearch",
    "description": "Answers one-shot web search queries for the kiro plugin's "
                    "websearch delegation path. Search-only — no filesystem, no shell.",
    "prompt": "You are a web research assistant. Use web_search to answer the query "
              "you are given, then reply with a concise summary of findings followed "
              "by a list of source URLs. Never use any tool other than web_search.",
    "tools": ["web_search"],
    "allowedTools": ["web_search"],
    "hooks": {}
}


def probe(timeout=90, model=None, effort=None):
    if not shutil.which("kiro-cli"):
        return "ABSENT", "command not found"
    sentinel = "KIRO_SETUP_PROBE"
    argv = ["kiro-cli", "chat", "--no-interactive", "--trust-tools=", "--wrap", "never",
            f"Reply with exactly this token and nothing else: {sentinel}"]
    # The V3 engine, which the delegate and review paths run on (websearch stays on the
    # default V2 engine). An invalid --model fails on V3 with exit 1 ("The model '<id>'
    # is not available") instead of a silent substitution.
    argv += ["--agent-engine", "v3"]
    if model:
        argv += ["--model", model]
    else:
        argv += ["--mode", "default"]
    if effort:
        argv += ["--effort", effort]
    with tempfile.TemporaryDirectory() as cwd:
        outp, errp = os.path.join(cwd, ".out"), os.path.join(cwd, ".err")
        try:
            # Capture to FILES, not PIPEs — kiro-cli's acp-callback auth refresh happens
            # over the host fds it was launched with; a pipe severs that and hangs to the
            # full timeout (see co-agent's check_panel.py probe(), same root cause).
            with open(outp, "w") as of, open(errp, "w") as ef:
                r = subprocess.run(argv, cwd=cwd, stdin=subprocess.DEVNULL, stdout=of,
                                    stderr=ef, timeout=timeout)
            with open(outp, encoding="utf-8", errors="replace") as f:
                out = f.read()
            with open(errp, encoding="utf-8", errors="replace") as f:
                err = f.read()
        except subprocess.TimeoutExpired:
            return "TIMEOUT", "probe exceeded the timeout"
        except OSError as e:
            return "ERROR", str(e)[:200]
        if r.returncode == 0 and model:
            import kiro_config  # same directory; deferred like kiro_review's kiro_setup import
            if kiro_config.model_not_applied(out, err):
                return "ERROR", kiro_config.model_not_applied_error(model)
        if r.returncode == 0 and sentinel in out.strip().split():
            return "READY", ""
        if _AUTH_RE.search(f"{out}\n{err}"):
            return "AUTH", "authentication required — run `kiro-cli` interactively to log in, or set KIRO_API_KEY"
        if r.returncode == 0:
            return "NO_INGEST", "ran but did not echo the sentinel"
        return "ERROR", f"exit {r.returncode}: {err.strip()[:200] or out.strip()[:200]}"


def list_models():
    if not shutil.which("kiro-cli"):
        print("kiro-cli not found on PATH", file=sys.stderr)
        return 2
    argv = ["kiro-cli", "chat", "--list-models", "--format", "json"]
    with tempfile.TemporaryDirectory() as cwd:
        outp, errp = os.path.join(cwd, ".out"), os.path.join(cwd, ".err")
        try:
            # Capture to FILES, not PIPEs — same reason as probe()/kiro_review.py:
            # kiro-cli's acp-callback auth refresh happens over the host fds it was
            # launched with, and a PIPE severs that, hanging this call to the full
            # timeout even when authenticated. A prior version of this function used
            # capture_output=True (a PIPE) and reintroduced exactly that bug.
            with open(outp, "w") as of, open(errp, "w") as ef:
                r = subprocess.run(argv, cwd=cwd, stdin=subprocess.DEVNULL, stdout=of,
                                    stderr=ef, timeout=30)
            with open(outp, encoding="utf-8", errors="replace") as f:
                out = f.read()
            with open(errp, encoding="utf-8", errors="replace") as f:
                err = f.read()
        except subprocess.TimeoutExpired:
            print("could not list models: kiro-cli --list-models timed out", file=sys.stderr)
            return 2
        except OSError as e:
            print(f"could not list models: {e}", file=sys.stderr)
            return 2
    if r.returncode != 0:
        print(f"kiro-cli --list-models exited {r.returncode}: {err.strip()[:300]}", file=sys.stderr)
        return 2
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        # Not every kiro-cli build supports --format json for this flag — fall back to
        # printing raw stdout so the caller (a human running /kiro:setup) can still read it.
        print(out)
        return 0
    ids = []
    if isinstance(data, list):
        for item in data:
            if isinstance(item, str):
                ids.append(item)
            elif isinstance(item, dict):
                ids.append(str(item.get("id") or item.get("model") or item.get("name") or item))
    elif isinstance(data, dict):
        for item in data.get("models", []):
            if isinstance(item, str):
                ids.append(item)
            elif isinstance(item, dict):
                ids.append(str(item.get("id") or item.get("model") or item.get("name") or item))
    for m in ids:
        print(m)
    return 0


def _escapes_root(path, root):
    """True if `path` — or any existing ancestor directory in it, e.g. a tracked
    `.kiro/agents` symlink — resolves outside `root`. An untrusted repo can check out
    `.kiro/agents` (or `.kiro` itself) as a symlink pointing anywhere on the
    filesystem; a plain `open(path, "w")` would then truncate/overwrite whatever that
    resolves to. `os.path.realpath` resolves symlinks in the EXISTING portion of the
    path and leaves a not-yet-created trailing component untouched, so this still
    catches a symlinked ancestor even before the target file itself exists.

    NOTE: this only catches an escape to OUTSIDE `root` — it does NOT catch an ancestor
    symlink that redirects somewhere ELSE INSIDE `root` (e.g. `.kiro` symlinked to
    `src/`), which still passes this check and then gets past `write_agents`'s
    `O_NOFOLLOW` too (O_NOFOLLOW only ever protects the FINAL path component per POSIX
    semantics — an ancestor symlink is followed like any other directory).
    `_resolves_through_symlink` below is the complete check; this function is kept only
    for its more specific error message on the truly-escaping case."""
    real_root = os.path.realpath(root)
    real_path = os.path.realpath(path)
    return not (real_path == real_root or real_path.startswith(real_root + os.sep))


def _resolves_through_symlink(path):
    """True if resolving `path` involves ANY symlink anywhere in the chain — whether it
    redirects outside `root` (`_escapes_root` already catches that case) or to a
    DIFFERENT location still inside `root`. A plugin-generated agent file a fresh
    `write-agents` run creates never involves a symlink at all, so ANY symlink in the
    chain is inherently suspicious here — fail closed regardless of where it ultimately
    points.

    Compares against `os.path.abspath(path)`, NOT `os.path.normpath(path)`: `realpath`
    always returns an ABSOLUTE path, but `normpath` on a RELATIVE input (e.g.
    `root="."`, the `_default_root()` fallback outside a git repo) stays relative — so
    `realpath(path) != normpath(path)` was True for every relative-root call regardless
    of any actual symlink, making `write-agents` fail unconditionally in that context.
    `abspath` makes the path absolute via the SAME cwd basis `realpath` uses, without
    resolving symlinks, so the comparison is correct regardless of whether `path` was
    given relative or absolute."""
    return os.path.realpath(path) != os.path.abspath(path)


def write_agents(root, force=False, enable_bash=False):
    d = os.path.join(root, ".kiro", "agents")
    if _escapes_root(d, root):
        print(f"❌ refusing to write to {d}: it (or a parent directory, e.g. a "
              f"symlinked .kiro/) resolves outside the repo root {root} — this looks "
              f"like a symlink-through-write escape, not a normal checkout. "
              f"Remove/replace it before running write-agents again.", file=sys.stderr)
        return 2
    if _resolves_through_symlink(d):
        print(f"❌ refusing to write to {d}: a symlink somewhere in its path redirects "
              f"it elsewhere (even if that's still inside the repo root) — writing "
              f"here would land in the wrong place. Remove/replace it before running "
              f"write-agents again.", file=sys.stderr)
        return 2
    os.makedirs(d, exist_ok=True)
    written = []
    skip_bad = []
    # An existing file equal to a V2-format file this plugin generated earlier (which
    # the V3 engine refuses) is upgraded in place without --force: it holds no
    # user edits to preserve. The upgrade keeps that file's own execute_bash choice;
    # --enable-bash, like any config change to an existing file, still needs --force.
    for name, spec in (("kiro-implementer.json", _implementer_agent(enable_bash)),
                        ("kiro-reviewer.json", _REVIEWER_AGENT),
                        ("kiro-websearch.json", _WEBSEARCH_AGENT)):
        p = os.path.join(d, name)
        # Re-check the FULL per-file path, not just `d` above — `os.makedirs(d,
        # exist_ok=True)` is a no-op if `d` already exists (symlink or not), and an
        # untrusted repo could instead plant just this one FILE as a symlink while `d`
        # stays a real directory. realpath(p) resolves the whole path in one call, so
        # this also re-catches a symlinked `d` — it's a superset of the check above,
        # kept for the fast, single up-front error message in the common case.
        if _escapes_root(p, root):
            print(f"❌ refusing to write {p}: it resolves outside the repo root "
                  f"{root} — this looks like a symlink-through-write escape, not a "
                  f"normal checkout. Remove/replace it before running write-agents "
                  f"again.", file=sys.stderr)
            return 2
        if _resolves_through_symlink(p):
            print(f"❌ refusing to write {p}: a symlink somewhere in its path "
                  f"redirects it elsewhere (even if that's still inside the repo "
                  f"root) — writing here would land in the wrong place. "
                  f"Remove/replace it before running write-agents again.", file=sys.stderr)
            return 2
        upgrade = None
        if os.path.isfile(p) and not force:
            try:
                with open(p, encoding="utf-8") as f:
                    current = json.load(f)
            except (OSError, ValueError):
                current = None
            hit, bash = _legacy_v2_match(name, current)
            if hit:
                upgrade = _implementer_agent(bash) if bash is not None else spec
        if upgrade is not None:
            spec = upgrade
            print(f"upgraded (plugin-generated V2 agent): {p}")
        elif os.path.isfile(p) and not force:
            # Still validate an existing file we're skipping — a PRIOR write-agents run
            # that hit a validation failure (e.g. kiro-cli was mid-upgrade and timed
            # out) already left a bad file on disk; without this, the natural recovery
            # move (re-run write-agents WITHOUT --force after seeing the earlier ❌)
            # reports "skip (exists)" and exit 0, reproducing exactly the silent-bad-
            # config problem this validation exists to catch.
            if not _validate_agent_file(p):
                skip_bad.append(p)
            print(f"skip (exists): {p} — pass --force to overwrite")
            continue
        # O_NOFOLLOW: refuse if `p` is itself a symlink, even one pointing to another
        # file INSIDE the repo root (e.g. a tracked source file) — the `_escapes_root`
        # check above only catches an escape to OUTSIDE root. This matters specifically
        # on a `--force` re-run: without it, `open(p, "w")` would silently truncate
        # whatever the symlink actually points at instead of writing a fresh agent
        # file. Race-free vs. a separate os.path.islink() check + open() call.
        # `getattr` — `os.O_NOFOLLOW` doesn't exist on Windows Python, so referencing it
        # unconditionally raises AttributeError (not caught by `except OSError` below)
        # before `os.open` is even called, crashing every write-agents call on that
        # platform; `0` degrades to a plain open there (no symlink protection on
        # Windows, a known platform gap).
        try:
            fd = os.open(p, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | getattr(os, "O_NOFOLLOW", 0), 0o644)
        except OSError as e:
            if e.errno == errno.ELOOP:
                print(f"❌ refusing to write {p}: it is itself a symlink — writing "
                      f"through it would truncate whatever it points at instead of "
                      f"writing a fresh agent file. Remove it and re-run.",
                      file=sys.stderr)
                return 2
            raise
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(spec, f, indent=2)
            f.write("\n")
        written.append(p)
    bad = [p for p in written if not _validate_agent_file(p)]
    for p in written:
        status = "⚠️  INVALID (see above)" if p in bad else "ok"
        print(f"wrote {p} — {status}")
    bad += skip_bad
    if bad:
        # A file already on disk (skip_bad) failed re-validation too — same message,
        # since the fix is identical either way: regenerate with --force.
        for p in skip_bad:
            print(f"⚠️  {p} — INVALID (existing file failed re-validation; --force to "
                  f"regenerate)", file=sys.stderr)
        print(f"❌ {len(bad)} agent file(s) failed `kiro-cli agent validate` — kiro-cli "
              f"would silently fall back to its default agent for these (no auto-approval "
              f"in headless mode, so every fs_write/fs_read/execute_bash call gets "
              f"rejected). Fix the generator and re-run with --force.", file=sys.stderr)
        return 1
    return 0


def _validate_agent_file(path):
    """`kiro-cli agent validate` prints an error to stderr on an invalid config but
    still EXITS 0 — the exit code can't be trusted as a SUCCESS signal, only the
    presence of an error message on stderr can.

    Fail-open (return True) ONLY when kiro-cli is absent from PATH entirely — this is
    a write-time sanity check, not a hard requirement that kiro-cli be installed on
    the machine running write-agents. Once kiro-cli IS on PATH, every other outcome
    (non-zero exit, timeout, OSError launching it, or an error message on stderr) is
    fail-CLOSED: this function's entire purpose is to stop a bad config from being
    treated as fine, so an inconclusive check must not report success — a transient
    kiro-cli hiccup is exactly the kind of ambiguity that should surface as an error
    for a human to look at, not be silently waved through as a passing validation."""
    if not shutil.which("kiro-cli"):
        return True
    try:
        r = subprocess.run(["kiro-cli", "agent", "validate", "--path", path],
                            capture_output=True, text=True, timeout=_VALIDATE_TIMEOUT)
    except (OSError, subprocess.TimeoutExpired) as e:
        print(f"❌ could not run `kiro-cli agent validate` on {path} ({e}) — "
              f"treating as a validation failure since kiro-cli is on PATH but this "
              f"invocation could not confirm the file is valid", file=sys.stderr)
        return False
    if r.returncode != 0:
        detail = ((r.stderr or '') + (r.stdout or '')).strip()
        print(f"❌ `kiro-cli agent validate` exited {r.returncode} on {path}:\n{detail}",
              file=sys.stderr)
        return False
    # Check BOTH streams, same as the returncode!=0 branch above — a future kiro-cli
    # build that prints its validation error to stdout instead of stderr (while still
    # exiting 0, the exact "can't trust the exit code" behavior this function exists
    # to work around) would sail past a stderr-only check, silently reintroducing the
    # bug this whole validation was added to catch.
    #
    # kiro-cli 2.11.1 has no machine-readable (--json) validate output, so this can't
    # be a structured check. A confirmed-clean file produces EMPTY stdout and stderr
    # (verified against the installed binary); a confirmed-invalid one produces a
    # non-empty message ("Error: ... invalid: missing field `command` ..."). Treating
    # "any output at all" as failure — rather than matching a specific substring like
    # "error" — is the more conservative signal: it can't be defeated by a future
    # kiro-cli release rewording/relocalizing the error text (still non-empty output),
    # and a genuinely silent success can never look like a failure.
    #
    # Known trade-off, accepted: a future kiro-cli that prints ANY non-error text on
    # an otherwise-valid file (a deprecation notice, a one-line success banner) would
    # make this function report a false failure and hard-block write-agents/setup for
    # a config that actually works. Against the installed 2.11.1 this doesn't happen
    # (verified: clean file -> empty stdout+stderr), and a false failure here is loud
    # and local (write-agents exits non-zero, nothing silently proceeds on a bad
    # config) rather than the silent pass-through this whole check exists to prevent
    # — so the trade favors this direction. If a future kiro-cli release needs it,
    # narrow this back to a substring/pattern match on the known error shapes
    # ("missing field", "invalid") instead of reverting to exit-code trust.
    combined = f"{r.stderr or ''}{r.stdout or ''}"
    if combined.strip():
        print(f"❌ kiro-cli rejects {path}:\n{combined.strip()}", file=sys.stderr)
        return False
    return True


def verify_agents(root):
    """Confirm .kiro/agents/kiro-implementer.json is one this plugin would have written,
    not a hand-edited/tampered file — the delegate pipeline copies it into a worktree and
    runs Kiro with `--agent kiro-implementer`, and its `preToolUse.runCommand` hook is a
    host command that executes, so a tampered hook is a host-command-execution vector.
    A file that only DIFFERS by a legitimate config choice (execute_bash on vs off) is
    fine; anything else (unexpected tools, a preToolUse.runCommand that isn't the plugin's
    known-good guard, wrong name) is rejected so the caller can regenerate it with
    `write-agents --force` rather than trust it.

    Exit 0 = matches a plugin-generated shape (bash on or off) AND kiro-cli accepts it.
    1 = mismatch/tampered/rejected-by-kiro-cli. 2 = file missing (caller should run
    write-agents)."""
    p = os.path.join(root, ".kiro", "agents", "kiro-implementer.json")
    if not os.path.isfile(p):
        print(f"missing: {p} — run `kiro_setup.py write-agents` first", file=sys.stderr)
        return 2
    try:
        with open(p, encoding="utf-8") as f:
            got = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"unreadable/invalid {p}: {e} — regenerate with write-agents --force", file=sys.stderr)
        return 1
    # Compare against BOTH legitimate shapes (execute_bash off / on). Comparing the whole
    # dict (incl. the preToolUse hook command) means a tampered hook can't slip through.
    # Only the universal format passes: the V3 engine refuses the older V2 format.
    if _legacy_v2_match("kiro-implementer.json", got)[0]:
        print(f"❌ {p} is a plugin-generated V2-format kiro-implementer agent, which the "
              f"V3 engine refuses — re-run `kiro_setup.py write-agents` (no --force "
              f"needed) to upgrade it in place before delegating", file=sys.stderr)
        return 1
    if not any(got == _implementer_agent(b) for b in (False, True)):
        print(f"❌ {p} does not match a plugin-generated kiro-implementer agent in the "
              f"universal format — re-run `kiro_setup.py write-agents` (it upgrades an "
              f"unedited plugin-generated V2 file in place); a tampered or hand-edited "
              f"file needs `write-agents --force`. Do this before delegating; the pipeline "
              f"runs this agent's preToolUse hook", file=sys.stderr)
        return 1
    # Shape match alone isn't enough: `write_agents` can write a file THAT IS the
    # generator's exact output and still have kiro-cli reject it (this function's
    # caller — the delegate pipeline — is exactly what write_agents's own validation
    # failure warns about). Since the on-disk content is then byte-identical to
    # `_implementer_agent()`, the dict-equality check above alone would pass a file
    # write_agents itself already flagged as invalid — re-run the same validation this
    # function's caller ultimately relies on, so verify-agents is the one checkpoint
    # that catches this regardless of how the file got onto disk.
    if not _validate_agent_file(p):
        print(f"❌ {p} matches the plugin-generated shape but kiro-cli rejects it — "
              f"regenerate with `kiro_setup.py write-agents --force` and confirm it "
              f"validates clean before delegating.", file=sys.stderr)
        return 1
    print(f"ok: {p} matches a plugin-generated kiro-implementer agent")
    return 0


def _default_root():
    """Best-effort repo root when the caller didn't pass --root. Shells out to `git
    rev-parse --show-toplevel` as a subprocess of THIS already-permitted python3
    process — not a new top-level Bash tool call — so command prose never needs its own
    `git rev-parse` invocation (and the permission prompt that would trigger under an
    `allowed-tools: Bash(python3:*)`-scoped command) just to resolve --root. Falls back
    to '.' outside a git repo, or if git itself is missing/times out."""
    try:
        r = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                            capture_output=True, text=True, timeout=10)
        if r.returncode == 0:
            return r.stdout.strip() or "."
    except (subprocess.TimeoutExpired, OSError):
        pass
    return "."


def main():
    argv = sys.argv[1:]
    root = _default_root()
    if "--root" in argv:
        i = argv.index("--root")
        if i + 1 >= len(argv):
            print("--root requires a value", file=sys.stderr)
            return 2
        root = argv[i + 1]
        del argv[i:i + 2]
    if not argv:
        print(__doc__)
        return 2
    cmd = argv[0]
    if cmd == "probe":
        if "--timeout" in argv:
            i = argv.index("--timeout")
            if i + 1 >= len(argv) or not argv[i + 1].isdigit():
                print("--timeout requires a positive integer value", file=sys.stderr)
                return 2
            timeout = int(argv[i + 1])
        else:
            timeout = 90
        status, reason = probe(timeout)
        print(status + (f"\t{reason}" if reason else ""))
        return 0
    if cmd == "list-models":
        return list_models()
    if cmd == "write-agents":
        return write_agents(root, force="--force" in argv, enable_bash="--enable-bash" in argv)
    if cmd == "verify-agents":
        return verify_agents(root)
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
