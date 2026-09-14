---
sidebar_position: 2
title: "aws-ops-plugin 설치"
---

{/* 영문 개편 이전의 섹션 링크를 유지합니다. */}
<span id="설치" />
<span id="사전-요구사항" />
<span id="필수-도구" />
<span id="aws-환경" />
<span id="설치-방법" />
<span id="1-마켓플레이스-설치-권장" />
<span id="2-로컬-설치-개발테스트용" />
<span id="mcp-서버-설정" />
<span id="mcp-서버-목록" />
<span id="uvx-설치" />
<span id="수동-mcp-설정-필요한-경우" />
<span id="설치-확인" />
<span id="플러그인-로드-확인" />
<span id="mcp-서버-상태-확인" />
<span id="에이전트-호출-테스트" />
<span id="문제-해결" />
<span id="uvx-명령을-찾을-수-없음" />
<span id="mcp-서버-타임아웃" />
<span id="aws-자격-증명-오류" />


# aws-ops-plugin 설치

## Claude Code {#claude-code}

```text
/plugin marketplace add Atom-oh/oh-my-cloud-skills
/plugin install aws-ops-plugin@oh-my-cloud-skills
```

저장소 체크아웃에서 로컬로 개발할 때는 다음과 같이 실행합니다:

```bash
claude --plugin-dir ./plugins/aws-ops-plugin
```

## Codex {#codex}

플러그인을 지원하는 Codex CLI에서 마켓플레이스를 등록합니다:

```bash
codex plugin marketplace add Atom-oh/oh-my-cloud-skills
```

`/plugins`를 열어 `aws-ops-plugin`을 설치하고 새 스레드를 시작합니다. 설치된 스킬을 선택하거나 원하는 작업을 설명합니다. 이 패키지는 `.codex-plugin/skills/`를 통해 스킬과 전문가 절차를 제공하며 별도 `commands/` 목록은 포함하지 않습니다. 위의 `/plugin` 명령은 Claude Code 설치를 관리합니다.

## 설정 및 검증 {#setup-and-verification}

매니페스트에 정의된 MCP 서버를 위해 Python/uvx를 준비하고 대상 계정과 리전에 맞게 AWS CLI 인증을 설정합니다. EKS 작업에는 kubectl과 올바른 컨텍스트도 필요합니다. 운영 작업을 요청하기 전에 로컬에서 자격 증명과 서버 상태를 확인합니다.

소스 체크아웃에서는 저장소 루트에서 두 호스트의 패키지를 검증합니다:

```bash
python3 scripts/test-plugins.py
python3 scripts/test-codex-plugins.py
```

예상한 항목이 없으면 플러그인 매니페스트와 생성된 오버레이를 확인합니다. 설치 성공만으로 외부 자격 증명, 다른 AI의 CLI 또는 클라우드 권한이 정상 작동한다고 판단하지 않습니다.

## 제거 {#remove}

Claude Code에서는 `/plugin uninstall aws-ops-plugin@oh-my-cloud-skills`를 사용하고, Codex에서는 `/plugins`에서 해당 항목을 제거합니다.
