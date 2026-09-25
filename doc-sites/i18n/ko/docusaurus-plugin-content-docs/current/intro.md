---
sidebar_position: 1
slug: /intro
title: "시작하기"
---

{/* 영문 개편 이전의 섹션 링크를 유지합니다. */}
<span id="oh-my-cloud-skills-시작하기" />
<span id="플러그인-목록" />
<span id="설치-방법" />
<span id="marketplace에서-설치-권장" />
<span id="로컬에서-직접-로드" />
<span id="플러그인-구조" />
<span id="사용-예시" />
<span id="콘텐츠-생성" />
<span id="인프라-운영" />
<span id="다음-단계" />


# 시작하기

이 마켓플레이스는 Claude Code와 Codex용 플러그인 8개를 제공합니다. 플러그인 정의와 도우미 스크립트가 제품이며, 이 사이트는 해당 워크플로를 안내합니다.

현재 릴리스는 **v2.0.0**입니다. Antigravity를 선택했던 기존 co-agent 설정을
업데이트하기 전에 [릴리스 노트 및 마이그레이션 가이드](/docs/releases/v2.0.0)를 읽습니다.

<span id="plugins" />

## 플러그인 선택 {#choose-a-plugin}

| 플러그인 | 용도 |
| --- | --- |
| [co-agent](/docs/co-agent/overview) | 외부 AI 검토를 통해 추가 의견, 의사결정, ADR, 구현 파이프라인을 지원합니다. 현재 호스트가 작업을 주도합니다. |
| [kiro](/docs/kiro/overview) | 구현과 선택적 검토를 Kiro CLI에 위임하고 현재 호스트가 계획, 검증, 커밋을 책임집니다. |
| [project-init](/docs/project-init/overview) | 두 호스트용 프로젝트 지침과 구조를 초기화하고 문서를 동기화하며 ADR, 운영 절차서, 참조 가이드를 작성합니다. |
| [aws-content-plugin](/docs/aws-content-plugin/overview) | 웹 프레젠테이션, 편집 가능한 PowerPoint 슬라이드, 다이어그램, 문서, 워크숍, 브로슈어, 포트폴리오 페이지를 만듭니다. |
| [aws-ops-plugin](/docs/aws-ops-plugin/overview) | 컴퓨팅, 네트워크, 자격 증명, 관측성, 스토리지, 데이터베이스, 분석, 비용 영역의 AWS 및 EKS 인시던트를 진단합니다. |
| [kiro-power-converter](/docs/kiro-power-converter/overview) | Claude 플러그인 소스와 개별 스킬을 steering, 훅, 에셋, MCP 설정을 포함한 Kiro Powers로 변환합니다. |
| [agentcore-creator](/docs/agentcore-creator/overview) | 에이전트를 로컬에서 설계·테스트한 뒤 AgentCore harness 설정 또는 생성된 Runtime 애플리케이션을 준비합니다. |
| [token-saver](/docs/token-saver/overview) | 짧은 답변을 위한 지침을 적용하면서 추론, 검증, 완성된 산출물과 필수 보고 형식을 유지합니다. |

<span id="quick-install" />

## 설치 {#install}

Claude Code에서는 저장소 마켓플레이스를 추가한 뒤 필요한 플러그인을 설치합니다:

```text
/plugin marketplace add Atom-oh/oh-my-cloud-skills
/plugin install aws-content-plugin@oh-my-cloud-skills
```

Codex에서는 이 저장소의 `.agents/plugins/marketplace.json`을 마켓플레이스 소스로 추가하고 `/plugins`에서 설치합니다. 설치 후 새 스레드를 시작합니다. 호스트의 스킬 선택기에서 설치된 스킬을 고르거나 문서에 설명된 워크플로를 영어 문장으로 요청합니다.

Claude 매니페스트는 에이전트, 스킬, 명령, 훅을 제공합니다. Codex 매니페스트는 생성된 스킬 오버레이와 호스트별 훅·MCP 어댑터를 가리킵니다. Claude 명령은 Codex에서 스킬 항목이 되며, Claude 하위 에이전트 등록과 도구 이름이 자동으로 이전되지는 않습니다. 등록된 모든 플러그인이 Codex 패키지를 제공합니다.

## 현재 설정 {#current-configuration}

[Claude 마켓플레이스](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/.claude-plugin/marketplace.json) · [Codex 마켓플레이스](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/.agents/plugins/marketplace.json)

이 매니페스트와 각 플러그인의 소스 디렉터리가 설치 항목을 정의합니다. 생성된 Codex 오버레이는 Claude 명령을 감싸므로 스킬 항목이 더 많을 수 있습니다. 모델 식별자, 추론 설정, 컨텍스트 한도는 각 플러그인의 설정을 따릅니다. 이 사이트는 별도의 모델 목록을 관리하지 않습니다.

## 검토 및 예제 {#review-and-examples}

콘텐츠 결과물은 게시 전에 content-review 품질 게이트를 통과해야 합니다. 로컬 검토 훅은 선택적 통제이며 CI 검사나 저장소 브랜치 보호를 대체하지 않습니다. 검토 발견 사항은 실제 변경 파일과 현재 설정에 대조해 확인해야 합니다.

삽입된 데모와 다운로드 가능한 산출물은 고정된 예제입니다. 언어, 모델 이름, 가격, 당시의 설명은 원래 결과를 보여 주며 현재 운영 지침이 아닙니다.

## 관련 링크 {#related-links}

- [Claude Code](https://claude.ai/code)
- [Remarp 가이드](/docs/remarp-guide/introduction)
