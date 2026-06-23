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
