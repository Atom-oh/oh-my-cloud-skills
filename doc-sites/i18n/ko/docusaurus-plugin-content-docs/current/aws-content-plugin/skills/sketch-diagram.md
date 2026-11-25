---
sidebar_position: 9
title: "스케치 다이어그램 스킬"
---

# 스케치 다이어그램 스킬

슬라이드 도입부나 쉬운 설명에 쓰는 가벼운 손그림 스타일의 움직이는 개념도를 만듭니다. 일렁이는 잉크 선, 옅은 색 바탕, 낙서 아이콘, 실제 흐름을 따라 움직이는 작은 점으로 구성됩니다.

## 사용 시점 {#when-to-use-it}

섹션의 첫 그림으로, 청중이 전체 아이디어를 한눈에 봐야 할 때 씁니다. 순환 구조, 파이프라인, 허브와 스포크, 비교, 타임라인이 대상입니다. 정확한 AWS 경계와 공식 아이콘이 필요하면 architecture-diagram이나 animated-diagram을 쓰고, 키를 누를 때마다 한 단계씩 진행하는 설명에는 [line-art-scene](/docs/aws-content-plugin/skills/line-art-scene)을 씁니다.

## 만들어지는 결과 {#what-it-produces}

자체 완결형 블록 하나입니다. `<style>` 요소와, 흐름을 한 문장으로 설명하는 `aria-label`이 붙은 인라인 SVG로 이루어집니다. 손그림 느낌은 공유 SVG 변위 필터와 살짝 휜 경로에서 나오고, 색은 덱의 테마 토큰을 써서 라이트와 다크 테마에서 모두 읽힙니다.

## 읽기 쉽게 유지하는 규칙 {#rules-that-keep-it-readable}

기본값인 상자 한 줄 대신 주제의 자연스러운 모양에서 레이아웃을 고릅니다. 먼저 흐름을 한 문장으로 쓰고(무엇이 움직이고 어디서 갈라지고 합쳐지고 되돌아가는지), 그 흐름이 지나는 모든 경로에 움직이는 점을 둡니다. 라벨은 짧게, 카드마다 낙서 아이콘은 하나, 반짝임은 몇 개만 씁니다. `prefers-reduced-motion`에서는 애니메이션이 꺼지고 정지 그림만으로도 완전해야 합니다.

## 삽입과 검증 {#embed-and-verify}

스타일과 SVG를 Remarp 슬라이드의 `:::html` 블록 하나에 함께 넣습니다. `:::css` 블록은 슬라이드별 대상 재정의만 받고 일반 규칙을 버리므로 여기에는 쓰지 않습니다. 덱을 검증하고 두 테마에서 결과를 열어 본 뒤, 발표자 노트는 발표자가 말하듯 자연스러운 어투로 씁니다.

[스킬, 레이아웃, 레시피, 템플릿](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-content-plugin/skills/sketch-diagram/SKILL.md)
