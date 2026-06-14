# superpowers ②③④ — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development /
> executing-plans. Checkbox (`- [x]`) tasks. Spec:
> `docs/superpowers/specs/2026-06-14-superpowers-integration-design.md`.

**Goal:** Complete the superpowers integration — wire ② finishing-a-development-branch,
③ requesting-code-review, ④ writing-plans into project-init / aws-content / aws-ops via
our-side description + CLAUDE.md routing only (superpowers is read-only). ① already merged (PR #74).

**Architecture:** Same pattern as ① — descriptions name the superpowers phase; the root
`CLAUDE.md` "superpowers Integration Routing" table is the always-in-context dispatcher (flip
②③④ from *planned* → active). One new `docs/reference/review-routing.md` for ③'s mixed-changeset
precedence, force-read from root CLAUDE.md.

**Tech Stack:** Markdown descriptions, plugin/root CLAUDE.md, one reference doc, bash structure test.

---

### Task 1: Extend structure test (TDD red)

**Files:** Modify `tests/structure/test-superpowers-integration.sh`

- [x] ②: assert `project-init/commands/sync-docs.md` + `generate-changelog.md` descriptions name `finishing-a-development-branch`; `project-init/CLAUDE.md` has the finish routing note.
- [x] ③: assert `content-review-agent.md` desc names `requesting-code-review`; `wellarchitected-agent.md` desc names review arm; `ops-security-audit` SKILL desc names `requesting-code-review`; `docs/reference/review-routing.md` exists + documents mixed-changeset precedence; root `CLAUDE.md` force-reads it.
- [x] ④: assert `wellarchitected-agent` + `ops-security-audit` descs name `writing-plans` (shift-left); `project-init/CLAUDE.md` has the plan-time security note.
- [x] root table: assert ②③④ rows are `✅ active` (not `planned`).
- [x] Run `bash tests/run-all.sh` → new assertions FAIL (red).

### Task 2: ② finishing-a-development-branch ↔ project-init

**Files:** `plugins/project-init/commands/sync-docs.md`, `generate-changelog.md`, `plugins/project-init/CLAUDE.md`

- [x] sync-docs.md + generate-changelog.md description: "— the doc-sync step before `superpowers:finishing-a-development-branch`."
- [x] project-init CLAUDE.md: routing note (run /sync-docs + /generate-changelog before finishing; /add-adr if a decision was made). Bilingual.

### Task 3: ③ requesting-code-review ↔ non-code gates

**Files:** `content-review-agent.md`, `wellarchitected-agent.md`, `ops-security-audit/SKILL.md`, NEW `docs/reference/review-routing.md`

- [x] content-review-agent desc: non-code-artifact analog of `superpowers:requesting-code-review`.
- [x] wellarchitected-agent desc: infrastructure review arm at review time.
- [x] ops-security-audit SKILL desc: mandatory security leg for IaC/AWS review (`superpowers:requesting-code-review`).
- [x] NEW `docs/reference/review-routing.md`: artifact type → gate, with **mixed-changeset precedence** (a diff touching code+IaC+docs triggers ALL matching gates).

### Task 4: ④ shift-left security at writing-plans

**Files:** `plugins/project-init/CLAUDE.md`, `wellarchitected-agent.md`, `ops-security-audit/SKILL.md`

- [x] project-init CLAUDE.md: plan-time security note — when a plan proposes AWS/IaC, cross-check mandates (0.0.0.0/0, IAM `*`, secrets-in-env) before implement.
- [x] wellarchitected + ops-security-audit descs: can run during `superpowers:writing-plans` as a shift-left pre-check.

### Task 5: root CLAUDE.md routing table — flip ②③④ active + force-read

**Files:** `CLAUDE.md`

- [x] Flip ②③④ rows `planned` → `✅ active`.
- [x] Add: at `requesting-code-review`, **read `docs/reference/review-routing.md`** for gate precedence.

### Task 6: Verify + commit

- [x] `bash tests/run-all.sh` — 0 non-hook failures.
- [x] Commit (explicit paths), one cohesive message.
