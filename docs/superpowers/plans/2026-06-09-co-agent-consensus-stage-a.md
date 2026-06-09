# co-agent Consensus Pipeline — Stage A Implementation Plan (P0–P2)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the lowest-risk slice of the consensus pipeline — detect the input document set, init a resumable session-state file, load-or-generate a TDD plan, and run a multi-model **plan consensus gate** — with **no edits to the target repo's code** (Stage A ends with a reviewed plan).

**Architecture:** Two new stdlib-only Python helpers — `consensus_state.py` (session state at `.claude/co-agent-consensus/state.local.md`, bound to repo/branch/HEAD/doc-hashes/session_id) and `parse_plan.py` (parse a writing-plans plan markdown into tasks + the allowed file set). The P1 plan-generation and P2 consensus-gate are orchestration prose in the `/co-agent:consensus` command + SKILL that REUSE the shipped fan-out (`ai-cli-adapters.md`), `co_agent_config.py` (`pairs`/`matrix`), and `check_citations.py`.

**Tech Stack:** Python 3 (stdlib only — `subprocess` for best-effort git, `uuid`, `json`, `re`, `hashlib`), Bash TAP tests sourced by `tests/run-all.sh`, Markdown command/skill/reference docs, `plugin.json`.

**Spec:** `docs/superpowers/specs/2026-06-09-co-agent-consensus-pipeline-design.md` (Stage A = P0–P2).

**Out of scope (later stages):** P3 TDD implement loop + hooks (Stage B); P4 final gate + P5 report + resume wiring (Stage C). Do NOT build those here.

---

## File Structure

| File | Responsibility |
|------|----------------|
| `plugins/co-agent/skills/co-agent/scripts/consensus_state.py` (NEW) | Session state: `init` (bind repo/branch/base/HEAD/doc-hashes/allowed-paths/session_id), `get`, `set`, `detect` (classify input docs → adr/spec/plan), `verify` (clean-tree + HEAD-drift). State at `.claude/co-agent-consensus/state.local.md`. |
| `plugins/co-agent/skills/co-agent/scripts/parse_plan.py` (NEW) | Parse a writing-plans plan `.md` → tasks JSON (`### Task N` → title + files + checkbox steps); `--files` (unique declared file set), `--count`. |
| `plugins/co-agent/commands/consensus.md` (MODIFY) | Add pipeline sub-modes (`plan`/`implement`/`review`/full) + `<doc>` arg + `--trust-plan`/`--deep`; document the P0–P2 workflow (Stage A executable part = plan + gate). |
| `plugins/co-agent/skills/co-agent/SKILL.md` (MODIFY) | Extend Mode 5 → "Consensus pipeline": conditional entry (ADR/spec → generate plan; plan doc → load) + always-run P2 gate. |
| `plugins/co-agent/skills/co-agent/references/consensus-pipeline.md` (NEW) | P0–P5 phase reference (Stage A implements P0–P2) + safety + entry decision table. |
| `tests/structure/test-co-agent-consensus-stage-a.sh` (NEW) | consensus_state (init/get/set/detect/verify) + parse_plan (tasks/files/count) + command refs. Auto-sourced by run-all.sh. |

`.gitignore` already excludes `.claude/co-agent-consensus/` (added v1.7.2) — no change needed.

---

## Task 1: `consensus_state.py` — session state + input detection

**Files:**
- Create: `plugins/co-agent/skills/co-agent/scripts/consensus_state.py`
- Test: locked by Task 6 suite; manual checks here

- [ ] **Step 1: Write the script**

```python
#!/usr/bin/env python3
"""co-agent consensus pipeline — session state + input-document detection.

State lives at <root>/.claude/co-agent-consensus/state.local.md as a human-readable
header plus a ```json fenced block. It binds a run to the repo/branch/base/HEAD, the
sha of each input doc, the allowed file set, a session_id, the current phase, and the
current task index — so the autonomous pipeline is resumable and so session-gated hooks
(Stage B) can no-op on unrelated work.

Commands:
  consensus_state.py init <root> --docs a.md,b.md [--base main] [--allowed f1,f2]
  consensus_state.py get <root> [key]
  consensus_state.py set <root> <key> <value>        # key in: phase, task_index
  consensus_state.py detect <root> <path>...         # classify docs → "path<TAB>kind"
  consensus_state.py verify <root>                   # exit 0 if clean tree + HEAD matches
Exit 0 ok / 1 verify-fail / 2 usage.
"""
import sys
import os
import re
import json
import uuid
import hashlib
import subprocess

STATE_REL = os.path.join(".claude", "co-agent-consensus", "state.local.md")
SET_KEYS = ("phase", "task_index")


def _git(root, *args):
    try:
        out = subprocess.run(["git", "-C", root, *args], capture_output=True,
                             text=True, timeout=10)
        return out.stdout.strip() if out.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def _sha12(path):
    try:
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()[:12]
    except OSError:
        return ""


def state_path(root):
    return os.path.join(root, STATE_REL)


def read_state(root):
    p = state_path(root)
    if not os.path.isfile(p):
        return None
    with open(p, encoding="utf-8") as f:
        text = f.read()
    m = re.search(r"```json\s*(\{.*?\})\s*```", text, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError:
        return None


def write_state(root, state):
    p = state_path(root)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    body = json.dumps(state, indent=2, ensure_ascii=False)
    with open(p, "w", encoding="utf-8") as f:
        f.write("<!-- co-agent-consensus session state — managed by consensus_state.py; "
                "DO NOT edit by hand. Ephemeral (gitignored). -->\n\n")
        f.write(f"# Consensus session `{state.get('session_id','')}`\n\n")
        f.write(f"phase: **{state.get('phase')}** · task: {state.get('task_index')} · "
                f"branch: {state.get('branch') or '?'}\n\n")
        f.write("```json\n" + body + "\n```\n")


def classify(path):
    """adr / spec / plan / unknown — by location then content."""
    low = path.replace("\\", "/").lower()
    base = os.path.basename(low)
    if "/docs/decisions/" in low or re.match(r"adr-\d", base):
        return "adr"
    try:
        with open(path, encoding="utf-8") as f:
            head = f.read(8000)
    except (OSError, UnicodeDecodeError):
        head = ""
    # a writing-plans plan: bite-sized checkbox tasks
    if ("/plans/" in low) or ("- [ ]" in head and re.search(r"^#{2,3}\s+Task\s", head, re.M)):
        return "plan"
    if "/specs/" in low or "design" in base or "spec" in base or "## Non-Goals" in head:
        return "spec"
    return "unknown"


def cmd_init(root, docs, base, allowed):
    state = {
        "session_id": uuid.uuid4().hex[:16],
        "phase": "P0",
        "task_index": 0,
        "rounds": {},
        "repo_root": os.path.abspath(root),
        "branch": _git(root, "rev-parse", "--abbrev-ref", "HEAD"),
        "base": base or "main",
        "head": _git(root, "rev-parse", "HEAD"),
        "docs": [{"path": d, "kind": classify(d), "sha": _sha12(d)} for d in docs],
        "allowed_paths": allowed,
    }
    write_state(root, state)
    print(f"session {state['session_id']} · phase P0 · "
          f"{len(docs)} doc(s): " + ", ".join(f"{d['kind']}:{os.path.basename(d['path'])}" for d in state["docs"]))
    return 0


def cmd_get(root, key):
    s = read_state(root)
    if s is None:
        print("no active consensus session (run init)", file=sys.stderr)
        return 2
    if key:
        v = s.get(key)
        print(json.dumps(v) if isinstance(v, (dict, list)) else (v if v is not None else ""))
    else:
        print(json.dumps(s, indent=2, ensure_ascii=False))
    return 0


def cmd_set(root, key, value):
    if key not in SET_KEYS:
        print(f"set key must be one of: {', '.join(SET_KEYS)}", file=sys.stderr)
        return 2
    s = read_state(root)
    if s is None:
        print("no active consensus session (run init)", file=sys.stderr)
        return 2
    s[key] = int(value) if key == "task_index" and value.isdigit() else value
    write_state(root, s)
    print(f"{key} = {s[key]}")
    return 0


def cmd_detect(root, paths):
    for p in paths:
        print(f"{p}\t{classify(p)}")
    return 0


def cmd_verify(root):
    """exit 0 if the working tree is clean AND HEAD still matches the recorded state."""
    s = read_state(root)
    if s is None:
        print("no active consensus session", file=sys.stderr)
        return 1
    dirty = _git(root, "status", "--porcelain")
    if dirty:
        print("❌ working tree not clean — consensus needs a clean tree", file=sys.stderr)
        return 1
    head = _git(root, "rev-parse", "HEAD")
    if s.get("head") and head and head != s["head"]:
        print(f"❌ HEAD drifted ({s['head'][:8]} → {head[:8]}) — unrelated changes mid-run", file=sys.stderr)
        return 1
    print("✅ clean tree, HEAD matches session")
    return 0


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__)
        return 2
    cmd, rest = a[0], a[1:]
    root = rest[0] if rest and not rest[0].startswith("--") else "."

    def opt(flag):
        return rest[rest.index(flag) + 1] if flag in rest and rest.index(flag) + 1 < len(rest) else None

    if cmd == "init":
        docs = [d for d in (opt("--docs") or "").split(",") if d]
        allowed = [p for p in (opt("--allowed") or "").split(",") if p]
        return cmd_init(root, docs, opt("--base"), allowed)
    if cmd == "get":
        key = rest[1] if len(rest) > 1 and not rest[1].startswith("--") else None
        return cmd_get(root, key)
    if cmd == "set":
        return cmd_set(root, rest[1], rest[2]) if len(rest) >= 3 else 2
    if cmd == "detect":
        paths = [p for p in rest[1:] if not p.startswith("--")]
        return cmd_detect(root, paths) if paths else 2
    if cmd == "verify":
        return cmd_verify(root)
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: chmod + syntax check**

Run: `chmod +x plugins/co-agent/skills/co-agent/scripts/consensus_state.py && python3 -c "import ast; ast.parse(open('plugins/co-agent/skills/co-agent/scripts/consensus_state.py').read()); print('ok')"`
Expected: `ok`

- [ ] **Step 3: Manual smoke test**

```bash
cd /home/ec2-user/oh-my-cloud-skills
T=$(mktemp -d)
printf '# ADR-007: x\n' > "$T/ADR-007-x.md"
printf '# Plan\n### Task 1: a\n- [ ] step\n' > "$T/plan.md"
S=plugins/co-agent/skills/co-agent/scripts/consensus_state.py
python3 "$S" detect "$T" "$T/ADR-007-x.md" "$T/plan.md"          # → adr / plan
python3 "$S" init "$T" --docs "$T/ADR-007-x.md,$T/plan.md" --base main
python3 "$S" get "$T" phase                                      # → P0
python3 "$S" set "$T" phase P2                                   # → phase = P2
python3 "$S" get "$T" session_id                                 # → 16-hex
test -f "$T/.claude/co-agent-consensus/state.local.md" && echo "state written"
rm -rf "$T"
```
Expected: detect prints `…ADR-007-x.md\tadr` and `…plan.md\tplan`; init prints a session line; `get phase` → `P0`; `set phase P2` → `phase = P2`; state file exists.

- [ ] **Step 4: Commit**

```bash
git add plugins/co-agent/skills/co-agent/scripts/consensus_state.py
git commit -m "feat(co-agent): consensus_state.py — session state + input-doc detection"
```

---

## Task 2: `parse_plan.py` — parse a writing-plans plan into tasks

**Files:**
- Create: `plugins/co-agent/skills/co-agent/scripts/parse_plan.py`
- Test: locked by Task 6 suite

- [ ] **Step 1: Write the script**

```python
#!/usr/bin/env python3
"""Parse a writing-plans implementation plan (.md) into structured tasks.

A plan has `### Task N: <title>` sections, each with a `**Files:**` block listing
`Create:`/`Modify:`/`Test:` paths and one or more `- [ ]` checkbox steps. This extracts
that structure so the consensus pipeline knows the task list and the ALLOWED FILE SET
(used for scope-lock in Stage B) without re-reading prose.

Usage:
  parse_plan.py <plan.md>            # JSON: [{n,title,files:[...],steps:N}]
  parse_plan.py <plan.md> --files    # unique declared file paths, one per line
  parse_plan.py <plan.md> --count    # number of tasks
Exit 0 ok / 2 usage/read error.
"""
import sys
import re
import json

TASK_RE = re.compile(r"^#{2,3}\s+Task\s+(\d+)\s*:\s*(.+?)\s*$", re.M)
FILE_RE = re.compile(r"^\s*-\s*(?:Create|Modify|Test)\s*:\s*`([^`]+)`", re.M)
STEP_RE = re.compile(r"^\s*-\s*\[\s?\]", re.M)


def parse(text):
    tasks = []
    matches = list(TASK_RE.finditer(text))
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end]
        files = []
        for fm in FILE_RE.finditer(body):
            # a Files entry may carry a line range like path:123-145 — keep just the path
            files.append(fm.group(1).split(":")[0].strip())
        tasks.append({
            "n": int(m.group(1)),
            "title": m.group(2).strip(),
            "files": list(dict.fromkeys(files)),
            "steps": len(STEP_RE.findall(body)),
        })
    return tasks


def main():
    args = [x for x in sys.argv[1:] if not x.startswith("--")]
    if not args:
        print(__doc__)
        return 2
    try:
        with open(args[0], encoding="utf-8") as f:
            text = f.read()
    except (OSError, UnicodeDecodeError) as e:
        print(f"❌ cannot read {args[0]}: {e}", file=sys.stderr)
        return 2
    tasks = parse(text)
    if "--count" in sys.argv[1:]:
        print(len(tasks))
    elif "--files" in sys.argv[1:]:
        seen = []
        for t in tasks:
            for f in t["files"]:
                if f not in seen:
                    seen.append(f)
        print("\n".join(seen))
    else:
        print(json.dumps(tasks, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: chmod + syntax check**

Run: `chmod +x plugins/co-agent/skills/co-agent/scripts/parse_plan.py && python3 -c "import ast; ast.parse(open('plugins/co-agent/skills/co-agent/scripts/parse_plan.py').read()); print('ok')"`
Expected: `ok`

- [ ] **Step 3: Manual smoke test (parse this very plan)**

```bash
cd /home/ec2-user/oh-my-cloud-skills
P=plugins/co-agent/skills/co-agent/scripts/parse_plan.py
python3 "$P" docs/superpowers/plans/2026-06-09-co-agent-consensus-stage-a.md --count   # >= 6
python3 "$P" docs/superpowers/plans/2026-06-09-co-agent-consensus-stage-a.md --files | grep -c consensus_state.py  # >= 1
```
Expected: count ≥ 6 (this plan's tasks); `--files` lists the declared paths incl. `consensus_state.py`.

- [ ] **Step 4: Commit**

```bash
git add plugins/co-agent/skills/co-agent/scripts/parse_plan.py
git commit -m "feat(co-agent): parse_plan.py — writing-plans plan → tasks + file set"
```

---

## Task 3: `references/consensus-pipeline.md` — phase reference

**Files:**
- Create: `plugins/co-agent/skills/co-agent/references/consensus-pipeline.md`

- [ ] **Step 1: Write the reference**

````markdown
# Consensus Pipeline (co-agent)

Autonomous **doc → plan → implementation** with cross-family multi-model consensus gates.
Borrows consensus-build's pipeline; the gates use co-agent's panel (Kiro models + Codex +
Gemini). **Stage A (this version) implements P0–P2 only** — it ends with a reviewed plan and
does NOT edit code. P3 implement loop = Stage B; P4 final gate + P5 report = Stage C.

## Entry — conditional on input documents

| Input | Entry |
|-------|-------|
| ADR only (no plan) | generate plan → P2 gate → (implement, Stage B) |
| Spec only (brainstorming design, no plan) | generate plan → P2 gate → (implement) |
| Plan doc present (writing-plans) | LOAD plan (no regen) → P2 gate → (implement) |

Detect with `scripts/consensus_state.py detect <root> <paths>` → `adr|spec|plan|unknown`.

## Phases (Stage A = P0–P2)

- **P0** — `consensus_state.py init` writes `.claude/co-agent-consensus/state.local.md`
  (session_id, phase, task_index, repo/branch/base/HEAD, per-doc sha, allowed_paths).
  Require a clean tree (`consensus_state.py verify`).
- **P1** — plan doc present → `parse_plan.py <plan>` to load tasks + file set; else generate a
  TDD+Tidy plan from the ADR/spec (Claude), then parse it.
- **P2 (ALWAYS)** — plan consensus gate: fan out the plan to the multi-model panel
  (`co_agent_config.py matrix` to show cost; `pairs` for the (ai,model) set; fan-out per
  `ai-cli-adapters.md`), collect findings, run `check_citations.py`, drop `unsupported`,
  synthesize by agreement + evidence (NOT vote-count). Iterate up to `consensus.max_rounds`
  until no CRITICAL/MAJOR. Check the plan for: implementability, bounded scope, missing tasks,
  and **AWS security-mandate violations**. `--trust-plan` skips this (plan already reviewed).

## Safety (applies fully in Stage B/C; relevant flags here)
- Local only; clean-tree required; session_id-gated; consent + cost matrix before fan-out;
  model output is untrusted (cannot change rounds/scope).
````

- [ ] **Step 2: Commit**

```bash
git add plugins/co-agent/skills/co-agent/references/consensus-pipeline.md
git commit -m "docs(co-agent): consensus-pipeline reference (P0-P2 / Stage A)"
```

---

## Task 4: `commands/consensus.md` — pipeline sub-modes + P0–P2 workflow

**Files:**
- Modify: `plugins/co-agent/commands/consensus.md`

- [ ] **Step 1: Replace the command body**

Read the current `consensus.md` (review-only). Replace its body (keep the frontmatter `description`/`allowed-tools`, but update `argument-hint`) so it documents the pipeline with sub-modes. New content below the frontmatter:

```markdown
# co-agent: consensus

Autonomous **doc → plan → implementation** with cross-family multi-model consensus gates.
**This version implements Stage A (P0–P2): plan + plan-review gate, no code edits.** P3
implement (Stage B) and P4/P5 (Stage C) land later. Full reference: `references/consensus-pipeline.md`.

Argument: `$ARGUMENTS`

## Sub-modes
- `plan <doc>` — P0–P2: detect input, load-or-generate the plan, run the plan consensus gate.
- `implement <plan>` — (Stage B, not yet) take a reviewed plan and implement it.
- `review` — the shipped multi-model diff review (P4 gate, standalone).
- (default) full pipeline — P0 onward (currently runs Stage A; implement arrives in Stage B).
- Flags: `--deep` (use each AI's full model list for gates), `--trust-plan` (skip P2).

## Stage A workflow (`plan <doc>`)
Let `SK="${CLAUDE_PLUGIN_ROOT}/skills/co-agent/scripts"`.

1. **Consent + cost**: confirm sending the doc(s) to third-party AIs; show
   `python3 "$SK/co_agent_config.py" matrix`.
2. **Detect & init**: `python3 "$SK/consensus_state.py" detect . <doc paths>` → if a `plan`
   doc is present, use it; else (`adr`/`spec`) you'll generate one. Then
   `python3 "$SK/consensus_state.py" init . --docs <comma paths> --base <trunk>` and
   `python3 "$SK/consensus_state.py" verify .` (clean tree required).
3. **P1 plan**: plan doc → `python3 "$SK/parse_plan.py" <plan>` (tasks + `--files` scope).
   No plan → GENERATE a TDD+Tidy plan from the ADR/spec (bite-sized `- [ ]` tasks, exact
   file paths, per-task commits) and write it to `docs/superpowers/plans/`, then parse it.
4. **P2 gate (unless `--trust-plan`)**: fan the plan out to the panel (`pairs` → per-(ai,model)
   fan-out per `references/ai-cli-adapters.md`), `check_citations.py` the findings, drop
   `unsupported`, synthesize by agreement+evidence. Iterate ≤ `consensus.max_rounds` until no
   CRITICAL/MAJOR. Verify the plan is implementable, scoped, complete, and violates no AWS
   security mandate. Set phase: `consensus_state.py set . phase P2`.
5. **Report** the reviewed plan + gate verdict. (Implementation = Stage B.)
```

- [ ] **Step 2: Validate manifest + refs**

Run: `python3 -c "import json,os; d=json.load(open('plugins/co-agent/.claude-plugin/plugin.json')); [print('MISSING',c) for c in d['commands'] if not os.path.isfile('plugins/co-agent/'+c.lstrip('./'))] or print('refs ok')"`
Expected: `refs ok` (consensus.md is already registered from v1.7.2; this only edits its body).

- [ ] **Step 3: Commit**

```bash
git add plugins/co-agent/commands/consensus.md
git commit -m "docs(co-agent): /co-agent:consensus pipeline sub-modes + Stage A (P0-P2) workflow"
```

---

## Task 5: `SKILL.md` — extend Mode 5 to the conditional pipeline

**Files:**
- Modify: `plugins/co-agent/skills/co-agent/SKILL.md`

- [ ] **Step 1: Replace the Mode 5 section**

Read SKILL.md. Replace the existing "Mode 5 — Consensus" block with:

```markdown
### Mode 5 — Consensus pipeline  (also **`/co-agent:consensus`**)
Autonomous **doc → plan → implementation** with cross-family multi-model gates. **This
version = Stage A (P0–P2)**: load-or-generate a plan and run the plan consensus gate (no
code edits). Implementation (P3) = Stage B. Full phases: `references/consensus-pipeline.md`.

Entry is conditional on the input docs:
- **plan doc present** (writing-plans) → LOAD it (`scripts/parse_plan.py`), do NOT regenerate.
- **ADR / spec only** (no plan) → GENERATE a TDD plan from the decision/design, then parse it.

Then ALWAYS run the **plan consensus gate**: fan the plan to the panel
(`scripts/co_agent_config.py` `matrix`/`pairs` + `references/ai-cli-adapters.md`), validate
findings with `scripts/check_citations.py` (drop `unsupported`), synthesize by agreement +
evidence (never vote-count), iterate to no CRITICAL/MAJOR — checking implementability,
bounded scope, missing tasks, and AWS security-mandate violations. Session state via
`scripts/consensus_state.py`; clean tree required.
```

- [ ] **Step 2: Add the new scripts to the References list**

Append to SKILL.md's References list:

```markdown
- `scripts/consensus_state.py` — consensus session state + input-doc detection (adr/spec/plan)
- `scripts/parse_plan.py` — parse a writing-plans plan into tasks + the allowed file set
- `references/consensus-pipeline.md` — P0–P5 phases (Stage A implements P0–P2) + entry table
```

- [ ] **Step 3: Commit**

```bash
git add plugins/co-agent/skills/co-agent/SKILL.md
git commit -m "docs(co-agent): SKILL Mode 5 → conditional consensus pipeline (Stage A)"
```

---

## Task 6: Tests — `tests/structure/test-co-agent-consensus-stage-a.sh`

**Files:**
- Create: `tests/structure/test-co-agent-consensus-stage-a.sh`

- [ ] **Step 1: Write the test (sourced — no shebang exec, no `exit`)**

```bash
#!/usr/bin/env bash
# Stage A of the consensus pipeline: consensus_state.py + parse_plan.py.

CO="plugins/co-agent/skills/co-agent"
ST="$CO/scripts/consensus_state.py"
PP="$CO/scripts/parse_plan.py"

assert_file_exists "$ST" "consensus_state.py exists"
assert_file_executable "$ST" "consensus_state.py is executable"
assert_file_exists "$PP" "parse_plan.py exists"
assert_file_exists "$CO/references/consensus-pipeline.md" "consensus-pipeline.md exists"

# --- input detection ---
D=$(mktemp -d "${TMPDIR:-/tmp}/cstate.XXXXXX")
printf '# ADR-007: choice\n' > "$D/ADR-007-choice.md"
printf '# Feature Plan\n### Task 1: thing\n- [ ] do it\n' > "$D/myplan.md"
printf '# Design Spec\n## Non-Goals\nx\n' > "$D/design.md"
DET=$(python3 "$ST" detect "$D" "$D/ADR-007-choice.md" "$D/myplan.md" "$D/design.md" 2>&1)
assert_contains "$DET" "$(printf 'ADR-007-choice.md\tadr')" "detect: ADR → adr"
assert_contains "$DET" "$(printf 'myplan.md\tplan')" "detect: checkbox-task doc → plan"
assert_contains "$DET" "$(printf 'design.md\tspec')" "detect: design/Non-Goals → spec"

# --- state init / get / set ---
python3 "$ST" init "$D" --docs "$D/myplan.md" --base main >/dev/null 2>&1
assert_eq "P0" "$(python3 "$ST" get "$D" phase 2>&1)" "init → phase P0"
SID=$(python3 "$ST" get "$D" session_id 2>&1)
assert_eq "1" "$(printf '%s' "$SID" | grep -cE '^[0-9a-f]{16}$')" "session_id is 16-hex"
python3 "$ST" set "$D" phase P2 >/dev/null 2>&1
assert_eq "P2" "$(python3 "$ST" get "$D" phase 2>&1)" "set phase → P2"
python3 "$ST" set "$D" task_index 3 >/dev/null 2>&1
assert_eq "3" "$(python3 "$ST" get "$D" task_index 2>&1)" "set task_index → 3"
assert_file_exists "$D/.claude/co-agent-consensus/state.local.md" "state file written"
# set rejects unknown key
python3 "$ST" set "$D" bogus x >/dev/null 2>&1 && SK=0 || SK=$?
assert_eq "2" "$SK" "set rejects unknown key"
rm -rf "$D"

# --- parse_plan ---
PD=$(mktemp "${TMPDIR:-/tmp}/plan.XXXXXX.md")
printf '# Plan\n\n### Task 1: alpha\n**Files:**\n- Create: `a/b.py`\n- Test: `t/x.sh`\n- [ ] step one\n- [ ] step two\n\n### Task 2: beta\n**Files:**\n- Modify: `a/b.py:10-20`\n- [ ] step\n' > "$PD"
assert_eq "2" "$(python3 "$PP" "$PD" --count 2>&1)" "parse_plan counts 2 tasks"
FILES=$(python3 "$PP" "$PD" --files 2>&1)
assert_contains "$FILES" "a/b.py" "parse_plan extracts Create/Modify path"
assert_contains "$FILES" "t/x.sh" "parse_plan extracts Test path"
assert_eq "2" "$(printf '%s\n' "$FILES" | grep -c .)" "parse_plan de-dupes a/b.py (2 unique files)"
rm -f "$PD"
```

- [ ] **Step 2: Run the suite**

Run: `bash tests/run-all.sh 2>&1 | tail -3`
Expected: `ALL TESTS PASSED`, 0 failed, total up by the new assertions.

- [ ] **Step 3: Commit**

```bash
git add tests/structure/test-co-agent-consensus-stage-a.sh
git commit -m "test(co-agent): consensus pipeline Stage A — state + plan parsing"
```

---

## Task 7: Final validation gate

- [ ] **Step 1: Full gate**

Run: `bash tests/run-all.sh 2>&1 | tail -2 && python3 scripts/test-plugins.py 2>&1 | tail -3 && python3 scripts/test-codex-plugins.py 2>&1 | tail -2`
Expected: all three report all-passed (co-agent command refs still resolve; new scripts are plain files).

- [ ] **Step 2: Confirm no code-editing crept in**

Run: `git diff --name-only main..HEAD | grep -vE '^(plugins/co-agent/(skills/co-agent/(scripts/(consensus_state|parse_plan)\.py|references/consensus-pipeline\.md|SKILL\.md)|commands/consensus\.md)|tests/structure/test-co-agent-consensus-stage-a\.sh|docs/superpowers/)' || echo "scope clean — only Stage A files touched"`
Expected: `scope clean — only Stage A files touched` (Stage A must not modify any unrelated file).

- [ ] **Step 3: Commit (if anything pending)**

```bash
git status --short
# nothing to commit expected; Stage A complete
```

---

## Self-Review

- **Spec coverage (Stage A = P0–P2):** P0 state init + clean-tree + session_id + doc-hash binding → Task 1 (`init`/`verify`); input detection (adr/spec/plan) → Task 1 (`detect`); P1 load (parse plan) → Task 2; P1 generate (ADR/spec) → orchestration prose in Task 4/5; P2 always-run gate (reuse fan-out/pairs/matrix/check_citations) → Task 4/5 workflow; sub-modes `plan`/`review` + `--trust-plan`/`--deep` → Task 4; reference → Task 3; tests → Task 6; final gate → Task 7. Stage B/C explicitly excluded. ✅
- **Placeholder scan:** full code in Task 1/2/6; concrete doc bodies in Task 3/4/5; exact commands + expected output in every run step. None found.
- **Type/name consistency:** `consensus_state.py` commands (`init`/`get`/`set`/`detect`/`verify`), `SET_KEYS=("phase","task_index")`, state path `.claude/co-agent-consensus/state.local.md`, `classify()` → `adr|spec|plan|unknown`, and `parse_plan.py` (`--count`/`--files`, task `{n,title,files,steps}`) are used consistently across Tasks 1/2/4/5/6. The detect TAB-output (`path\tkind`) matches the test's `printf '...\t...'` assertions.
