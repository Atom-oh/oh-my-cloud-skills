# Codex Compatibility Remediation Plan

**Status:** Proposed on 2026-10-11; implementation has not started.
**Goal:** Resolve the seven confirmed Major findings, close the remaining host-adaptation gaps, and establish native hook execution evidence on the supported Codex CLI.

## Baseline and scope

Reviewed HEAD: `5020d83ad55c4f8986ae5c7858b184627f256b9d`, including the existing uncommitted changes. Preserve those changes; do not reset, stash, commit, or overwrite unrelated work during implementation. Establish an isolated checkout containing the intended candidate before running workflows that require a clean tree.

The current marketplace has eight plugins, 23 source skills, 28 source agents and 20 source commands. Same-name aliases produce 69 Codex entries. Actual Codex CLI 0.162.1 installation discovered all 69 entries and 24 plugin hook handlers. Project-init separately supplies three consumer-project hook events.

Both manifest validators, all-plugin generation freshness, and all 23 skill evaluations passed. The full TAP suite passed all 1,418 assertions after environment-related subprocess failures were resolved. These counts are baseline evidence, not fixed future assertion totals.

The shipped native patch/project-hook fixture failed on the current checkout and HEAD baseline. Its pinned model did not expose the expected custom patch tool; changing the model alone also encountered a request shape without the expected tools field. Native patch denials and complete project-hook dispatch remain unverified.

The review evidence and complete component inventory were saved in `/tmp/codex-compat-review/`. The findings and completion criteria below remain usable without those temporary files.

## Findings and priority

| ID | Priority | Maintained source | Required outcome |
|---|---|---|---|
| M1 | P0 | Kiro Power converter, output/install preparation | Equal, nested, or symlink-aliased paths cannot delete input or unrelated directories |
| M2 | P0 | Kiro delegation worktree preparation | Every support-file destination is checked before writing; spec symlinks cannot redirect copies |
| M3 | P0 | AWS Ops IAM diagnostic procedure | Credential values cannot enter diagnostic output |
| M4 | P1 | Co-agent consensus P2 citation instructions | Valid plan findings survive; a citation-tool error cannot produce PASS |
| M5 | P1 | AgentCore generated Strands entrypoint | Generated handlers accept the SDK RequestContext and use the selected deployment region |
| M6 | P1 | AgentCore hook migration report | Migration claims match actual generated behavior |
| M7 | P1 | Kiro Power YAML generation | Valid descriptions produce valid, semantically equivalent target metadata |
| H1 | P1 | Native Codex hook fixture | Supported native patch denial and project-trust sequences execute with preserved evidence |
| H2 | P2 | Codex workflow guidance and project-init routing | Supported delegation/inline behavior is explicit; Claude-only migration is identified accurately |
| H3 | P2 | Converter details and readiness documentation | No silent MCP omission, unsupported option success, or misleading dependency/readiness claims |

## Delivery order and ownership

| Batch | Tasks | Dependency and ownership |
|---|---|---|
| A: safety | 1–3 | Independent plugin changes can proceed in parallel |
| B: functional correctness | 4–6 | Task 4 follows Task 1 because both modify the Power converter |
| C: host integration | 7–9 | Task 8 can start alongside A; Tasks 7–9 finish before final acceptance |
| D: integration | 10 | Depends on all earlier tasks |

Use one owner for each of the Power converter, Kiro delegation, AWS Ops, co-agent, AgentCore, native runtime probes, and shared Codex generator/templates. Tasks touching the same maintained file stay with the same owner and run sequentially. Only the integration owner regenerates all plugin overlays. Workers must accommodate existing edits and other owners' changes.

Separate reviewable changes into safety, functional, and host-integration batches. Each batch needs its affected regressions and applicable security review before integration. Do not merge a batch with active Critical/Major findings.

## Security pre-check

The planned AWS changes were checked against the repository's `ops-security-audit` mandates. They replace value-bearing credential diagnostics, correct nonsecret region configuration, and describe hook coverage accurately. No new security-group ingress, IAM grants, public endpoint, secret environment variable, data-store configuration, or CloudTrail deletion is proposed.

Fixtures use synthetic values and local stubs. Do not print real credentials, deploy generated resources, modify user trust/settings, or change the external review roster. If implementation introduces AWS/IaC changes beyond this scope, run the matching mandatory security and Well-Architected reviews before acceptance.

## Implementation tasks

### Task 1: Prevent destructive Power conversion and installation

**Files:**
- Modify: `plugins/kiro-power-converter/skills/kiro-convert/scripts/convert_plugin_to_power.py`
- Modify: `plugins/kiro-power-converter/skills/kiro-convert/references/conversion-rules.md`
- Create: `tests/structure/test-power-converter-regressions.py`
- Create: `tests/structure/test-power-converter-regressions.sh`

- [ ] Reproduce M1 with disposable input and outside sentinels.
- [ ] Validate resolved source, conversion output, and installation paths before any removal or directory replacement. Cover equal paths, either containment direction, symlink aliases, and unsafe filesystem roots.
- [ ] Apply the same validation to full-plugin conversion, standalone modes, and installation. Preserve successful conversion to distinct destinations.
- [ ] Build and validate output in temporary storage before replacing an allowed destination. Failure must preserve the source and existing destination and return nonzero.
- [ ] Document the refusal behavior and recovery expectations without adding interactive confirmations.

**Acceptance:** Every invalid-path fixture leaves all input/destination sentinel bytes unchanged. Normal conversion and installation still produce expected files. Mid-conversion failure preserves the prior valid destination.

### Task 2: Make Kiro support-file preparation deterministic

**Files:**
- Modify: `plugins/kiro/agents/kiro-delegate-agent.md`
- Create: `plugins/kiro/skills/kiro-delegate/scripts/prepare_worktree.py`
- Create: `tests/structure/test-kiro-worktree-preparation.py`
- Create: `tests/structure/test-kiro-worktree-preparation.sh`

- [ ] Reproduce M2 using a committed spec-file symlink in a disposable worktree.
- [ ] Move directory, leaf, and tracked-collision validation before all preparation writes. Validate every actual spec file copied, including additional Markdown files.
- [ ] Implement one bundled preparation helper with safe filesystem operations; refuse symlink traversal, including a changed destination between validation and write. Preserve the existing diff/scope guard.
- [ ] Route the source procedure through the installed helper and keep task/spec text out of executable shell interpolation.
- [ ] Store per-run/per-attempt logs under unique run directories and aggregate only that run's credit records.

**Acceptance:** An outside sentinel cannot change; tracked collisions abort before writing. Normal preparation works with spaces in paths. Concurrent runs retain separate logs and credit totals. No claim is made that the Kiro process itself is sandboxed by the applied-diff guard.

### Task 3: Remove credential-bearing AWS diagnostics

**Files:**
- Modify: `plugins/aws-ops-plugin/agents/iam-agent.md`
- Create: `tests/structure/test-iam-diagnostic-output.py`
- Create: `tests/structure/test-iam-diagnostic-output.sh`

- [ ] Replace the raw AWS environment dump with name/presence-only checks or explicitly safe, nonsecret fields.
- [ ] Perform filtering inside the pod before output reaches the host transcript; do not redact only after capturing raw values.
- [ ] Execute the documented diagnostic against a fake pod/CLI with synthetic access-key and session-token values.
- [ ] Review adjacent diagnostic instructions against the no-credential-output rule.

**Acceptance:** Neither synthetic secret value appears in stdout or stderr; useful variable-presence and identity evidence remains. No live pod or AWS account is required for the regression.

### Task 4: Correct Power metadata and integration conversion

**Files:**
- Modify: `plugins/kiro-power-converter/skills/kiro-convert/scripts/convert_plugin_to_power.py`
- Modify: `plugins/kiro-power-converter/skills/kiro-convert/references/conversion-rules.md`
- Modify: `tests/structure/test-power-converter-regressions.py`
- Test: `tests/structure/test-converter-marketplace.sh`

- [ ] Fix M7 using a shared scalar serializer for agent, steering-skill, preserved-skill, and standalone outputs. JSON-quoted scalars are compatible with the repository's standard-library-only convention.
- [ ] Test quotes, colons, backslashes, Unicode and line breaks, including this repository's architecture skill/agent. Check complete generated metadata and semantic round trips.
- [ ] Support both standalone MCP configuration and inline manifest server declarations. Define deterministic precedence/conflict reporting and preserve credential placeholders safely.
- [ ] Make input SessionStart-hook handling explicit. Generate the promised supported disabled mapping only if it preserves the meaning; otherwise record an unconverted/manual gap and correct the documentation.

**Acceptance:** All four metadata modes handle the fixtures correctly. AWS Content's inline Playwright declaration is retained. Hook reports identify every input handler and never silently omit one.

### Task 5: Preserve consensus findings for plan artifacts

**Files:**
- Modify: `plugins/co-agent/commands/consensus.md`
- Modify: `plugins/co-agent/skills/co-agent/references/consensus-pipeline.md`
- Modify: `plugins/co-agent/skills/co-agent/references/consensus-mode.md`
- Modify: `plugins/co-agent/skills/co-agent/scripts/check_citations.py`
- Modify: `plugins/co-agent/skills/decision-reconcile/SKILL.md`
- Create: `tests/structure/test-consensus-plan-citations.py`
- Create: `tests/structure/test-consensus-plan-citations.sh`

- [ ] Apply the existing hybrid-gate distinction consistently: diff citations use the diff helper; plan findings are verified against the plan's actual text/sections by the chair.
- [ ] Reject non-diff artifacts passed to the diff helper rather than returning a successful all-unsupported classification. Handle legitimate empty and deletion-only diffs explicitly.
- [ ] Ensure helper errors and unresolved citations require review and cannot erase active Critical/Major findings.
- [ ] Test a valid Major plan finding, a fabricated quotation, malformed input, normal diff findings and a deletion-only diff.
- [ ] Correct decision-reconcile's automatic Claude-tier availability claim and stale Kiro tool-trust example. Report actual host/provider diversity.

**Acceptance:** A real blocking plan finding remains active until resolved. A malformed citation check cannot produce PASS. Existing task/cumulative-diff citation behavior remains supported.

### Task 6: Correct AgentCore generated execution and coverage reports

**Files:**
- Modify: `plugins/agentcore-creator/skills/agentcore-create/scripts/convert_plugin_to_agentcore.py`
- Modify: `plugins/agentcore-creator/skills/agentcore-create/SKILL.md`
- Modify: `plugins/agentcore-creator/skills/agentcore-create/references/agent-code-templates.md`
- Modify: `plugins/agentcore-creator/skills/agentcore-create/references/agentcore-mapping-rules.md`
- Create: `tests/structure/test-agentcore-conversion-regressions.py`
- Create: `tests/structure/test-agentcore-conversion-regressions.sh`
- Test: `tests/structure/test-agentcore-tool-names.sh`

- [ ] Carry the selected conversion/deployment region into generated code without calling dict methods on RequestContext. Verify every generated framework path against its documented SDK interface.
- [ ] Invoke generated code with an SDK-shaped context and local model/SDK stubs; the fixture must reach the stubbed model call without an AWS request.
- [ ] Replace M6's unsupported migration claims with per-hook actual status: generated instruction, manual follow-up, or not migrated. Instruction text must not be described as native enforcement.
- [ ] Test a marker hook and verify the report matches the generated prompt/adapters.
- [ ] Reject `--enable-lambda` clearly before output mutation while Lambda generation is unsupported; remove success claims from linked instructions. Lambda implementation is a separate feature.

**Acceptance:** Both framework paths honor the selected region and valid SDK context. No report asserts absent protections. Unsupported Lambda conversion returns a clear nonzero result without changing output.

### Task 7: Close Codex orchestration and project-init routing gaps

**Files:**
- Modify: `scripts/codex/runtime.md`
- Modify: `scripts/codex/aws-ops-plugin.md`
- Modify: `scripts/codex/aws-content-plugin.md`
- Modify: `scripts/codex/project-init.md`
- Modify: `scripts/sync-codex-plugins.py`
- Create: `scripts/codex/project-init-skills/migrate-hooks.md`
- Modify: `plugins/aws-ops-plugin/CLAUDE.md`
- Modify: `tests/structure/test-codex-portability.py`
- Modify: `tests/structure/test-codex-project-template.py`

- [ ] Map TeamCreate/TaskCreate/TaskList/TaskUpdate/TeamDelete concepts to available host orchestration or explicit inline execution. Do not invent native roles or inherit permissions/model/memory from source frontmatter.
- [ ] Replace project-init's broad description substitutions with explicit host applicability. Preserve Claude-only migrate-hooks routing and provide a Codex-specific explanation that does not report false migration success.
- [ ] Preserve upstream-owned project-init sources and the stable source-command-health-check name. Codex adaptation stays in repository-owned templates/generator code.
- [ ] Replace the absent deploy-on-aws dependency claim with actual capability discovery and maintained fallback references.
- [ ] Verify valid entry metadata, source links, installed-root resolution and project-plus-hook trust sequencing.

**Acceptance:** A Codex-only consumer is not told its broken hook configuration was migrated by a Claude-only procedure. Team workflows have a usable available-tools/inline path, and missing required capabilities remain explicit gaps.

### Task 8: Restore native Codex hook proof

**Files:**
- Modify: `scripts/test-codex-native-hooks.py`
- Modify: `scripts/test-codex-runtime.py`
- Modify: `scripts/test-token-saver-native.py`
- Modify: `tests/structure/test-codex-rpc.py`
- Modify: `docs/reference/codex-runtime-verification.md`

- [ ] Capture the actual request/tool schema from the supported CLI and explain the current failure before changing the fixture. A model-name replacement alone is insufficient.
- [ ] Support an explicit fixture model/capability configuration and the observed request shapes; give missing tool/schema errors useful diagnostics.
- [ ] Retain loopback-only responses, disposable homes, exact installed-source checks, and zero external inference/user-config changes.
- [ ] Execute the nine translated denial cases through a native supported patch tool. Each native run must be blocked and both attempted files must remain absent.
- [ ] Prove untrusted hooks do not execute, trusted handlers do execute, and project trust precedes hook trust for all three project-template events.
- [ ] Preserve the passing token-saver once-per-session test. Record CLI version, model/capability configuration, events, trust state and error details in JSON.

**Acceptance:** The shipped command passes on supported local Codex CLI 0.162.1 or a deliberately documented successor, including all denial and project-template assertions. Missing capabilities fail clearly; they never count as a pass. Do not claim a broad version matrix without running it.

### Task 9: Document feature readiness and installation requirements

**Files:**
- Create: `docs/reference/plugin-runtime-readiness.md`
- Modify: `docs/onboarding.md`
- Modify: `plugins/aws-content-plugin/skills/aws-light-fcd/SKILL.md`
- Modify: `plugins/aws-content-plugin/skills/reactive-presentation/SKILL.md`

- [ ] Distinguish package loading, local feature prerequisites, hook trust, external-provider readiness and completed workflow evidence for all eight plugins.
- [ ] Link canonical installation guidance for PPTX, PDF and browser dependencies and verify installed-package module/browser resolution.
- [ ] Document peer CLI/authentication requirements and the Codex-host harness's explicit host-implementation path.
- [ ] Make unavailable dependencies actionable for the requested feature. Do not silently install globally, change model settings, trust hooks, or weaken content review.

**Acceptance:** A user can identify why a specific feature cannot run without interpreting a successful package-load check as full readiness. Dependency checks disclose missing components without exposing credentials.

### Task 10: Regenerate overlays and verify the integrated candidate

**Files:**
- Modify: `plugins/agentcore-creator/.codex-plugin/runtime.md`
- Modify: `plugins/aws-content-plugin/.codex-plugin/runtime.md`
- Modify: `plugins/aws-ops-plugin/.codex-plugin/runtime.md`
- Modify: `plugins/co-agent/.codex-plugin/runtime.md`
- Modify: `plugins/kiro/.codex-plugin/runtime.md`
- Modify: `plugins/kiro-power-converter/.codex-plugin/runtime.md`
- Modify: `plugins/project-init/.codex-plugin/runtime.md`
- Modify: `plugins/token-saver/.codex-plugin/runtime.md`
- Modify: `plugins/aws-content-plugin/.codex-plugin/workflow.md`
- Modify: `plugins/aws-ops-plugin/.codex-plugin/workflow.md`
- Modify: `plugins/project-init/.codex-plugin/workflow.md`
- Modify: `plugins/project-init/.codex-plugin/skills/migrate-hooks/SKILL.md`
- Modify: `docs/superpowers/plans/2026-10-11-codex-compatibility-remediation.md`

- [ ] Regenerate with `python3 scripts/sync-codex-plugins.py` once maintained changes are integrated; inspect the actual generated diff.
- [ ] Keep every plugin in generation/validation. If generation changes further files, declare exact paths and review the scope expansion before editing them; the current scope guard does not expand glob paths.
- [ ] Run affected behavioral regressions, the mandatory full suite, both manifest validators, all-plugin freshness and skill evaluation.
- [ ] Reinstall all eight plugins into disposable Codex configuration; verify complete source coverage, names, installed paths and hook declarations without duplicate entries.
- [ ] Run the corrected native project/patch-hook and token-saver fixtures. Collect evidence from the actual candidate HEAD.
- [ ] Complete applicable code/security reviews and both latest-HEAD AI review and Codex package CI. Content artifacts need their own rubric PASS before publication.
- [ ] Append a dated completion record with actual commit, command outcomes, inventory, unresolved limitations and review verdict. An implementation plan itself is not acceptance evidence.

**Acceptance commands:**

```bash
bash tests/run-all.sh
python3 scripts/test-plugins.py
python3 scripts/test-codex-plugins.py
python3 scripts/sync-codex-plugins.py --check
python3 scripts/eval-skills.py
python3 scripts/test-codex-runtime.py
python3 scripts/test-codex-native-hooks.py --project-init --report /var/tmp/codex-remediation-native.json
python3 scripts/test-token-saver-native.py --host codex --report /var/tmp/codex-remediation-token-saver.json
```

Choose writable, adequately sized disposable storage. Compare suspected environment failures on base and candidate under the same conditions; do not waive required checks.

## Completion criteria

All seven Major reproductions are prevented by the maintained implementation and meaningful regression coverage. Codex-specific routing/orchestration behavior is explicit. Native hook proof passes for the supported CLI. Every plugin's generated projection is fresh, all required checks pass on the actual candidate, and no active Critical/Major finding remains.

External provider authentication, live AWS operation, Kiro IDE activation, and deployment are separate evidence requirements. This plan does not classify untested external readiness as success.

## Implementation status — 2026-10-11

Implementation uses isolated branch `fix/codex-compat-remediation`, based on refreshed
origin/main `1cf95b62a681031f169293ab1b7e263438c93730`. The original user's uncommitted
changes remain in the original checkout and are excluded from this candidate.

Tasks 1–9 are implemented. Independent review found and corrected further publication
and final-preparation races; meaningful regression cases cover those fixes. Full
acceptance and remote latest-HEAD review are pending. No merge/deployment is claimed.

Reviewed scope expansions required for consistent source instructions and existing
regression fixtures:

- `tests/structure/test-kiro-plugin.sh`: replace obsolete shell-copy assertions with
  the bundled preparation helper behavior, retaining root-side spec checks.
- `tests/structure/test-co-agent-consensus.sh`: correct a malformed test hunk header.
- `plugins/co-agent/skills/co-agent/SKILL.md`,
  `plugins/co-agent/skills/co-agent/references/hybrid-gate.md`,
  `plugins/co-agent/skills/co-agent/references/relay-chain-gate.md`, and
  `plugins/co-agent/agents/gate-chair.md`: align citation artifact/error treatment.
- All twelve generated project-init entry descriptions/associated explicit-worker
  metadata and the relevant generated workflow/runtime files: regenerate from
  maintained descriptions/templates; no manual overlay edits.

The Power converter requires POSIX no-follow directory descriptors and an accessible
`/proc/self/fd` or `/dev/fd` for safe staged builds; unavailable platforms refuse
before output mutation. Kiro preparation requires no-follow and locking operations.
These are explicit runtime prerequisites, not claims of a verified OS matrix.

## Local acceptance — 2026-10-11

All eight local acceptance commands passed in the isolated candidate worktree:

- Full TAP: 1,398 passed, 0 failed.
- Both manifest validators, all-plugin generation freshness (161 artifacts), and
  all 23 skill evaluations passed.
- Codex CLI 0.162.1 installed eight plugins and discovered 69 entries/24 hooks.
- Native gpt-5.5 loopback fixture passed nine translated denials (all 18 files
  absent), accepted-patch payload, project trust then exact-hook trust, and all
  three project-template events. Homes/state were disposable; no provider called.
- Token-saver native fixture passed untrusted skip and one SessionStart over two turns.
- Independent code review resolved its publication/preparation race findings.
  Markdown content review passed 90/90 (visual testing exempt), Critical 0/Warning 0.

Running outside the subprocess-restricting sandbox for local fixture sockets/tests
is an execution-environment detail; it is not a skipped check or permission change
in a consumer. Generated outputs were regenerated from maintained source.

The candidate is ready to commit and publish for required latest-HEAD PR review.
Remote CI/review and any future main integration remain separate acceptance steps.
