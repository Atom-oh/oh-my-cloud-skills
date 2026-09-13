---
sidebar_position: 3
title: "aws-content-plugin 설치"
---

{/* 영문 개편 전의 기존 섹션 링크를 유지합니다. */}
<span id="설치" />
<span id="marketplace-설치" />
<span id="로컬-로딩" />
<span id="설치-확인" />
<span id="파일-참조-확인" />
<span id="플러그인-구조" />
<span id="자동-호출" />
<span id="다음-단계" />


# aws-content-plugin 설치

## Claude Code {#claude-code}

```text
/plugin marketplace add Atom-oh/oh-my-cloud-skills
/plugin install aws-content-plugin@oh-my-cloud-skills
```

저장소 체크아웃에서 로컬 개발을 진행할 때는 다음 명령을 사용합니다.

```bash
claude --plugin-dir ./plugins/aws-content-plugin
```

## Codex {#codex}

플러그인을 지원하는 Codex CLI에 마켓플레이스를 등록합니다.

```bash
codex plugin marketplace add Atom-oh/oh-my-cloud-skills
```

`/plugins`를 열어 `aws-content-plugin`을 설치하고 새 스레드를 시작합니다. 설치된 스킬을 선택하거나 원하는 작업을 설명합니다. 이 패키지는 `.codex-plugin/skills/`를 통해 스킬과 전문 에이전트 절차를 제공하며, 별도의 `commands/` 목록은 포함하지 않습니다. 위의 `/plugin` 명령은 Claude Code 설치를 관리합니다.

## 설정과 검증 {#setup-and-verification}

매니페스트에는 렌더링된 콘텐츠 검사용 Playwright가 포함되어 있습니다. 선택한 결과물에 필요한 로컬 도구만 설치합니다. 예를 들어 Python, 다이어그램 내보내기용 Draw.io, 기본 PowerPoint 제작용 Node/PptxGenJS와 문서에 명시된 글꼴 도구를 사용합니다.

소스를 체크아웃한 경우 저장소 루트에서 두 호스트 패키지를 검증합니다.

```bash
python3 scripts/test-plugins.py
python3 scripts/test-codex-plugins.py
```

예상한 항목이 없으면 플러그인 매니페스트와 생성된 오버레이를 확인합니다. 설치 성공만으로 외부 자격 증명, 피어 CLI나 클라우드 권한이 작동한다고 판단하지 않습니다.

## 제거 {#remove}

Claude Code에서는 `/plugin uninstall aws-content-plugin@oh-my-cloud-skills`을 실행하고, Codex에서는 `/plugins`에서 해당 항목을 제거합니다.

## 관련 링크 {#related-links}

- [프레젠테이션 에이전트](./agents/presentation-agent)
- [아키텍처 다이어그램 에이전트](./agents/architecture-diagram-agent)
- [콘텐츠 리뷰 에이전트](./agents/content-review-agent)
