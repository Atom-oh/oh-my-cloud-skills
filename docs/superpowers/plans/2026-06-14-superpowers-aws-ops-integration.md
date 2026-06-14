# superpowers ① — systematic-debugging ↔ aws-ops Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or
> superpowers:executing-plans. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Route `superpowers:systematic-debugging` into the aws-ops domain runbooks when the
failing system is AWS/EKS — via our-side description + CLAUDE.md routing only (no superpowers edits).

**Architecture:** Description-driven skill selection + an aggressive routing table at the top of
root `CLAUDE.md` (D2-risk mitigation from panel review). The "test" is a `tests/structure/`
grep-assertion that the integration markers exist; behavior is metadata, so `run-all.sh` stays green.

**Tech Stack:** Markdown skill/agent descriptions, plugin `CLAUDE.md`, bash structure test.

**Spec:** `docs/superpowers/specs/2026-06-14-superpowers-integration-design.md` (① + D2-risk).

---

### Task 1: Failing structure test (TDD red)

**Files:** Create `tests/structure/test-superpowers-integration.sh`

- [ ] Assert `ops-troubleshoot/SKILL.md` description names `systematic-debugging`.
- [ ] Assert `aws-ops-plugin/CLAUDE.md` has a routing note naming `superpowers:systematic-debugging`
      AND the five domain agents (`eks-agent`, `network-agent`, `iam-agent`, `storage-agent`,
      `database-agent`) AND a Korean trigger (`디버깅` or `systematic-debugging`).
- [ ] Assert root `CLAUDE.md` has a routing-table row mapping `systematic-debugging` → `ops-troubleshoot`.
- [ ] Run `bash tests/run-all.sh` — the new assertions FAIL (red). Confirm failure is the new ones.

### Task 2: ops-troubleshoot SKILL.md — position as the AWS/EKS domain arm

**Files:** Modify `plugins/aws-ops-plugin/skills/ops-troubleshoot/SKILL.md`

- [ ] Description: append "— the AWS/EKS domain arm of `superpowers:systematic-debugging`".
- [ ] Add a short body section: when invoked from systematic-debugging, we supply domain
      reproduce/diagnose commands; the *method* (hypothesis → reproduce → verify) stays with
      `superpowers:systematic-debugging`. Return root cause to the debugging loop.
- [ ] Re-run test — Task 1's first assertion passes.

### Task 3: aws-ops CLAUDE.md — routing note with explicit domain agents + triggers

**Files:** Modify `plugins/aws-ops-plugin/CLAUDE.md` (new subsection under Workflow Patterns)

- [ ] Add "superpowers handoff" note: inside `superpowers:systematic-debugging`, when the failing
      system is AWS/EKS, route reproduce→diagnose to `ops-troubleshoot` OR the matched domain
      agent — name each + its symptom trigger (eks: NotReady/pod crash; network: DNS/LB/IP
      exhaustion; iam: AccessDenied/IRSA; storage: PVC/mount; database: throttling/connection).
- [ ] Bilingual (KO/EN). Re-run test — the CLAUDE.md assertion passes.

### Task 4: root CLAUDE.md — aggressive routing table (D2-risk mitigation)

**Files:** Modify `CLAUDE.md` (new section near the top, before deep plugin detail)

- [ ] Add "## superpowers Integration Routing" with a table; first row:
      `systematic-debugging` + AWS/EKS signal → `aws-ops: ops-troubleshoot / domain agent`.
      Leave the table extensible for ②③④ (note them as "planned").
- [ ] Re-run test — root CLAUDE.md assertion passes (all green).

### Task 5: Verify + commit

- [ ] `bash tests/run-all.sh` — all green (new + existing).
- [ ] Commit (explicit paths): the test + 3 edited files, one task-scoped message.
