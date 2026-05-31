---
name: co-agent
description: "Collaborate with other AI agents (Kiro CLI, Codex, Gemini) for a second opinion. Three modes — multi-AI review of code/architecture, decision support when you're unsure, and ADR co-authoring. Claude chairs and synthesizes the final answer. 멀티 AI 협업: 리뷰, 의사결정 보조, ADR 협업."
triggers:
  - "co-agent"
  - "second opinion"
  - "다른 ai"
  - "ai 협업"
  - "multi-ai review"
  - "architecture review"
  - "아키텍처 리뷰"
  - "코드 리뷰"
  - "잘 모르겠"
  - "모르겠어"
  - "의사결정"
  - "decide"
  - "help me decide"
  - "adr"
  - "협업해서 결정"
allowed-tools:
  - Bash
  - Read
  - Write
  - Grep
  - Glob
  - AskUserQuestion
---

# co-agent — Multi-AI Collaboration

Consult **other AI agents** (Kiro CLI, Codex, Gemini) and let **Claude chair the
panel** and synthesize the final answer. The external AIs are advisors; Claude
always produces the decision/report. Use whichever AI CLIs are installed — degrade
gracefully, never hard-fail.

> CLI invocation, detection, and per-tool quirks: **`references/ai-cli-adapters.md`**.

## Step 0: Detect the panel (always first)

```bash
PANEL=""
# Detect by binary presence only — kiro-cli is usable headless via EITHER an
# interactive login session OR $KIRO_API_KEY (Pro+). Don't pre-gate on the env
# key; if a CLI isn't actually authenticated it just errors at call time and
# we skip it (graceful fallback), same as codex/gemini.
command -v kiro-cli >/dev/null 2>&1 && PANEL="$PANEL kiro-cli"
command -v codex    >/dev/null 2>&1 && PANEL="$PANEL codex"
command -v gemini   >/dev/null 2>&1 && PANEL="$PANEL gemini"
echo "Panel: ${PANEL:-(none — Claude will answer solo and say so)}"
```

> ⚠️ **The Kiro binary is `kiro-cli`, NOT `kiro`.** Always invoke `kiro-cli chat …`.
> (codex/gemini binaries match their names; only Kiro differs — labels above use the
> exact binary name so you never type a bare `kiro`.)

Tell the user which AIs are on the panel. If none are available, do the task as
Claude alone and state that no external panel was reached.

## Three modes

Route by intent (triggers above):

### Mode 1 — Review  (`review`, "코드/아키텍처 리뷰", "second opinion")
Get multiple AIs to review a change, then synthesize.

1. Capture the diff (detect the repo's default branch — don't assume `main`):
   ```bash
   # Resolve the trunk from origin/HEAD (handles main / master / custom trunk).
   BASE=$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null | sed 's@^origin/@@')
   BASE=${BASE:-$(git rev-parse --verify --quiet main >/dev/null 2>&1 && echo main || echo master)}
   DIFF=$(git diff "origin/$BASE...HEAD" 2>/dev/null); [ -z "$DIFF" ] && DIFF=$(git diff "$BASE...HEAD" 2>/dev/null)
   [ -z "$DIFF" ] && DIFF=$(git diff HEAD~1...HEAD 2>/dev/null)   # last-resort: previous commit
   [ -z "$DIFF" ] && echo "EMPTY DIFF — pass an explicit base or check the branch"
   ```
2. Fan out the SAME review prompt to each panel member (run in parallel, capture to
   files). Prompt: *"Review this diff. Report [SEVERITY] file:line — issue. Cover
   correctness, error handling, security, tests, and AWS Well-Architected concerns."*
   See `ai-cli-adapters.md` for the exact per-CLI commands.
3. **Claude synthesizes** into one report:
   - **Consensus** (issues ≥2 AIs agree on) — highest confidence.
   - **Dissent / unique findings** (only one AI raised) — note which AI.
   - Severity table + AWS Well-Architected (use `references/aws-well-architected.md`).
   - Verdict: **PASS** (Critical 0, High ≤2) / **REVIEW** / **FAIL** — rubric in
     `references/architecture-review-framework.md`.

### Mode 2 — Decision support  (`decide`, "잘 모르겠어", "의사결정", "help me decide")
When the user is unsure, bring the panel in.

1. Pin down the decision + options. If the user only gave a question, Claude first
   enumerates 2-4 concrete options, then asks the panel about those.
2. Fan out: *"Decision: <X>. Options: <A/B/C>. Recommend ONE with 2-3 reasons and the
   key trade-off. Be concise."* to each panel member.
3. **Claude synthesizes** a comparison table:

   | Option | Kiro | Codex | Gemini | Claude |
   |--------|------|-------|--------|--------|
   | A | ✅ reason | — | ✅ reason | ✅ |

   Then give a **single recommendation** and name the trade-off that decided it.
   If the panel splits, say so and explain the split — don't fake consensus.

### Mode 3 — ADR co-authoring  (`adr`, "ADR 협업")
Co-author an Architecture Decision Record with the panel.

1. Establish context + the decision to record.
2. Fan out: *"For this decision, list realistic ALTERNATIVES, their TRADE-OFFS, and
   RISKS/CONSEQUENCES. Be specific."* to each panel member.
3. **Claude drafts the ADR** (Nygard format) merging the panel input:
   `# ADR-NNN: <title>` → Status · Context · Decision · **Considered Alternatives**
   (enriched by the panel, attributing notable points) · **Consequences** (pros/cons,
   risks the panel surfaced) · Date.
4. **project-init integration**: if the repo uses `/add-adr` (project-init), co-agent
   provides this collaboration layer; write the ADR to `docs/decisions/ADR-NNN.md`
   following that convention. (We don't modify `/add-adr` — it can optionally invoke
   co-agent; see `references/ai-cli-adapters.md` → ADR hand-off.)

## Chair principle (non-negotiable)

- External AIs **advise**; **Claude decides and writes the final artifact**.
- Always **attribute** notable points to the AI that made them ("Gemini flagged …").
- **Surface disagreement** instead of hiding it — divergent opinions are the value.
- If a CLI errors or is missing, skip it, note it, continue. Never block on one AI.

## References

- `references/ai-cli-adapters.md` — Kiro/Codex/Gemini CLI commands, detection, fan-out pattern, fallbacks
- `references/architecture-review-framework.md` — review rubric, severity, PASS/REVIEW/FAIL
- `references/aws-well-architected.md` — 6-pillar checklist for the review mode
