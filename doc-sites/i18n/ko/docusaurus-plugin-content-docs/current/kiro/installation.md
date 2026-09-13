---
sidebar_position: 2
title: "kiro 설치"
---

{/* 영문 개편 이전의 섹션 링크를 유지합니다. */}
<span id="설치" />
<span id="marketplace에서-설치" />
<span id="로컬에서-직접-로드" />
<span id="사전-요구사항-필수" />
<span id="첫-실행-kirosetup" />
<span id="제거" />


# kiro 설치

## Claude Code {#claude-code}

```text
/plugin marketplace add Atom-oh/oh-my-cloud-skills
/plugin install kiro@oh-my-cloud-skills
```

저장소 체크아웃에서 로컬로 개발할 때는 다음과 같이 실행합니다:

```bash
claude --plugin-dir ./plugins/kiro
```

## Codex {#codex}

`/plugins`를 사용해 이 저장소의 Codex 마켓플레이스에서 `kiro`를 설치한 뒤 새 스레드를 시작합니다. 패키지는 생성된 `.codex-plugin/skills/` 항목을 불러옵니다. 설치된 스킬 선택기를 사용하거나 원하는 작업을 설명합니다. 이 가이드의 슬래시 명령은 대응하는 Claude 워크플로의 이름입니다.

## 설정 및 검증 {#setup-and-verification}

`kiro-cli`를 설치하고 인증한 뒤 `/kiro:setup`을 실행합니다. 설정 절차는 CLI를 시험하고 로컬 에이전트를 준비합니다. 위임, 커밋·푸시 검토 훅, 웹 검색, 셸 실행은 각각 별도의 설정을 사용합니다. 자동 동작을 켜기 전에 이 설정을 확인합니다.

소스 체크아웃에서는 저장소 루트에서 두 호스트의 패키지를 검증합니다:

```bash
python3 scripts/test-plugins.py
python3 scripts/test-codex-plugins.py
```

예상한 항목이 없으면 플러그인 매니페스트와 생성된 오버레이를 확인합니다. 설치 성공만으로 외부 자격 증명, 다른 AI의 CLI 또는 클라우드 권한이 정상 작동한다고 판단하지 않습니다.

## 제거 {#remove}

Claude Code에서는 `/plugin uninstall kiro@oh-my-cloud-skills`를 사용하고, Codex에서는 `/plugins`에서 해당 항목을 제거합니다.

## 관련 링크 {#related-links}

- [kiro.dev](https://kiro.dev)
