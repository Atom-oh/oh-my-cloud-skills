---
sidebar_position: 1
slug: /intro
title: 시작하기
---

# oh-my-cloud-skills 시작하기

**oh-my-cloud-skills**는 AWS 클라우드 작업을 위한 [Claude Code](https://claude.ai/code) 플러그인 마켓플레이스입니다. 6개의 플러그인이 총 25개의 AI 에이전트와 20개의 스킬을 제공합니다.

## 플러그인 목록

| 플러그인 | 설명 | Agents | Skills |
|----------|------|--------|--------|
| [co-agent](/docs/co-agent/overview) | 멀티-AI 협업 (Kiro/Codex/Agy) — 리뷰·의사결정·ADR·컨텍스트 동기화·consensus·harness 파이프라인, 5개 명령 | 3 | 1 |
| [project-init](/docs/project-init/overview) | 프로젝트 스캐폴딩, 문서 동기화, ADR 모순 검토, 10개 명령 | 1 | 3 |
| [aws-content-plugin](/docs/aws-content-plugin/overview) | 프레젠테이션(웹+네이티브 PPTX), 다이어그램, 문서, GitBook, 워크샵, 브로셔 | 9 | 8 |
| [aws-ops-plugin](/docs/aws-ops-plugin/overview) | EKS, 네트워크, IAM, 옵저버빌리티, 스토리지, DB, 비용, Well-Architected | 10 | 6 |
| [kiro-power-converter](/docs/kiro-power-converter/overview) | Claude Code 플러그인 → Kiro Power 변환 | 1 | 1 |
| [agentcore-creator](/docs/agentcore-creator/overview) | Claude Code 플러그인 → Bedrock AgentCore 배포 | 1 | 1 |

## 설치 방법

### Marketplace에서 설치 (권장)

```bash
# 마켓플레이스 추가
/plugin marketplace add https://github.com/Atom-oh/oh-my-cloud-skills

# 플러그인 설치
/plugin install aws-content-plugin@oh-my-cloud-skills
/plugin install aws-ops-plugin@oh-my-cloud-skills
/plugin install kiro-power-converter@oh-my-cloud-skills
/plugin install agentcore-creator@oh-my-cloud-skills
/plugin install co-agent@oh-my-cloud-skills
/plugin install project-init@oh-my-cloud-skills
```

### 로컬에서 직접 로드

```bash
# 저장소 클론
git clone https://github.com/Atom-oh/oh-my-cloud-skills.git

# 플러그인 디렉토리를 직접 지정하여 로드
claude --plugin-dir ./oh-my-cloud-skills/plugins/aws-content-plugin
claude --plugin-dir ./oh-my-cloud-skills/plugins/aws-ops-plugin
claude --plugin-dir ./oh-my-cloud-skills/plugins/kiro-power-converter
claude --plugin-dir ./oh-my-cloud-skills/plugins/agentcore-creator
claude --plugin-dir ./oh-my-cloud-skills/plugins/co-agent
claude --plugin-dir ./oh-my-cloud-skills/plugins/project-init
```

## 플러그인 구조

각 플러그인은 동일한 구조를 따릅니다:

```
plugins/<plugin-name>/
├── .claude-plugin/plugin.json    # 매니페스트: agents[], skills[]
├── .mcp.json                     # MCP 서버 설정 (ops-plugin만 해당)
├── CLAUDE.md                     # 자동 호출 키워드 → 에이전트 라우팅 규칙
├── agents/<name>.md              # 에이전트 정의 (YAML frontmatter + markdown)
└── skills/<name>/                # 스킬 디렉토리
    ├── SKILL.md                  # 진입점 (YAML frontmatter + triggers)
    └── references/               # 참조 문서
```

## 사용 예시

### 콘텐츠 생성

```
"AWS EKS 스케일링에 대한 교육 프레젠테이션을 만들어주세요"
→ presentation-agent가 자동 활성화되어 인터랙티브 HTML 슬라이드를 생성합니다.

"VPC 아키텍처 다이어그램을 그려주세요"
→ architecture-diagram-agent가 Draw.io XML을 생성합니다.

"서비스 간 트래픽 흐름을 애니메이션으로 보여주세요"
→ animated-diagram-agent가 SVG + SMIL 애니메이션을 생성합니다.
```

### 인프라 운영

```
"EKS 노드가 NotReady 상태입니다. 트러블슈팅해주세요"
→ eks-agent가 5분 트리아지를 수행하고 해결 방법을 제시합니다.

"ALB에서 502 에러가 발생합니다"
→ network-agent가 네트워크 진단을 시작합니다.

"IAM IRSA 설정이 안 됩니다"
→ iam-agent가 IRSA 구성을 검증하고 수정합니다.
```

## 다음 단계

- [aws-content-plugin 개요](/docs/aws-content-plugin/overview) — 콘텐츠 생성 플러그인
- [aws-ops-plugin 개요](/docs/aws-ops-plugin/overview) — 인프라 운영 플러그인
- [kiro-power-converter 개요](/docs/kiro-power-converter/overview) — Kiro Power 변환 플러그인
- [agentcore-creator 개요](/docs/agentcore-creator/overview) — Bedrock AgentCore 배포 플러그인
- [co-agent 개요](/docs/co-agent/overview) — 멀티-AI 협업 플러그인 (리뷰·의사결정·ADR·컨텍스트 동기화 + `/co-agent:configure`)
- [project-init 개요](/docs/project-init/overview) — 프로젝트 스캐폴딩 플러그인
- [Remarp Guide](/docs/remarp-guide/introduction) — 차세대 프레젠테이션 마크다운 포맷
