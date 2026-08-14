<p align="center">
  <kbd><a href="#한국어">한국어</a></kbd> · <kbd><a href="#english">English</a></kbd>
</p>

---

# 한국어

## 시스템 개요

oh-my-cloud-skills는 Claude Code용 플러그인 마켓플레이스로, AWS 클라우드 콘텐츠 생성(프레젠테이션, 다이어그램, 문서, 워크숍), 인프라 운영/트러블슈팅, 멀티-AI 협업, 개발자 툴링을 위한 7개 플러그인을 제공합니다.

## 컴포넌트 구조

### 플러그인 레이어

| 컴포넌트 | 역할 | 주요 기술 |
|----------|------|----------|
| aws-content-plugin | 콘텐츠 생성 (9 agents, 9 skills) | Python, HTML/CSS/JS, Draw.io |
| aws-ops-plugin | 인프라 운영 (10 agents, 6 skills) | MCP servers, AWS CLI |
| kiro-power-converter | 플러그인 → Kiro Power 변환 (1 agent, 1 skill) | YAML/JSON 변환 |
| agentcore-creator | Claude Code → Bedrock AgentCore 변환 (1 agent, 1 skill) | AWS CLI, Python |
| co-agent | 멀티-AI 협업 — 리뷰/의사결정/ADR/컨텍스트 동기화/consensus/harness (5 agents, 3 skills, 6 commands) | Kiro/Codex/Antigravity CLI |
| project-init | 프로젝트 초기화 및 문서 관리 (1 agent, 1 skill, 9 commands, upstream mirror) | Bash, Markdown |
| kiro | 비용 절감형 위임 — Claude가 계획/검증, Kiro CLI가 구현 (1 agent, 1 skill, 4 commands) | Kiro CLI |

### 도구 레이어

| 컴포넌트 | 역할 |
|----------|------|
| remarp_to_slides.py | Markdown → HTML 슬라이드 변환기 (stack-based parser) |
| extract_pptx_theme.py | PPTX → theme-manifest.json + CSS 변수 추출 |
| remarp-vscode | VSCode 확장 (미리보기, 비주얼 편집, 프롬프트 바) |
| eval-skills.py | 스킬 품질 평가 |
| eval-skill-behavior.py | E2E 스킬 행동 테스트 |

### 문서 레이어

| 컴포넌트 | 역할 |
|----------|------|
| doc-sites/ | Docusaurus 데모/문서 사이트 (GitHub Pages 배포) |
| docs/ | 내부 문서 — ADR, 런북, superpowers specs/plans (이 파일) |
| marketplace.json | 플러그인 레지스트리 |

## 아키텍처 다이어그램

```
┌───────────────────────────────────────────────────────────────────────┐
│                      oh-my-cloud-skills — Plugin Marketplace          │
├────────────────────┬────────────────────┬──────────────────────────┤
│ aws-content-plugin  │ aws-ops-plugin      │ co-agent                 │
│ 9 agents, 9 skills  │ 10 agents, 6 skills │ 5 agents, 3 skills,      │
│ 콘텐츠 생성          │ 인프라 운영         │ 6 commands — 멀티-AI     │
├────────────────────┼────────────────────┼──────────────────────────┤
│ kiro-power-converter│ agentcore-creator   │ project-init             │
│ 1 agent, 1 skill    │ 1 agent, 1 skill    │ 1 agent, 1 skill,        │
│ Kiro Power 변환      │ AgentCore 변환      │ 9 commands (upstream)    │
├────────────────────┴────────────────────┴──────────────────────────┤
│ kiro — 1 agent, 1 skill, 4 commands — Kiro CLI 구현 위임              │
├───────────────────────────────────────────────────────────────────────┤
│ Tools: remarp_to_slides.py · extract_pptx_theme.py · remarp-vscode ·  │
│        eval-skills.py · eval-skill-behavior.py                       │
│ Docs:  doc-sites/ (Docusaurus) · docs/ (ADR/런북/superpowers)         │
└───────────────────────────────────────────────────────────────────────┘
```

## 데이터 흐름

```
사용자 프롬프트 → 키워드 라우팅 (CLAUDE.md) → Agent → Skill/MCP → 아티팩트 생성 → Quality Gate → 배포
```

## 핵심 설계 결정

| 결정 | 이유 |
|------|------|
| 플러그인별 독립 구조 | 개별 설치/업데이트 가능, 관심사 분리 |
| 키워드 기반 자동 라우팅 | 사용자가 에이전트를 직접 선택할 필요 없음 |
| 한/영 이중 키워드 | 한국어 사용자 우선 지원 |
| Quality Gate 필수 | content-review-agent 통과 없이 배포 불가 |
| 단일 버전 관리 | 7개 plugin.json + marketplace.json 전부 동일 버전 동기화 |
| Kiro CLI 외부 리뷰 통합 | 다중 관점 심층 리뷰 + 적대적 보안 검증 ([ADR-003](decisions/ADR-003-kiro-cli-architecture-deep-review.md)) |
| AgentCore 변환 독립 플러그인 | Claude Code 플러그인 → Bedrock AgentCore 배포 변환 ([ADR-004](decisions/ADR-004-agentcore-creator-skill.md)) |
| Rejection Loop (거절 루프) | Remarp 빌드 전 validate로 품질 강제 — CRITICAL 0건이어야 빌드 진행 ([ADR-005](decisions/ADR-005-rejection-loop.md)) |
| project-init 플러그인 도입 | 프로젝트 초기화/문서 동기화를 독립 플러그인으로 분리 ([ADR-006](decisions/ADR-006-project-init-plugin.md)) |
| Remarp ratio 필수화 | ratio 누락 시 VSCode Extension 프리뷰 비율 깨짐 방지 ([ADR-007](decisions/ADR-007-ratio-enforcement.md)) |

---

# English

## System Overview

oh-my-cloud-skills is a Claude Code plugin marketplace providing 7 plugins for AWS cloud content creation (presentations, diagrams, docs, workshops), infrastructure operations/troubleshooting, multi-AI collaboration, and developer tooling.

## Component Structure

### Plugin Layer

| Component | Role | Tech |
|-----------|------|------|
| aws-content-plugin | Content creation (9 agents, 9 skills) | Python, HTML/CSS/JS, Draw.io |
| aws-ops-plugin | Infrastructure ops (10 agents, 6 skills) | MCP servers, AWS CLI |
| kiro-power-converter | Plugin → Kiro Power conversion (1 agent, 1 skill) | YAML/JSON transform |
| agentcore-creator | Claude Code → Bedrock AgentCore conversion (1 agent, 1 skill) | AWS CLI, Python |
| co-agent | Multi-AI collaboration — review/decide/ADR/sync-context/consensus/harness (5 agents, 3 skills, 6 commands) | Kiro/Codex/Antigravity CLI |
| project-init | Project scaffolding & doc management (1 agent, 1 skill, 9 commands, upstream mirror) | Bash, Markdown |
| kiro | Cost-savings delegation — Claude plans/verifies, Kiro CLI implements (1 agent, 1 skill, 4 commands) | Kiro CLI |

### Tool Layer

| Component | Role |
|-----------|------|
| remarp_to_slides.py | Markdown → HTML slide converter (stack-based parser) |
| extract_pptx_theme.py | PPTX → theme-manifest.json + CSS variable extraction |
| remarp-vscode | VSCode extension (preview, visual editing, prompt bar) |
| eval-skills.py | Skill quality evaluation |
| eval-skill-behavior.py | E2E skill behavior testing |

### Documentation Layer

| Component | Role |
|-----------|------|
| doc-sites/ | Docusaurus demo/docs site (published to GitHub Pages) |
| docs/ | Internal docs — ADRs, runbooks, superpowers specs/plans (this file) |
| marketplace.json | Plugin registry |

## Architecture Diagram

```
┌───────────────────────────────────────────────────────────────────────┐
│                      oh-my-cloud-skills — Plugin Marketplace          │
├────────────────────┬────────────────────┬──────────────────────────┤
│ aws-content-plugin  │ aws-ops-plugin      │ co-agent                 │
│ 9 agents, 9 skills  │ 10 agents, 6 skills │ 5 agents, 3 skills,      │
│ content creation    │ infra operations    │ 6 commands — multi-AI    │
├────────────────────┼────────────────────┼──────────────────────────┤
│ kiro-power-converter│ agentcore-creator   │ project-init             │
│ 1 agent, 1 skill    │ 1 agent, 1 skill    │ 1 agent, 1 skill,        │
│ → Kiro Power        │ → Bedrock AgentCore │ 9 commands (upstream)    │
├────────────────────┴────────────────────┴──────────────────────────┤
│ kiro — 1 agent, 1 skill, 4 commands — delegates implementation to    │
│ Kiro CLI                                                              │
├───────────────────────────────────────────────────────────────────────┤
│ Tools: remarp_to_slides.py · extract_pptx_theme.py · remarp-vscode ·  │
│        eval-skills.py · eval-skill-behavior.py                       │
│ Docs:  doc-sites/ (Docusaurus) · docs/ (ADRs/runbooks/superpowers)    │
└───────────────────────────────────────────────────────────────────────┘
```

## Data Flow

```
User prompt → Keyword routing (CLAUDE.md) → Agent → Skill/MCP → Artifact → Quality Gate → Deploy
```

## Key Design Decisions

| Decision | Why |
|----------|-----|
| Independent plugin structure | Individual install/update, separation of concerns |
| Keyword-based auto-routing | Users don't need to manually select agents |
| Bilingual KR/EN keywords | Korean-first user support |
| Mandatory Quality Gate | No deployment without content-review-agent pass |
| Single version management | All 7 plugin.json + marketplace.json kept in sync at one version |
| Kiro CLI external review integration | Multi-perspective deep review + adversarial security verification ([ADR-003](decisions/ADR-003-kiro-cli-architecture-deep-review.md)) |
| AgentCore converter as standalone plugin | Claude Code plugin to Bedrock AgentCore deployment conversion ([ADR-004](decisions/ADR-004-agentcore-creator-skill.md)) |
| Rejection Loop | Validate before build — zero CRITICAL issues required to proceed ([ADR-005](decisions/ADR-005-rejection-loop.md)) |
| project-init plugin | Separated project scaffolding/doc sync into standalone plugin ([ADR-006](decisions/ADR-006-project-init-plugin.md)) |
| Remarp ratio enforcement | Prevent VSCode Extension preview aspect ratio breakage ([ADR-007](decisions/ADR-007-ratio-enforcement.md)) |
