---
description: Panel-readiness preflight — detect each peer's best access path (official plugin → raw CLI + install nudge → none), probe real CLI usability, and record a readiness summary the autonomous flows consult.
allowed-tools: Bash(python3:*), Bash(npm:*), AskUserQuestion
---

# co-agent: setup

Let `SK="${CLAUDE_PLUGIN_ROOT}/skills/co-agent/scripts"`.

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
   `.claude/co-agent-panel.local.json`; the flows consult it (gate-eligible peers only —
   `status==READY` **and** `raw_cli`). **No-peer behavior is mode-specific (decided here, in
   one place):** **review / decide / ADR** degrade to **solo** (say so); **consensus / harness**
   are **non-degraded** — with no gate-eligible peer they **block** and tell the user to run
   `/co-agent:setup` (or install/auth a raw peer), never silently solo.
6. If at least one peer is gate-eligible, offer the pre-push lens gate ONCE via
   `AskUserQuestion`: a 3-lens review (correctness/security/scope) that runs before every
   `git push` and can block it — `git push` only succeeds after the gate passes. State
   what "passes" means in the ask itself: **≥2 lenses flagging → BLOCKED** (push stops);
   **exactly 1 → CHAIR JUDGMENT REQUIRED** (push still stops with exit 2, but the finding
   is uncorroborated — the host reads it against the actual change and may bypass);
   **0 → PASS**. Also state the honest limit: a push the gate genuinely cannot review
   (no peer reachable, no parseable verdict, or the command doesn't match a plain
   same-repo `git push`) fails **open** — the push proceeds — by design, so an offline
   peer can never permanently block pushing. First check whether kiro's `review.on_push`
   is already on for this repo (`python3 "${CLAUDE_PLUGIN_ROOT}/../kiro/skills/
   kiro-delegate/scripts/kiro_config.py" review-on-push --root .` — best-effort, kiro may
   not be installed; ignore a failure silently) — if it is, put that fact in the option
   description ("kiro's own pre-push gate is already on for this repo; turning this on
   too means every push runs both — not recommended") rather than refusing the option.
   Options: `Enable it (Recommended)` →
   `python3 "$SK/co_agent_config.py" set push_gate enabled on`; `Skip for now` → leave it
   off (this plugin's default). Never enable it without this explicit ask — enabling is
   consent to external diff fan-out on every push.

   If **no** peer is gate-eligible, don't just skip this step silently — tell the user
   the gate exists, is off, and needs at least one gate-eligible peer before it can be
   offered; re-running `/co-agent:setup` after fixing auth/install is what surfaces the
   ask.
