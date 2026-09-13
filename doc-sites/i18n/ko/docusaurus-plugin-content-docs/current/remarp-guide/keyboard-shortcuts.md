---
sidebar_position: 13
title: "키보드 단축키"
---

{/* 영문 개편 전의 기존 섹션 링크를 유지합니다. */}
<span id="키보드-단축키" />
<span id="기본-네비게이션" />
<span id="프래그먼트--스텝" />
<span id="인터랙티브-슬라이드" />
<span id="뷰-모드" />
<span id="프레젠터-뷰" />
<span id="오버뷰-모드" />
<span id="터치-제스처-모바일" />
<span id="키보드-커스터마이징" />
<span id="커스터마이즈-가능한-키" />
<span id="퀵-레퍼런스" />
<span id="발표-시작-전" />
<span id="발표-중" />
<span id="네비게이션" />


# 키보드 단축키

아래 기본값은 현재 `SlideFramework.getKeyAction()` 구현을 기준으로 합니다. 덱에서 자체 키·동작 매핑으로 재정의할 수 있습니다.

| 키 | 동작 |
| --- | --- |
| Right, Space, PageDown | 다음 내용을 단계별로 표시한 뒤 다음 슬라이드로 이동 |
| Left, PageUp | 지원되는 경우 이전 단계의 내용을 숨긴 뒤 이전 슬라이드로 이동 |
| Down / Up | 등록된 슬라이드 동작, 상호작용 항목 순환, 단계별 표시·슬라이드 탐색 순서로 처리 |
| Home / End | 첫 / 마지막 슬라이드 |
| P | 발표자 보기 열기 |
| F | 전체 화면 전환 |
| O | 전체 보기 전환 |
| S | 전체 화면이 아닐 때 사이드바 전환 |
| Escape | 전체 보기 또는 전체 화면 종료 |

input이나 textarea에 입력하는 동안에는 덱 탐색이 실행되지 않습니다. 덱을 터치 스와이프하여 이전·다음으로 이동할 수 있습니다. Compare/tabs/Canvas 동작은 해당 슬라이드에 등록된 상호작용에 따라 달라집니다.

## 사용자 지정 매핑 {#custom-mappings}

```yaml
keys:
  n: next
  Backspace: prev
```

런타임은 키·동작 매핑 객체를 읽습니다. 탐색 분기문에 구현된 동작만 지원합니다. 현재 기본 매핑에는 숫자 키, 노트 패널용 N, 화면 암전용 B가 연결되어 있지 않습니다. 이를 나열한 과거 예제는 현재 런타임 명세가 아닙니다.

## 발표자 보기와 전체 보기 {#presenter-and-overview}

보조 화면으로 발표하기 전에 P를 눌러 창 동기화를 확인합니다. O를 눌러 전체 보기를 열고 이동할 슬라이드를 선택합니다. 특히 기본 키를 바꾸는 경우에는 실제 생성된 덱에서 사용자 지정 키 매핑을 테스트합니다.

[런타임 키 매핑](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-content-plugin/skills/reactive-presentation/assets/slide-framework.js)
