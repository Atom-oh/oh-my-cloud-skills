# co-agent Consensus Mode — Implementation Plan (Phase 1 / MVP)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add higher-confidence multi-AI review to co-agent via tiered citation validation (all modes) + a model-diverse panel + a `/co-agent:consensus` iterative review-only mode.

**Architecture:** Three deterministic Python helpers + one new command + skill/reference docs. Each independent fan-out round is unchanged (STDIN, parallel, size-guarded); the new pieces are (1) `check_citations.py` classifies findings against the diff, (2) `co_agent_config.py` gains per-AI model lists + a `deep` profile + a call cap + a pre-run matrix, (3) the `consensus` mode/command orchestrate a review-only loop. **Autonomous fixing (`--apply`) is OUT of this phase** — it is Phase 2 (separate plan).

**Tech Stack:** Python 3 (stdlib only), Bash (TAP tests sourced by `tests/run-all.sh`), Markdown skill/command/reference files, `plugin.json` manifest.

**Spec:** `docs/superpowers/specs/2026-06-08-co-agent-consensus-mode-design.md`

**Cut (do NOT build):** confidence-weighted voting, persistent decisions/learnings files, autonomous-fix-by-default.

---

## File Structure

| File | Responsibility |
|------|----------------|
| `plugins/co-agent/skills/co-agent/scripts/check_citations.py` (NEW) | Classify each AI finding `supported`/`needs-review`/`unsupported` by comparing its `file:line[:snippet]` to the unified diff. Pure stdlib; used by every mode. |
| `plugins/co-agent/skills/co-agent/scripts/co_agent_config.py` (MODIFY) | Add per-AI `models: []`; `profile` (default→single model, deep→full list); `consensus` params (`max_calls`); new sub-commands `pairs` (expanded `(ai,model)` list, capped) and `matrix` (pretty cost table). |
| `plugins/co-agent/skills/co-agent/co-agent.defaults.json` (MODIFY) | Add `profile: "default"`, per-AI `models: []`, `consensus: {max_calls: 12, max_rounds: 2}`. |
| `plugins/co-agent/commands/consensus.md` (NEW) | `/co-agent:consensus` command — review-only iterative review (Phase 1). |
| `plugins/co-agent/.claude-plugin/plugin.json` (MODIFY) | Register `./commands/consensus.md`. |
| `plugins/co-agent/skills/co-agent/SKILL.md` (MODIFY) | Mode 5 "Consensus" (review-only) + a "Citation validation" step promoted into Modes 1–4. |
| `plugins/co-agent/skills/co-agent/references/ai-cli-adapters.md` (MODIFY) | Fan-out expands by `(ai,model)` pairs via `pairs`; print `matrix` before running. |
| `plugins/co-agent/skills/co-agent/references/consensus-mode.md` (NEW) | Consensus workflow, citation tiers, multi-model rules, quorum guard. |
| `tests/structure/test-co-agent-consensus.sh` (NEW) | Citation tiers, model-pair expansion, cap, matrix, defaults. Auto-discovered by `run-all.sh`. |

---

## Task 1: `check_citations.py` — tiered citation validation

**Files:**
- Create: `plugins/co-agent/skills/co-agent/scripts/check_citations.py`
- Test: `tests/structure/test-co-agent-consensus.sh` (created in Task 7; Task 1 is exercised manually here, locked by the suite later)

- [ ] **Step 1: Write the script**

```python
#!/usr/bin/env python3
"""Classify each AI review finding against the actual diff — mechanical
"verify, don't vote-count". For every finding citing file:line (optionally a
snippet), decide:

  supported     — file is in the diff AND line is in/adjacent (±3) to a changed
                  hunk AND (no snippet OR snippet matches a nearby added line)
  needs-review  — file is in the diff but the line/snippet doesn't line up
  unsupported   — file is not in the diff at all (likely hallucinated path)

Input findings JSON: a list of objects, each with at least:
  {"ai": "...", "severity": "...", "file": "path", "line": 42,
   "snippet": "optional quoted code", "issue": "..."}
Output: the same list with a "citation" field added, plus a summary line.

Usage:
  python3 check_citations.py <diff_file> <findings_json_file>
  python3 check_citations.py <diff_file> <findings_json_file> --json
Exit 0 always (classifier, not a gate). Exit 2 on usage/parse error.
"""
import sys
import re
import json

ADJACENT = 3  # a cited line within ±3 of a changed line still counts as supported


def parse_diff(text):
    """Return {filepath: {new_lineno: added_line_text}} for added/context lines,
    parsed from a unified diff. Only the NEW-file line numbers are tracked."""
    files = {}
    cur = None
    new_ln = 0
    for line in text.splitlines():
        if line.startswith("+++ "):
            path = line[4:].strip()
            path = re.sub(r"^b/", "", path)
            if path == "/dev/null":
                cur = None
            else:
                cur = files.setdefault(path, {})
            continue
        if line.startswith("@@"):
            m = re.search(r"\+(\d+)", line)
            new_ln = int(m.group(1)) if m else 0
            continue
        if cur is None:
            continue
        if line.startswith("+") and not line.startswith("+++"):
            cur[new_ln] = line[1:]
            new_ln += 1
        elif line.startswith("-") and not line.startswith("---"):
            pass  # removed line: does not advance the new-file counter
        else:
            new_ln += 1  # context line
    return files


def classify(finding, files):
    path = (finding.get("file") or "").strip()
    # match by exact path or basename (AIs sometimes drop the dir prefix)
    hit = None
    if path in files:
        hit = files[path]
    else:
        base = path.rsplit("/", 1)[-1]
        for fp, lines in files.items():
            if fp.rsplit("/", 1)[-1] == base:
                hit = lines
                break
    if hit is None:
        return "unsupported"
    try:
        line = int(finding.get("line"))
    except (TypeError, ValueError):
        return "needs-review"  # file matched but no usable line
    near = [ln for ln in hit if abs(ln - line) <= ADJACENT]
    if not near:
        return "needs-review"
    snippet = (finding.get("snippet") or "").strip()
    if not snippet:
        return "supported"
    if any(snippet in hit[ln] for ln in near):
        return "supported"
    return "needs-review"


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) < 2:
        print(__doc__)
        return 2
    diff_path, findings_path = args[0], args[1]
    as_json = "--json" in sys.argv[1:]
    try:
        with open(diff_path, encoding="utf-8") as f:
            diff = f.read()
        with open(findings_path, encoding="utf-8") as f:
            findings = json.load(f)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as e:
        print(f"❌ cannot read inputs: {e}", file=sys.stderr)
        return 2
    if not isinstance(findings, list):
        print("❌ findings JSON must be a list of objects", file=sys.stderr)
        return 2

    files = parse_diff(diff)
    counts = {"supported": 0, "needs-review": 0, "unsupported": 0}
    for fnd in findings:
        c = classify(fnd, files)
        fnd["citation"] = c
        counts[c] += 1

    if as_json:
        print(json.dumps(findings, ensure_ascii=False, indent=2))
    else:
        for fnd in findings:
            mark = {"supported": "✅", "needs-review": "🟡", "unsupported": "❌"}[fnd["citation"]]
            print(f"{mark} [{fnd.get('severity','?')}] {fnd.get('file','?')}:{fnd.get('line','?')} "
                  f"({fnd.get('ai','?')}) — {fnd.get('issue','')[:80]}")
        print(f"\ncitations: {counts['supported']} supported · "
              f"{counts['needs-review']} needs-review · {counts['unsupported']} unsupported")
        if counts["unsupported"]:
            print("→ Drop unsupported findings (likely hallucinated paths). "
                  "Treat needs-review with caution; verify before reporting.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: chmod + syntax check**

Run: `chmod +x plugins/co-agent/skills/co-agent/scripts/check_citations.py && python3 -c "import ast; ast.parse(open('plugins/co-agent/skills/co-agent/scripts/check_citations.py').read()); print('ok')"`
Expected: `ok`

- [ ] **Step 3: Manual smoke test (supported / needs-review / unsupported)**

```bash
cd /home/ec2-user/oh-my-cloud-skills
printf 'diff --git a/foo.py b/foo.py\n--- a/foo.py\n+++ b/foo.py\n@@ -1,2 +1,3 @@\n ctx\n+open(path)\n+x = 1\n' > /tmp/d.diff
printf '[{"ai":"kiro","severity":"HIGH","file":"foo.py","line":2,"snippet":"open(path)","issue":"leak"},{"ai":"codex","severity":"LOW","file":"foo.py","line":99,"issue":"far"},{"ai":"gemini","severity":"HIGH","file":"ghost.py","line":1,"issue":"hallucinated"}]' > /tmp/f.json
python3 plugins/co-agent/skills/co-agent/scripts/check_citations.py /tmp/d.diff /tmp/f.json
```
Expected: foo.py:2 → ✅ supported; foo.py:99 → 🟡 needs-review; ghost.py:1 → ❌ unsupported; summary `1 supported · 1 needs-review · 1 unsupported`.

- [ ] **Step 4: Commit**

```bash
git add plugins/co-agent/skills/co-agent/scripts/check_citations.py
git commit -m "feat(co-agent): check_citations.py — tiered citation validation"
```

---

## Task 2: `co_agent_config.py` — per-AI model lists, `profile`, `pairs`, `matrix`, cap

**Files:**
- Modify: `plugins/co-agent/skills/co-agent/co-agent.defaults.json`
- Modify: `plugins/co-agent/skills/co-agent/scripts/co_agent_config.py`
- Test: locked by Task 7 suite; manual checks here

- [ ] **Step 1: Add defaults**

Edit `co-agent.defaults.json` — add `profile`, per-AI `models`, and a `consensus` block. Result:

```json
{
  "_comment": "co-agent panel defaults. profile: default = one model per AI (the single `model`); deep = use each AI's `models` list. consensus.max_calls caps rounds × (ai,model) pairs. See /co-agent:configure.",
  "timeout": 240,
  "sync_on_change": false,
  "profile": "default",
  "consensus": { "max_calls": 12, "max_rounds": 2 },
  "panel": {
    "kiro":   { "enabled": true, "model": "auto", "models": ["claude-opus-4.8", "deepseek-3.2", "glm-5"], "context_limit": 1000000 },
    "codex":  { "enabled": true, "model": null, "effort": "medium", "models": [], "context_limit": 272000 },
    "gemini": { "enabled": true, "model": null, "models": [], "context_limit": 1000000 }
  }
}
```

- [ ] **Step 2: Add `set profile` + per-AI `models` parsing**

In `co_agent_config.py` `cmd_set`, add an `elif rest[0] == "profile":` branch (next to `timeout`/`autosync`):

```python
    elif rest[0] == "profile":
        if len(rest) != 2 or rest[1] not in ("default", "deep"):
            print("usage: set profile <default|deep>", file=sys.stderr)
            return 2
        local["profile"] = rest[1]
```

And inside the per-AI `else` block, add a `models` key (after the `model` branch):

```python
        elif key == "models":
            items = [m for m in re.split(r"[,\s]+", val) if m]
            bad = [m for m in items if not MODEL_RE.match(m)]
            if bad:
                print(f"invalid model name(s): {', '.join(bad)} "
                      f"(letters/digits/. _ : / - only)", file=sys.stderr)
                return 2
            slot["models"] = items
```

Update the `unknown key` message to include `models`:

```python
            keys = "enabled, model, models, context_limit" + (", effort" if ai == "codex" else "")
```

- [ ] **Step 3: Add `effective_models(cfg, ai)`, `cmd_pairs`, `cmd_matrix`**

Add these functions (after `effective`):

```python
def effective_models(cfg, ai):
    """Models to run for an AI given the profile. default → [single model];
    deep → the `models` list (fallback to single model if list empty)."""
    p = cfg["panel"].get(ai, {})
    single = p.get("model")
    if cfg.get("profile") == "deep" and p.get("models"):
        return list(dict.fromkeys(p["models"]))  # de-dupe, keep order
    return [single]  # single may be None → CLI default


def panel_pairs(cfg):
    """Enabled (ai, model) pairs, capped at consensus.max_calls / rounds."""
    pairs = []
    for ai in AIS:
        if not cfg["panel"].get(ai, {}).get("enabled", True):
            continue
        for m in effective_models(cfg, ai):
            pairs.append((ai, m))
    return pairs


def cmd_pairs(root):
    cfg = effective(root)
    cap = int(cfg.get("consensus", {}).get("max_calls", 12))
    rounds = int(cfg.get("consensus", {}).get("max_rounds", 2))
    per_round_cap = max(1, cap // max(1, rounds))
    pairs = panel_pairs(cfg)
    if len(pairs) > per_round_cap:
        print(f"⚠️  {len(pairs)} pairs exceeds per-round cap {per_round_cap} "
              f"(max_calls {cap} / {rounds} rounds) — trimming", file=sys.stderr)
        pairs = pairs[:per_round_cap]
    for ai, m in pairs:
        print(f"{ai}\t{m or '(default)'}")
    return 0


def cmd_matrix(root):
    cfg = effective(root)
    rounds = int(cfg.get("consensus", {}).get("max_rounds", 2))
    pairs = panel_pairs(cfg)
    print(f"co-agent panel matrix  (profile {cfg.get('profile','default')} · "
          f"{len(pairs)} pairs × up to {rounds} rounds = {len(pairs)*rounds} max calls)")
    print(f"  {'AI':7} {'model':22} {'ctx(tok)':>11}")
    fam = {}
    for ai, m in pairs:
        ctx = int(cfg['panel'].get(ai, {}).get('context_limit', 0) or 0)
        print(f"  {ai:7} {(m or '(default)'):22} {(f'{ctx:,}' if ctx else '—'):>11}")
        fam.setdefault(ai, 0)
        fam[ai] += 1
    for ai, n in fam.items():
        if n > 1:
            print(f"  ⚠️  {ai}: {n} models (same provider family — diminishing returns vs cost)")
    return 0
```

Route them in `main()` (next to the other `if cmd == ...` lines):

```python
    if cmd == "pairs":
        return cmd_pairs(root)
    if cmd == "matrix":
        return cmd_matrix(root)
```

- [ ] **Step 4: Manual checks**

```bash
cd /home/ec2-user/oh-my-cloud-skills
S=plugins/co-agent/skills/co-agent/scripts/co_agent_config.py
python3 -c "import ast; ast.parse(open('$S').read()); print('ok')"
T=$(mktemp -d)
python3 "$S" pairs --root "$T"            # default profile → kiro \t auto (single per AI)
python3 "$S" set profile deep --root "$T" >/dev/null
python3 "$S" pairs --root "$T"            # deep → kiro×3 models + codex + gemini
python3 "$S" matrix --root "$T"           # table + same-family warning for kiro
rm -rf "$T"
```
Expected: default → 3 lines (one per AI). deep → 5 lines (kiro 3 + codex 1 + gemini 1); matrix shows `5 pairs × up to 2 rounds = 10 max calls` and a `⚠️ kiro: 3 models` warning.

- [ ] **Step 5: Commit**

```bash
git add plugins/co-agent/skills/co-agent/co-agent.defaults.json plugins/co-agent/skills/co-agent/scripts/co_agent_config.py
git commit -m "feat(co-agent): per-AI model lists + deep profile + pairs/matrix + call cap"
```

---

## Task 3: Fan-out doc — expand by `(ai,model)` pairs + print matrix

**Files:**
- Modify: `plugins/co-agent/skills/co-agent/references/ai-cli-adapters.md` (the "Fan-out pattern" code block)

- [ ] **Step 1: Replace the panel-derivation + launch loop**

Replace the current `PANEL=$(...)` line and the `for ai in $PANEL` loop with a pair-driven version. New block:

```bash
CFG="${CLAUDE_PLUGIN_ROOT}/skills/co-agent/scripts/co_agent_config.py"
T=$(python3 "$CFG" timeout 2>/dev/null || echo 240)
python3 "$CFG" matrix          # show provider·model·ctx + max-calls BEFORE running (cost visibility)
TOKENS=$(( ( $(wc -c < "$CTX_FILE") + 3 ) / 4 ))

# One fan-out per ENABLED (ai, model) pair (capped). `pairs` emits "ai<TAB>model".
i=0
python3 "$CFG" pairs 2>/dev/null | while IFS=$'\t' read -r ai model; do
  i=$((i+1)); slot="$RUN/${ai}-${i}"
  MFLAGS=(); [ "$model" != "(default)" ] && MFLAGS=(--model "$model")   # codex/gemini use -m; see note
  if ! python3 "$CFG" fits "$ai" "$TOKENS" 2>/dev/null; then
    echo "[skip] $ai/$model — context ~${TOKENS} tok > model window"; continue
  fi
  case "$ai" in
    kiro)   command -v kiro-cli >/dev/null 2>&1 && ( cat "$CTX_FILE" | timeout "$T" \
              kiro-cli chat "$PROMPT" "${MFLAGS[@]}" --no-interactive --trust-tools=read,grep --wrap never \
              > "$slot.md" 2>"$slot.err" || echo "[skip] kiro/$model" ) & ;;
    codex)  command -v codex >/dev/null 2>&1 && ( cat "$CTX_FILE" | timeout "$T" \
              codex exec -s read-only "${MFLAGS[@]/--model/-m}" "$PROMPT" \
              > "$slot.md" 2>"$slot.err" || echo "[skip] codex/$model" ) & ;;
    gemini) command -v gemini >/dev/null 2>&1 && ( cat "$CTX_FILE" | timeout "$T" \
              gemini "${MFLAGS[@]/--model/-m}" -p "$PROMPT" -o text \
              > "$slot.md" 2>"$slot.err" || echo "[skip] gemini/$model" ) & ;;
  esac
done
wait
# Synthesize from $RUN/*-*.md. Empty/errored/size-skipped = that pair skipped.
# QUORUM GUARD: if ≤1 pair produced usable output, do NOT call it consensus —
# report as single-opinion review and say so.
```

Add a sentence under the block:

```markdown
- **Multi-model**: the panel is now `(ai, model)` pairs from `co_agent_config.py pairs`
  (default = one per AI; `deep` profile = each AI's `models` list, capped by
  `consensus.max_calls`). `matrix` prints the effective set + max calls before running.
```

- [ ] **Step 2: Verify the doc's bash block parses**

Run: `sed -n '/```bash/,/```/p' plugins/co-agent/skills/co-agent/references/ai-cli-adapters.md | sed '1d;$d' > /tmp/fanout.sh; bash -n /tmp/fanout.sh && echo "bash syntax ok"`
Expected: `bash syntax ok` (note: if multiple bash blocks exist, extract the fan-out one specifically; it must pass `bash -n`).

- [ ] **Step 3: Commit**

```bash
git add plugins/co-agent/skills/co-agent/references/ai-cli-adapters.md
git commit -m "docs(co-agent): fan-out expands by (ai,model) pairs + cost matrix"
```

---

## Task 4: `/co-agent:consensus` command (review-only) + register

**Files:**
- Create: `plugins/co-agent/commands/consensus.md`
- Modify: `plugins/co-agent/.claude-plugin/plugin.json`

- [ ] **Step 1: Write the command**

```markdown
---
description: Multi-AI consensus review — model-diverse independent rounds with citation validation (review-only; --apply fix loop is Phase 2)
allowed-tools: Read, Glob, Grep, Bash, AskUserQuestion
argument-hint: "[--deep] [diff base ref]   (review-only in this version)"
---

# co-agent: consensus

Higher-confidence review by fanning a diff to a **model-diverse** panel and
**mechanically validating citations**. Review-only in this version — it does NOT edit
code (the `--apply` fix loop is Phase 2).

Argument: `$ARGUMENTS`

## Steps
1. **Consent + scope** (mandatory first fan-out): confirm with `AskUserQuestion` what to
   send (diff-only / selected files), and that the repo isn't private/secret-bearing.
2. **Show the panel matrix** (cost visibility):
   `python3 ${CLAUDE_PLUGIN_ROOT}/skills/co-agent/skills/co-agent/scripts/co_agent_config.py matrix`
   (Use `--deep` → first run `co_agent_config.py set profile deep` for this run; reset after.)
3. **Capture the diff** (default-branch aware — see SKILL.md Mode 1 step 2).
4. **Fan out one round** over `(ai,model)` pairs (see `references/ai-cli-adapters.md`).
5. **Validate citations**: write each AI's findings to JSON, run
   `check_citations.py <diff> <findings.json>`; **drop `unsupported`**, mark `needs-review`.
6. **Synthesize** (chair): report by **raw agreement** ("3/4 pairs flagged …") + **evidence
   strength** — NEVER vote-count or compute confidence weights. Surface dissent + attribution.
   Verdict PASS/REVIEW/FAIL (`references/architecture-review-framework.md`).
7. **Quorum guard**: if ≤1 pair returned usable output, say "single-opinion review (no
   quorum)" — do not present it as consensus.

> Iterating to fix is Phase 2 (`--apply`). See `references/consensus-mode.md`.
```

- [ ] **Step 2: Register in plugin.json**

Add `./commands/consensus.md` to the `commands` array:

```json
  "commands": [
    "./commands/configure.md",
    "./commands/sync-context.md",
    "./commands/consensus.md"
  ],
```

- [ ] **Step 3: Validate manifest + refs**

Run: `python3 -c "import json,os; d=json.load(open('plugins/co-agent/.claude-plugin/plugin.json')); [print('MISSING',c) for c in d['commands'] if not os.path.isfile('plugins/co-agent/'+c.lstrip('./'))] or print('refs ok')"`
Expected: `refs ok`

- [ ] **Step 4: Commit**

```bash
git add plugins/co-agent/commands/consensus.md plugins/co-agent/.claude-plugin/plugin.json
git commit -m "feat(co-agent): /co-agent:consensus command (review-only)"
```

---

## Task 5: SKILL.md — Mode 5 + promote citation validation to all modes

**Files:**
- Modify: `plugins/co-agent/skills/co-agent/SKILL.md`

- [ ] **Step 1: Add a citation-validation step to Mode 1 (Review), step 4**

Insert before "Claude synthesizes" in Mode 1:

```markdown
   3b. **Validate citations (all modes)**: collect each AI's findings as JSON
      `[{ai,severity,file,line,snippet,issue}]` and run
      `python3 scripts/check_citations.py <diff_file> <findings.json>`. **Drop `unsupported`**
      (hallucinated paths); treat `needs-review` with caution. This makes
      "verify, don't vote-count" mechanical.
```

- [ ] **Step 2: Add Mode 5 after Mode 4**

```markdown
### Mode 5 — Consensus  (also the command **`/co-agent:consensus`**)
Higher-confidence review via a **model-diverse** panel + **citation validation**.
Review-only in this version; the `--apply` fix loop is Phase 2 (`references/consensus-mode.md`).

1. Consent + scope (as Mode 1 step 0). Show `co_agent_config.py matrix` (cost).
2. Build the panel from `(ai,model)` pairs (`deep` profile = each AI's model list, capped).
3. One independent fan-out round → `check_citations.py` → drop `unsupported`.
4. **Claude synthesizes** by raw agreement + evidence strength (NO confidence math).
   Quorum guard: ≤1 usable pair → "single-opinion review", not consensus.
5. Verdict PASS/REVIEW/FAIL.
```

- [ ] **Step 3: Add the two new scripts + reference to the References list**

```markdown
- `scripts/check_citations.py` — tiered citation validation (supported/needs-review/unsupported) for all review modes
- `references/consensus-mode.md` — consensus loop, multi-model rules, quorum guard
```

- [ ] **Step 4: Commit**

```bash
git add plugins/co-agent/skills/co-agent/SKILL.md
git commit -m "docs(co-agent): SKILL Mode 5 consensus + citation validation in all modes"
```

---

## Task 6: `references/consensus-mode.md`

**Files:**
- Create: `plugins/co-agent/skills/co-agent/references/consensus-mode.md`

- [ ] **Step 1: Write the reference**

````markdown
# Consensus Mode (co-agent)

Review-only higher-confidence review. (The `--apply` autonomous fix loop is Phase 2 — see
the design spec; not implemented in this version.)

## Why
- **Model diversity** (different families catch different bugs) > intra-family duplication.
- **Citation validation** turns "verify, don't vote-count" into a mechanical filter.

## Flow (review-only)
1. Consent + scope; print `co_agent_config.py matrix` (provider·model·ctx + max calls).
2. One **independent** round over `(ai,model)` pairs (`pairs` command; `deep` profile for
   the full per-AI model lists; capped by `consensus.max_calls`, default 12).
3. `check_citations.py` classifies findings → drop `unsupported`, flag `needs-review`.
4. Chair synthesis: **raw agreement + evidence strength**, attribute dissent. No confidence
   weighting (contradicts the chair principle).
5. **Quorum guard**: ≤1 usable pair → single-opinion review, not "consensus".

## Multi-model rules
- Default = one model per AI. `deep` profile activates each AI's `models` list.
- Cap: `rounds × pairs ≤ max_calls`; trim same-family duplicates first, then warn.
- Same provider family (e.g. two Claude variants) = diminishing returns; the matrix warns.

## NOT in this version (Phase 2)
- `--apply` fix loop, scope-lock, test gate, security veto, checkpoint patch, clean-tree,
  no-progress/oscillation stop. See `docs/superpowers/specs/2026-06-08-co-agent-consensus-mode-design.md`.
````

- [ ] **Step 2: Commit**

```bash
git add plugins/co-agent/skills/co-agent/references/consensus-mode.md
git commit -m "docs(co-agent): consensus-mode reference"
```

---

## Task 7: Tests — `tests/structure/test-co-agent-consensus.sh`

**Files:**
- Create: `tests/structure/test-co-agent-consensus.sh`

- [ ] **Step 1: Write the test (sourced by run-all.sh — no shebang exec, no `exit`)**

```bash
#!/usr/bin/env bash
# Tests for co-agent consensus mode: citation tiers + multi-model panel.

CO="plugins/co-agent/skills/co-agent"
CIT="$CO/scripts/check_citations.py"
CFG="$CO/scripts/co_agent_config.py"

assert_file_exists "$CIT" "check_citations.py exists"
assert_file_executable "$CIT" "check_citations.py is executable"
assert_file_exists "$CO/references/consensus-mode.md" "consensus-mode.md exists"

# --- citation tiers ---
CD=$(mktemp "${TMPDIR:-/tmp}/cit.XXXXXX.diff"); CJ=$(mktemp "${TMPDIR:-/tmp}/cit.XXXXXX.json")
printf 'diff --git a/foo.py b/foo.py\n--- a/foo.py\n+++ b/foo.py\n@@ -1,2 +1,3 @@\n ctx\n+open(path)\n+x = 1\n' > "$CD"
printf '[{"ai":"kiro","severity":"HIGH","file":"foo.py","line":2,"snippet":"open(path)","issue":"leak"},{"ai":"codex","severity":"LOW","file":"foo.py","line":99,"issue":"far"},{"ai":"gemini","severity":"HIGH","file":"ghost.py","line":1,"issue":"halluc"}]' > "$CJ"
COUT=$(python3 "$CIT" "$CD" "$CJ" 2>&1)
assert_contains "$COUT" "1 supported" "citation: one supported"
assert_contains "$COUT" "1 needs-review" "citation: one needs-review"
assert_contains "$COUT" "1 unsupported" "citation: one unsupported (hallucinated path)"
rm -f "$CD" "$CJ"

# --- multi-model panel ---
R=$(mktemp -d "${TMPDIR:-/tmp}/coc.XXXXXX")
DEF=$(python3 "$CFG" pairs --root "$R" 2>/dev/null | wc -l | tr -d ' ')
assert_eq "3" "$DEF" "default profile → one pair per AI (3)"
python3 "$CFG" set profile deep --root "$R" >/dev/null 2>&1
DEEP=$(python3 "$CFG" pairs --root "$R" 2>/dev/null | wc -l | tr -d ' ')
assert_eq "5" "$DEEP" "deep profile → kiro 3 models + codex + gemini (5)"
assert_contains "$(python3 "$CFG" matrix --root "$R" 2>&1)" "max calls" "matrix prints max-calls budget"
assert_contains "$(python3 "$CFG" matrix --root "$R" 2>&1)" "same provider family" "matrix warns on same-family duplicates"
# invalid model name in list rejected
python3 "$CFG" set kiro models "good-model, bad model" --root "$R" >/dev/null 2>&1 && MB=0 || MB=$?
assert_eq "2" "$MB" "models list rejects names with spaces/metacharacters"
rm -rf "$R"
```

- [ ] **Step 2: Run the suite**

Run: `bash tests/run-all.sh 2>&1 | tail -3`
Expected: `ALL TESTS PASSED`, total count increased by the new assertions, 0 failed.

- [ ] **Step 3: Commit**

```bash
git add tests/structure/test-co-agent-consensus.sh
git commit -m "test(co-agent): consensus citation tiers + multi-model panel"
```

---

## Task 8: gitignore artifact dir + final validation

**Files:**
- Modify: `.gitignore`

- [ ] **Step 1: Add the consensus session-artifact dir to .gitignore**

Append:

```
# co-agent consensus session artifacts (raw model outputs, validated findings — ephemeral)
.claude/co-agent-consensus/
```

- [ ] **Step 2: Full validation gate**

Run: `bash tests/run-all.sh 2>&1 | tail -2 && python3 scripts/test-plugins.py 2>&1 | tail -3`
Expected: both `ALL TESTS PASSED` / `RESULT: ALL TESTS PASSED` (co-agent now has 3 commands; refs resolve).

- [ ] **Step 3: Commit**

```bash
git add .gitignore
git commit -m "chore(co-agent): gitignore consensus session artifacts"
```

---

## Phase 2 (separate plan — NOT in this one)

`--apply` opt-in autonomous fix loop: `consensus.py` (session binding to repo/branch/base/HEAD/diff-hash/allowed-paths), checkpoint patch, scope-lock, test gate (`tests/run-all.sh` + `test-plugins.py`), security-mandate veto, clean-tree requirement, `max_rounds=2`, no-progress/oscillation stop, regression-round framing. Write as `docs/superpowers/plans/<date>-co-agent-consensus-apply.md` after Phase 1 lands.

---

## Self-Review

- **Spec coverage**: citation validation (Task 1, all modes via Task 5) ✅; multi-model panel + default-single + deep + cap + matrix (Task 2/3) ✅; `/co-agent:consensus` review-only (Task 4) + Mode 5 (Task 5) ✅; quorum guard (Task 3/4/6) ✅; gitignored artifacts (Task 8) ✅; CUT items (voting/persistent logs/auto-fix) absent ✅. `--apply` + guardrails → explicitly deferred to Phase 2 (spec §"--apply"; matches panel "later"). 
- **Placeholder scan**: all code steps contain full code; commands have expected output. None found.
- **Type/name consistency**: `effective_models`/`panel_pairs`/`cmd_pairs`/`cmd_matrix` defined in Task 2 and used by name in Task 3/7; `pairs` emits `ai<TAB>model` consumed by the fan-out and the test; `check_citations.py` finding schema (`ai/severity/file/line/snippet/issue` + added `citation`) consistent across Task 1/4/5/7.
