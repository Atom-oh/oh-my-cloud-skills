---
sidebar_position: 2
title: "kiro-power-converter 설치"
---

{/* 영문 개편 이전의 섹션 링크를 유지합니다. */}
<span id="kiro-power-converter-설치" />
<span id="마켓플레이스-설치" />
<span id="로컬-로딩" />
<span id="설치-확인" />
<span id="매니페스트-검증" />
<span id="파일-참조-검증" />
<span id="플러그인-구조" />
<span id="자동-호출-키워드" />


# kiro-power-converter 설치

## Claude Code {#claude-code}

```text
/plugin marketplace add Atom-oh/oh-my-cloud-skills
/plugin install kiro-power-converter@oh-my-cloud-skills
```

저장소 체크아웃에서 로컬로 개발할 때는 다음과 같이 실행합니다:

```bash
claude --plugin-dir ./plugins/kiro-power-converter
```

## Codex {#codex}

`/plugins`를 사용해 이 저장소의 Codex 마켓플레이스에서 `kiro-power-converter`를 설치한 뒤 새 스레드를 시작합니다. 패키지는 생성된 `.codex-plugin/skills/` 항목을 불러옵니다. 설치된 스킬 선택기를 사용하거나 원하는 작업을 설명합니다. 이 가이드의 슬래시 명령은 대응하는 Claude 워크플로의 이름입니다.

## 설정 및 검증 {#setup-and-verification}

변환기는 Python으로 실행하며 GitHub 입력에는 git이 필요합니다. Codex에서 변환기를 호출하더라도 로컬 플러그인에는 `.claude-plugin/plugin.json`이 반드시 있어야 합니다.

소스 체크아웃에서는 저장소 루트에서 두 호스트의 패키지를 검증합니다:

```bash
python3 scripts/test-plugins.py
python3 scripts/test-codex-plugins.py
```

예상한 항목이 없으면 플러그인 매니페스트와 생성된 오버레이를 확인합니다. 설치 성공만으로 외부 자격 증명, 다른 AI의 CLI 또는 클라우드 권한이 정상 작동한다고 판단하지 않습니다.

## 제거 {#remove}

Claude Code에서는 `/plugin uninstall kiro-power-converter@oh-my-cloud-skills`를 사용하고, Codex에서는 `/plugins`에서 해당 항목을 제거합니다.
