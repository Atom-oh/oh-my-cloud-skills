---
sidebar_position: 2
title: "co-agent 설치"
---

{/* 영문 개편 이전의 섹션 링크를 유지합니다. */}
<span id="설치" />
<span id="marketplace에서-설치" />
<span id="로컬에서-직접-로드" />
<span id="사전-요구사항-선택적--있는-것만-사용" />
<span id="제거" />


# co-agent 설치

## Claude Code {#claude-code}

```text
/plugin marketplace add Atom-oh/oh-my-cloud-skills
/plugin install co-agent@oh-my-cloud-skills
```

저장소 체크아웃에서 로컬로 개발할 때는 다음과 같이 실행합니다:

```bash
claude --plugin-dir ./plugins/co-agent
```

## Codex {#codex}

`/plugins`를 사용해 이 저장소의 Codex 마켓플레이스에서 `co-agent`를 설치한 뒤 새 스레드를 시작합니다. 패키지는 생성된 `.codex-plugin/skills/` 항목을 불러옵니다. 설치된 스킬 선택기를 사용하거나 원하는 작업을 설명합니다. 이 가이드의 슬래시 명령은 대응하는 Claude 워크플로의 이름입니다.

## 설정 및 검증 {#setup-and-verification}

1.x에서 업그레이드할 때는 [v2.0.0 마이그레이션 가이드](/docs/releases/v2.0.0#co-agent-migration)에 따라
지원 종료된 Antigravity 설정을 제거하고 지원되는 외부 AI를 선택합니다.

`/co-agent:setup`을 실행해 설치된 외부 AI를 시험하고 준비 상태를 기록합니다. review, decide, ADR 작업은 사용 가능한 외부 AI가 없을 때 명확히 안내한 뒤 단독 진행할 수 있습니다. consensus와 harness에는 READY 외부 AI가 필요합니다.

소스 체크아웃에서는 저장소 루트에서 두 호스트의 패키지를 검증합니다:

```bash
python3 scripts/test-plugins.py
python3 scripts/test-codex-plugins.py
```

예상한 항목이 없으면 플러그인 매니페스트와 생성된 오버레이를 확인합니다. 설치 성공만으로 외부 자격 증명, 다른 AI의 CLI 또는 클라우드 권한이 정상 작동한다고 판단하지 않습니다.

## 제거 {#remove}

Claude Code에서는 `/plugin uninstall co-agent@oh-my-cloud-skills`를 사용하고, Codex에서는 `/plugins`에서 해당 항목을 제거합니다.
