# Skill Review — 22 skills, 7 plugins (2026-07-27)

Review of every `SKILL.md` in this marketplace, run via `/skill-creator`. Report only —
no skill or script edits were made.

## 1. Summary — two scorers, two verdicts

| Scorer | Result |
|--------|--------|
| `scripts/eval-skills.py` (this repo) | **19 PASS / 3 REVIEW / 0 FAIL** |
| `skill-creator`'s `quick_validate.py` (official) | **4 valid / 18 invalid** |

They disagree because they measure different things. The repo scorer grades prose quality
(structure, disclosure, concreteness, completeness, efficiency). The official validator
checks frontmatter against the actual skill schema — which the repo scorer never does.

**Nothing is currently broken.** The offending frontmatter keys are *inert*: the runtime
ignores unknown keys rather than rejecting the skill. `pr-autofix` (`triggers:`) and
`slide-fix` (`model:`) both load normally in a live session. Read this report as "silent
no-ops with one real consequence", not as an outage.

The schema allows exactly six properties:

```
allowed-tools, compatibility, description, license, metadata, name
```

Everything else in our skills — `model:`, `triggers:`, `invocation:`, `tools:`,
`user-invocable:` — does nothing.

Corroborating evidence: across ~117 `SKILL.md` files in the local plugin cache
(`~/.claude/plugins/cache/`), **the only files using `model:` or `triggers:` are this
repo's own skills.** No official or third-party skill uses either key.

## 2. Finding A — undertriggering risk from inert `triggers:` (highest impact)

Since `triggers:` is a no-op, **`description` is the sole triggering mechanism.** Any
keyword that lives only in `triggers:` is invisible to skill selection.

11 skills have trigger keywords that appear nowhere in their description:

| Skill | desc len | Keywords stranded in inert `triggers:` |
|-------|---------:|----------------------------------------|
| `ops-health-check` | 56 | `health check`, `상태 점검`, `헬스체크`, `cluster health`, `인프라 점검` |
| `ops-network-diagnosis` | 66 | `network issue`, `네트워크 오류`, `연결 문제`, `connectivity`, `DNS failure` |
| `pr-autofix` | 104 | `pr autofix`, `pr review fix`, `PR 자동 수정` |
| `kiro-convert` | 135 | `convert to kiro`, `kiro convert`, `키로 변환`, `키로 파워`, `claude to kiro` |
| `ops-wellarchitected-review` | 154 | `WAF review`, `well architected review`, `pillar review`, `인프라 진단`, `아키텍처 리뷰`, `심층 진단`, `WAF 점검`, `인프라 점수` |
| `ops-observability` | 177 | `monitoring`, `모니터링`, `로그 분석`, `알람`, `logs insights`, `otel`, `오픈소스 모니터링`, `distributed tracing`, `데브옵스 에이전트`, `incident investigation` |
| `ops-troubleshoot` | 221 | `장애`, `디버깅`, `문제 해결`, `incident` |
| `agentcore-create` | 286 | 13 keywords, incl. every Korean form — `에이전트코어 생성/변환/배포`, `하네스 배포`, `베드락 에이전트`, `런타임 배포` |
| `co-agent` | 326 | `다른 AI`, `다른 AI한테`, `다른 AI로 리뷰`, `AI 패널`, `잘 모르겠어`, `의사결정 도와`, `협업해서 결정` |
| `decision-reconcile` | 518 | `의사결정 모순`, `adr 번복`, `decision reconcile`, `conflicting adr` |
| `ops-security-audit` | 535 | `보안 점검`, `security review`, `보안 감사`, `시큐리티 에이전트`, `pentest`, `code security review`, `취약점 점검` |

Note the correlation: the thinnest descriptions are precisely the ones hiding their
keywords in the inert block. `ops-health-check` ships a 56-character description while
all five of its trigger phrases sit in dead YAML.

**Korean keywords are hit hardest.** `헬스체크`, `아키텍처 리뷰`, `모니터링`, `장애`,
`보안 점검` have no English cognate in their descriptions to fall back on, so a Korean
prompt has nothing to match against. This directly undercuts the convention stated in the
root `CLAUDE.md` ("Korean/English bilingual keywords in all auto-invocation rules") — the
bilingual keywords exist, they just aren't where selection looks.

**Mitigating factor, stated honestly:** for `aws-ops-plugin`,
`plugins/aws-ops-plugin/CLAUDE.md:116-117` carries a keyword→skill routing table with
these same Korean terms, and that file is always in context. Ops routing may therefore
still work via `CLAUDE.md` instruction-following rather than via description matching.
That is a different mechanism with different reliability characteristics, and it does not
cover `kiro-convert`, `agentcore-create`, `pr-autofix`, `decision-reconcile`, or
`co-agent`.

**Recommendation (for a follow-up change):** merge each `triggers:` keyword into the
skill's `description`, then delete the `triggers:` and `model:` keys. This is the only
option that both improves triggering and passes the official validator. Deleting the keys
without merging would pass validation while leaving the undertriggering in place.

`kiro-delegate` needs no merge — its description already restates all five triggers
verbatim. It still carries an inert `triggers:` block to delete.

## 3. Finding B — `project-scaffolder` uses `tools:`, not `allowed-tools:`

`plugins/project-init/skills/project-scaffolder/SKILL.md` declares `tools:` and
`user-invocable:`. Unlike the other extras, `tools:` is not merely ignored-and-harmless:
the intended tool allowlist is silently discarded, because the schema key is
`allowed-tools`. One-line fix, but it belongs in its own bucket rather than the cosmetic
pile.

## 4. Finding C — the repo scorer's schema blind spot

`scripts/eval-skills.py` → `score_structure()` (around lines 224-270) awards:

```
+3  model and allowed-tools present
+1  only model or allowed-tools present
```

It grants points for `model:` — a field that is not part of the skill schema. Nothing in
the file references the allowed-key set, so a skill can score 100/100 while failing
official validation. `workshop-creator` does exactly that: **100/100 from our scorer**,
invalid per the official one (`invocation:`, `model:`).

Recommendation: add an allowed-key assertion to `score_structure`, and drop or repoint the
`model:` credit, so the repo's gate stops diverging from the official one.

Note `eval-skills.py` is not wired into CI — `.github/workflows/` contains only
`deploy-docs.yml` and `pr-review.yml`, so this scorer runs manually today.

## 5. Scorer false negatives — do not "fix" these

The three REVIEW verdicts, triaged:

- **`slide-fix` (78)** and **`kiro-delegate` (78)** — points lost to heuristics that
  misfire on routing/dispatch docs. Both lack a Mermaid tree (`has_mermaid`) and an
  `## Output` heading (`has_output_format`); `kiro-delegate` scores **4/20** on
  Concreteness solely because it documents its commands in a markdown table instead of a
  fenced block, so `has_command_examples` and `count_code_blocks` both read zero. Both
  files are well-written for what they are — a router and a trust-boundary explainer.
  Chasing these points would add ceremony, not quality.
- **`pr-autofix` (73)** — genuine. A 301-line body against a `references/` dir holding
  only `pr-review-workflow.yml` (no `.md` files), so Progressive Disclosure scores 8/20.
  The body embeds long inline security rationale — the hash-discipline commentary at
  `SKILL.md:151-165` and the verification rationale at `240-268` — which is reference
  material, not workflow. Recommend extracting both into `references/`.

## 6. Per-skill table

`OK` = valid both ways · `cosmetic` = inert keys only, keywords already in description ·
`triggering risk` = inert keys **and** stranded keywords · `real defect` = wrong key name
or genuine structural issue.

| Skill | Plugin | Repo score | Official | Offending keys | Verdict |
|-------|--------|-----------:|----------|----------------|---------|
| `workshop-creator` | aws-content | 100 | ✗ | `invocation`, `model` | cosmetic |
| `ops-network-diagnosis` | aws-ops | 97 | ✗ | `model`, `triggers` | triggering risk |
| `ops-observability` | aws-ops | 97 | ✗ | `model`, `triggers` | triggering risk |
| `animated-diagram` | aws-content | 94 | ✗ | `model` | cosmetic |
| `gitbook` | aws-content | 94 | ✗ | `model` | cosmetic |
| `ops-troubleshoot` | aws-ops | 94 | ✗ | `model`, `triggers` | triggering risk |
| `decision-reconcile` | project-init | 94 | ✗ | `triggers` | triggering risk |
| `architecture-diagram` | aws-content | 93 | ✗ | `model` | cosmetic |
| `ops-wellarchitected-review` | aws-ops | 92 | ✗ | `model`, `triggers` | triggering risk |
| `reactive-presentation` | aws-content | 91 | ✓ | — | OK |
| `gh-home` | aws-content | 90 | ✓ | — | OK |
| `aws-light-fcd` | aws-content | 89 | ✓ | — | OK |
| `ops-health-check` | aws-ops | 89 | ✗ | `model`, `triggers` | triggering risk |
| `ops-security-audit` | aws-ops | 89 | ✗ | `model`, `triggers` | triggering risk |
| `co-agent` | co-agent | 88 | ✗ | `triggers` | triggering risk |
| `agentcore-create` | agentcore-creator | 86 | ✗ | `argument-hint`, `model`, `triggers` | triggering risk |
| `brochure` | aws-content | 86 | ✓ | — | OK |
| `kiro-convert` | kiro-power-converter | 86 | ✗ | `model`, `triggers` | triggering risk |
| `project-scaffolder` | project-init | 86 | ✗ | `tools`, `user-invocable` | **real defect** |
| `slide-fix` | aws-content | 78 | ✗ | `model` | cosmetic (scorer false negative) |
| `kiro-delegate` | kiro | 78 | ✗ | `triggers` | cosmetic (scorer false negative) |
| `pr-autofix` | project-init | 73 | ✗ | `triggers` | triggering risk + **real defect** |

## 7. Suggested order of work

1. `project-scaffolder`: `tools:` → `allowed-tools:` (only change that restores lost
   behavior).
2. Merge stranded keywords into `description` for the 11 skills in §2, then delete
   `triggers:`/`model:`/`invocation:`/`argument-hint:` repo-wide. Prioritize the four
   thinnest descriptions (`ops-health-check`, `ops-network-diagnosis`, `pr-autofix`,
   `kiro-convert`).
3. `eval-skills.py`: add the allowed-key assertion (§4), so 1 and 2 can't regress.
4. `pr-autofix`: extract the inline security rationale into `references/` (§5).

## Reproducing

```bash
# repo scorer — reproduces the 19 PASS / 3 REVIEW baseline
python3 scripts/eval-skills.py

# official validator — reproduces 4 valid / 18 invalid
cd ~/.claude/plugins/cache/claude-plugins-official/skill-creator/unknown/skills/skill-creator
for d in /home/atomoh/oh-my-cloud-skills/plugins/*/skills/*/; do
  printf "%-28s " "$(basename $d)"
  python3 -m scripts.quick_validate "$d" 2>&1 | head -1
done
```

## Scope and limits

- Report only. No `SKILL.md` was edited; `scripts/eval-skills.py` was not modified.
- The `skill-creator` description-optimization loop (`run_loop.py`) was **not** run — it
  needs ~20 human-reviewed trigger eval queries per skill. It is the right tool to
  validate the §2 description merges once they're written.
- **Ops triggering was not verified end-to-end.** `aws-ops-plugin` was not loaded in the
  review session (no SessionStart announcement, no `ops-*` entries in the available-skills
  list), so all `ops-*` findings come from file analysis, not observed routing behavior.
  The undertriggering risk in §2 is inferred from the schema, not measured.

---

## Resolution (applied 2026-07-27)

All findings above are fixed. Two claims in this report were **corrected** while planning
the fix — read these before trusting the sections they qualify:

1. **§1/§4's "official validator" is not the schema.** `skill-creator`'s
   `quick_validate.py` self-describes as a "minimal version" with a hardcoded allow-list,
   and it *rejects* `user-invocable` / `disable-model-invocation` — fields official
   Anthropic skills (`claude-automation-recommender`, `clickhouse/setup`, the codex
   skills) actually use. The authority is the spec itself
   (`https://agentskills.io/specification`): exactly six fields — `name`, `description`,
   `license`, `compatibility`, `metadata`, `allowed-tools`. So the "4 valid / 18 invalid"
   split overstates the case; the real defect was narrower and is stated in §2.
2. **§3's `project-scaffolder` `tools:` finding is reframed.** `tools:` is not
   unambiguously broken — official skills use it too. But `allowed-tools` *is* the spec
   field, so it was switched anyway (`allowed-tools: Read Glob`). `user-invocable: false`
   was left alone: removing it would make the skill user-invocable, a behavior change
   rather than a cleanup.

### What changed

- **19 SKILL.md files**: deleted every inert key (`triggers:`, `model:`, `invocation:`,
  `argument-hint:`). For the 11 skills whose trigger keywords appeared nowhere in their
  `description`, the keywords were folded into the description as trigger prose first.
  All descriptions stay under the spec's 1024-char cap (largest 793).
- **`kiro-delegate` / `co-agent`**: their `triggers:` blocks carried substantive rationale
  (why review/informational phrasings are deliberately excluded). That reasoning was moved
  into the SKILL.md body / description rather than deleted with the block.
- **`workshop-creator`**: description strengthened, since deleting `invocation:` removed
  the only `/workshop-creator` hint.
- **`project-scaffolder`**: `tools:` → `allowed-tools:`. Kept in YAML-list form, not the
  spec's space-separated string — `scripts/test-plugins.py` hard-errors on the string form
  (`'allowed-tools' must be a list`) and all 21 other skills use the list. Claude Code
  accepts both; matching the repo validator is the cheaper correctness.
- **`scripts/eval-skills.py`**: `score_structure()` no longer awards points for `model:`.
  It now scores spec conformance against `SPEC_FRONTMATTER_KEYS` — any unknown key scores
  0 for that 3-point slot. Dimension total unchanged (20). Scores after the change:
  19 PASS / 3 REVIEW / 0 FAIL — same distribution as the pre-fix baseline.
- **Root `CLAUDE.md`**: the "Skill File Format" section no longer describes `triggers` as
  a frontmatter field; it now names the allowed key set and states that trigger keywords
  belong in `description`.

### Still open

- §5's `pr-autofix` `references/` extraction was **not** done (it's a body-length fix, not
  a frontmatter one — `pr-autofix` remains REVIEW at 74).
- The `skill-creator` description-optimization loop still hasn't been run against the
  merged descriptions, and the ops-triggering limitation below still stands: the merge's
  benefit is inferred from the spec, not measured.
