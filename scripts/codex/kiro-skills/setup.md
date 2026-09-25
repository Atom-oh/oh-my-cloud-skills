## Codex setup

Resolve `<plugin-root>` from the installed skill path and keep cwd at the target
repository. Diagnose first without modifying user configuration:

```text
python3 "<plugin-root>/.codex-plugin/run.py" skills/kiro-delegate/scripts/kiro_codex.py doctor
```

This reports the installed helper, CLI version, effective configuration and
whether authentication was probed. `READY` with `NOT_PROBED` confirms local
availability only. To verify a real response using the existing review model and
effort, run `doctor --probe`. Report `ABSENT`, `AUTH`, `TIMEOUT`, `NO_INGEST` or
`ERROR` as failures with the returned reason; never silently select another model.
For authentication, let the user complete Kiro's interactive login.
If `ACP new_session failed` occurs inside Codex's sandbox, retry through the
host's normal escalation mechanism before diagnosing an account or model fault.
Keep the selected model, effort and empty tool trust unchanged.

Read-only `kiro:review` works without writing project agent files or enabling
hooks. Preserve existing model, effort, delegation and hook settings unless the
user requests changes. To choose a model when none is configured, use the bundled
`kiro_setup.py list-models` and `kiro_config.py set` helpers; do not guess model IDs.

For implementation delegation, continue with the shared setup procedure's
`write-agents` and `verify-agents` steps. Existing authorization applies; missing
shell authorization means omit `--enable-bash`. Enabling automatic delegation,
commit/push reviews or web search is a separate setting, not an installation
requirement. Ask only for choices or authorization still missing using the
available Codex user-input mechanism.
