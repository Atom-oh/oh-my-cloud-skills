---
sidebar_position: 1
slug: /intro
title: 시작하기
---

# oh-my-cloud-skills 시작하기

**oh-my-cloud-skills**는 AWS 클라우드 작업을 위한 [Claude Code](https://claude.ai/code) 플러그인 마켓플레이스입니다. 3개의 플러그인이 총 18개의 AI 에이전트와 11개의 스킬을 제공합니다.

## 플러그인 목록

| 플러그인 | 설명 | Agents | Skills |
|----------|------|--------|--------|
| [aws-content-plugin](/docs/aws-content-plugin/overview) | 프레젠테이션, 다이어그램, 문서, GitBook, 워크샵 | 8 | 5 |
| [aws-ops-plugin](/docs/aws-ops-plugin/overview) | EKS, 네트워크, IAM, 옵저버빌리티, 스토리지, DB, 비용 | 9 | 5 |
| [kiro-power-converter](/docs/kiro-power-converter/overview) | Claude Code 플러그인 → Kiro Power 변환 | 1 | 1 |

## 설치 방법

### Marketplace에서 설치 (권장)

```bash
# Claude Code 세션에서 실행
/plugin marketplace add aws-content-plugin
/plugin marketplace add aws-ops-plugin
/plugin marketplace add kiro-power-converter
```

### 로컬에서 직접 로드

```bash
# 저장소 클론
git clone https://github.com/Atom-oh/oh-my-cloud-skills.git

# 플러그인 디렉토리를 직접 지정하여 로드
claude --plugin-dir ./oh-my-cloud-skills/plugins/aws-content-plugin
claude --plugin-dir ./oh-my-cloud-skills/plugins/aws-ops-plugin
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
- [Remarp Guide](/docs/remarp-guide/introduction) — 차세대 프레젠테이션 마크다운 포맷
