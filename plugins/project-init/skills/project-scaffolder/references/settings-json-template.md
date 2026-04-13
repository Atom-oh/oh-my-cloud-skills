# settings.json Template

Use this template for `.claude/settings.json`.

---

## Full Template (All Hooks)

```json
{
  "permissions": {
    "allow": [],
    "deny": [
      "Bash(rm -rf:*)",
      "Bash(rm -r:*)",
      "Bash(git push --force:*)",
      "Bash(git reset --hard:*)",
      "Bash(git clean -f:*)",
      "Bash(chmod 777:*)",
      "Bash(curl*| bash*)",
      "Bash(wget*| bash*)",
      "Bash(eval:*)",
      "Bash(python3 -c*import os*)"
    ]
  },
  "hooks": {
    "SessionStart": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/session-context.sh 2>/dev/null || true"
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/secret-scan.sh 2>/dev/null || true"
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
            "command": "bash .claude/hooks/check-doc-sync.sh \"$TOOL_INPUT_PATH\" 2>/dev/null || true"
          }
        ]
      }
    ],
    "Notification": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/notify.sh \"$EVENT\" \"$MESSAGE\" 2>/dev/null || true"
          }
        ]
      }
    ]
  }
}
```

## Hook Explanation

| Event | Hook Script | Purpose |
|-------|-------------|---------|
| `SessionStart` | `session-context.sh` | Load project context (type, branch, recent activity) at session start |
| `PreToolUse` (Bash) | `secret-scan.sh` | Scan staged files for secrets and API keys before shell commands |
| `PostToolUse` (Write/Edit) | `check-doc-sync.sh` | Detect missing CLAUDE.md, ADRs, and runbooks after file changes |
| `Notification` | `notify.sh` | Send webhook notifications on significant events |

## Minimal Template (Documentation Sync Only)

For projects that only need documentation sync:

```json
{
  "permissions": {
    "allow": [],
    "deny": []
  },
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/check-doc-sync.sh \"$TOOL_INPUT_PATH\" 2>/dev/null || true"
          }
        ]
      }
    ]
  }
}
```

## Customization

Add permissions as needed:

```json
{
  "permissions": {
    "allow": [
      "Bash(npm test:*)",
      "Bash(npm run lint:*)",
      "Bash(pytest:*)",
      "Bash(go test:*)"
    ],
    "deny": [
      "Bash(rm -rf:*)",
      "Bash(git push --force:*)",
      "Bash(drop database:*)"
    ]
  }
}
```
