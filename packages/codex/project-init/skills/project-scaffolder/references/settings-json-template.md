# settings.json Template

Template for `.claude/settings.json`: write the Core template, merge in the Optional registrations the user checked (tiers as in [hook-scripts.md](hook-scripts.md)), and validate with `python3 -m json.tool .claude/settings.json`.

Do not add `model` or top-level `effortLevel`, because project settings apply to everyone and to every model.

---

## Core Template

```json
{
  "permissions": {
    "allow": [],
    "deny": [
      "Bash(rm -rf *)",
      "Bash(rm -fr *)",
      "Bash(rm -r *)",
      "Bash(git push --force *)",
      "Bash(git push -f *)",
      "Bash(git reset --hard *)",
      "Bash(git clean -f *)",
      "Bash(chmod 777 *)",
      "Bash(curl*| bash*)",
      "Bash(wget*| bash*)",
      "Bash(eval *)",
      "Bash(python3 -c*import os*)",
      "Read(./.env)",
      "Read(./.env.*)",
      "Read(!.env.example)"
    ]
  },
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "bash \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/secret-scan.sh"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "bash \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/check-doc-sync.sh 2>/dev/null || true"
          }
        ]
      }
    ]
  }
}
```

- **allow**: /init-project adds the detected test and lint commands (for example `"Bash(npm test *)"`), so `/test-all` runs without permission prompts.
- **deny**: `Bash(command *)` form (a trailing ` *` also matches the bare command); deny wins over allow. It guards against common destructive commands and is not a sandbox.
- **Read(./.env)**, **Read(./.env.\*)**: keep secrets out of Claude's context, and also cover Edit, Write, and Bash `cat`/`head`/`tail`/`sed` on those paths. `Read(!.env.example)` keeps `.env.example` readable and editable.

## Hook Registration

| Event (matcher) | Script | Tier | Kind | Registration suffix |
|-----------------|--------|------|------|---------------------|
| `PreToolUse` (`Bash`) | `secret-scan.sh` | Core | Gate: exit 2 blocks the commit | none |
| `PostToolUse` (`Write\|Edit`) | `check-doc-sync.sh` | Core | Observational: notes a missing module CLAUDE.md | `2>/dev/null \|\| true` |
| `SessionStart` | `session-context.sh` | Optional | Observational: local-environment facts | `2>/dev/null \|\| true` |
| `Notification` | `notify.sh` | Optional | Observational: webhook notification | `2>/dev/null \|\| true` |
| `Stop` | `verify-on-stop.sh` | Optional | Gate: exit 2 keeps Claude working while the fast check fails | none |

Every command starts with `bash "$CLAUDE_PROJECT_DIR"/.claude/hooks/`, because a relative path exits 127 once Claude `cd`s into a subdirectory, and a gate that exits 127 does not block. A gate has no suffix, because `|| true` would turn its exit 2 into success; an observational hook's suffix keeps its failure from interrupting the user.

## Optional Hook Registrations

Merge each checked hook's `hooks` entry into the Core template's `hooks` object.

### session-context.sh (Optional)

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "bash \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/session-context.sh 2>/dev/null || true"
          }
        ]
      }
    ]
  }
}
```

### notify.sh (Optional)

```json
{
  "hooks": {
    "Notification": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "bash \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/notify.sh 2>/dev/null || true"
          }
        ]
      }
    ]
  }
}
```

### verify-on-stop.sh (Optional)

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "bash \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/verify-on-stop.sh",
            "timeout": 120
          }
        ]
      }
    ]
  }
}
```

`timeout` is in seconds. Keep it above the fast check's run time, because a hook that reaches it is cancelled and the turn ends unchecked; without it, a hung check holds the turn for the 600-second default.

## Optional: Team Effort Cap

Add `maxEffortLevel` only when the team wants a cost or latency ceiling. It caps effort for every model, including skill and subagent `effort` frontmatter; each developer still picks any level below it. `"max"` means no cap. Requires Claude Code 2.1.267 or later.

```json
{
  "maxEffortLevel": "high"
}
```

## Optional: Subagent Model

Add `CLAUDE_CODE_SUBAGENT_MODEL` only when the team wants subagents on a lower-cost model than the session, for example read-heavy audits on Haiku 5.5 while sessions run Opus 5.5. It applies to every subagent without a `model` field, the generated agents included; a frontmatter `model`, or a model Claude passes for one run, still wins. The built-in Explore and Plan subagents keep their own model unless `CLAUDE_CODE_SUBAGENT_MODEL_FORCE` is also `"1"` (Claude Code 2.1.257 or later), which also overrides frontmatter `model`. On the Anthropic API, `haiku` resolves to Haiku 5.5 (Claude Code 2.1.293 or later). On Amazon Bedrock, Google Cloud, Microsoft Foundry, and Claude Platform on AWS it resolves to Haiku 4.5, which has no effort levels, so there also set `ANTHROPIC_DEFAULT_HAIKU_MODEL` to the provider's Haiku 5.5 model ID; that variable also sets the model for background tasks. A developer can set the variable in their own environment instead.

```json
{
  "env": {
    "CLAUDE_CODE_SUBAGENT_MODEL": "haiku"
  }
}
```
