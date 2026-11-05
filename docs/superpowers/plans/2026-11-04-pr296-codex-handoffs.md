# PR #296 follow-up: host-safe handoffs and diagnostics

Scope: fix the confirmed review issues from the already-merged PR #296 on a
separate worktree based on main. Preserve the original workspace and locked
worktree. Push a follow-up branch; do not merge or deploy cloud resources.

## Task 1 — Regression evidence
- [x] Add `tests/structure/test-aws-ops-handoffs.py` and its TAP wrapper.
- [x] Exercise the documented jq filters with offline pod fixtures: ready,
  container-unready, readiness-gated, missing Ready condition, Pending,
  Succeeded and Failed. Check Runtime CLI separation, companion availability,
  secret-store guidance, the CNI link and mixed authentication mode.
- [x] Run the suite before fixes and confirm failures match the reviewed defects.

## Task 2 — Maintained procedures
- [x] Restore an explicit Python starter-toolkit Runtime deployment using a local
  virtual environment, separate from the Node Harness CLI and its deploy skill.
- [x] Add one canonical companion-skill preflight under aws-ops references;
  wire shared guidance, direct handoff sections and the Codex workflow to it.
  Discover loaded skills, stop a missing section, retain explicit install/trust
  consent and never infer availability from another host's cache.
- [x] Correct security-audit routing metadata and paired public EN/KO guidance.
- [x] Store webhook secrets in Secrets Manager/SSM, never env or diagnostic output.
- [x] Repair CNI cross-reference; document both sources in API_AND_CONFIG_MAP;
  use the Pod Ready condition for Running-but-NotReady diagnostics.

## Task 3 — Delivery evidence
- [x] Regenerate all host packages and overlays without plugin filters.
- [x] Run TAP, both manifest validators, all-plugin freshness, skill evaluation,
  selected installed Codex runtime discovery and site typecheck/build/locales.
- [x] Request independent code/content/security review; resolve blocking findings.
- [ ] Commit exact task paths and normal-push the follow-up branch. Report the
  branch/PR and actual checks; AWS deployment and companion execution remain untested.

## Review follow-up (2026-11-04)

Independent review additionally identified unsafe toolkit role-creation defaults,
an unsupported default Python interpreter and stale unqualified Runtime examples.
The maintained procedure now requires supported Python and audited existing Runtime
and CodeBuild execution roles, blocks unchanged generated helpers, and links the
mapping reference back to the canonical deployment flow. Python `dev` support is
not confused with Node-specific flags. These additions have observed RED→GREEN
regression evidence. This note records implementation scope, not provider readiness.

Independent maintained-source code and security verdicts: PASS. Content gate:
90/90 (Markdown visual-exempt), zero Critical and zero Warning findings.
The first full TAP run had a presentation-browser timeout; the unchanged base and
final head both passed that suite in isolation. No presentation source was changed
or check disabled. Fresh unfiltered TAP reruns passed; see the final snapshot below.

Local AWS CLI 2.35.11 input skeletons also confirmed the EKS capability advisory:
`deletePropagationPolicy: RETAIN` belongs to capability creation/configuration;
`delete-capability` has no deletion-policy option. The maintained guidance now
requires inspection, retained-resource planning and explicit deletion approval.
This uses parser/skeleton evidence only, with no AWS API call.

## Verification snapshot (2026-11-05)

- Final-snapshot unfiltered TAP: 1,510 passed, zero failed; focused regressions:
  10 passed. No browser case was disabled or skipped for delivery.
- Both manifest validators passed; all-plugin freshness checked 9,487 files;
  skill evaluation returned 25 PASS, zero REVIEW and zero FAIL.
- Codex CLI 0.166.0 discovered 18 installed skills across the two affected plugins,
  with no duplicate names or source-path fallback. Native hook fixtures passed
  with `--project-init --tmp-dir /tmp`; no external inference was performed.
- Site typecheck, bilingual production build and locale/link checks passed:
  116 English/Korean pairs and four catalogs. Existing manifest/site warnings
  remain non-blocking; no dependency changes were made.
- A restricted-sandbox retry could not initialize Playwright. The identical local
  browser diagnostic succeeded outside that sandbox; the final complete TAP run
  used the normal local environment without changing tests or their timeouts.

The delivery checkbox records this pre-commit snapshot; the follow-up PR reports
the subsequent commit, normal push and PR creation. No AWS deployment/resource
mutation or external companion workflow was executed.
