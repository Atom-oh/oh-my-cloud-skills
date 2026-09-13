---
sidebar_position: 8
title: "AWS 라이트 PowerPoint 스킬"
---

# AWS 라이트 PowerPoint 스킬

{/* 영문 개편 전의 기존 섹션 링크를 유지합니다. */}
<span id="aws-light-fcd-skill" />
<span id="트리거-키워드" />
<span id="언제-이-스킬을-쓰나-그리고-안-쓰나" />
<span id="제공-자산" />
<span id="워크플로우" />
<span id="핵심-규칙-non-negotiable" />
<span id="제공-자산-위치" />

제공된 AWS 라이트 테마, Pretendard 글꼴, 그라데이션 강조, 재사용 가능한 레이아웃과 AWS/AgentCore 아이콘 도구로 기본 개체를 편집할 수 있는 PowerPoint 덱을 만듭니다.

## 이 작업 흐름을 사용하는 경우 {#use-this-workflow}

편집 가능한 AWS 라이트 `.pptx`가 필요할 때 이 스킬을 선택합니다. 인터랙티브 웹 슬라이드가 필요하면 reactive-presentation을 사용하고, 원하는 결과물이 슬라이드 캡처라면 해당 스킬의 스크린샷 기반 내보내기를 사용합니다.

## 빌드 {#build}

키트와 참고 레이아웃을 확인하고 일관된 발표 흐름을 계획합니다. 편집이 필요한 부분에는 기본 PowerPoint 도형·텍스트를 사용하고 `kit.icon()`으로 아이콘을 불러옵니다. 슬라이드 레이아웃을 확인한 뒤 제공된 도구로 빌드하고 글꼴을 포함합니다.

준비된 덱 작업 공간에서 실행합니다. 도구가 제공된 글꼴에 접근할 수 있도록
`PPTX_SKILL`을 실제 설치된 `aws-light-fcd` 디렉터리로 지정합니다.

```bash
PPTX_SKILL="/absolute/path/to/installed/plugin/skills/aws-light-fcd"
NODE_PATH=$(npm root -g) node build.js
python3 "$PPTX_SKILL/scripts/check_pptx.py" deck.pptx
python3 "$PPTX_SKILL/scripts/embed_fonts.py" deck.pptx
```

작업 공간에는 생성된 `build.js`가 있습니다. 글꼴 도구를 다른 위치에 복사했다면
제공된 글꼴 디렉터리를 `--fonts-dir`로 지정합니다. 스크립트만 복사하면 기본
`assets/fonts` 경로를 찾을 수 없습니다. 글꼴을 포함하기 전에 `check_pptx.py`
점수가 80 이상이고 `[geometry]` 지적이 없는지 확인합니다. 게시 전 콘텐츠 리뷰도 필요합니다.

## 에셋과 검증 {#assets-and-verification}

키트는 표지, 목차, 통계, AgentCore 카드와 아키텍처 레이아웃을 제공합니다. `kit.icon()`은 같은 플러그인의 reactive-presentation 아이콘 라이브러리를 사용하도록 설계되어 있습니다. 편집 가능한 개체를 정렬하고 기준 에셋을 사용하며 내보낸 슬라이드를 확인한 뒤 게시 전에 콘텐츠 리뷰를 수행합니다.


[스킬, 리소스와 품질 요구 사항](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-content-plugin/skills/aws-light-fcd/SKILL.md)
