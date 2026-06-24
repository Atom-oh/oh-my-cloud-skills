# co-agent:harness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `co-agent:harness` — a host-designs / peer-implements / panel-reviews orchestrator where an external AI writes code only inside an isolated git worktree and the host owns the red test, validation, and every commit.

**Architecture:** A new `/co-agent:harness` command + skill mode drives design → delegated-implement → review. The review steps reuse the existing consensus gate. New mechanical pieces are added to `co_agent_config.py` (implementer resolution + write-mode flags) and `consensus_state.py` (`needs-human` status, `stage-result` subcommand, `rebind`), plus one new `scripts/worktree.py` for the trust-boundary core. Orchestration prose lives in a lean `references/delegated-implement.md`.

**Tech Stack:** Python 3 (stdlib only — matches existing scripts), Bash test harness (`tests/run-all.sh`, TAP-style `assert_*` helpers, auto-discovered `tests/structure/*.sh`), git worktrees.

## Global Constraints

- Python scripts use the **standard library only** (no third-party imports) — matches every existing co-agent script.
- Model/AI identifiers are validated against `MODEL_RE` in `co_agent_config.py`. **Shipped
  value: `^[A-Za-z0-9 ._:/()-]+$`** — deliberately allows spaces + parentheses for Agy tokens
  like `Gemini 3.1 Pro (High)`; shell metacharacters stay rejected. (The original
  `^[A-Za-z0-9._:/-]+$` was widened in a later change — this note supersedes it.)
- **Implementer = sandbox CLI only (trust boundary).** The delegated implementer is
  restricted to the workspace-write **sandbox CLIs `codex`/`agy`**; `implementer_ai()`,
  `cmd_set`, and `cmd_impl_flags` all reject any other `ai` (exit 2). Host defaults:
  claude-host → `codex`, codex-host → `agy` (never a non-sandbox peer like `claude`).
  `claude --permission-mode acceptEdits`, `kiro-cli --trust-tools=read,write,grep`, and
  `gemini --yolo` are broad permission grants, **not** worktree-scoped write sandboxes
  (design spec §5: a worktree is git isolation, NOT a security sandbox), so they can
  never be implementer flags. The Task 1 / Task 2 code and tests below encode this
  directly via the `SANDBOX_IMPLEMENTERS = ("codex", "agy")` whitelist.
- The hosts are `claude` and `codex`; the panel AIs are `kiro-cli, claude, codex, agy, gemini`
  (`ALL_AIS` in `co_agent_config.py`, after the repo-wide `kiro`→`kiro-cli` rename). Only the
  sandbox subset `(codex, agy)` (`SANDBOX_IMPLEMENTERS`) may implement.
- **Execution order — rename precondition (owner: `co-agent:setup` plan, Task 0).** This plan
  reads `ALL_AIS`/`panel.kiro-cli`/`SANDBOX_IMPLEMENTERS` and assumes the label is `kiro-cli`,
  but it does **not** perform the `kiro`→`kiro-cli` rename itself. That rename is owned by the
  setup plan's **Task 0** (repo-wide `kiro`→`kiro-cli` across `co_agent_config.py` `ALL_AIS`,
  adapters, configs, and tests). **Verify, don't assume** it has landed before starting Task 1:
  `grep -q '"kiro-cli"' plugins/co-agent/skills/co-agent/scripts/co_agent_config.py` (the runtime
  already ships `ALL_AIS = ("kiro-cli", …)`). If that grep fails in your tree, run setup Task 0
  first — this plan **depends-on** it; otherwise both plans fail on a `kiro`/`kiro-cli` key mismatch.
- Write-mode adapters (workspace-write sandbox) exist **only** on the harness implement path; review/decide/ADR/gate paths stay read-only/advisory.
- The host is the **only** committer to the working branch; external AIs write only inside a worktree.
- Local commits only — never push/reset/rebase autonomously.
- New test file `tests/structure/test-co-agent-harness.sh` is auto-discovered (glob); `assert_*` helpers are exported by `run-all.sh` — call them directly, do not redefine.
- Run the **full suite** after each task: `bash tests/run-all.sh`.

---

### Task 1: Harness config defaults + implementer resolution

**Files:**
- Modify: `plugins/co-agent/skills/co-agent/co-agent.defaults.json`
- Modify: `plugins/co-agent/skills/co-agent/scripts/co_agent_config.py`
- Test: `tests/structure/test-co-agent-harness.sh` (create)

**Interfaces:**
- Produces: `co_agent_config.py implementer --host <claude|codex>` → prints the effective implementer AI id (counterpart when `harness.implementer` is null); exits 2 if the configured implementer equals the host.
- Consumes: existing `normalize_host`, `panel_ais`, `effective`, `MODEL_RE`.

- [ ] **Step 1: Write the failing test**

Create `tests/structure/test-co-agent-harness.sh`:

```bash
#!/usr/bin/env bash
# Tests for co-agent:harness — implementer resolution, write-mode flags,
# stage-result/needs-human/rebind state, and the worktree helper.
CFG="plugins/co-agent/skills/co-agent/scripts/co_agent_config.py"
ST="plugins/co-agent/skills/co-agent/scripts/consensus_state.py"
WT="plugins/co-agent/skills/co-agent/scripts/worktree.py"

# --- Task 1: implementer resolution (sandbox CLIs codex/agy only) ---
R=$(mktemp -d "${TMPDIR:-/tmp}/coagent-harness.XXXXXX")
assert_eq "codex" "$(python3 "$CFG" implementer --host claude --root "$R" 2>/dev/null)" "default implementer for claude host = codex (sandbox)"
assert_eq "agy" "$(python3 "$CFG" implementer --host codex --root "$R" 2>/dev/null)" "default implementer for codex host = agy (sandbox, not claude)"
python3 "$CFG" set harness implementer agy --root "$R" >/dev/null 2>&1
assert_eq "agy" "$(python3 "$CFG" implementer --host claude --root "$R" 2>/dev/null)" "override implementer respected"
# a non-sandbox implementer (claude/kiro-cli/gemini) is rejected at set time
python3 "$CFG" set harness implementer claude --root "$R" >/dev/null 2>&1 && SRC=0 || SRC=$?
assert_eq "2" "$SRC" "non-sandbox implementer 'claude' rejected by set (exit 2)"
# implementer equal to the host is rejected (codex implementer on a codex host)
python3 "$CFG" set harness implementer codex --root "$R" >/dev/null 2>&1
python3 "$CFG" implementer --host codex --root "$R" >/dev/null 2>&1 && IRC=0 || IRC=$?
assert_eq "2" "$IRC" "implementer equal to host rejected (exit 2)"
rm -rf "$R"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `bash tests/run-all.sh 2>&1 | grep -A1 'test-co-agent-harness'`
Expected: FAIL — `implementer` subcommand unknown (prints usage) so assertions mismatch.

- [ ] **Step 3: Add the `harness` defaults block**

In `co-agent.defaults.json`, add after the `panel` object (sibling key):

```json
  "harness": { "implementer": null, "max_fix_rounds": null }
```

- [ ] **Step 4: Implement implementer resolution in `co_agent_config.py`**

Add near `panel_ais`:

```python
# Only CLIs with a real worktree-scoped write sandbox may implement, so a delegated
# peer can never write outside its worktree (design spec §5). claude/kiro-cli/gemini
# have permission grants but no such sandbox, so they are NOT eligible implementers.
SANDBOX_IMPLEMENTERS = ("codex", "agy")


def implementer_ai(cfg, host):
    """Effective implementer: configured harness.implementer, else the sandbox-CLI
    default for this host (claude-host → codex, codex-host → agy). Restricted to
    SANDBOX_IMPLEMENTERS. Returns (ai, error_str|None)."""
    default = "agy" if host == "codex" else "codex"
    ai = (cfg.get("harness", {}) or {}).get("implementer") or default
    if ai == host:
        return ai, f"implementer '{ai}' cannot equal the current host '{host}'"
    if ai not in SANDBOX_IMPLEMENTERS:
        return ai, (f"implementer '{ai}' is not a sandbox CLI; choose one of: "
                    f"{', '.join(SANDBOX_IMPLEMENTERS)}")
    return ai, None


def cmd_implementer(root, host):
    ai, err = implementer_ai(effective(root), host)
    if err:
        print(err, file=sys.stderr)
        return 2
    print(ai)
    return 0
```

Extend `cmd_set` to accept the `harness` namespace. Add this branch where `ai`/`timeout`/`profile` keys are dispatched (before the per-AI panel branch):

```python
    if rest and rest[0] == "harness":
        if len(rest) != 3:
            print("usage: set harness <implementer|max_fix_rounds> <value>", file=sys.stderr)
            return 2
        _, key, val = rest
        h = local.setdefault("harness", {})
        if key == "implementer":
            if val in ("", "none", "null"):
                h["implementer"] = None
            elif not MODEL_RE.match(val) or val not in SANDBOX_IMPLEMENTERS:
                print(f"implementer must be a sandbox CLI: {', '.join(SANDBOX_IMPLEMENTERS)}", file=sys.stderr)
                return 2
            else:
                h["implementer"] = val
        elif key == "max_fix_rounds":
            if not val.isdigit() or int(val) < 1:
                print("max_fix_rounds must be a positive integer", file=sys.stderr)
                return 2
            h["max_fix_rounds"] = int(val)
        else:
            print("harness keys: implementer, max_fix_rounds", file=sys.stderr)
            return 2
        with open(lp, "w") as f:
            json.dump(local, f, indent=2)
            f.write("\n")
        print(f"wrote {lp}")
        return cmd_show(root, host)
```

(Place this block after `local` and `lp` are defined in `cmd_set`; mirror how the timeout/profile branches are structured in the current file. Verify variable names against the surrounding code before inserting.)

Wire the dispatch in `main()` next to the other commands:

```python
    if cmd == "implementer":
        return cmd_implementer(root, host)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `bash tests/run-all.sh 2>&1 | grep 'implementer'`
Expected: all five `implementer` assertions PASS.

- [ ] **Step 6: Commit**

```bash
git add plugins/co-agent/skills/co-agent/co-agent.defaults.json \
        plugins/co-agent/skills/co-agent/scripts/co_agent_config.py \
        tests/structure/test-co-agent-harness.sh
git commit -m "feat(co-agent): harness config + implementer resolution"
```

---

### Task 2: Write-mode implementer flags (workspace-write sandbox)

**Files:**
- Modify: `plugins/co-agent/skills/co-agent/scripts/co_agent_config.py`
- Test: `tests/structure/test-co-agent-harness.sh`

**Interfaces:**
- Produces: `co_agent_config.py impl-flags <ai> --host <h>` → **shell-quoted** (`shlex.join`) write-mode flags scoping the peer to a workspace-write sandbox plus its model/effort; consumers word-split the output as a shell word list (so a model name like `Gemini 3.1 Pro (High)` survives). Rejects an `ai` equal to the host **or** any non-sandbox `ai` (exit 2).
- Consumes: `implementer_ai`, `SANDBOX_IMPLEMENTERS`, existing per-AI `flags` model/effort logic.

- [ ] **Step 1: Write the failing test** (append to `test-co-agent-harness.sh`)

```bash
# --- Task 2: write-mode implementer flags (sandbox CLIs codex/agy only) ---
R2=$(mktemp -d "${TMPDIR:-/tmp}/coagent-harness2.XXXXXX")
assert_contains "$(python3 "$CFG" impl-flags codex --host claude --root "$R2" 2>/dev/null)" "workspace-write" "codex impl-flags use workspace-write sandbox"
assert_contains "$(python3 "$CFG" impl-flags agy --host claude --root "$R2" 2>/dev/null)" "sandbox" "agy impl-flags keep sandbox"
# a non-sandbox implementer (claude/kiro-cli/gemini) has no workspace-write sandbox → rejected (exit 2)
python3 "$CFG" impl-flags claude --host codex --root "$R2" >/dev/null 2>&1 && FRC=0 || FRC=$?
assert_eq "2" "$FRC" "non-sandbox implementer 'claude' rejected by impl-flags (exit 2)"
# regression: read-only review flags never carry a write sandbox
assert_grep_no_match "workspace-write|acceptEdits" "$(python3 "$CFG" flags codex --host claude --root "$R2" 2>/dev/null)" "review flags stay read-only (no write sandbox)"
rm -rf "$R2"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `bash tests/run-all.sh 2>&1 | grep 'impl-flags\|write sandbox'`
Expected: FAIL — `impl-flags` unknown command.

- [ ] **Step 3: Implement `cmd_impl_flags`**

```python
def cmd_impl_flags(root, ai, host):
    if ai == host:
        print(f"implementer '{ai}' cannot equal host '{host}'", file=sys.stderr)
        return 2
    # Implementers are restricted to workspace-write sandbox CLIs (codex/agy). A
    # non-sandbox peer (claude/kiro-cli/gemini) could write outside the worktree, so
    # it gets no write-mode flags — it is rejected, never granted acceptEdits/--yolo.
    if ai not in SANDBOX_IMPLEMENTERS:
        print(f"implementer '{ai}' is not a sandbox CLI; choose one of: "
              f"{', '.join(SANDBOX_IMPLEMENTERS)}", file=sys.stderr)
        return 2
    p = effective(root)["panel"].get(ai, {})
    model = p.get("model")
    parts = []
    if ai == "codex":
        parts += ["-s", "workspace-write"]
        if model:
            parts += ["-m", model]
        if p.get("effort"):
            parts += ["-c", f'model_reasoning_effort="{p["effort"]}"']
    elif ai == "agy":
        parts += ["--sandbox"]
        if model:
            parts += ["--model", model]
    # shlex.join quotes tokens containing spaces/parens (e.g. model "Gemini 3.1 Pro
    # (High)") so a shell consumer can `read -ra` / word-split the output back into argv
    # without mis-splitting the model name. Consumers MUST treat the output as a shell
    # word list (not re-split on raw whitespace).
    import shlex
    print(shlex.join(parts))
    return 0
```

Wire in `main()`:

```python
    if cmd == "impl-flags":
        return cmd_impl_flags(root, rest[0], host) if rest else 2
```

- [ ] **Step 4: Run test to verify it passes**

Run: `bash tests/run-all.sh 2>&1 | grep 'impl-flags\|write sandbox'`
Expected: all four assertions PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/co-agent/skills/co-agent/scripts/co_agent_config.py tests/structure/test-co-agent-harness.sh
git commit -m "feat(co-agent): write-mode implementer flags (workspace-write sandbox)"
```

---

### Task 3: `needs-human` status in consensus_state.py

**Files:**
- Modify: `plugins/co-agent/skills/co-agent/scripts/consensus_state.py` (`cmd_set` status branch)
- Test: `tests/structure/test-co-agent-harness.sh`

**Interfaces:**
- Produces: `consensus_state.py set . status needs-human` accepted; `get . status` returns `needs-human`.

- [ ] **Step 1: Write the failing test** (append)

```bash
# --- Task 3: needs-human status ---
R3=$(mktemp -d "${TMPDIR:-/tmp}/coagent-harness3.XXXXXX")
( cd "$R3" && git init -q && git config user.email t@example.invalid && git config user.name t \
    && git commit -q --allow-empty -m init )
python3 "$ST" init "$R3" --docs none --base main >/dev/null 2>&1
python3 "$ST" set "$R3" status needs-human >/dev/null 2>&1 && NRC=0 || NRC=$?
assert_eq "0" "$NRC" "status needs-human accepted (exit 0)"
assert_eq "needs-human" "$(python3 "$ST" get "$R3" status 2>&1)" "get status returns needs-human"
python3 "$ST" set "$R3" status bogus >/dev/null 2>&1 && BRC=0 || BRC=$?
assert_eq "2" "$BRC" "invalid status still rejected (exit 2)"
rm -rf "$R3"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `bash tests/run-all.sh 2>&1 | grep 'needs-human'`
Expected: FAIL — `needs-human` rejected by current `("running","done","aborted")` check.

- [ ] **Step 3: Implement** — in `cmd_set`, change the status validation:

```python
    elif key == "status":
        if value not in ("running", "done", "aborted", "needs-human"):
            print("status must be running|done|aborted|needs-human", file=sys.stderr)
            return 2
        s[key] = value
```

- [ ] **Step 4: Run test to verify it passes**

Run: `bash tests/run-all.sh 2>&1 | grep 'needs-human'`
Expected: all three assertions PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/co-agent/skills/co-agent/scripts/consensus_state.py tests/structure/test-co-agent-harness.sh
git commit -m "feat(co-agent): needs-human escalation status in consensus_state"
```

---

### Task 4: `stage-result` subcommand (durable output gate)

**Files:**
- Modify: `plugins/co-agent/skills/co-agent/scripts/consensus_state.py`
- Test: `tests/structure/test-co-agent-harness.sh`

**Interfaces:**
- Produces:
  - `consensus_state.py stage-result write <path.json> --stage <s> --verdict <PASS|REVIEW|FAIL> [--green true|false] [--in-scope true|false] [--rounds N] [--implementer <ai>] [--wall <tsv>]` → writes a schema-valid result.json (creating parent dirs); if `--wall` given, appends `<stage>\t<verdict>\t<green>` to the tsv.
  - `consensus_state.py stage-result check <path.json> [--stage <s>]` → exit 0 if the file exists and has `stage` + `verdict` (one of PASS/REVIEW/FAIL). With `--stage`, additionally enforces that stage's output schema: an implement/task stage (`implement`/`task`/`H3`) must be `green` **and** `in_scope`; a code/final gate (`code-gate`/`final`/`H4`) must be `verdict == PASS` (no unresolved CRITICAL/MAJOR). Else exit 1.

- [ ] **Step 1: Write the failing test** (append)

```bash
# --- Task 4: stage-result output gate ---
R4=$(mktemp -d "${TMPDIR:-/tmp}/coagent-harness4.XXXXXX")
python3 "$ST" stage-result check "$R4/missing.json" >/dev/null 2>&1 && M=0 || M=$?
assert_eq "1" "$M" "stage-result check on missing artifact fails (exit 1)"
python3 "$ST" stage-result write "$R4/plan-gate/result.json" --stage plan-gate --verdict PASS --rounds 1 --wall "$R4/stage_wall.tsv" >/dev/null 2>&1
assert_file_exists "$R4/plan-gate/result.json" "stage-result write creates result.json"
assert_json_valid "$R4/plan-gate/result.json" "result.json is valid JSON"
python3 "$ST" stage-result check "$R4/plan-gate/result.json" >/dev/null 2>&1 && C=0 || C=$?
assert_eq "0" "$C" "stage-result check on valid artifact passes (exit 0)"
assert_contains "$(cat "$R4/stage_wall.tsv")" "plan-gate" "stage_wall.tsv got a row"
# stage-aware check: an implement/task stage (H3) must be green AND in-scope
python3 "$ST" stage-result write "$R4/impl/bad.json" --stage impl --verdict PASS --green false --in-scope true >/dev/null 2>&1
python3 "$ST" stage-result check "$R4/impl/bad.json" --stage H3 >/dev/null 2>&1 && G=0 || G=$?
assert_eq "1" "$G" "stage-aware check (H3) fails when green=false"
python3 "$ST" stage-result write "$R4/impl/ok.json" --stage impl --verdict PASS --green true --in-scope true >/dev/null 2>&1
python3 "$ST" stage-result check "$R4/impl/ok.json" --stage H3 >/dev/null 2>&1 && GO=0 || GO=$?
assert_eq "0" "$GO" "stage-aware check (H3) passes when green=true and in_scope=true"
# stage-aware check: a code/final gate (H4) must be PASS (REVIEW/FAIL → block)
python3 "$ST" stage-result write "$R4/gate/result.json" --stage code-gate --verdict REVIEW >/dev/null 2>&1
python3 "$ST" stage-result check "$R4/gate/result.json" --stage H4 >/dev/null 2>&1 && H=0 || H=$?
assert_eq "1" "$H" "stage-aware check (H4) blocks a non-PASS code gate"
rm -rf "$R4"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `bash tests/run-all.sh 2>&1 | grep 'stage-result\|stage_wall'`
Expected: FAIL — `stage-result` unknown command.

- [ ] **Step 3: Implement `cmd_stage_result`**

```python
def cmd_stage_result(root, rest):
    if not rest or rest[0] not in ("write", "check"):
        print("usage: stage-result write <path> --stage S --verdict V [...] | check <path>", file=sys.stderr)
        return 2
    action = rest[0]
    args = rest[1:]
    if not args:
        print("stage-result: missing <path>", file=sys.stderr)
        return 2
    path = args[0]
    if action == "check":
        stage_kind = None
        for j in range(1, len(args) - 1):
            if args[j] == "--stage":
                stage_kind = args[j + 1]
        if not os.path.isfile(path):
            return 1
        try:
            with open(path, encoding="utf-8") as f:
                d = json.load(f)
        except Exception:
            return 1
        if not (d.get("stage") and d.get("verdict") in ("PASS", "REVIEW", "FAIL")):
            return 1
        # Stage-aware output gate: a stage advances only when ITS schema checks out,
        # not merely when verdict is a known value. An implement/task stage must be
        # green and in-scope; a code/final gate must be PASS (no CRITICAL/MAJOR left).
        if stage_kind in ("implement", "task", "H3"):
            return 0 if (d.get("green") is True and d.get("in_scope") is True) else 1
        if stage_kind in ("code-gate", "final", "H4"):
            return 0 if d.get("verdict") == "PASS" else 1
        return 0
    # write
    opts, i = {}, 1
    while i < len(args):
        if args[i].startswith("--") and i + 1 < len(args):
            opts[args[i][2:]] = args[i + 1]
            i += 2
        else:
            i += 1
    verdict = opts.get("verdict")
    if opts.get("stage") is None or verdict not in ("PASS", "REVIEW", "FAIL"):
        print("stage-result write needs --stage and --verdict PASS|REVIEW|FAIL", file=sys.stderr)
        return 2
    rec = {"stage": opts["stage"], "verdict": verdict}
    for k in ("green", "in-scope"):
        if k in opts:
            rec[k.replace("-", "_")] = opts[k].lower() in ("true", "1", "yes")
    if "rounds" in opts:
        rec["rounds"] = int(opts["rounds"]) if opts["rounds"].isdigit() else 0
    if "implementer" in opts:
        rec["implementer"] = opts["implementer"]
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rec, f, indent=2, ensure_ascii=False)
        f.write("\n")
    if "wall" in opts:
        with open(opts["wall"], "a", encoding="utf-8") as w:
            w.write(f"{rec['stage']}\t{verdict}\t{rec.get('green', '')}\n")
    print(f"wrote {path}")
    return 0
```

Wire in `main()`:

```python
    if cmd == "stage-result":
        return cmd_stage_result(root, rest)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `bash tests/run-all.sh 2>&1 | grep 'stage-result\|stage_wall'`
Expected: all eight assertions PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/co-agent/skills/co-agent/scripts/consensus_state.py tests/structure/test-co-agent-harness.sh
git commit -m "feat(co-agent): stage-result subcommand for durable output gates"
```

---

### Task 5: `rebind` (resume after manual fix)

**Files:**
- Modify: `plugins/co-agent/skills/co-agent/scripts/consensus_state.py`
- Test: `tests/structure/test-co-agent-harness.sh`

**Interfaces:**
- Produces: `consensus_state.py rebind <root>` → re-records `head` (and `base` left intact) to the current `HEAD`, so a subsequent `verify` passes after an intentional manual commit. Exit 0 on success, 2 if no session.

- [ ] **Step 1: Write the failing test** (append)

```bash
# --- Task 5: rebind after manual commit ---
R5=$(mktemp -d "${TMPDIR:-/tmp}/coagent-harness5.XXXXXX")
( cd "$R5" && git init -q && git config user.email t@example.invalid && git config user.name t \
    && git commit -q --allow-empty -m init )
python3 "$ST" init "$R5" --docs none --base main >/dev/null 2>&1
( cd "$R5" && git commit -q --allow-empty -m "manual fix" )
python3 "$ST" verify "$R5" >/dev/null 2>&1 && V1=0 || V1=$?
assert_eq "1" "$V1" "verify fails after HEAD drift (exit 1)"
python3 "$ST" rebind "$R5" >/dev/null 2>&1 && RB=0 || RB=$?
assert_eq "0" "$RB" "rebind succeeds (exit 0)"
python3 "$ST" verify "$R5" >/dev/null 2>&1 && V2=0 || V2=$?
assert_eq "0" "$V2" "verify passes after rebind (exit 0)"
rm -rf "$R5"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `bash tests/run-all.sh 2>&1 | grep 'rebind\|HEAD drift'`
Expected: FAIL — `rebind` unknown command.

- [ ] **Step 3: Implement `cmd_rebind`** (use the existing `_git` and `read_state`/`write_state` helpers)

```python
def cmd_rebind(root):
    s = read_state(root)
    if s is None:
        print("no active consensus session (run init)", file=sys.stderr)
        return 2
    head = _git(root, "rev-parse", "HEAD")
    if not head:
        print("cannot read HEAD", file=sys.stderr)
        return 2
    s["head"] = head
    write_state(root, s)
    print(f"rebound head → {head[:8]}")
    return 0
```

Wire in `main()`:

```python
    if cmd == "rebind":
        return cmd_rebind(root)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `bash tests/run-all.sh 2>&1 | grep 'rebind\|HEAD drift'`
Expected: all three assertions PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/co-agent/skills/co-agent/scripts/consensus_state.py tests/structure/test-co-agent-harness.sh
git commit -m "feat(co-agent): rebind to resume after a manual commit"
```

---

### Task 6: `worktree.py` — the trust-boundary core

**Files:**
- Create: `plugins/co-agent/skills/co-agent/scripts/worktree.py`
- Test: `tests/structure/test-co-agent-harness.sh`

**Interfaces:**
- Produces:
  - `worktree.py add <wt_path> --base <ref> [--root DIR]` → `git worktree add <wt_path> <ref>`; exit 0.
  - `worktree.py capture-diff <wt_path>` → stages all **non-ignored** changes inside the worktree (`git -C <wt> add -A`, which respects `.gitignore`) and prints `git -C <wt> diff --cached`. New normal files are included; `.gitignore`d files are excluded **by construction**. It additionally unstages any **tracked-but-now-ignored** path (`ls-files -i -c` → `reset HEAD`), the one case `add -A` would otherwise still carry, so a hidden ignored file can never reach the main tree.
  - `worktree.py remove <wt_path> [--root DIR]` → `git worktree remove --force <wt_path>` then `git worktree prune`; exit 0.
  - `worktree.py prune [--root DIR]` → `git worktree prune`; exit 0.

> NOTE — this refines spec §5: the precise mechanism is "stage with `add -A` (gitignore-respecting) and take the cached diff", NOT "delete untracked+ignored" (which would also delete legitimate new source files). New non-ignored files MUST survive; only ignored files are excluded. Update the spec bullet to match when convenient.

- [ ] **Step 1: Write the failing test** (append)

```bash
# --- Task 6: worktree helper excludes gitignored, keeps new source ---
R6=$(mktemp -d "${TMPDIR:-/tmp}/coagent-harness6.XXXXXX")
( cd "$R6" && git init -q && git config user.email t@example.invalid && git config user.name t \
    && printf 'secret.env\n' > .gitignore && git add .gitignore && git commit -q -m init )
assert_file_exists "$WT" "worktree.py exists"
WTD="$R6/.wt-task0"
python3 "$WT" add "$WTD" --base HEAD --root "$R6" >/dev/null 2>&1 && A=0 || A=$?
assert_eq "0" "$A" "worktree add succeeds"
# implementer writes a new source file (good) and a gitignored file (must be excluded)
printf 'def f():\n    return 1\n' > "$WTD/feature.py"
printf 'TOKEN=abc\n' > "$WTD/secret.env"
DIFF=$(python3 "$WT" capture-diff "$WTD" 2>/dev/null)
assert_contains "$DIFF" "feature.py" "capture-diff includes the new non-ignored file"
assert_grep_no_match "secret.env" "$DIFF" "capture-diff excludes the gitignored file"
python3 "$WT" remove "$WTD" --root "$R6" >/dev/null 2>&1 && RM=0 || RM=$?
assert_eq "0" "$RM" "worktree remove succeeds"
assert_grep_no_match "." "$(git -C "$R6" worktree list --porcelain | grep -F "$WTD")" "no stale worktree ref after remove"
# tracked-BEFORE-ignored edge case: a file committed earlier, later gitignored, must NOT leak
( cd "$R6" && printf 'orig\n' > pre.tracked && git add pre.tracked && git commit -q -m "track pre.tracked" )
WTD2="$R6/.wt-task1"
python3 "$WT" add "$WTD2" --base HEAD --root "$R6" >/dev/null 2>&1
printf 'pre.tracked\n' >> "$WTD2/.gitignore"   # now ignore the already-tracked file
printf 'LEAK=1\n' >> "$WTD2/pre.tracked"        # and modify it inside the worktree
DIFF2=$(python3 "$WT" capture-diff "$WTD2" 2>/dev/null)
assert_grep_no_match "LEAK=1" "$DIFF2" "capture-diff drops a tracked-then-ignored file's changes"
python3 "$WT" remove "$WTD2" --root "$R6" >/dev/null 2>&1
rm -rf "$R6"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `bash tests/run-all.sh 2>&1 | grep 'worktree'`
Expected: FAIL — `worktree.py` does not exist.

- [ ] **Step 3: Implement `worktree.py`**

```python
#!/usr/bin/env python3
"""Isolated git-worktree helper for the co-agent:harness delegated-implement path.

A worktree isolates the git working tree but is NOT a security sandbox; combine with
a workspace-write CLI sandbox (see co_agent_config.py impl-flags). capture-diff stages
only non-ignored changes so a .gitignore'd file can never be carried to the main tree.

Usage:
  worktree.py add <wt_path> --base <ref> [--root DIR]
  worktree.py capture-diff <wt_path>
  worktree.py remove <wt_path> [--root DIR]
  worktree.py prune [--root DIR]
"""
import sys
import subprocess


def git(cwd, *args):
    return subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True)


def main():
    argv = sys.argv[1:]
    root = "."
    if "--root" in argv:
        i = argv.index("--root")
        root = argv[i + 1]
        del argv[i:i + 2]
    if not argv:
        print(__doc__)
        return 2
    cmd = argv[0]
    if cmd == "add":
        wt = argv[1]
        base = "HEAD"
        if "--base" in argv:
            base = argv[argv.index("--base") + 1]
        r = git(root, "worktree", "add", wt, base)
        sys.stderr.write(r.stderr)
        return r.returncode
    if cmd == "capture-diff":
        wt = argv[1]
        git(wt, "add", "-A")              # new ignored files are not staged (respects .gitignore)
        # `add -A` still re-stages a file that was tracked BEFORE it was gitignored. Unstage any
        # currently-ignored-but-tracked path so an ignored file's changes can never reach main
        # (`reset HEAD` leaves the worktree untouched; it just drops the change from the diff).
        ignored = git(wt, "ls-files", "-i", "-c", "--exclude-standard").stdout.split("\n")
        for f in (p for p in ignored if p):
            git(wt, "reset", "--quiet", "HEAD", "--", f)
        r = git(wt, "diff", "--cached")
        sys.stdout.write(r.stdout)
        return r.returncode
    if cmd == "remove":
        wt = argv[1]
        r = git(root, "worktree", "remove", "--force", wt)
        git(root, "worktree", "prune")
        sys.stderr.write(r.stderr)
        return r.returncode
    if cmd == "prune":
        git(root, "worktree", "prune")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
```

Make it executable: `chmod +x plugins/co-agent/skills/co-agent/scripts/worktree.py`.

- [ ] **Step 4: Run test to verify it passes**

Run: `bash tests/run-all.sh 2>&1 | grep 'worktree'`
Expected: all seven assertions PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/co-agent/skills/co-agent/scripts/worktree.py tests/structure/test-co-agent-harness.sh
git commit -m "feat(co-agent): worktree helper (isolation + gitignore-safe capture-diff)"
```

---

### Task 7: `references/delegated-implement.md`

**Files:**
- Create: `plugins/co-agent/skills/co-agent/references/delegated-implement.md`
- Test: `tests/structure/test-co-agent-harness.sh`

**Interfaces:**
- Produces: a lean reference the skill/command links to. Must document: workspace-write sandbox per CLI, `capture-diff` (gitignore-safe), host-owns-red-test, host-only-commit, the bounded fix loop, the fallback chain (counterpart → other peer → host), and the per-stage output gate.

- [ ] **Step 1: Write the failing test** (append)

```bash
# --- Task 7: delegated-implement reference ---
REF="plugins/co-agent/skills/co-agent/references/delegated-implement.md"
assert_file_exists "$REF" "delegated-implement.md exists"
assert_contains "$(cat "$REF" 2>/dev/null)" "workspace-write" "reference documents workspace-write sandbox"
assert_contains "$(cat "$REF" 2>/dev/null)" "capture-diff" "reference documents capture-diff"
assert_contains "$(cat "$REF" 2>/dev/null)" "only committer" "reference states host is the only committer"
assert_grep_no_match "AKIA[0-9A-Z]{16}|-----BEGIN" "$(cat "$REF" 2>/dev/null)" "reference has no leaked secrets"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `bash tests/run-all.sh 2>&1 | grep 'delegated-implement\|workspace-write\|capture-diff\|only committer'`
Expected: FAIL — file missing.

- [ ] **Step 3: Write the reference** — create `references/delegated-implement.md` with these sections (lean, ≤ ~150 lines): **Trust boundary** (worktree ≠ sandbox; workspace-write sandbox per CLI — **sandbox CLIs only**: `codex -s workspace-write`, `agy --sandbox`; via `co_agent_config.py impl-flags`, which rejects any non-sandbox implementer), **Per-task loop** (host writes red test → `worktree.py add` → implementer writes in worktree → `worktree.py capture-diff` → `scope_guard.py` → host applies patch to main → `tests/run-all.sh` on main → bounded fix loop ≤ `harness.max_fix_rounds` → `consensus_state.py stage-result` → host commits → `worktree.py remove`), **Host-only-commit** (external AIs never commit; host is the only committer), **Fallback chain** (counterpart → next installed peer → host-implement; never block), **Output gate** (a stage advances only when its `result.json` checks out). Keep prose minimal; link to `consensus-mode.md` for the review gate and `ai-cli-adapters.md` for CLI details.

- [ ] **Step 4: Run test to verify it passes**

Run: `bash tests/run-all.sh 2>&1 | grep 'delegated-implement\|workspace-write\|capture-diff\|only committer\|leaked secrets'`
Expected: all assertions PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/co-agent/skills/co-agent/references/delegated-implement.md tests/structure/test-co-agent-harness.sh
git commit -m "docs(co-agent): delegated-implement reference"
```

---

### Task 8: `/co-agent:harness` command + skill wiring

**Files:**
- Create: `plugins/co-agent/commands/harness.md`
- Modify: `plugins/co-agent/skills/co-agent/SKILL.md` (add a Mode 6 — harness — pointer + trigger)
- Modify: `plugins/co-agent/.claude-plugin/plugin.json` (`commands[]` += `./commands/harness.md`)
- Modify: `plugins/co-agent/.codex-plugin/plugin.json` (mirror the command list if it enumerates commands; otherwise no change)
- Version bump: adding a `commands[]` entry is a release change — bump the single shared `"version"` across every `plugins/*/plugin.json` + `marketplace.json`, add a `CHANGELOG.md` entry, and tag `v{version}` (repo versioning rule). Run the version-consistency check in the root `CLAUDE.md` before the release commit.
- Test: `tests/structure/test-co-agent-harness.sh`

**Interfaces:**
- Produces: a `/co-agent:harness` command that orchestrates H0–H5 by delegating to `references/delegated-implement.md` and the consensus gate.

- [ ] **Step 1: Write the failing test** (append)

```bash
# --- Task 8: command + manifest wiring ---
CMD="plugins/co-agent/commands/harness.md"
assert_file_exists "$CMD" "harness command file exists"
assert_contains "$(cat "$CMD" 2>/dev/null)" "delegated-implement" "command links the delegated-implement reference"
assert_contains "$(cat "$CMD" 2>/dev/null)" "worktree" "command references the worktree isolation"
PJ="plugins/co-agent/.claude-plugin/plugin.json"
assert_eq "True" "$(python3 -c "import json;print('./commands/harness.md' in json.load(open('$PJ'))['commands'])" 2>&1)" "harness command registered in plugin.json"
assert_contains "$(cat plugins/co-agent/skills/co-agent/SKILL.md 2>/dev/null)" "harness" "SKILL.md mentions the harness mode"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `bash tests/run-all.sh 2>&1 | grep 'harness command\|delegated-implement reference\|registered in plugin'`
Expected: FAIL — command file + registration missing.

- [ ] **Step 3: Implement**

Create `plugins/co-agent/commands/harness.md` (frontmatter matching `consensus.md`'s style — inspect it first), body documenting H0–H5: detect host/panel/implementer (`co_agent_config.py implementer/impl-flags --host`), consent + cost matrix, load/generate plan (reuse consensus P1), plan gate (consensus gate), delegated implement per `references/delegated-implement.md` (worktree + workspace-write + host red test + capture-diff + scope_guard + tests-on-main + bounded fix loop + host commit), final gate (consensus P4), report (`consensus_state.py report` + `stage-result`/`stage_wall.tsv`). State the trust boundary up front.

Add `./commands/harness.md` to the `commands` array in `.claude-plugin/plugin.json` (and `.codex-plugin/plugin.json` if it lists commands).

In `SKILL.md`, add a short "Mode 6 — harness" pointer under the modes list and a trigger word `harness` / `co-agent harness`.

- [ ] **Step 4: Run test to verify it passes**

Run: `bash tests/run-all.sh 2>&1 | grep 'harness command\|delegated-implement reference\|registered in plugin\|harness mode'`
Expected: all four assertions PASS. Also confirm the manifest still validates:
`python3 -c "import json;json.load(open('plugins/co-agent/.claude-plugin/plugin.json'))"`

- [ ] **Step 5: Version bump (M6 — explicit, not prose)**

Adding a `commands[]` entry is a release change, so bump the single shared version across
**every** `plugins/*/.claude-plugin/plugin.json` + `marketplace.json` (they must stay
identical), add a `CHANGELOG.md` entry, and tag `v{NEW}`:

```bash
NEW="<next-version>"   # pick per semver; ALL plugin.json + marketplace.json must match
python3 - "$NEW" <<'PY'
import json, glob, sys
new = sys.argv[1]
for p in glob.glob("plugins/*/.claude-plugin/plugin.json"):
    d = json.load(open(p)); d["version"] = new
    json.dump(d, open(p, "w"), indent=2); open(p, "a").write("\n")
mp = ".claude-plugin/marketplace.json"; d = json.load(open(mp))
for pl in d.get("plugins", []): pl["version"] = new
json.dump(d, open(mp, "w"), indent=2); open(mp, "a").write("\n")
PY
# verify alignment (the version-consistency check in the root CLAUDE.md) before committing.
```

- [ ] **Step 6: Commit**

```bash
git add plugins/co-agent/commands/harness.md plugins/co-agent/skills/co-agent/SKILL.md \
        plugins/*/.claude-plugin/plugin.json .claude-plugin/marketplace.json CHANGELOG.md
# .codex-plugin/plugin.json exists only for some plugins and may not enumerate commands —
# add it ONLY if it is present and actually changed, so a missing file can't fail the commit.
[ -n "$(git status --porcelain plugins/co-agent/.codex-plugin/plugin.json 2>/dev/null)" ] && \
    git add plugins/co-agent/.codex-plugin/plugin.json
git commit -m "feat(co-agent): /co-agent:harness command + skill wiring (v$NEW)"
```

---

### Task 9: Full-suite green + docs sync

**Files:**
- Modify (as needed): `plugins/co-agent/CLAUDE.md`, `docs/architecture.md`, `CLAUDE.md` inventory line for co-agent
- Test: whole suite

- [ ] **Step 1: Run the full suite**

Run: `bash tests/run-all.sh`
Expected: `# ALL TESTS PASSED` for every co-agent test (pre-existing unrelated hook-syntax failures, if any, are out of scope — confirm they predate this branch).

- [ ] **Step 2: Update co-agent inventory docs**

Add a one-line `harness` mode/command entry to `plugins/co-agent/CLAUDE.md` (Modes table + Commands), and the co-agent section of the root `CLAUDE.md` plugin inventory. Keep it factual and short.

- [ ] **Step 3: Commit**

```bash
git add plugins/co-agent/CLAUDE.md docs/architecture.md CLAUDE.md
git commit -m "docs(co-agent): document harness mode in inventories"
```

---

## Self-Review

**Spec coverage:**
- §3 roles / implementer mapping → Task 1 (resolution, counterpart default, host≠implementer).
- §5 trust boundary → Task 2 (workspace-write flags) + Task 6 (worktree, gitignore-safe capture-diff, remove+prune) + Task 7 (documented).
- §7 config (`harness.implementer`, `max_fix_rounds`) → Task 1.
- §8 error handling (needs-human, rebind, fallback chain) → Tasks 3, 5 + Task 7 (fallback documented; orchestration prose).
- §11 artifacts + output gates → Task 4 (`stage-result`, `stage_wall.tsv`, result.json schema).
- §4/§6 flow + command/skill → Task 8.
- §9 testing invariants → spread across Tasks 1–8; full suite in Task 9.

**Gaps / deferred (intentional, orchestration-level — enforced by the command prose + scope_guard, not unit tests):** the host-only-commit and live-tree-untouched *behaviors* are guaranteed by design (external AIs only ever run inside a worktree; host runs every `git commit`) and documented in Task 7; they are driven by the skill, not a single script, so they are asserted structurally (Task 8) rather than via a runtime harness. A future end-to-end test could simulate a full task loop.

**Placeholder scan:** no TBD/TODO; every code step shows real code; test code is concrete.

**Type/name consistency:** subcommands used consistently — `implementer`, `impl-flags`, `stage-result {write,check}`, `rebind`, `worktree.py {add,capture-diff,remove,prune}`; config namespace `harness.{implementer,max_fix_rounds}`; status value `needs-human`.

## Notes for the executor — READ BEFORE STARTING

Two preconditions are NOT satisfied yet and are out of this plan's scope:
1. **Clean tree.** The branch has ~22 uncommitted files (the chair-by-host work). Commit or stash them before any task — every task ends in a commit and the suite must be attributable.
2. **Degraded consensus gate.** The live panel currently can't ingest a piped doc reliably (Kiro ignores stdin; Codex self-routes), so the multi-model gates used by H2/H4 degrade to a single advisory AI. This plan builds the harness mechanics; it does not depend on the gate upgrades (#1/#2). If you run the gates during implementation, treat a single-AI result as advisory, not consensus.
