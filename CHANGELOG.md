# Changelog

<a href="#english"><img src="https://img.shields.io/badge/lang-English-blue.svg" alt="English"></a>
<a href="#korean"><img src="https://img.shields.io/badge/lang-한국어-red.svg" alt="Korean"></a>

---

<a id="english"></a>

# English

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.6.0] - 2026-05-30

### Added
- **AWS DevOps Agent** integration in `aws-ops-plugin` ops-observability — incident escalation via Agent Spaces, CloudWatch→EventBridge→Lambda→webhook wiring, `aws devopsagent create-backlog-task`, and Kiro-compatible mitigation plans ([#25](https://github.com/Atom-oh/oh-my-cloud-skills/pull/25))
- **AWS Security Agent** integration in `aws-ops-plugin` ops-security-audit — design/code security review, on-demand penetration testing, org requirements, CI/CD API
- Open-source observability reference in ops-observability — OpenTelemetry, Grafana, Loki, Tempo, ClickHouse, VictoriaMetrics/Thanos/Mimir — plus a Version Compatibility section (ClickHouse server ↔ OTel exporter ↔ operator ↔ distro pinning)
- `/add-reference-doc` command and implementation-reference-docs workflow in `project-init` (synced from upstream): init-project Step 4.5, sync-docs Phase 1.5, doc-sync-checker validation
- Opus 4.8 compatibility section in `agentcore-creator` mapping rules and code templates (4.6/4.7 retained as history)

### Changed
- Migrate `agentcore-creator` `opus` alias to `us.anthropic.claude-opus-4-8` (MODEL_MAP + mirrored docs); bump `agentcore-creator-agent` to opus; de-stale "most capable" 4.6/4.7 claims
- Rewrite `kiro-review` Kiro CLI integration for Kiro CLI 2.5.0 — delegate via `kiro-cli chat --no-interactive` (headless) instead of the non-existent `Skill(skill: "kiro-cli:review")`; fix detection with `command -v kiro-cli`; drop over-provisioned `model: opus` pin (inherit parent session)
- Harden `project-init` rsync exclude list so upstream sync no longer clobbers local CLAUDE.md/SKILL.md customizations
- Bump all plugins and `marketplace.json` to 1.6.0

### Fixed
- `kiro-review`: add the missing delegation mechanism (`kiro-cli:review` is a slash command, not a skill); fix adversarial review (`/kiro-cli:adversarial-review`, not `review --adversarial`); guard `git diff | kiro-cli` pipes against empty-diff false PASS and kiro-cli runtime failure
- `pr-autofix`: fix invalid `gh pr reviews` → `gh pr view --json reviews`; fix `&&/||` precedence that ran `npx tsc` with no `package.json`; fix fail-open build verification that hid compiler errors (now keeps stderr visible and blocks commit on failure); update model IDs/Co-Authored-By to Opus 4.8
- Fix wrong Altinity ClickHouse operator Helm repo URL (`docs.altinity.com` → `helm.altinity.com`)

## [1.5.1] - 2026-05-14

### Changed
- Migrate all plugin Bedrock model IDs from Claude 4.0 (`-4-20250514`) to current models (Opus 4.7, Sonnet 4.6, Haiku 4.5) in `agentcore-creator` MODEL_MAP and templates
- Update generated agent code (`convert_plugin_to_agentcore.py`) to include 4.7-compatible defaults (`max_tokens=16000`, adaptive thinking guidance, no `temperature`/`top_p`/`top_k`)
- Update `kiro-power-converter` model examples from `claude-sonnet-4` to `claude-sonnet-4-6`

### Added
- Add Model-Specific Compatibility Notes section to `agentcore-mapping-rules.md` (Opus 4.7 breaking changes, 4.6 deprecations, Haiku 4.5 limitations)
- Add Model Selection Guide table to `agentcore-create/SKILL.md` Phase 2.1 with Bedrock model recommendations per task profile
- Add Recommended Inference Defaults section to `agent-code-templates.md` with 4.7-specific defaults
- Add Subagent Spawn Policy section to `aws-content-plugin/CLAUDE.md` (4.7 compatibility — explicit spawn/skip conditions)

### Fixed
- Fix invalid model ID `anthropic.claude-sonnet-4-6-20250514` in AIOps demo pages (date suffix was Claude 4.0 release date, not 4.6)

## [1.5.0] - 2026-04-29

### Added
- Add iterative refinement (rejection loop) for reactive-presentation quality validation ([#19](https://github.com/Atom-oh/oh-my-cloud-skills/pull/19))
- Add pr-autofix skill to project-init plugin ([#23](https://github.com/Atom-oh/oh-my-cloud-skills/pull/23))

### Fixed
- Fix PPTX theme extraction color palette using luminance-based selection instead of dk/lt slot names (handles inverted dark themes)
- Fix PPTX theme extraction footer misidentification with bottom-20% position filter
- Fix PPTX theme extraction layout background with keyword-based matching and `<p:bgRef>` XML parsing
- Fix PDF export CSS path resolution with dynamic `_resolveCommonPath()` instead of hardcoded `../common/`
- Fix PPTX export missing theme background by extracting colors from `window.__remarpTheme` in block HTML
- Fix TOC export block card selector to support both `<div class="block-card">` and `<a class="block-card">` structures

## [1.4.0] - 2026-04-14

### Added
- Add agentcore-creator plugin with interactive 5-phase workflow for Bedrock AgentCore deployment
- Add project-init plugin with 8 commands for project scaffolding and documentation sync
- Add kiro-review plugin for comprehensive architecture deep review via Kiro CLI
- Add Well-Architected Framework 6-pillar review to aws-ops-plugin (wellarchitected-agent, 100-point scoring) ([#16](https://github.com/Atom-oh/oh-my-cloud-skills/pull/16))
- Add slide-fix skill for Remarp slide issue annotation processing
- Add issue annotation system for Remarp VSCode extension (prompt bar, `<!-- issue: -->` annotations, issue badges in sidebar)
- Add PPTX image export via html2canvas iframe capture
- Add Pandoc-style colon-count nesting for ::: blocks with stack-based block parser
- Add PPTX template extraction with Slide Master metadata, --figma and --stitch design source options
- Add session-context, secret-scan, doc-sync hooks and safety permissions

### Changed
- Simplify issue annotation syntax from `<!-- !issue: -->` to `<!-- issue: -->`
- Replace submit button with /slide-fix guidance toast (remove `claude --print` CLI dependency)

### Fixed
- Fix XSS defense and frontmatter regex in preview.ts
- Fix 3 bugs in stack-based block parser
- Fix canvas editor slide context targeting
- Fix canvas DSL whitespace handling around commas
- Fix regex group indices in _group_p_with_list and NameError in compile_preset_to_js
- Restore kiro-review SessionStart hook and fix converter quote escaping

## [1.2.5] - 2026-04-06

### Added
- Add README.md to README.ko.md auto-translate hook
- Add live diagram demos to documentation site ([#11](https://github.com/Atom-oh/oh-my-cloud-skills/pull/11))
- Add detailed skill guides with 8 demo pages ([#9](https://github.com/Atom-oh/oh-my-cloud-skills/pull/9))

### Fixed
- Fix table th/td font-size to inherit from parent table element
- Fix fragment wrappers crossing column boundaries and heading-group spacing
- Fix :::click blocks not working when nested inside :::left/:::right columns

## [1.2.3] - 2026-03-20

### Added
- Add Canvas complexity gate in content-review-agent
- Add HTML Architecture pattern and STOP gate in reactive-presentation SKILL.md
- Add interactive slide patterns guide (interactive-patterns-guide.md)

### Changed
- Strengthen canvas vs HTML selection guidance in agent and SKILL.md decision guides
- Fix monitoring/dashboard mapping from canvas to html+script

### Fixed
- Fix canvas overuse -- agent no longer defaults all diagrams to :::canvas

## [1.2.2] - 2026-03-15

### Added
- Add orthogonal arrow routing to Canvas DSL
- Add data visualization design guide for reactive-presentation
- Add visual editor, canvas editor, and CSS editor to Remarp VSCode extension
- Add :::prompt block support and per-block export buttons
- Add AIOps 90-minute presentation demo

### Changed
- Enhance plugin skills with hooks, references, and improved patterns
- Migrate plugins to latest Claude Code format with hooks, validation, and token optimization

### Fixed
- Fix blocks config bug in multi-block presentations

## [1.2.1] - 2026-03-05

### Added
- Add Remarp VSCode extension completions and preview improvements
- Add Remarp-first workflow documentation

### Changed
- Enhance canvas animation prompts, PPTX theme extractor, and kiro conversion rules
- Update plugin CLAUDE.md keyword routing and team workflow docs
- Remove hardcoded model field from agent frontmatter

### Fixed
- Strip 'Block N:' prefix from slide titles in converter
- Correct `../common/` to `./common/` asset paths in remarp_to_slides.py
- Fix 3 rendering bugs in remarp_to_slides.py converter

## [1.1.0] - 2026-03-03

### Added
- Add kiro-power-converter plugin for Claude Code to Kiro Power conversion
- Add Docusaurus documentation site with GitHub Pages deployment
- Add i18n support (ko default, en placeholder)
- Add Remarp VSCode extension for syntax highlighting and preview
- Add audience frontmatter field and strengthen agent planning questions

### Changed
- Replace cloudwatch-agent with observability-agent, add analytics-agent
- Make Remarp the default content authoring format for presentations

### Fixed
- Fix PPTX theme extraction with Slide Master layout details

## [1.0.0] - 2026-02-26

### Added
- Initial release
- Add aws-content-plugin: presentation, architecture diagram, animated diagram, document, gitbook, workshop agents
- Add aws-ops-plugin: EKS, network, IAM, observability, storage, database, cost, analytics, ops-coordinator agents
- Add reactive-presentation skill with Canvas animations, quizzes, and keyboard navigation
- Add content review quality gate (100-point scale)
- Add PPTX/PDF theme extraction
- Add AWS Architecture Icons integration (4,224 files)
- Add presenter view with speaker notes

[Unreleased]: https://github.com/Atom-oh/oh-my-cloud-skills/compare/v1.4.0...HEAD
[1.4.0]: https://github.com/Atom-oh/oh-my-cloud-skills/compare/v1.2.5...v1.4.0
[1.2.5]: https://github.com/Atom-oh/oh-my-cloud-skills/compare/v1.2.3...v1.2.5
[1.2.3]: https://github.com/Atom-oh/oh-my-cloud-skills/compare/v1.2.2...v1.2.3
[1.2.2]: https://github.com/Atom-oh/oh-my-cloud-skills/compare/v1.2.1...v1.2.2
[1.2.1]: https://github.com/Atom-oh/oh-my-cloud-skills/compare/v1.1.0...v1.2.1
[1.1.0]: https://github.com/Atom-oh/oh-my-cloud-skills/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/Atom-oh/oh-my-cloud-skills/releases/tag/v1.0.0

---

<a id="korean"></a>

# 한국어

이 프로젝트의 모든 주요 변경 사항은 이 파일에 기록됩니다.
이 문서는 [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)를 기반으로 하며,
[Semantic Versioning](https://semver.org/spec/v2.0.0.html)을 따릅니다.

## [1.6.0] - 2026-05-30

### Added
- `aws-ops-plugin` ops-observability에 **AWS DevOps Agent** 연동 — Agent Spaces, CloudWatch→EventBridge→Lambda→webhook 연결, `aws devopsagent create-backlog-task`, Kiro 호환 완화 계획을 통한 인시던트 에스컬레이션 ([#25](https://github.com/Atom-oh/oh-my-cloud-skills/pull/25))
- `aws-ops-plugin` ops-security-audit에 **AWS Security Agent** 연동 — 설계/코드 보안 리뷰, 온디맨드 침투 테스트, 조직 보안 요구사항, CI/CD API
- ops-observability에 오픈소스 observability 레퍼런스 추가 — OpenTelemetry, Grafana, Loki, Tempo, ClickHouse, VictoriaMetrics/Thanos/Mimir — 및 버전 호환성 섹션 (ClickHouse 서버 ↔ OTel exporter ↔ operator ↔ 디스트로 고정)
- `project-init`에 `/add-reference-doc` 커맨드 및 implementation-reference-docs 워크플로우 추가 (upstream 동기화): init-project Step 4.5, sync-docs Phase 1.5, doc-sync-checker 검증
- `agentcore-creator` 매핑 규칙/코드 템플릿에 Opus 4.8 호환성 섹션 추가 (4.6/4.7은 이력 보존)

### Changed
- `agentcore-creator` `opus` 별칭을 `us.anthropic.claude-opus-4-8`로 마이그레이션 (MODEL_MAP + 미러 문서); `agentcore-creator-agent`를 opus로 상향; "most capable" 4.6/4.7 표기 정리
- `kiro-review`의 Kiro CLI 연동을 Kiro CLI 2.5.0 기준으로 재작성 — 존재하지 않는 `Skill(skill: "kiro-cli:review")` 대신 `kiro-cli chat --no-interactive`(headless) 위임; `command -v kiro-cli` 탐지로 수정; 과도한 `model: opus` 핀 제거
- `project-init` rsync exclude 목록 강화 — upstream 동기화가 로컬 CLAUDE.md/SKILL.md 커스터마이징을 덮어쓰지 않도록
- 모든 플러그인 및 `marketplace.json`을 1.6.0으로 상향

### Fixed
- `kiro-review`: 누락된 위임 메커니즘 추가 (`kiro-cli:review`는 스킬이 아닌 슬래시 커맨드); 적대적 리뷰 수정 (`/kiro-cli:adversarial-review`); `git diff | kiro-cli` 파이프의 빈 diff 거짓 PASS 및 kiro-cli 실패 가드
- `pr-autofix`: 잘못된 `gh pr reviews` → `gh pr view --json reviews` 수정; `package.json` 없이 `npx tsc`가 실행되던 `&&/||` 우선순위 수정; 컴파일 에러를 숨기던 fail-open 빌드 검증 수정 (stderr 노출 + 실패 시 커밋 차단); 모델 ID/Co-Authored-By를 Opus 4.8로 갱신
- 잘못된 Altinity ClickHouse operator Helm repo URL 수정 (`docs.altinity.com` → `helm.altinity.com`)

## [1.5.1] - 2026-05-14

### Changed
- 모든 플러그인의 Bedrock 모델 ID를 Claude 4.0 (`-4-20250514`)에서 최신 모델(Opus 4.7, Sonnet 4.6, Haiku 4.5)로 마이그레이션 (`agentcore-creator` MODEL_MAP 및 템플릿)
- 생성되는 에이전트 코드(`convert_plugin_to_agentcore.py`)에 4.7 호환 기본값 적용 (`max_tokens=16000`, adaptive thinking 가이드, `temperature`/`top_p`/`top_k` 제거)
- `kiro-power-converter` 모델 예시를 `claude-sonnet-4`에서 `claude-sonnet-4-6`로 업데이트

### Added
- `agentcore-mapping-rules.md`에 Model-Specific Compatibility Notes 섹션 추가 (Opus 4.7 breaking changes, 4.6 deprecations, Haiku 4.5 제약)
- `agentcore-create/SKILL.md` Phase 2.1에 작업 프로필별 Bedrock 모델 추천 테이블 추가
- `agent-code-templates.md`에 Recommended Inference Defaults 섹션과 4.7 specific defaults 추가
- `aws-content-plugin/CLAUDE.md`에 Subagent Spawn Policy 섹션 추가 (4.7 호환 — 명시적 spawn/skip 조건)

### Fixed
- AIOps 데모 페이지의 잘못된 모델 ID `anthropic.claude-sonnet-4-6-20250514` 수정 (date suffix는 Claude 4.6이 아닌 Claude 4.0 출시일)

## [1.5.0] - 2026-04-29

### Added
- reactive-presentation 품질 검증을 위한 반복 개선(rejection loop) 추가 ([#19](https://github.com/Atom-oh/oh-my-cloud-skills/pull/19))
- project-init 플러그인에 pr-autofix 스킬 추가 ([#23](https://github.com/Atom-oh/oh-my-cloud-skills/pull/23))

### Fixed
- PPTX 테마 추출 색상 팔레트를 dk/lt 슬롯명 대신 휘도 기반 선택으로 수정 (반전된 다크 테마 처리)
- PPTX 테마 추출 푸터 오인식을 하단 20% 위치 필터로 수정
- PPTX 테마 추출 레이아웃 배경을 키워드 기반 매칭 및 `<p:bgRef>` XML 파싱으로 수정
- PDF 내보내기 CSS 경로를 하드코딩된 `../common/` 대신 동적 `_resolveCommonPath()`로 수정
- PPTX 내보내기에서 블록 HTML의 `window.__remarpTheme`에서 색상을 추출하여 누락된 테마 배경 수정
- TOC 내보내기 블록 카드 셀렉터를 `<div class="block-card">`와 `<a class="block-card">` 구조 모두 지원하도록 수정

## [1.4.0] - 2026-04-14

### Added
- Bedrock AgentCore 배포를 위한 agentcore-creator 플러그인 추가 (5-Phase 대화형 워크플로우)
- 프로젝트 스캐폴딩 및 문서 동기화를 위한 project-init 플러그인 추가 (8개 명령)
- Kiro CLI 기반 종합 아키텍처 심층 리뷰를 위한 kiro-review 플러그인 추가
- aws-ops-plugin에 Well-Architected Framework 6-pillar 리뷰 추가 (wellarchitected-agent, 100점 스코어링) ([#16](https://github.com/Atom-oh/oh-my-cloud-skills/pull/16))
- Remarp 슬라이드 이슈 어노테이션 처리를 위한 slide-fix 스킬 추가
- Remarp VSCode 확장에 이슈 어노테이션 시스템 추가 (프롬프트 바, `<!-- issue: -->` 어노테이션, 사이드바 이슈 배지)
- html2canvas iframe 캡처를 통한 PPTX 이미지 내보내기 추가
- 스택 기반 블록 파서와 Pandoc 스타일 콜론 카운트 ::: 블록 중첩 추가
- Slide Master 메타데이터, --figma, --stitch 디자인 소스 옵션을 포함한 PPTX 템플릿 추출 추가
- session-context, secret-scan, doc-sync 훅 및 안전 권한 추가

### Changed
- 이슈 어노테이션 구문 간소화: `<!-- !issue: -->` → `<!-- issue: -->`
- 제출 버튼을 /slide-fix 안내 토스트로 교체 (`claude --print` CLI 의존성 제거)

### Fixed
- preview.ts의 XSS 방어 및 frontmatter 정규식 수정
- 스택 기반 블록 파서 버그 3건 수정
- 캔버스 에디터 슬라이드 컨텍스트 타겟팅 수정
- 캔버스 DSL 좌표 쉼표 주변 공백 처리 수정
- _group_p_with_list의 정규식 그룹 인덱스 및 compile_preset_to_js NameError 수정
- kiro-review SessionStart 훅 복원 및 컨버터 따옴표 이스케이프 수정

## [1.2.5] - 2026-04-06

### Added
- README.md → README.ko.md 자동 번역 훅 추가
- 문서 사이트에 라이브 다이어그램 데모 추가 ([#11](https://github.com/Atom-oh/oh-my-cloud-skills/pull/11))
- 상세 스킬 가이드 및 8개 데모 페이지 추가 ([#9](https://github.com/Atom-oh/oh-my-cloud-skills/pull/9))

### Fixed
- 테이블 th/td 폰트 크기가 부모 테이블 요소에서 상속되도록 수정
- fragment 래퍼가 열 경계를 넘는 문제 및 heading-group 간격 수정
- :::left/:::right 열 내부에서 :::click 블록이 작동하지 않는 문제 수정

## [1.2.3] - 2026-03-20

### Added
- content-review-agent에 Canvas 복잡도 게이트 추가
- reactive-presentation SKILL.md에 HTML 아키텍처 패턴 및 STOP 게이트 추가
- 인터랙티브 슬라이드 패턴 가이드 추가 (interactive-patterns-guide.md)

### Changed
- 에이전트 및 SKILL.md 결정 가이드에서 canvas vs HTML 선택 지침 강화
- monitoring/dashboard 매핑을 canvas에서 html+script로 수정

### Fixed
- canvas 과다 사용 수정 -- 에이전트가 더 이상 모든 다이어그램을 :::canvas로 기본 설정하지 않음

## [1.2.2] - 2026-03-15

### Added
- Canvas DSL에 직교 화살표 라우팅 추가
- reactive-presentation 데이터 시각화 디자인 가이드 추가
- Remarp VSCode 확장에 비주얼 에디터, 캔버스 에디터, CSS 에디터 추가
- :::prompt 블록 지원 및 블록별 내보내기 버튼 추가
- AIOps 90분 프레젠테이션 데모 추가

### Changed
- 플러그인 스킬에 훅, 참조 문서, 개선된 패턴 적용
- 플러그인을 최신 Claude Code 형식으로 마이그레이션 (훅, 검증, 토큰 최적화)

### Fixed
- 멀티 블록 프레젠테이션의 blocks config 버그 수정

## [1.2.1] - 2026-03-05

### Added
- Remarp VSCode 확장 자동완성 및 미리보기 개선
- Remarp 우선 워크플로우 문서 추가

### Changed
- 캔버스 애니메이션 프롬프트, PPTX 테마 추출기, kiro 변환 규칙 개선
- 플러그인 CLAUDE.md 키워드 라우팅 및 팀 워크플로우 문서 업데이트
- 에이전트 frontmatter에서 하드코딩된 model 필드 제거

### Fixed
- 컨버터에서 'Block N:' 접두사 슬라이드 제목 제거
- remarp_to_slides.py의 `../common/` → `./common/` 에셋 경로 수정
- remarp_to_slides.py 컨버터 렌더링 버그 3건 수정

## [1.1.0] - 2026-03-03

### Added
- Claude Code → Kiro Power 변환을 위한 kiro-power-converter 플러그인 추가
- GitHub Pages 배포를 포함한 Docusaurus 문서 사이트 추가
- i18n 지원 추가 (ko 기본, en 플레이스홀더)
- 구문 하이라이팅 및 미리보기를 위한 Remarp VSCode 확장 추가
- audience frontmatter 필드 추가 및 에이전트 계획 질문 강화

### Changed
- cloudwatch-agent를 observability-agent로 교체, analytics-agent 추가
- Remarp를 프레젠테이션 기본 콘텐츠 저작 포맷으로 지정

### Fixed
- Slide Master 레이아웃 세부사항이 포함된 PPTX 테마 추출 수정

## [1.0.0] - 2026-02-26

### Added
- 최초 릴리스
- aws-content-plugin 추가: presentation, architecture diagram, animated diagram, document, gitbook, workshop 에이전트
- aws-ops-plugin 추가: EKS, network, IAM, observability, storage, database, cost, analytics, ops-coordinator 에이전트
- Canvas 애니메이션, 퀴즈, 키보드 내비게이션을 포함한 reactive-presentation 스킬 추가
- 콘텐츠 리뷰 품질 게이트 추가 (100점 척도)
- PPTX/PDF 테마 추출 추가
- AWS Architecture Icons 통합 추가 (4,224개 파일)
- 발표자 뷰 및 발표자 노트 추가

[Unreleased]: https://github.com/Atom-oh/oh-my-cloud-skills/compare/v1.4.0...HEAD
[1.4.0]: https://github.com/Atom-oh/oh-my-cloud-skills/compare/v1.2.5...v1.4.0
[1.2.5]: https://github.com/Atom-oh/oh-my-cloud-skills/compare/v1.2.3...v1.2.5
[1.2.3]: https://github.com/Atom-oh/oh-my-cloud-skills/compare/v1.2.2...v1.2.3
[1.2.2]: https://github.com/Atom-oh/oh-my-cloud-skills/compare/v1.2.1...v1.2.2
[1.2.1]: https://github.com/Atom-oh/oh-my-cloud-skills/compare/v1.1.0...v1.2.1
[1.1.0]: https://github.com/Atom-oh/oh-my-cloud-skills/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/Atom-oh/oh-my-cloud-skills/releases/tag/v1.0.0
