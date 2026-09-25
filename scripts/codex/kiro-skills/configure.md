## Codex configuration

Use the installed runner from the consumer repository:

```text
python3 "<plugin-root>/.codex-plugin/run.py" skills/kiro-delegate/scripts/kiro_config.py show
python3 "<plugin-root>/.codex-plugin/run.py" skills/kiro-delegate/scripts/kiro_config.py set review model "<requested model>"
```

Resolve `<plugin-root>` from this skill's installed path, not an environment
variable or a guessed cache version. Forward each validated argument separately
and quote it. Use `--root "<target>"` only to target a different repository.
The shared `.claude/kiro.local.json` remains the configuration source for both
hosts; do not create a competing Codex settings file. Preserve model and effort
unless the user explicitly changes them. Configuration does not grant Codex hook
trust, install Kiro CLI or authenticate it.
