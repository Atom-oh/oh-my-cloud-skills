<p align="center">
  <kbd><a href="#한국어">한국어</a></kbd> · <kbd><a href="#english">English</a></kbd>
</p>

---

# 한국어

## 시스템 개요

oh-my-cloud-skills는 Claude Code용 플러그인 마켓플레이스로, AWS 클라우드 콘텐츠 생성(프레젠테이션, 다이어그램, 문서, 워크숍)과 인프라 운영/트러블슈팅을 위한 6개 플러그인을 제공합니다.

## 컴포넌트 구조

### 플러그인 레이어

| 컴포넌트 | 역할 | 주요 기술 |
|----------|------|----------|
| aws-content-plugin | 콘텐츠 생성 (8 agents, 6 skills) | Python, HTML/CSS/JS, Draw.io |
| aws-ops-plugin | 인프라 운영 (10 agents, 6 skills) | MCP servers, AWS CLI |
| kiro-power-converter | 플러그인 → Kiro Power 변환 | YAML/JSON 변환 |
| co-agent | 멀티-AI 협업 — 리뷰/의사결정/ADR/컨텍스트 동기화/consensus 파이프라인 (1 agent, 1 skill, 3 commands) | Kiro/Codex/Gemini CLI |
| agentcore-creator | Claude Code → Bedrock AgentCore 변환 (1 agent, 1 skill) | AWS CLI, Python |
| project-init | 프로젝트 초기화 및 문서 관리 — 스캐폴딩/문서 동기화/ADR 모순 조정 (1 agent, 3 skills, 10 commands) | Bash, Markdown |

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
| Docusaurus site | 데모/문서 사이트 (docs/) |
| marketplace.json | 플러그인 레지스트리 |

## 아키텍처 다이어그램

```
┌─────────────────────────────────────────────────────────────────┐
│                    oh-my-cloud-skills                            │
│                   Plugin Marketplace                             │
├─────────────────┬──────────────────┬───────────────────────────┤
│                 │                  │                             │
│  ┌──────────────▼───────────────┐  │  ┌─────────────────────┐   │
│  │   aws-content-plugin         │  │  │  aws-ops-plugin      │   │
│  │                              │  │  │                      │   │
│  │  Agents:                     │  │  │  Agents:             │   │
│  │  ├─ presentation-agent       │  │  │  ├─ eks-agent        │   │
│  │  ├─ reactive-presentation    │  │  │  ├─ network-agent    │   │
│  │  ├─ architecture-diagram     │  │  │  ├─ iam-agent        │   │
│  │  ├─ animated-diagram         │  │  │  ├─ observability    │   │
│  │  ├─ document-agent           │  │  │  ├─ storage-agent    │   │
│  │  ├─ gitbook-agent            │  │  │  ├─ database-agent   │   │
│  │  ├─ workshop-agent           │  │  │  ├─ cost-agent       │   │
│  │  └─ content-review-agent     │  │  │  ├─ analytics-agent  │   │
│  │                              │  │  │  ├─ ops-coordinator  │   │
│  │                              │  │  │  └─ wellarchitected  │   │
│  │  Skills:                     │  │  │                      │   │
│  │  ├─ reactive-presentation    │  │  │  Skills:             │   │
│  │  ├─ architecture-diagram     │  │  │  ├─ ops-troubleshoot │   │
│  │  ├─ animated-diagram         │  │  │  ├─ ops-health-check │   │
│  │  ├─ gitbook                  │  │  │  ├─ ops-network      │   │
│  │  ├─ workshop-creator         │  │  │  ├─ ops-observability│   │
│  │  └─ slide-fix                │  │  │  ├─ ops-security     │   │
│  └──────────────────────────────┘  │  │  └─ ops-wellarchitect│   │
│                                    │  └─────────────────────┘   │
│  ┌──────────────────────────────┐  │  ┌─────────────────────┐   │
│  │  kiro-power-converter        │  │  │  co-agent         │   │
│  │  └─ kiro-converter-agent     │  │  │  └─ co-agent│   │
│  └──────────────────────────────┘  │  └─────────────────────┘   │
│  ┌──────────────────────────────┐  │  ┌─────────────────────┐   │
│  │  agentcore-creator           │  │  │  project-init        │   │
│  │  └─ agentcore-creator-agent  │  │  │  └─ doc-sync-checker │   │
│  └──────────────────────────────┘  │  └─────────────────────┘   │
├────────────────────────────────────┼─────────────────────────────┤
│  Tools                             │  Docs                       │
│  ├─ remarp_to_slides.py            │  ├─ Docusaurus site         │
│  ├─ extract_pptx_theme.py          │  ├─ README.md / .ko.md     │
│  ├─ remarp-vscode (VSCode ext)     │  └─ CHANGELOG.md            │
│  ├─ eval-skills.py                 │                             │
│  └─ eval-skill-behavior.py         │                             │
└────────────────────────────────────┴─────────────────────────────┘
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
| 단일 버전 관리 | 모든 plugin.json + marketplace.json 동기화 |
| Kiro CLI 외부 리뷰 통합 | 다중 관점 심층 리뷰 + 적대적 보안 검증 ([ADR-003](decisions/ADR-003-kiro-cli-architecture-deep-review.md)) |
| AgentCore 변환 독립 플러그인 | Claude Code 플러그인 → Bedrock AgentCore 배포 변환 ([ADR-004](decisions/ADR-004-agentcore-creator-skill.md)) |
| Rejection Loop (거절 루프) | Remarp 빌드 전 validate로 품질 강제 — CRITICAL 0건이어야 빌드 진행 ([ADR-005](decisions/ADR-005-rejection-loop.md)) |
| project-init 플러그인 도입 | 프로젝트 초기화/문서 동기화를 독립 플러그인으로 분리 ([ADR-006](decisions/ADR-006-project-init-plugin.md)) |
| Remarp ratio 필수화 | ratio 누락 시 VSCode Extension 프리뷰 비율 깨짐 방지 ([ADR-007](decisions/ADR-007-ratio-enforcement.md)) |

---

# English

## System Overview

oh-my-cloud-skills is a Claude Code plugin marketplace providing 6 plugins for AWS cloud content creation (presentations, diagrams, docs, workshops), infrastructure operations/troubleshooting, and developer tooling.

## Component Structure

### Plugin Layer

| Component | Role | Tech |
|-----------|------|------|
| aws-content-plugin | Content creation (8 agents, 6 skills) | Python, HTML/CSS/JS, Draw.io |
| aws-ops-plugin | Infrastructure ops (10 agents, 6 skills) | MCP servers, AWS CLI |
| kiro-power-converter | Plugin → Kiro Power conversion | YAML/JSON transform |
| co-agent | Multi-AI collaboration — review/decide/ADR/sync-context/consensus pipeline (1 agent, 1 skill, 3 commands) | Kiro/Codex/Gemini CLI |
| agentcore-creator | Claude Code → Bedrock AgentCore conversion (1 agent, 1 skill) | AWS CLI, Python |
| project-init | Project scaffolding & doc management — scaffolding/doc-sync/ADR reconciliation (1 agent, 3 skills, 10 commands) | Bash, Markdown |

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
| Docusaurus site | Demo/docs site (docs/) |
| marketplace.json | Plugin registry |

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    oh-my-cloud-skills                            │
│                   Plugin Marketplace                             │
├─────────────────┬──────────────────┬───────────────────────────┤
│                 │                  │                             │
│  ┌──────────────▼───────────────┐  │  ┌─────────────────────┐   │
│  │   aws-content-plugin         │  │  │  aws-ops-plugin      │   │
│  │                              │  │  │                      │   │
│  │  Agents:                     │  │  │  Agents:             │   │
│  │  ├─ presentation-agent       │  │  │  ├─ eks-agent        │   │
│  │  ├─ reactive-presentation    │  │  │  ├─ network-agent    │   │
│  │  ├─ architecture-diagram     │  │  │  ├─ iam-agent        │   │
│  │  ├─ animated-diagram         │  │  │  ├─ observability    │   │
│  │  ├─ document-agent           │  │  │  ├─ storage-agent    │   │
│  │  ├─ gitbook-agent            │  │  │  ├─ database-agent   │   │
│  │  ├─ workshop-agent           │  │  │  ├─ cost-agent       │   │
│  │  └─ content-review-agent     │  │  │  ├─ analytics-agent  │   │
│  │                              │  │  │  ├─ ops-coordinator  │   │
│  │                              │  │  │  └─ wellarchitected  │   │
│  │  Skills:                     │  │  │                      │   │
│  │  ├─ reactive-presentation    │  │  │  Skills:             │   │
│  │  ├─ architecture-diagram     │  │  │  ├─ ops-troubleshoot │   │
│  │  ├─ animated-diagram         │  │  │  ├─ ops-health-check │   │
│  │  ├─ gitbook                  │  │  │  ├─ ops-network      │   │
│  │  ├─ workshop-creator         │  │  │  ├─ ops-observability│   │
│  │  └─ slide-fix                │  │  │  ├─ ops-security     │   │
│  └──────────────────────────────┘  │  │  └─ ops-wellarchitect│   │
│                                    │  └─────────────────────┘   │
│  ┌──────────────────────────────┐  │  ┌─────────────────────┐   │
│  │  kiro-power-converter        │  │  │  co-agent         │   │
│  │  └─ kiro-converter-agent     │  │  │  └─ co-agent│   │
│  └──────────────────────────────┘  │  └─────────────────────┘   │
│  ┌──────────────────────────────┐  │  ┌─────────────────────┐   │
│  │  agentcore-creator           │  │  │  project-init        │   │
│  │  └─ agentcore-creator-agent  │  │  │  └─ doc-sync-checker │   │
│  └──────────────────────────────┘  │  └─────────────────────┘   │
├────────────────────────────────────┼─────────────────────────────┤
│  Tools                             │  Docs                       │
│  ├─ remarp_to_slides.py            │  ├─ Docusaurus site         │
│  ├─ extract_pptx_theme.py          │  ├─ README.md / .ko.md     │
│  ├─ remarp-vscode (VSCode ext)     │  └─ CHANGELOG.md            │
│  ├─ eval-skills.py                 │                             │
│  └─ eval-skill-behavior.py         │                             │
└────────────────────────────────────┴─────────────────────────────┘
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
| Single version management | All plugin.json + marketplace.json in sync |
| Kiro CLI external review integration | Multi-perspective deep review + adversarial security verification ([ADR-003](decisions/ADR-003-kiro-cli-architecture-deep-review.md)) |
| AgentCore converter as standalone plugin | Claude Code plugin to Bedrock AgentCore deployment conversion ([ADR-004](decisions/ADR-004-agentcore-creator-skill.md)) |
| Rejection Loop | Validate before build — zero CRITICAL issues required to proceed ([ADR-005](decisions/ADR-005-rejection-loop.md)) |
| project-init plugin | Separated project scaffolding/doc sync into standalone plugin ([ADR-006](decisions/ADR-006-project-init-plugin.md)) |
| Remarp ratio enforcement | Prevent VSCode Extension preview aspect ratio breakage ([ADR-007](decisions/ADR-007-ratio-enforcement.md)) |
