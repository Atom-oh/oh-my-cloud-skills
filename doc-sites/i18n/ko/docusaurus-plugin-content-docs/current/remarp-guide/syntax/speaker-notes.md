---
sidebar_position: 6
title: "발표자 노트"
---

{/* 영문 개편 전의 기존 섹션 링크를 유지합니다. */}
<span id="발표자-노트" />
<span id="기본-문법" />
<span id="타이밍-마커" />
<span id="큐-마커" />
<span id="큐-타입-레퍼런스" />
<span id="노트-작성-가이드라인" />
<span id="권장-사항" />
<span id="품질-기준-필수" />
<span id="모범-사례" />
<span id="프레젠터-뷰" />
<span id="프레젠터-뷰-구성" />
<span id="레이아웃-조절" />
<span id="슬라이드와-동기화" />
<span id="전체-예제" />


# 발표자 노트

발표 안내를 `:::notes`에 작성합니다. 청중용 슬라이드가 아닌 발표자 보기에서 확인할 수 있습니다.

```markdown
:::notes
{timing: 3min}
[요약]
- Explain the decision.
- Connect it to the measured evidence.
- Identify the remaining limitation.

Start by describing the observed failure and why it matters to the user.
Walk through the evidence supporting the selected fix, then explain what
its verification covers and which conditions still require follow-up.
{cue: question}
Ask which assumption the audience would test next.
{cue: transition}
Move to the example that exercises that assumption.
:::
```

## 정확한 표시와 언어 {#exact-marker-and-language}

현재 검증기는 해당 콘텐츠 슬라이드에서 요약을 뜻하는 리터럴 `[요약]` 표시를 찾습니다. 영어 덱에서도 이 문법을 유지합니다. 목록과 발표 대본은 요청된 발표 언어로 작성하되, 파서가 요구하는 리터럴을 지원되지 않는 별칭으로 번역하지 않습니다.

## 시간과 진행 안내 {#timing-and-cues}

`{timing: 3min}` 또는 `{timing: 90s}`를 사용합니다. `{cue: demo}`, `{cue: pause}`, `{cue: question}`, `{cue: transition}`, `{cue: poll}`, `{cue: break}` 같은 표시로 발표 진행 동작을 지정합니다. 슬라이드 내용을 반복하기보다 실무적 의미와 다음 내용으로의 전환을 설명합니다.

## 검증 {#validation}

소스 검증기는 노트 누락, 짧은 노트와 구조가 없는 노트를 구분하고 슬라이드 유형별 면제 규칙을 적용합니다. 안내에서는 150자 이상을 권장하며 필요하면 더 자세히 작성하도록 합니다. 정확한 심각도 기준은 검증기에 정의되어 있습니다. 소스 검증과 독립적인 콘텐츠 리뷰 점수는 구분합니다.

## 발표자 보기 {#presenter-view}

P를 누르면 현재·다음 슬라이드, 노트, 시간과 탐색 기능을 갖춘 별도 보기가 열립니다. 분할선을 조절해 슬라이드·노트 영역의 크기를 바꾸면 비율이 로컬에 저장됩니다. 발표자 창과 기본 창은 프레임워크의 채널로 동기화되므로 실제 생성된 덱에서 동작을 테스트합니다.

[노트 검증 규칙](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py)
