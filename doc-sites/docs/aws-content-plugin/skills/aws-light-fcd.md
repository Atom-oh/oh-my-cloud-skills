---
sidebar_position: 8
title: "AWS Light FCD (Native PPTX)"
---

# AWS Light FCD Skill

**AWS Light 테마 PowerPoint(.pptx)**를 PptxGenJS로 직접 생성하는 네이티브 PPTX 스킬. 실제 AWS Korea 고객 발표자료에서 추출한 디자인 시스템을 그대로 사용합니다 — Pretendard 타이포그래피, 화이트 캔버스, 시그니처 purple→blue→green 그라디언트. 모든 레이아웃은 이미 시각적으로 검증되었습니다.

## 트리거 키워드

- "AWS 라이트 deck", "AWS 슬라이드 만들어줘", "PPTX 만들어줘"
- "Bedrock 발표자료", "AgentCore 슬라이드", "AWS 고객 브리핑"
- Amazon Bedrock, AgentCore, EKS, SageMaker, AWS 아키텍처 다이어그램 관련 요청

## 언제 이 스킬을 쓰나 (그리고 안 쓰나)

| 필요 | 사용 |
|------|------|
| **네이티브 PPTX(.pptx)** 발표자료 — 파워포인트로 편집·발표 | **aws-light-fcd** (이 스킬) |
| 웹/HTML 인터랙티브 슬라이드 | `reactive-presentation` |
| PPTX ↔ 웹 슬라이드 자동 선택 | `presentation-agent` 디스패처가 라우팅 |

`presentation-agent` 디스패처가 "pptx/파워포인트/ppt" 키워드나 사용자의 PPTX 선택을 감지하면 이 스킬로 라우팅합니다. python-pptx를 직접 쓰지 말고 이 스킬을 호출하세요.

## 제공 자산

- 공유 kit (`scripts/deck_kit.js`) — 디자인 토큰 + 4개 레이아웃 빌더(`cover`, `agenda`, `agentcoreCards`, `bigStat`) + 푸터/로고 헬퍼
- 아키텍처 다이어그램 kit (`scripts/arch_kit.js`) — `groupBox`, `svc`, `stepMarker`, `arrow`, `stepLegend` 프리미티브 + react-icon 렌더러
- 번들 아이콘: AgentCore 11개 + AWS 서비스 10개(`assets/icons/`), AWS 로고, 배경 이미지(`assets/backgrounds/`)
- **AWS Architecture Icons 811개 전체**를 `kit.icon("<Name>")`으로 사용 — sibling `reactive-presentation` 스킬의 아이콘 라이브러리를 **제자리에서 공유**(복제 없음)

## 워크플로우

```
소스 문서 읽기 → 프레젠터/언어/슬라이드 수 확인 → layouts.md로 레이아웃 선택
  → build.js 작성(deck_kit.js 호출) → node build.js 실행
  → PDF→JPG QA (오버플로/겹침 확인) → embed_fonts.py로 폰트 임베드
  → .pptx 전달
```

| 단계 | 내용 |
|------|------|
| 1. 소스 읽기 | md/txt/pptx/docx에서 섹션 맵 구성 |
| 2. 확인 | 프레젠터(기본값 있음)·언어·슬라이드 수 — 과도하게 되묻지 않고 기본값으로 진행 |
| 3. 레이아웃 선택 | `references/layouts.md`(레이아웃), `references/icons.md`(아이콘명) 참조 |
| 4. 빌드 스크립트 작성 | `NODE_PATH=$(npm root -g) node build.js`로 실행 |
| 5. QA | PDF→JPG 변환 후 시각 검수, 오버플로/겹침 수정 |
| 6. 폰트 임베드 | `python scripts/embed_fonts.py your_deck.pptx` — Pretendard 어디서나 동일 렌더 보장 |
| 7. 전달 | `.pptx`를 출력 위치로 이동 |

완전한 동작 예시는 `scripts/demo_build.js`에 있습니다 — 5개 레이아웃을 모두 사용하는 가장 빠른 학습 경로입니다.

## 핵심 규칙 (NON-NEGOTIABLE)

1. **폰트는 Pretendard만.** 폴백 없음.
2. **16:9 전용** — kit이 `W16x9`(13.333 × 7.5)를 정의.
3. **그라디언트는 이미지/도형에만** — 시그니처 그라디언트(`AD5CFF→41B3FF→00E500`)는 pill 헤더 등에만 쓰고 **텍스트에는 절대 사용 안 함**. 큰 숫자/헤딩은 솔리드 컬러.
4. **모든 콘텐츠 슬라이드에 푸터** — 저작권(좌) + 작은 AWS 로고 + 페이지 번호(우). 커버는 큰 로고 + 작은 푸터 로고 없음.
5. **아젠다는 콘텐츠 챕터만** — "다음 단계/PoC/워크샵 제안/감사합니다" 같은 클로징 항목을 아젠다에 자동 삽입하지 않음.

## 제공 자산 위치

| 종류 | 경로 |
|------|------|
| Deck kit | `scripts/deck_kit.js` |
| Architecture kit | `scripts/arch_kit.js` |
| 레이아웃 참조 | `references/layouts.md` |
| 아이콘 참조 | `references/icons.md` |
| 폰트 임베드 | `scripts/embed_fonts.py` |
| 데모 빌드 | `scripts/demo_build.js` |
