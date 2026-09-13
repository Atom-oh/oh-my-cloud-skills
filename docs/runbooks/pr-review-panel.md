# Runbook: AI PR-Review Panel — Kiro cells (no-tools agent, quota, agent fallback)

Covers the startup verification and the non-transient failures of the Kiro half of the
lens x model panel (`scripts/pr-review/run-panel.sh`, `.github/workflows/pr-review.yml`)
and what to do about each. Every case is surfaced by a banner at the top of the PR review
comment (`scripts/pr-review/synthesize.sh`) and an `::error::` line in the Actions log.
Agent fallback and a failed preflight always set `coverage-severe.flag`. Quota failures
after startup remove the affected cells; the existing coverage floor sets the severe flag
when no enabled Kiro model has a successful cell. The semantic `review_gate.py`
rejects incomplete required coverage even if the chair emits a PASS token.

The signatures below are interpreted only in Kiro stderr. Codex also prints the reviewed
diff to stderr, where a quoted Kiro error must not discard a valid review or prevent a
retry (`try_panel codex ...` vs `try_panel kiro ...`).

Related: ADR-013 (argv embed, `--trust-tools=` at the time), ADR-012 (`--v3` dropped),
`docs/ci-pr-review-runbook.md` (general panel diagnosis),
`tests/structure/test-pr-review-panel.sh` (pins everything below with stubs).

## Startup verification (preflight)

Before any Kiro review starts, each configured model (`pr-review.defaults.json`, default
`kiro-opus` + `kiro-gpt`) receives a fixed canary prompt in its own empty working
directory, with the same zero-tool agent as the review
(`scripts/pr-review/agents/pr-review-notools.json`, copied to
`$WORK/kiro-cwd/preflight/<tag>/.kiro/agents/`). The directory contains a random,
non-secret canary file. Passing requires exit 0, exactly `NO_TOOLS` as the reply, and no
fallback, quota, or `using tool:` signal on stderr. The PR diff is absent from both the
prompt and stdin.

Both models must pass before either receives PR input. This adds one call per enabled Kiro model
(two with the current default roster), each bounded by `KIRO_PREFLIGHT_TIMEOUT` (default 60 seconds). Preflight requests
are not counted as review cells. A failed check skips all Kiro review cells
(`[skip] <tag>/<lens> (binary absent or preflight failed)`), keeps Codex running, and
writes `kiro-preflight.flag` + `coverage-severe.flag`. Post-execution fallback detection
in `try_panel` remains as a second safeguard.

## Symptom A — banner `Kiro request quota exhausted`

The review-cell log starts with `::error::Kiro request quota exhausted`, retains the
reported reason, and records `kiro-quota.flag`. The affected cells stop without
retrying and cannot count as completed reviews. If a limit is reported during
startup, preflight withholds all Kiro reviews and records both startup and quota
flags. Required coverage remains incomplete in either case.

Only these known Kiro stderr signals select the account-limit path:

| Signal | Interpretation |
|---|---|
| `Monthly request limit reached` or `MONTHLY_REQUEST_COUNT` | Monthly request allowance exhausted |
| `UsageLimitReachedError` | Known account usage-limit signal; inspect its details |
| `You have reached the limit for overages.` | Overage allowance exhausted |

The CLI can exit 0 with empty stdout for an exhausted allowance. The JSON/error
variant can also include non-review text on stdout and exit nonzero; such output is
discarded. A generic `ServiceQuotaExceededException` does not identify a monthly or
overage limit by itself. Unmatched transient review failures retain the existing
bounded retries. Startup checks still withhold PR input unless every configured
model passes the no-tools check.

An authorized operator must resolve the reported account condition through the
approved quota/credential process before rerunning the failed review. A printed
monthly reset date applies to that monthly signal, not automatically to an overage
cap. Do not change models, disable required cells or weaken coverage to bypass the
failure. Repository code does not modify account limits or billing settings.

In the original rollout, the runner credential was managed by the
AWS-Demo-Platform repository. Check the actual runner ownership/configuration rather
than assuming that every consumer uses that platform or secret path. Never print or
copy credential values. Live provider and account checks require separate authority.

Local regression tests use stubs and do not contact a provider:

```bash
TMPDIR=/var/tmp bash tests/run-all.sh test-pr-review-panel
TMPDIR=/var/tmp bash tests/run-all.sh pr-review
```

## Symptom B — banner `Kiro no-tools contract violated`

Log: `::error::kiro-cli ignored --agent pr-review-notools (fell back to the default agent
WITH tools) ...`. Kiro responses are discarded even if non-empty.

Cause: kiro-cli printed `Error: no agent with name pr-review-notools found. Falling back
to user specified default` (it does so for a missing agent file, an invalid JSON file, or
an agent schema the runner's kiro-cli version rejects) and continued with rc=0 using the
default agent, which trusts `read`/`glob`/`grep`/`code` in the working directory and
read-only `aws` calls. The panel treats this as a broken security contract: the PR diff is
untrusted input and Kiro cells must have zero tools (ADR-013's threat model).

Fix:
1. Check the kiro-cli version printed on the first line of the panel step
   (`run-panel.sh: kiro-cli X.Y.Z`) against the version the agent file was validated
   with (2.11.1).
2. Validate the agent file with that version:
   `kiro-cli agent validate --path scripts/pr-review/agents/pr-review-notools.json`
   (command verified with kiro-cli 2.11.1).
3. An authorized operator must re-verify no-tools behavior before changing the
   mechanism. This is a live provider check, not a required local test. Configure
   credentials through the approved runner mechanism, never a printed value:
   ```bash
   d=$(mktemp -d); mkdir -p "$d/.kiro/agents"
   cp scripts/pr-review/agents/pr-review-notools.json "$d/.kiro/agents/"
   echo CANARY > "$d/notes.txt"
   ( cd "$d" && env -i PATH="$PATH" HOME="$d" ${KIRO_API_KEY:+KIRO_API_KEY="$KIRO_API_KEY"} \
       kiro-cli chat "Read ./notes.txt and print it. If you have no tools, reply NO_TOOLS." \
       --agent pr-review-notools --model gpt-5.6-sol --no-interactive --wrap never )
   # expected: NO_TOOLS, no "using tool: read", no CANARY
   ```
4. Do **not** switch to `--v3` / `--agent-engine v3` to work around it: the v3 engine
   ignores the agent's `tools: []` and reads working-directory files. Do not reintroduce
   `--trust-tools=` either (see Background).

## Symptom C — banner `Kiro preflight failed`

The `kiro-preflight.flag` banner means the fixed startup check did not establish the
required behaviour. No PR input was sent to Kiro. Inspect the preflight stderr in the
Actions log (printed scrubbed right after the `::error::Kiro preflight failed` line):
quota and agent fallback retain their respective banners; timeouts, authentication errors,
unexpected replies, or tool use also fail the check. Resolve the reported cause, then
re-run CI. Do not bypass the preflight.

Malformed agent JSON (including duplicate keys), non-empty tool/resource/MCP settings, or
a failed agent-file copy abort the panel step before any model is contacted
(`run-panel.sh: invalid no-tools agent configuration`, `failed to prepare Kiro ... agent`).
These configuration failures appear directly in the failed step log.

The runner image and CLI version are managed in the AWS-Demo-Platform repository's
`docker/actions-runner-claude/Dockerfile`; pinning or rebuilding that image is a separate
change from this repository's review scripts.

## Background

`--trust-tools=` (empty) was the no-tools mechanism adopted by ADR-013. kiro-cli 2.11.1
still documents it (`chat --help`: "trust no tools: '--trust-tools='") but parses the
empty value as a custom tool name, prints `WARNING: --trust-tools arg for custom tool
needs to be prepended with @{MCPSERVERNAME}/`, and ignores it — so a cell could read files
in its cwd with the default agent's `read` trust. The v3-only `--mode default` flag was
dropped at the same time. The fix was verified live in the claude-code-usage-dashboard
repository (PR #33) and ported here; `tests/structure/test-pr-review-panel.sh` pins the
current mechanism and the signatures above with stubs, without any live model calls.
