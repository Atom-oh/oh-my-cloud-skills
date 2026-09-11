<!-- oh-my-cloud-skills-pr-review -->
## 🤖 AI Code Review (Claude Fable 5.1 chair · 4-model panel)

_Cells (model): codex/FULL kiro-opus/FULL kiro-gpt/FULL _

**Status: PASSED** — No blocking issues found

## Summary

PR #177은 atlas와 project-init에 생성된 Codex overlay(`.codex-plugin/skills/`, `runtime.md`, `run.py`, atlas는 hook bridge까지)를 배포하고, project-init을 `.agents/plugins/marketplace.json`에 등록하며, `atlas_index.py --validate`의 exit code 의미를 `atlas_sync.py`의 commit gate와 일치시킵니다(advisory-only → exit 0). 생성기 `scripts/sync-codex-plugins.py`와 hook 템플릿은 base에 이미 존재하고 `test-codex-published.sh`의 `--check`가 overlay 동일성을 강제하므로 구조적 무결성은 확인됐습니다. 남는 실제 문제는 공유 `runtime.md` 템플릿이 hook이 없는 project-init에도 "hooks are connected" 문장을 그대로 싣는 점과, 배포 이후에도 `CLAUDE_ONLY` staging 예외와 root `CLAUDE.md`의 "not yet published" 서술이 그대로 남는 문서/validator 드리프트입니다.

## Issues

### CRITICAL
없음. 자격증명 노출, 런타임 파괴, 명시된 contract 위반은 확인되지 않았습니다. upstream mirror 파일(`plugins/project-init/{agents,commands,skills}`)은 건드리지 않고 overlay만 추가했으며, 이는 root `CLAUDE.md`가 허용하는 경로입니다.

### MAJOR

1. **`plugins/project-init/.codex-plugin/runtime.md:73-81` — 존재하지 않는 hook 배선을 단언 (codex + kiro-gpt + kiro-opus 3-cell convergent, diff로 확인됨).** "This plugin's command hooks are connected through `.codex-plugin/hooks.json`. The adapter translates a Codex `apply_patch`…"라고 적혀 있지만 project-init overlay에는 `hooks.json`/`hook.py`가 없고 `plugin.json`에 `hooks` 키도 없습니다. 원인은 개별 파일이 아니라 `scripts/codex/runtime.md`가 `OPTIONAL_ARTIFACTS` 존재 여부와 무관하게 무조건 복사되는 생성기 설계(`sync-codex-plugins.py:113`)입니다 — 지금까지는 hook을 가진 kiro만 생성 대상이었기 때문에 드러나지 않았습니다. Codex agent가 project-init 설치만으로 secret advisory/hook coverage가 있다고 전제할 수 있습니다. 같은 문단의 "Installation alone does not establish that hooks ran" 완화 문장이 있어 FAIL 사유는 아니지만, overlay를 직접 고치면 `--check`가 stale로 거부하므로 **템플릿에서** 조건부 문단으로 바꿔야 합니다.

### MINOR

- **`scripts/codex/project-init-project/.codex/hooks.json` (및 overlay 사본) — `$(git rev-parse --show-toplevel)` 경로 해석 (codex).** 프로젝트가 상위 git repo의 하위 디렉터리로 초기화되면 세 hook 모두 상위 root의 `.codex/hooks/project_context.py`를 찾다 실패합니다(`project_context.py` 자체는 `parents[2]`로 자기 위치를 쓰므로 launcher만 문제). `workflow.md`는 non-Git 케이스만 언급하고 nested-git은 언급하지 않습니다. Codex hook cwd 의미론은 이 저장소에서 검증할 수 없으므로 advisory로 둡니다.
- **`project_context.py:27` — `+++` 필터가 `++`로 시작하는 추가 내용까지 버림 (codex).** `--unified=0`에서도 `+++ b/…` 헤더는 남으므로 필터 자체는 필요하지만, `++AKIA…` 같은 추가 라인은 검사에서 빠집니다. 낮은 확률의 edge case.
- **`project_context.py` PreToolUse/`Bash` 매 호출마다 `git diff --cached` (kiro-opus).** non-Git 디렉터리에서는 매 shell 호출마다 "Staged-secret advisory unavailable" 잡음이 납니다. `workflow.md`가 "full Git-project setup" 전용이라고 한정하고 있어 완화됨.
- **`scripts/test-codex-plugins.py:35` `CLAUDE_ONLY = {"project-init"}` 및 root `CLAUDE.md` 서술이 이 PR 이후 stale.** `scripts/CLAUDE.md`는 "once the generated overlay and entry ship, it must not excuse missing Codex delivery"라고 명시하는데, overlay를 배포한 이 PR이 예외를 제거하지 않아 향후 overlay가 삭제되어도 validator가 통과합니다. root `CLAUDE.md`의 "Project-init's generated overlay and entry are approved but not yet published on this base"와 "CLAUDE_ONLY temporarily permits project-init's unpublished adapter"도 이제 사실과 다릅니다(chair 자체 확인).
- **`docs/reference/project-init-upstream-sync.md:16-25` 한/영 비대칭 (kiro-gpt + kiro-opus convergent).** 영문 단락이 추가한 "`CLAUDE_ONLY` exception does not exempt a present overlay from validation" 명제가 한국어 단락에 없습니다.
- **`workflow.md` / `scripts/codex/project-init.md` — 소스 수치 재서술 (kiro-opus).** "its listed weights sum to 195"는 `commands/health-check.md`의 값을 복제한 것으로, upstream이 바뀌면 조용히 썩습니다. memory의 "restatement drifts from authoritative source" 패턴과 동일 계열.
- **`plugins/atlas/CLAUDE.md:104-106` 문장 (kiro-opus).** "Orphan advisories remain visible but yield validation exit 0"는 advisory가 0을 강제하는 것처럼 읽힙니다. 새 테스트 `test_broken_related_link_still_fails_alongside_orphan_warning`이 보여주듯 hard error 공존 시 exit 1 — "alone" 한정어 필요. 잔재 확인 결과 `SKILL.md:126`("allowed to exit non-zero")과 `frontmatter-schema.md:41`(schema error → exit 1)은 여전히 참이며, 다른 "exits 1 on any problem" 잔재는 없습니다.
- **테스트 격리/컨벤션 nit (kiro-opus).** `test-codex-project-template.py`는 `test-atlas-validation.py`와 달리 `GIT_CONFIG_NOSYSTEM`/`hooksPath` 고정이 없고, `test-atlas-validation.sh`는 sourced 파일인데 shebang이 있습니다(`tests/CLAUDE.md` 컨벤션: "no shebang"). 동작상 무해.

### Dismissed (diff/base 대조 결과 미지지)

- **kiro-opus MAJOR 1 "생성기가 base에 없어 sync 절차가 하드 실패"** — `scripts/sync-codex-plugins.py`, `scripts/codex/{hook.py,run.py,runtime.md}`는 base에 존재하며 `tests/structure/test-codex-published.sh`가 이미 `--check`로 실행 중입니다. `if [ -f … ]` 폴백 제거는 정당합니다.
- **kiro-opus MAJOR 3 "atlas manifest consent 후퇴"** — 이전 `longDescription`에도 Anthropic 데이터 송출 고지는 없었고("Claude Code-only and off by default"만 있었음), 이 PR이 hook을 Codex에 실제로 배선하므로 "Claude Code-only"를 유지하면 오히려 거짓이 됩니다. 새 문구 "optional, separately configured"는 opt-in을 유지하고, 실제 consent gate는 `hooks/pre-push-sync.sh:7,21`의 `sync.on_push` 기본값 false에 있으며 변경되지 않았습니다. 송출 고지는 생성 `skills/atlas/SKILL.md` description에 원문 그대로 보존됩니다.
- **kiro-opus MINOR `"authentication": "ON_INSTALL"`** — `.agents/plugins/marketplace.json`의 기존 7개 엔트리 전부 동일 값이고, `sync-codex-plugins.py:187`이 생성하는 값입니다.
- **kiro-opus MINOR `hook.py` PreToolUse `continue:false` 축소** — `hook.py`는 이 diff가 변경하지 않은 공유 템플릿(`scripts/codex/hook.py`)의 사본으로 kiro에 이미 머지되어 있고 `--check`가 동일성을 강제합니다. `test-codex-hook-routing.py::test_pre_continue_true_is_removed_…`가 의도된 동작임을 보여줍니다. 이 PR 범위 밖.
- **kiro-opus MINOR "테스트가 overlay 대신 생성기 입력본을 검증"** — `sync-codex-plugins.py:117-123, 228`이 `project-template` 트리를 생성·prune 대상에 포함하고 `test-codex-published.sh`가 `--check`를 돌리므로 두 blob의 동일성은 CI에서 고정됩니다.

## Suggestions

1. `scripts/codex/runtime.md`의 "Hooks and evidence" 문단을 생성기에서 조건부로 렌더링(hooks 있음/없음 두 변형) 하거나, "If this package ships `.codex-plugin/hooks.json`…"로 일반화한 뒤 `--plugin atlas --plugin project-init --plugin kiro`로 재생성.
2. `CLAUDE_ONLY`에서 `project-init` 제거 + root `CLAUDE.md`의 "not yet published"/"unpublished adapter" 두 문장과 `docs/reference/project-init-upstream-sync.md` 한국어 단락을 같은 PR에서 갱신. 8-plugin acceptance 상태 문구는 그대로 두되 "overlay 미배포" 서술만 제거.
3. `hooks.json` 템플릿의 launcher를 nested-git에도 안전하게: `workflow.md`에 "프로젝트 root가 git toplevel과 다르면 절대 경로로 등록" 지침 추가, 또는 `project_context.py`처럼 스크립트 자기 위치 기준으로 해석되는 방식으로 통일.
4. `project_context.py`: `+++` 필터를 `line.startswith("+++ ") and (line[4:].startswith(("a/", "b/")) or line[4:] == "/dev/null")`처럼 헤더 형태로 좁히기; PreToolUse에서 `git rev-parse --is-inside-work-tree` 실패 시 빈 문자열 반환으로 non-Git 잡음 억제.
5. `workflow.md`의 "195" 수치를 지우고 "do not copy the source's hard-coded denominator; sum the applicable weights" 정도로 소스를 가리키게 변경.
6. `plugins/atlas/CLAUDE.md:105`에 "advisories alone" 한정어 추가.

### 🧠 MEMORY CANDIDATES

- **False-positive pattern:** "이 diff에 스크립트 X가 추가되지 않았으므로 X는 존재하지 않는다" — 참조 대상이 diff 밖의 base 트리에 이미 있는지 확인 없이 '존재 검사 제거 = 하드 실패'로 단정. `scripts/sync-codex-plugins.py`는 base에 있었고 CI가 이미 `--check`로 실행 중이었음 (source: PR #177, kiro-opus MAJOR).
- **False-positive pattern:** marketplace `policy`/메타데이터 값을 형제 엔트리 및 생성기(`sync-codex-plugins.py`)가 emit하는 값과 대조하지 않고 '불필요한 인증 프롬프트'로 플래그 — `ON_INSTALL`은 전 엔트리 공통 (source: PR #177, kiro-opus MINOR).
- **False-positive pattern:** `scripts/codex/<plugin>-project/` 소스와 `plugins/<plugin>/.codex-plugin/project-template/` overlay 중 한쪽만 테스트한다는 지적 — `test-codex-published.sh`의 `sync-codex-plugins.py --check`가 두 트리의 byte 동일성을 CI에서 강제함 (source: PR #177).
- **Recurring real:** 공유 생성 템플릿(`scripts/codex/runtime.md`)이 optional artifact(`hooks.json`)의 존재를 무조건 단언하면, 그 artifact가 없는 플러그인이 처음 생성 대상이 되는 순간 shipped 문서가 거짓이 된다. 새 플러그인을 생성기에 올릴 때 템플릿의 단언을 `OPTIONAL_ARTIFACTS` 산출 여부와 대조할 것; 수정은 overlay가 아니라 템플릿에서 (source: PR #177, 3-cell convergent, chair confirmed against generator).
- **Recurring real:** staging 예외 상수(`CLAUDE_ONLY`)와 "not yet published" 문서 서술은 해당 artifact를 배포하는 바로 그 PR에서 제거/갱신해야 한다 — 남겨두면 artifact가 다시 사라져도 validator가 통과하고, `scripts/CLAUDE.md`가 명시한 "must not excuse missing Codex delivery" 계약이 비어 버린다 (source: PR #177, chair finding).

### PANEL QUALITY
PANEL-QUALITY: kiro-opus=5/11

## Verdict

merge 시 실제로 깨지거나 자격증명이 새거나 명시된 contract를 위반하는 finding 없음. MAJOR 1건은 생성 문서의 부정확한 단언(템플릿 수정 사안)이며 runtime 동작에는 영향이 없습니다.


---
_Triggered by commit `1a24a9d20ddaa7250e46005ff7b5c842caf7f444` · workflow: `.github/workflows/pr-review.yml`_
