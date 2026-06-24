# co-agent:setup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `/co-agent:setup` — a panel-readiness preflight that picks the best access path per peer (official plugin → raw CLI + install nudge → none), probes real CLI usability through each adapter's true input channel, and records a readiness summary the autonomous flows consult.

**Architecture:** A new `scripts/check_panel.py` (stdlib only) holds a pure `classify()`, a `probe()` that spawns each peer's read-only adapter from an empty cwd, `detect_cli`/`detect_plugin`/`decide_access`, and a `report` that writes `.claude/co-agent-panel.local.json` atomically. A new `commands/setup.md` orchestrates it (report → offer the official plugin install for a CLI-only peer → present). The Kiro adapter is corrected to v3 (positional `[INPUT]` argv, `--v3`, `fs_read`), which also resolves the long-standing `NO_INGEST`.

**Tech Stack:** Python 3 stdlib only; Bash TAP test harness (`tests/run-all.sh`, auto-discovered `tests/structure/*.sh`, exported `assert_*` helpers); git; the peer AI CLIs (codex, kiro-cli, agy, gemini) — tests use fake shims on `PATH`, never the real CLIs.

## Global Constraints

- Python scripts use the **standard library only** — matches every existing co-agent script.
- The peer labels are `kiro-cli`, `claude`, `codex`, `agy`, `gemini` (label == binary; a bare `kiro` is "command not found"). The Kiro binary/label is **`kiro-cli`**.
- Sibling imports follow the existing pattern (`_HERE = dirname(abspath(__file__)); sys.path.insert(0, _HERE); import co_agent_config`).
- Readiness summary path: `.claude/co-agent-panel.local.json` (already gitignored by `.claude/*`); writes are **atomic** (temp file + `os.replace`).
- New test file `tests/structure/test-co-agent-setup.sh` is auto-discovered; it is **sourced** (no shebang exec, no `exit`); use the exported `assert_*` helpers; guard any failing command with `&& X=0 || X=$?` (a bare `ERR=$(failing-cmd)` trips `set -e` and aborts the file).
- **Precondition (verify before Task 1):** the `assert_*` helpers this file uses — `assert_eq`, `assert_contains`, `assert_file_exists`, `assert_json_valid`, `assert_grep_no_match` — must be exported by `run-all.sh` (`grep -nE 'assert_(json_valid|grep_no_match)\(\)' tests/run-all.sh`). A missing helper aborts the whole sourced structure run with command-not-found under `set -e`; add it to `run-all.sh` first if absent.
- Tests must NOT invoke the real peer CLIs — use fake shim scripts placed first on `PATH`, and isolate `PATH` (shim dir + a `python3` symlink + `/usr/bin:/bin`, **not** `~/.local/bin`/`/usr/local/bin`) so `report()`/`probe()` can never reach a real `agy`/`kiro-cli`/`gemini` and hang on an interactive CLI.
- Run the full suite after each task: `bash tests/run-all.sh`. Pre-existing failures (missing `.claude/hooks/*.sh`; reactive-presentation pptx-token tests) are out of scope — confirm they predate this work.
- Out of scope (separate follow-up plan): configure/sync-context v3-alignment (generating Kiro v3 Markdown agent configs via `kiro-cli agent create`).

---

### Task 0 (precondition): repo-wide `kiro` → `kiro-cli` rename — **owner of the rename this plan and the harness plan both assume**

The peer label/binary is `kiro-cli` (Global Constraints): `co_agent_config.py` must expose
`ALL_AIS`/`PEERS` with `kiro-cli`, and every adapter/config/test must use it. This already
landed in the repo, so Task 0 is normally a **verification gate** rather than new work — but it
is recorded here so the sequencing the harness plan **depends-on** has an explicit owner and is
re-runnable from a tree where it has *not* landed.

- [ ] **Verify it has landed** (must pass before Task 1):

```bash
# Match the ALL_AIS tuple itself — a bare "kiro-cli" anywhere (e.g. a BINARIES mapping) would
# pass a loose grep while the panel key is still "kiro".
grep -qE 'ALL_AIS *= *\([^)]*"kiro-cli"' plugins/co-agent/skills/co-agent/scripts/co_agent_config.py \
  && echo "rename landed (ALL_AIS uses kiro-cli)" \
  || echo "RENAME NOT LANDED — perform it before any further task"
```

- [ ] **If NOT landed**, do the rename as the first change and commit it separately before Task 1:
  replace the bare `kiro` label with `kiro-cli` across `co_agent_config.py` (`ALL_AIS`/`PEERS`/defaults),
  `references/ai-cli-adapters.md`, `co-agent.defaults.json`, and any test fixtures; update the
  fan-out `kiro)` case to `kiro-cli)`. Commit: `refactor(co-agent): kiro → kiro-cli label/binary rename`.

---

### Task 1: `check_panel.py` skeleton + `classify()` (pure)

**Files:**
- Create: `plugins/co-agent/skills/co-agent/scripts/check_panel.py`
- Test: `tests/structure/test-co-agent-setup.sh` (create)

**Interfaces:**
- Produces: `check_panel.py classify --sentinel <S> --exit <N> --timeout <0|1>` reads candidate
  stdout on its own stdin and prints one of `READY|NO_INGEST|AUTH|TIMEOUT|ERROR`.
- Produces (pure fn for later tasks): `classify(sentinel, stdout, stderr, returncode, timed_out) -> (status, reason)`.

- [ ] **Step 1: Write the failing test** — create `tests/structure/test-co-agent-setup.sh`:

```bash
#!/usr/bin/env bash
# Tests for co-agent:setup — classify(), access tiers, probe via fake CLIs, report/readers.
CP="plugins/co-agent/skills/co-agent/scripts/check_panel.py"

# --- Task 1: classify() taxonomy ---
assert_file_exists "$CP" "check_panel.py exists"
cl() { printf '%s' "$2" | python3 "$CP" classify --sentinel "$1" --exit "$3" --timeout "$4" 2>&1; }
assert_eq "READY"     "$(cl TOK 'TOK' 0 0)"            "classify: exact sentinel + exit0 → READY"
assert_eq "READY"     "$(cl TOK '  TOK
'  0 0)"                                                "classify: sentinel with surrounding whitespace → READY"
assert_eq "NO_INGEST" "$(cl TOK 'hello there' 0 0)"   "classify: exit0 but no sentinel → NO_INGEST"
assert_eq "AUTH"      "$(cl TOK 'Error: not logged in. Run login' 1 0)" "classify: auth pattern → AUTH"
assert_eq "TIMEOUT"   "$(cl TOK '' 0 1)"              "classify: timed_out → TIMEOUT"
assert_eq "ERROR"     "$(cl TOK 'boom' 7 0)"          "classify: non-zero unknown → ERROR"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `bash tests/run-all.sh 2>&1 | grep -i classify`
Expected: FAIL — `check_panel.py` does not exist.

- [ ] **Step 3: Implement `check_panel.py` skeleton + `classify`**

```python
#!/usr/bin/env python3
"""co-agent panel-readiness preflight: detect + probe + report per peer.

Usage:
  check_panel.py classify --sentinel S --exit N --timeout 0|1   # stdin = candidate stdout
  check_panel.py report [--root DIR] [--json]
  check_panel.py status <peer> [--root DIR]
  check_panel.py access <peer> [--root DIR]
"""
import sys
import os
import re

# Narrow patterns so normal output ("authenticate the request", "author", "4012",
# "run the build then login flow") doesn't misclassify a working peer as an auth failure:
# require explicit auth-failure phrasing, a bounded "run … login" hint, and word-bounded 401.
_AUTH_RE = re.compile(
    r"not logged in|unauthenticated|authentication (failed|required)|"
    r"please (log|sign) in|run [^\n]{0,40}\blogin\b|\b401\b",
    re.I,
)


def classify(sentinel, stdout, stderr, returncode, timed_out):
    """Pure: map a probe result to (status, reason)."""
    if timed_out:
        return "TIMEOUT", "probe exceeded the per-CLI timeout"
    text = (stdout or "")
    if returncode == 0 and sentinel and sentinel in text.strip().split():
        return "READY", ""
    if returncode == 0:
        # Exit 0 but no sentinel = ran fine, didn't consume input. Decide this BEFORE the
        # AUTH check so an exit-0 peer whose output merely mentions "login"/"auth" (e.g.
        # "run X to finish login") is NOT misclassified AUTH and silently dropped from the panel.
        return "NO_INGEST", "ran but did not echo the sentinel (input channel not consumed)"
    # Non-zero exit only: distinguish an auth failure from a generic error.
    if _AUTH_RE.search(f"{stdout}\n{stderr}"):
        return "AUTH", "authentication required"
    return "ERROR", f"exit {returncode}"


def _cmd_classify(argv):
    def opt(name, default=None):
        return argv[argv.index(name) + 1] if name in argv and argv.index(name) + 1 < len(argv) else default
    sentinel = opt("--sentinel", "")
    rc = int(opt("--exit", "0"))
    timed_out = opt("--timeout", "0") in ("1", "true", "yes")
    stdout = sys.stdin.read()
    status, _reason = classify(sentinel, stdout, "", rc, timed_out)
    print(status)
    return 0


def main():
    argv = sys.argv[1:]
    if not argv:
        print(__doc__)
        return 2
    if argv[0] == "classify":
        return _cmd_classify(argv[1:])
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
```

Make executable: `chmod +x plugins/co-agent/skills/co-agent/scripts/check_panel.py`.

> `READY` requires the sentinel to appear as a whitespace-delimited token in `stdout` after
> `strip()` — exact-ish match, not a loose substring, to avoid a prompt-echo false positive.

- [ ] **Step 4: Run test to verify it passes**

Run: `bash tests/run-all.sh 2>&1 | grep -i classify`
Expected: all six `classify` assertions PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/co-agent/skills/co-agent/scripts/check_panel.py tests/structure/test-co-agent-setup.sh
git commit -m "feat(co-agent): check_panel.py classify() taxonomy"
```

---

### Task 2: detection registry + `decide_access()` (tiered)

**Files:**
- Modify: `plugins/co-agent/skills/co-agent/scripts/check_panel.py`
- Test: `tests/structure/test-co-agent-setup.sh`

**Interfaces:**
- Produces: `PEER_PLUGINS = {"codex": "openai/codex-plugin-cc"}`; `PEERS = ("kiro-cli","claude","codex","agy","gemini")`.
- Produces: `detect_cli(peer) -> path|None` (`shutil.which(peer)`); `detect_plugin(peer, plugins_root) -> bool`;
  `decide_access(peer, has_cli, has_plugin) -> ("plugin"|"raw"|"none", suggest_install: bool)`.
- Produces CLI: `check_panel.py access <peer> --root DIR` resolves from a fixture but for this task
  is unit-driven via a hidden `--selftest-access <peer> <has_cli 0|1> <has_plugin 0|1>` that prints
  `<access> <suggest_install>`.

- [ ] **Step 1: Write the failing test** (append)

```bash
# --- Task 2: tiered access decision ---
ac() { python3 "$CP" --selftest-access "$1" "$2" "$3" 2>&1; }
assert_eq "plugin 0" "$(ac codex 1 1)" "codex with plugin+cli → plugin (no install nudge)"
assert_eq "plugin 0" "$(ac codex 0 1)" "codex with plugin only → plugin"
assert_eq "raw 1"    "$(ac codex 1 0)" "codex cli-only → raw + install nudge"
assert_eq "raw 0"    "$(ac agy 1 0)"   "agy cli-only → raw, no nudge (no official plugin)"
assert_eq "none 0"   "$(ac gemini 0 0)" "gemini absent → none"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `bash tests/run-all.sh 2>&1 | grep -iE "tiered|→ plugin|→ raw|→ none"`
Expected: FAIL — `--selftest-access` unknown.

- [ ] **Step 3: Implement**

```python
import shutil

PEERS = ("kiro-cli", "claude", "codex", "agy", "gemini")
PEER_PLUGINS = {"codex": "openai/codex-plugin-cc"}   # peer → official Claude Code plugin repo


def detect_cli(peer):
    return shutil.which(peer)


def detect_plugin(peer, plugins_root):
    """True if the peer's official plugin appears installed under the plugin cache."""
    repo = PEER_PLUGINS.get(peer)
    if not repo or not plugins_root or not os.path.isdir(plugins_root):
        return False
    needle = repo.split("/")[-1]   # e.g. "codex-plugin-cc"
    for dirpath, dirnames, _files in os.walk(plugins_root):
        # EXACT basename match (== / set membership), NOT substring — else a fork/backup dir like
        # "codex-plugin-cc-fork" would falsely count as the official plugin → route to a missing command.
        if os.path.basename(dirpath) == needle or needle in dirnames:
            return True
    return False


def decide_access(peer, has_cli, has_plugin):
    if has_plugin:
        return "plugin", False
    if has_cli:
        return "raw", peer in PEER_PLUGINS   # suggest installing the official plugin if one exists
    return "none", False
```

Add to `main()`:

```python
    if argv[0] == "--selftest-access":
        peer, hc, hp = argv[1], argv[2] == "1", argv[3] == "1"
        access, suggest = decide_access(peer, hc, hp)
        print(f"{access} {1 if suggest else 0}")
        return 0
```

- [ ] **Step 4: Run test to verify it passes**

Run: `bash tests/run-all.sh 2>&1 | grep -iE "→ plugin|→ raw|→ none|install nudge"`
Expected: all five assertions PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/co-agent/skills/co-agent/scripts/check_panel.py tests/structure/test-co-agent-setup.sh
git commit -m "feat(co-agent): tiered peer-access decision (plugin > raw+nudge > none)"
```

---

### Task 3: `probe()` through the adapter's real input channel

**Files:**
- Modify: `plugins/co-agent/skills/co-agent/scripts/check_panel.py`
- Test: `tests/structure/test-co-agent-setup.sh`

**Interfaces:**
- Produces: `ADAPTERS` map (peer → {argv-template, channel}); `probe(peer, timeout=20) -> (status, reason)`.
  - stdin-channel peers (`codex`/`agy`/`gemini`): sentinel on **stdin**; the argv prompt does NOT contain the token.
  - argv-channel peer (`kiro-cli`): sentinel embedded in the positional `[INPUT]` (kiro's real input).
  - Spawned with `cwd=<empty temp dir>`, `start_new_session=True` (own process group), a hard
    timeout (kill the group on expiry), and an output-size cap.
- Produces CLI: `check_panel.py probe <peer> [--timeout N]` prints the status (used by tests with fake CLIs on PATH).

- [ ] **Step 1: Write the failing test** (append)

```bash
# --- Task 3: probe via fake CLIs on PATH (never the real ones) ---
SHIM=$(mktemp -d "${TMPDIR:-/tmp}/coagent-shim.XXXXXX")
# codex/agy read stdin: a good shim echoes stdin; a bad shim ignores it.
printf '#!/usr/bin/env bash\ncat\n' > "$SHIM/codex"          # echoes stdin → sentinel returns
printf '#!/usr/bin/env bash\necho ignored\n' > "$SHIM/agy"   # ignores stdin → NO_INGEST
# kiro-cli reads the positional INPUT (last non-flag arg). Echo every arg so the sentinel returns.
printf '#!/usr/bin/env bash\nfor a in "$@"; do printf "%%s\\n" "$a"; done\n' > "$SHIM/kiro-cli"
chmod +x "$SHIM/codex" "$SHIM/agy" "$SHIM/kiro-cli"
# Isolated PATH: keep python3 + coreutils reachable, but DROP the dirs where real peer CLIs
# install (~/.local/bin, /usr/local/bin) so probe can NEVER hit a real CLI — only the shims
# above resolve, and an un-shimmed peer (gemini) is deterministically ABSENT.
PYBIN=$(dirname "$(command -v python3)")
ISO="$SHIM:$PYBIN:/usr/bin:/bin"
assert_eq "READY"     "$(PATH="$ISO" python3 "$CP" probe codex 2>&1)"    "probe: stdin-echo codex → READY"
assert_eq "NO_INGEST" "$(PATH="$ISO" python3 "$CP" probe agy 2>&1)"      "probe: stdin-ignoring agy → NO_INGEST"
assert_eq "READY"     "$(PATH="$ISO" python3 "$CP" probe kiro-cli 2>&1)" "probe: kiro-cli argv INPUT echoed → READY"
assert_eq "ABSENT"    "$(PATH="$ISO" python3 "$CP" probe gemini 2>&1)"   "probe: un-shimmed CLI → ABSENT (python3 still reachable)"
rm -rf "$SHIM"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `bash tests/run-all.sh 2>&1 | grep -iE "probe:"`
Expected: FAIL — `probe` unknown.

- [ ] **Step 3: Implement**

```python
import subprocess
import tempfile
import signal

# Read-only adapters, mirroring references/ai-cli-adapters.md. "{P}" = prompt, "{I}" = INPUT (prompt+sentinel).
# Every peer in PEERS MUST have an adapter here, else report()→probe() returns
# "ERROR unknown peer" for it. `claude` is a peer (it can be a read-only panel member when
# Codex hosts), so it needs an adapter too.
ADAPTERS = {
    "codex":    {"argv": ["codex", "exec", "-s", "read-only", "{P}"], "channel": "stdin"},
    "agy":      {"argv": ["agy", "-p", "{P}", "--sandbox"], "channel": "stdin"},
    "gemini":   {"argv": ["gemini", "-p", "{P}", "-o", "text"], "channel": "stdin"},
    "claude":   {"argv": ["claude", "-p", "{P}", "--permission-mode", "plan", "--output-format", "text"], "channel": "stdin"},
    "kiro-cli": {"argv": ["kiro-cli", "chat", "{I}", "--v3", "--mode", "default",
                          "--no-interactive", "--trust-tools=fs_read", "--wrap", "never"],
                 "channel": "argv"},
}
# Explicit check (NOT `assert`, which `python -O` strips): every PEER needs an adapter.
if set(ADAPTERS) != set(PEERS):
    raise RuntimeError(f"ADAPTERS {set(ADAPTERS)} != PEERS {set(PEERS)}")
_CAP = 64 * 1024   # output-size cap


def _kill_group(p):
    """SIGKILL the whole process group, tolerating an already-reaped pid so a probe never
    leaks a zombie or raises on cleanup."""
    try:
        os.killpg(os.getpgid(p.pid), signal.SIGKILL)
    except (ProcessLookupError, OSError):
        pass


def probe(peer, timeout=20, nonce="STATIC"):
    if peer not in ADAPTERS:
        return "ERROR", f"unknown peer {peer}"
    if not detect_cli(peer):
        return "ABSENT", "command not found"
    sentinel = f"COAGENT_PROBE_{nonce}"
    spec = ADAPTERS[peer]
    if spec["channel"] == "stdin":
        prompt = "Read the single token provided on stdin and reply with exactly that token, nothing else."
        argv = [a.replace("{P}", prompt) for a in spec["argv"]]
        stdin_data = sentinel + "\n"
    else:  # argv
        inp = f"Reply with exactly this token and nothing else: {sentinel}"
        argv = [a.replace("{I}", inp) for a in spec["argv"]]
        stdin_data = ""
    with tempfile.TemporaryDirectory() as cwd:
        try:
            p = subprocess.Popen(argv, cwd=cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, text=True, start_new_session=True)
            try:
                # `timeout` bounds the time window (a sentinel reply is tiny) and `_CAP` below
                # bounds what classify() sees. NOTE (hardening follow-up): communicate() buffers
                # output in memory until the timeout, so a CLI that floods within the window can
                # spike memory before the `[:_CAP]` slice. A hard memory bound would redirect
                # stdout/stderr to a TemporaryFile (no pipe-buffer deadlock) + read back only _CAP.
                out, err = p.communicate(input=stdin_data, timeout=timeout)
                timed_out = False
            except subprocess.TimeoutExpired:
                _kill_group(p)        # SIGKILL the whole session; tolerate an already-reaped pid
                out, err = p.communicate()
                timed_out = True
            return classify(sentinel, out[:_CAP], (err or "")[:_CAP], p.returncode, timed_out)
        except FileNotFoundError:
            return "ABSENT", "command not found"
        except Exception as e:  # never hard-fail a probe
            return "ERROR", str(e)[:200]
```

Add to `main()`:

```python
    if argv[0] == "probe":
        peer = argv[1]
        timeout = int(argv[argv.index("--timeout") + 1]) if "--timeout" in argv else 20
        status, _ = probe(peer, timeout=timeout)
        print(status)
        return 0
```

- [ ] **Step 4: Run test to verify it passes**

Run: `bash tests/run-all.sh 2>&1 | grep -iE "probe:"`
Expected: all four `probe:` assertions PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/co-agent/skills/co-agent/scripts/check_panel.py tests/structure/test-co-agent-setup.sh
git commit -m "feat(co-agent): probe peers via each adapter's real input channel"
```

---

### Task 4: `report` + atomic summary + `status`/`access` readers

**Files:**
- Modify: `plugins/co-agent/skills/co-agent/scripts/check_panel.py`
- Test: `tests/structure/test-co-agent-setup.sh`

**Interfaces:**
- Produces: `report(root, plugins_root)` assembles `{schema_version, generated_at, config_hash, peers:{peer:{access,status,cli_path,...}}}`,
  writes it atomically to `<root>/.claude/co-agent-panel.local.json`, and prints a human table.
- Produces CLI: `check_panel.py report [--root DIR] [--plugins-root DIR] [--json]`,
  `check_panel.py status <peer> [--root DIR]`, `check_panel.py access <peer> [--root DIR]`.
- Consumes: `detect_cli`, `detect_plugin`, `decide_access`, `probe`; `co_agent_config.effective(root)` (sibling import) for `config_hash`.

- [ ] **Step 1: Write the failing test** (append)

```bash
# --- Task 4: report + readers (fake CLIs so probe is deterministic) ---
S2=$(mktemp -d "${TMPDIR:-/tmp}/coagent-shim2.XXXXXX"); R=$(mktemp -d "${TMPDIR:-/tmp}/coagent-root.XXXXXX")
printf '#!/usr/bin/env bash\ncat\n' > "$S2/codex"; chmod +x "$S2/codex"   # codex READY via stdin echo
# Isolated PATH so report() probes ONLY the codex shim — never a real kiro-cli/agy/gemini on
# the runner (deterministic; honors the plan's "tests must not invoke real peer CLIs" rule).
PYBIN=$(dirname "$(command -v python3)"); ISO2="$S2:$PYBIN:/usr/bin:/bin"
PATH="$ISO2" python3 "$CP" report --root "$R" --plugins-root /nonexistent >/dev/null 2>&1
SUM="$R/.claude/co-agent-panel.local.json"
assert_file_exists "$SUM" "report writes the readiness summary"
assert_json_valid "$SUM" "summary is valid JSON"
assert_contains "$(cat "$SUM")" "schema_version" "summary has schema_version"
assert_contains "$(cat "$SUM")" "generated_at" "summary has generated_at"
assert_contains "$(cat "$SUM")" "config_hash" "summary has config_hash"
assert_eq "READY" "$(PATH="$ISO2" python3 "$CP" status codex --root "$R" 2>&1)" "status reader returns codex READY"
assert_eq "raw"   "$(PATH="$ISO2" python3 "$CP" access codex --root "$R" 2>&1)" "access reader returns codex raw (no plugin)"
assert_eq "none"  "$(python3 "$CP" access codex --root "$(mktemp -d)" 2>&1)" "access reader: no summary → sane default none"
# M4: a summary older than the TTL is stale → readers ignore it and fall back to the absent default
python3 - "$SUM" <<'PY'
import json, sys
with open(sys.argv[1]) as f: d = json.load(f)
d["generated_at"] = "2000-01-01T00:00:00+00:00"
with open(sys.argv[1], "w") as f: json.dump(d, f)
PY
EMPTY=$(mktemp -d)
assert_eq "$(python3 "$CP" status codex --root "$EMPTY" 2>/dev/null)" "$(PATH="$ISO2" python3 "$CP" status codex --root "$R" 2>/dev/null)" "TTL-stale summary is ignored (reader falls back to absent default)"
rm -rf "$S2" "$R" "$EMPTY"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `bash tests/run-all.sh 2>&1 | grep -iE "readiness summary|status reader|access reader"`
Expected: FAIL — `report` unknown.

- [ ] **Step 3: Implement** (sibling import + atomic write)

```python
import json
import datetime
import hashlib

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
try:
    import co_agent_config  # sibling — for config_hash
except Exception:
    co_agent_config = None

SCHEMA_VERSION = 1


def _config_hash(root):
    if co_agent_config is None:
        return ""
    try:
        blob = json.dumps(co_agent_config.effective(root), sort_keys=True)
        return hashlib.sha256(blob.encode()).hexdigest()[:16]
    except Exception:
        return ""


def _summary_path(root):
    return os.path.join(root, ".claude", "co-agent-panel.local.json")


def _atomic_write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, path)


def report(root, plugins_root, as_json=False):
    peers = {}
    for peer in PEERS:
        cli = detect_cli(peer)
        has_plugin = detect_plugin(peer, plugins_root)
        access, suggest = decide_access(peer, bool(cli), has_plugin)
        # raw_cli is recorded INDEPENDENTLY of access so a raw consumer (the harness implementer /
        # impl-flags, which need an actual write-mode CLI) can distinguish a plugin-only peer
        # (status READY but raw_cli false) from one with a usable raw CLI. Raw consumers MUST check
        # raw_cli, not status, before treating a peer as implementer-eligible.
        entry = {"access": access, "raw_cli": bool(cli)}
        if access == "plugin":
            entry["plugin"] = PEER_PLUGINS.get(peer)
            if cli:                       # also has a raw CLI → probe it so raw usability is known
                status, reason = probe(peer)
                entry["status"] = status
                entry["cli_path"] = cli
                if reason:
                    entry["reason"] = reason
            else:
                entry["status"] = "READY"  # plugin-only: the plugin handles ingestion
        elif access == "raw":
            status, reason = probe(peer)
            entry["status"] = status
            entry["cli_path"] = cli
            if reason:
                entry["reason"] = reason
            if suggest:
                entry["suggest_install"] = PEER_PLUGINS.get(peer)
        else:
            entry["status"] = "ABSENT"
        peers[peer] = entry
    summary = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.datetime.now().astimezone().isoformat(),
        "config_hash": _config_hash(root),
        "peers": peers,
    }
    _atomic_write_json(_summary_path(root), summary)
    if as_json:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    else:
        print(f"{'peer':10} {'access':7} {'status':10} note")
        for peer, e in peers.items():
            note = e.get("suggest_install") or e.get("reason") or e.get("plugin") or ""
            print(f"{peer:10} {e['access']:7} {e['status']:10} {note}")
    return 0


# A readiness summary goes stale: a peer can be installed/removed or its config
# changed after the summary was written (spec §5). Readers must treat a summary
# older than the TTL, or one whose config_hash no longer matches the current config,
# as absent — otherwise the fan-out routes to a peer that is no longer usable (or
# skips one that just became ready).
_SUMMARY_TTL_SEC = 24 * 3600


def _is_stale(root, s):
    ch = _config_hash(root)
    if ch and s.get("config_hash") and s["config_hash"] != ch:
        return True
    ts = s.get("generated_at")
    if not ts:
        return True
    try:
        gen = datetime.datetime.fromisoformat(ts)
    except ValueError:
        return True
    now = datetime.datetime.now(gen.tzinfo)
    return (now - gen).total_seconds() > _SUMMARY_TTL_SEC


def _read_summary(root):
    p = _summary_path(root)
    if not os.path.isfile(p):
        return None
    try:
        with open(p, encoding="utf-8") as f:
            s = json.load(f)
    except Exception:
        return None
    if _is_stale(root, s):  # TTL- or config-hash-stale → treat as absent
        return None
    return s


def _reader(root, peer, field, default):
    s = _read_summary(root)
    if not s:
        return default
    return s.get("peers", {}).get(peer, {}).get(field, default)
```

Add to `main()` (parse `--root`/`--plugins-root` defaulting `--root` to `.`, `--plugins-root` to
`os.path.expanduser("~/.claude/plugins")`):

```python
    if argv[0] == "report":
        root = argv[argv.index("--root") + 1] if "--root" in argv else "."
        proot = argv[argv.index("--plugins-root") + 1] if "--plugins-root" in argv else os.path.expanduser("~/.claude/plugins")
        return report(root, proot, as_json="--json" in argv)
    if argv[0] in ("status", "access"):
        peer = argv[1]
        root = argv[argv.index("--root") + 1] if "--root" in argv else "."
        default = "ABSENT" if argv[0] == "status" else "none"
        print(_reader(root, peer, argv[0], default))
        return 0
```

- [ ] **Step 4: Run test to verify it passes**

Run: `bash tests/run-all.sh 2>&1 | grep -iE "readiness summary|valid JSON|schema_version|status reader|access reader"`
Expected: all assertions PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/co-agent/skills/co-agent/scripts/check_panel.py tests/structure/test-co-agent-setup.sh
git commit -m "feat(co-agent): readiness report (atomic summary + status/access readers)"
```

---

### Task 5: `/co-agent:setup` command + registration

**Files:**
- Create: `plugins/co-agent/commands/setup.md`
- Modify: `plugins/co-agent/.claude-plugin/plugin.json` (`commands[]` += `./commands/setup.md`)
- Modify: `plugins/co-agent/skills/co-agent/SKILL.md` (add a setup-mode pointer)
- Modify: `.gitignore` (explicit `.claude/co-agent-panel.local.json` entry, for parity with the other `.claude/*` entries)
- Version bump: adding a `commands[]` entry is a release change — bump the single shared `"version"` across every `plugins/*/plugin.json` + `marketplace.json`, add a `CHANGELOG.md` entry, and tag `v{version}` (repo versioning rule).
- Test: `tests/structure/test-co-agent-setup.sh`

**Interfaces:**
- Produces: a `/co-agent:setup` command that runs `check_panel.py report`, and for a `raw` peer
  with `suggest_install` offers the official plugin install once via `AskUserQuestion`
  (`/plugin marketplace add <repo>`), and for an absent codex with npm available offers the CLI
  install (mirrors `/codex:setup`). Auth stays guidance-only.

- [ ] **Step 1: Write the failing test** (append)

```bash
# --- Task 5: command + manifest wiring ---
CMD="plugins/co-agent/commands/setup.md"
assert_file_exists "$CMD" "setup command file exists"
assert_contains "$(cat "$CMD" 2>/dev/null)" "check_panel.py" "command runs check_panel.py"
assert_contains "$(cat "$CMD" 2>/dev/null)" "marketplace add" "command offers the official plugin install"
PJ="plugins/co-agent/.claude-plugin/plugin.json"
assert_eq "True" "$(python3 -c "import json;print('./commands/setup.md' in json.load(open('$PJ'))['commands'])" 2>&1)" "setup registered in plugin.json"
assert_contains "$(cat plugins/co-agent/skills/co-agent/SKILL.md 2>/dev/null)" "co-agent:setup" "SKILL.md mentions setup"
assert_contains "$(cat .gitignore 2>/dev/null)" "co-agent-panel.local.json" "panel summary is gitignored"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `bash tests/run-all.sh 2>&1 | grep -iE "setup command|runs check_panel|plugin install|registered in plugin|mentions setup|gitignored"`
Expected: FAIL — files/entries missing.

- [ ] **Step 3: Implement**

Create `plugins/co-agent/commands/setup.md` (frontmatter mirroring `configure.md`'s style — inspect it first), body:

````markdown
---
description: Panel-readiness preflight — detect each peer's best access path (official plugin → raw CLI + install nudge → none), probe real CLI usability, and record a readiness summary the autonomous flows consult.
allowed-tools: Bash(python3:*), Bash(npm:*), AskUserQuestion
---

# co-agent: setup

Let `SK="${CLAUDE_PLUGIN_ROOT:-plugins/co-agent}/skills/co-agent/scripts"`.

1. Run the preflight and show the table:
   ```bash
   python3 "$SK/check_panel.py" report
   ```
2. For each peer whose row shows `raw` + a `suggest_install` repo (e.g. codex →
   `openai/codex-plugin-cc`), use `AskUserQuestion` **once** to offer installing the official
   plugin. Put the install option first, suffixed `(Recommended)`:
   - `Install the official <peer> plugin (Recommended)` → tell the user to run
     `/plugin marketplace add <repo>` (co-agent does not auto-install plugins).
   - `Keep the raw CLI fallback`
3. If a peer is `none`, codex specifically is missing, and `npm` is available, offer the CLI
   install once (`npm install -g @openai/codex`), then re-run the report.
4. Auth issues (`AUTH` status) are guidance only — tell the user to run the peer's login
   (e.g. `!codex login`, `!kiro-cli` login). Do not automate auth.
5. Present the final readiness table. The summary is written to
   `.claude/co-agent-panel.local.json`; review / consensus / harness consult it (READY peers
   only; if none are usable they degrade to solo and say so).
````

Add `./commands/setup.md` to the `commands` array in `.claude-plugin/plugin.json`.
Add a "setup" pointer to `SKILL.md` (a short mode line mentioning `/co-agent:setup`).
Add `.claude/co-agent-panel.local.json` to `.gitignore` (next to the other `.claude/*` entries).

- [ ] **Step 4: Run test to verify it passes**

Run: `bash tests/run-all.sh 2>&1 | grep -iE "setup command|runs check_panel|plugin install|registered in plugin|mentions setup|gitignored"`
Expected: all assertions PASS. Confirm the manifest still parses:
`python3 -c "import json;json.load(open('plugins/co-agent/.claude-plugin/plugin.json'))"`

- [ ] **Step 5: Version bump (M6 — explicit, not prose)**

Adding `./commands/setup.md` to `commands[]` is a release change. Bump the single shared
version across **every** `plugins/*/.claude-plugin/plugin.json` + `marketplace.json` and add a
`CHANGELOG.md` entry (same recipe as the harness plan's Step 5). **Coordinate with the harness
plan:** if both the `harness` and `setup` commands land in the same release, bump the version
**once** (not twice) — do the bump in whichever lands last and skip it in the other to avoid a
version collision. Verify alignment with the root `CLAUDE.md` version-consistency check.

- [ ] **Step 6: Commit**

```bash
git add plugins/co-agent/commands/setup.md plugins/*/.claude-plugin/plugin.json \
        plugins/co-agent/skills/co-agent/SKILL.md .gitignore .claude-plugin/marketplace.json \
        CHANGELOG.md tests/structure/test-co-agent-setup.sh
git commit -m "feat(co-agent): /co-agent:setup command + registration"
```

---

### Task 6: Kiro v3 adapter fix + readiness consult in the flows (docs)

**Files:**
- Modify: `plugins/co-agent/skills/co-agent/references/ai-cli-adapters.md`
- Modify: `plugins/co-agent/skills/co-agent/references/delegated-implement.md`
- Modify: `plugins/co-agent/commands/harness.md`
- Test: `tests/structure/test-co-agent-setup.sh`

**Interfaces:**
- Produces (doc contract): the Kiro adapter passes content via the positional `[INPUT]` (argv),
  uses `--v3 --mode default` and `--trust-tools=fs_read`; the flows consult the readiness summary
  and use only READY peers, routing a Tier-1 peer to its plugin command.

- [ ] **Step 1: Write the failing test** (append)

```bash
# --- Task 6: v3 adapter + readiness consult documented ---
ADP="plugins/co-agent/skills/co-agent/references/ai-cli-adapters.md"
# Needle must NOT start with "-" or assert_contains's `grep -q "$needle"` parses it as an option
# and fails even when present. A leading space keeps it dash-safe AND pins the literal `--v3`
# flag (this is the post-Task-6-Step-3 adapter line — a TDD failing-test-first assertion).
assert_contains "$(cat "$ADP" 2>/dev/null)" " --v3 --mode" "Kiro adapter documents --v3 --mode"
assert_contains "$(cat "$ADP" 2>/dev/null)" "fs_read" "Kiro adapter uses fs_read tool name"
assert_contains "$(cat "$ADP" 2>/dev/null)" "co-agent-panel.local.json" "adapters doc references the readiness summary"
assert_contains "$(cat plugins/co-agent/commands/harness.md 2>/dev/null)" "co-agent-panel" "harness consults readiness (run /co-agent:setup)"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `bash tests/run-all.sh 2>&1 | grep -iE "Kiro adapter|fs_read|readiness summary|harness consults"`
Expected: FAIL — docs not yet updated.

- [ ] **Step 3: Implement** — update the docs:
  - `ai-cli-adapters.md` Kiro row: change the command to
    `kiro-cli chat "<PROMPT + CONTEXT as the positional INPUT>" --v3 --mode default --no-interactive --trust-tools=fs_read --wrap never`
    and note: content goes in the positional `[INPUT]` (argv), NOT piped stdin (root cause of the
    earlier no-output); `fs_read` is the real read-only tool name. Update the fan-out `kiro-cli)`
    case to pass `"$PROMPT"`/context as the positional arg rather than piping the diff to stdin.
  - Add a short "Readiness" subsection to `ai-cli-adapters.md`: the fan-out consults
    `.claude/co-agent-panel.local.json` (via `check_panel.py access/status`) and includes only
    READY peers; a Tier-1 peer (codex with `access: plugin`) routes to `/codex:review` /
    `/codex:rescue`; if no peer is READY, degrade to solo and say so. Suggest `/co-agent:setup`.
  - `harness.md` H0 + `delegated-implement.md`: before fan-out / implementer selection, consult the
    readiness summary; skip non-READY peers; if none usable, block the multi-model gate and tell
    the user to run `/co-agent:setup`.

- [ ] **Step 4: Run test to verify it passes**

Run: `bash tests/run-all.sh 2>&1 | grep -iE "Kiro adapter|fs_read|readiness summary|harness consults"`
Expected: all four assertions PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/co-agent/skills/co-agent/references/ai-cli-adapters.md \
        plugins/co-agent/skills/co-agent/references/delegated-implement.md \
        plugins/co-agent/commands/harness.md tests/structure/test-co-agent-setup.sh
git commit -m "fix(co-agent): Kiro v3 adapter (argv INPUT, --v3, fs_read) + flows consult readiness"
```

---

### Task 7: Full-suite green + inventory docs

**Files:**
- Modify: `plugins/co-agent/CLAUDE.md`, root `CLAUDE.md` (co-agent inventory: add the setup command)
- Test: whole suite

- [ ] **Step 1: Run the full suite**

Run: `bash tests/run-all.sh`
Expected: every co-agent test passes; only the pre-existing unrelated failures remain (confirm
they predate this branch with `git stash` or by inspecting their subjects).

- [ ] **Step 2: Update inventories**

Add a one-line `/co-agent:setup` entry to `plugins/co-agent/CLAUDE.md` (Commands/Modes) and the
co-agent section of the root `CLAUDE.md`. Factual, short.

- [ ] **Step 3: Commit**

```bash
git add plugins/co-agent/CLAUDE.md CLAUDE.md
git commit -m "docs(co-agent): document /co-agent:setup in inventories"
```

---

## Self-Review

**Spec coverage:**
- §3 tiered access → Task 2 (`decide_access`) + Task 4 (report records `access`).
- §4 detection (plugin/CLI/usable) + probe taxonomy → Tasks 1 (classify), 2 (detect), 3 (probe).
- §4.1 probe (real input channel, empty cwd, exact match, process-group kill, output cap) → Task 3.
- §5 readiness summary (schema_version/generated_at/config_hash, atomic, readers) → Task 4.
- §6 components (`check_panel.py`, `setup.md`, registry, registration) → Tasks 1–5.
- §6.1 kiro-cli label == binary → already landed (repo-wide rename); `PEERS`/adapters use `kiro-cli`.
- §6.2 Kiro v3 adapter (argv INPUT, --v3, fs_read) → Task 6.
- §7 routing/synthesis + §integration (flows consult readiness, solo degrade) → Task 6.
- §8 safety (read-only probe, empty cwd, no hard-fail, no auto-auth, install consented once) → Tasks 3, 5.
- §9 testing → each task's test block + Task 7 suite.

**Deferred (intentional, separate follow-up plan):** §6.3 configure/sync-context v3-alignment
(generating Kiro v3 Markdown agent configs via `kiro-cli agent create`) — needs the agent-config
schema verified first (§10 open question). Not blocked by this plan.

**Placeholder scan:** no TBD/TODO; every code step shows real code; test code is concrete.

**Type/name consistency:** `classify(sentinel, stdout, stderr, returncode, timed_out)`,
`detect_cli`/`detect_plugin`/`decide_access`, `probe(peer, timeout, nonce)`, `report(root, plugins_root, as_json)`,
`PEERS`/`PEER_PLUGINS`/`ADAPTERS`, CLI verbs `classify`/`probe`/`report`/`status`/`access` — used
consistently across tasks. Summary path `.claude/co-agent-panel.local.json` and status strings
(`READY`/`NO_INGEST`/`AUTH`/`TIMEOUT`/`ERROR`/`ABSENT`) match the spec.

## Notes for the executor

- Tests use **fake CLI shims on `PATH`** — never the real peer CLIs (deterministic, offline).
- The probe uses a static nonce in tests (`nonce="STATIC"`); in real runs the command may pass a
  random nonce, but `check_panel.py` must not call `Math.random`/time for the nonce in a way that
  breaks determinism of unit tests — keep the default nonce fixed and only vary it from the
  command layer if needed.
- Clean tree before starting; each task ends in its own commit.
