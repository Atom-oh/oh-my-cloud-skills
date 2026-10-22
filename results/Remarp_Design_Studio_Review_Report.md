# Content Review Report

## Review Metadata

| Field | Value |
|---|---|
| Review Type | English internal Markdown design proposal |
| Artifact | `docs/superpowers/specs/2026-10-21-remarp-design-studio.md` |
| Iteration | #2 |
| Review Date | 2026-10-21 |
| Inspected Baseline | `2036419c` |
| Artifact SHA-256 | `dbf2abf15368a5582b72616726c79ad840ecd532771f84811daa50bc5239e973` |
| Current Score | **90/90 — Visual Testing exempt** |
| Verdict | **PASS** |

Scope: review the proposal, not certify an implemented editor or authorize deployment. Markdown has no rendered UI under review, so the 10-point Visual Testing category is excluded. No Studio browser tests, screenshots, AI-provider execution, or latency measurements were performed or inferred.

## Quality Gate Result

### Verdict: PASS

The three independent bands are: score **90/90 (PASS >=77)**; Critical **0 (PASS)**; Warning **0 (PASS <=3)**. Their worst verdict is PASS. No separate numerical gate is substituted for the prescribed exempt scale.

| Category | Critical | Warning | Info |
|---|---:|---:|---:|
| Language Consistency | 0 | 0 | 0 |
| All other scored categories | 0 | 0 | 0 |
| **Total** | **0** | **0** | **0** |

### Deterministic Score

Each category starts at full marks. A Critical defect would make its category zero. For non-Critical defects, sum one quarter of the category's maximum per defect, round the summed deduction once to the nearest 0.5 (exact .25/.75 midpoints round up), then floor the category score at 1. No deduction is made without a finding. No defects remain in iteration #2, so every category receives its full score. The single iteration #1 first-use abbreviation warning (W1, previously -2 points in Language Consistency) is resolved by the reviewed edits.

| Scored category | Maximum | Defects / finding | Deduction | Score |
|---|---:|---|---:|---:|
| Layout | 8 | None | 0 | 8 |
| Terminology | 8 | None | 0 | 8 |
| No Hallucination | 12 | None | 0 | 12 |
| Language Consistency | 8 | None; W1 resolved | 0 | 8 |
| No Sensitive Data | 12 | None | 0 | 12 |
| Content-Type Quality | 2 | None | 0 | 2 |
| Icon Usage & Appropriateness | 5 | None; no icon-bearing artifact required | 0 | 5 |
| Readability | 5 | None | 0 | 5 |
| Accessibility | 5 | None; UI requirements specified, not tested implementation | 0 | 5 |
| Structural Completeness | 5 | None | 0 | 5 |
| Data Accuracy & External References | 5 | None | 0 | 5 |
| Legal Compliance | 5 | None; not AWS-branded public collateral | 0 | 5 |
| Message Clarity | 5 | None | 0 | 5 |
| Duplication/Gaps | 5 | None | 0 | 5 |
| **Total** | **90** | | **0** | **90** |

## Critical Issues (Must Fix)

None.

## Warning Issues (Should Fix)

None remaining.

### Resolved from iteration #1

W1 (Language Consistency): the artifact now expands domain-specific language (DSL), input method editor (IME), remote procedure call (RPC), Uniform Resource Identifier (URI), and Full HD (FHD, 1920×1080) at first use. The revision is verified in the actual updated file; the earlier 2-point deduction is removed. These are clarification edits and introduce no new capability or implementation claims.

## Evidence and Verification

1. **Current authority:** Read `docs/CLAUDE.md`, `docs/superpowers/CLAUDE.md`, `tools/CLAUDE.md`, `tools/remarp-vscode/CLAUDE.md`, plugin guidance, `docs/reference/review-routing.md`, and `docs/decisions/ADR-024-remarp-source-contract.md`. ADR-024 currently supports saved-source compiled preview and explicitly leaves visual writeback unsupported. The proposal accurately labels both changes as proposals requiring a follow-up accepted decision (lines 23–28), not implemented features or a policy waiver.
2. **Existing preview/controller behavior:** `src/extension.ts` instantiates a new compiled preview panel after building, saves dirty same-directory project sources in the build path, and has no `VisualEditorController` activation. Its source-change handler updates the existing approximate preview. `media/prompt-bar.js` posts issue annotations, not an AI-provider execution. These match the existing/missing table and AI-handoff limitations.
3. **Compiler provenance:** `Slide` declares `raw_source` and `source_index`; `ParsedBlock` declares nested content/children but no source spans. `SlideType` has exactly the 16 listed enum values. No proposed editor protocol is misrepresented as a current CLI API.
4. **CSS target defect:** `_gen_css_overrides` directly emits `[data-remarp-id="s{index}-{target}"]`; card generation emits `s{index}-card-{i}`. `CssEditor.elementIdToTarget` returns colon-form targets. The corrected `/tmp/remarp-design-probe.json` independently records actual tag-only DOM IDs `s0-card-0`/`s0-card-1`, CSS selector `s0-card:0`, and `css_target_matches_dom: false`. The proposal's stated mismatch is real, not a selector accidentally counted as a DOM attribute.
5. **Parsing and dimensions:** The corrected probe confirms two real slides despite fenced separator/directive-looking content. Theme CSS uses a 1080-high deck with ratio-derived width; compiler Canvas defaults are 960x400. The proposal distinguishes screen, slide and Canvas coordinates and does not mistake legacy 960x540 variables for the design canvas.
6. **Tests:** `npm test --prefix tools/remarp-vscode` passed compilation plus the test file. In this runner its outer TAP summary aggregates one file; direct `node tools/remarp-vscode/test/extension.test.cjs` exposed **19 named cases, pass 19, fail 0**, corroborating the document's investigation claim. These are current-extension tests, not Studio feature tests.
7. **References:** All **10** Markdown relative links resolve to existing maintained files. No external product behavior or statistics require web-source validation because Claude Design is explicitly an experience analogy, not a feature-parity claim (lines 18–21), and performance numbers are labeled unmeasured targets.
8. **Sensitive data:** Pattern scans found no AWS access keys, concrete private IP addresses, emails, credential-style token assignments, or password assignments. Technical field names such as `token` and `auth` do not imply leaked secrets.
9. **Safety:** Host-owned typed intents, explicit capabilities, revision/generation checks, lossless patching, source ownership, symlink/resource bounds, isolated authored-script rendering, consent and candidate Apply/Reject are specified. `WorkspaceEdit` is explicitly not promised as atomic multi-file compare-and-swap. Publish/build's validation gate is preserved. The document creates no AWS/IaC security configuration and does not trigger that artifact gate.

## Source-omission Findings

Original source material is the user's current brief plus the maintained Remarp/extension references inspected for design. The earlier unrelated plugin/agent questions are not requirements for this editor. This is a scoped design proposal, not a full reproduction of the Remarp format guide.

| Source section / requirement | Output status | Note |
|---|---|---|
| Inspect Remarp's actual format | INCLUDED | Sections 2 and 4 cover YAML, project blocks, directives, nested Markdown, Canvas DSL, CSS, notes/fragments and opaque islands. |
| Improve Preview fidelity and updates | INCLUDED | Canonical compiler/runtime rendering, unsaved snapshots, real thumbnails, state retention, stale diagnostics and phased acceptance criteria. |
| Design editing and source writeback | INCLUDED | Typed transaction service, minimal source spans, Undo, revision conflicts, inherited/reset properties and constrained edit coverage. |
| Claude Design-like experience | INCLUDED | Canvas/inspector/layers, scoped AI proposals, candidate preview, variants and Apply/Reject; no unverified product implementation claims. |
| Current Remarp source-first contract and validation | INCLUDED | Explicit ADR-024 status/change requirement; generated HTML remains output; publish gates stay intact. |
| Current dormant visual-edit and issue helpers | INCLUDED | Accurate limitations and maintained-file delivery ownership; no claim that loading helpers alone creates complete visual editing. |
| User's choice of VS Code versus browser | PARTIAL / unresolved | No selected preference was available; the provisional VS Code-first choice is disclosed, and a browser host is reserved behind a shared protocol and separate filesystem/auth design. This is not a silent omission. |
| Full implementation, working UI or visual verification | Not requested / not supplied | The brief asks to inspect and devise an approach. Scope/status and limitations explicitly exclude shipped implementation and screenshots. |

No load-bearing source omission was found.

## Revision Checklist

### Critical (Must Fix)

None.

### Warnings (Should Fix)

- [x] W1: First-use abbreviation expansions verified in iteration #2.

No active revision requirements remain.

### Score Impact Summary

| If Fixed | Critical | Warnings | Projected Score |
|---|---:|---:|---|
| Final reviewed artifact | 0 | 0 | 90/90 |
| Iteration #1 W1 fixed | 0 | 0 | 88/90 → 90/90 |

## Next Steps

The proposal passes its content gate at **90/90**, with **0 Critical and 0 Warning findings**, and may be delivered as a design. This final iteration applies only to the artifact hash recorded above; materially changed content needs a fresh review. Product implementation must still meet the proposal's exit criteria, current policy and required repository checks. This report is not deployment approval for a Studio implementation that does not exist.

## Repository Verification — Primary Agent, 2026-10-21

This section records execution results separately from the document's content score.
Commands ran in `/home/atomoh/oh-my-cloud-skills`, except extension checks in
`tools/remarp-vscode` and baseline comparisons in a disposable `git archive HEAD`
tree at `2036419c`. No implementation files or generated packages were changed.

| Check | Result |
|---|---|
| Extension `npm test` | PASS: TypeScript compilation and extension test file; 19 named cases corroborated by the reviewer's direct test-file execution |
| `bash tests/run-all.sh` | **FAIL**, exit 1: 1,475 passed, 4 failed, 1,479 total |
| `python3 scripts/test-plugins.py` | PASS, exit 0; 4 advisory manifest warnings |
| `python3 scripts/test-codex-plugins.py` | PASS, exit 0; 10 plugins, no errors/warnings |
| `python3 scripts/sync-codex-plugins.py --check` | PASS, exit 0; all-plugin freshness, 9,483 artifacts checked |
| `python3 scripts/eval-skills.py` | PASS, exit 0; 25 PASS, 0 REVIEW, 0 FAIL |
| Source probe / local links | CSS mismatch and fenced parsing reproduced; all 10 local references resolve |

### Failed checks and baseline comparison

- **PR review template:** the wrapper failed because its Python fixture had 9
  assertion failures among 18 tests. `bash tests/run-all.sh pr-review-template`
  reproduced the same failing cases on the archived baseline and current tree
  (both: 0 wrapper assertions passed, 1 failed). Root cause was not diagnosed or
  repaired as part of this design task.
- **Three browser suites:** deck detail, deck navigation and presenter preview
  failed while opening a localhost fixture server, with
  `PermissionError: [Errno 1] Operation not permitted`. These runs did not verify
  browser rendering. `bash tests/run-all.sh reactive` reproduced identical errors
  on baseline and current tree (both: 282 passed, 3 failed, 285 total).

Logs are in `/tmp/remarp-studio-checks/` for this session. Baseline reproduction
does not waive the failing required checks or make the full suite green. The
design can be delivered with these limitations disclosed; no Studio implementation,
browser visual verification, merge or deployment is certified here.
