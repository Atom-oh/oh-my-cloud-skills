---
sidebar_position: 8
title: "Brochure Agent"
---

# Brochure Agent

AWS 솔루션·제품을 위한 **단일 페이지 반응형 온라인 브로셔(랜딩 페이지)**를 자기완결 HTML 한
파일로 만들고 GitHub Pages로 공개 배포하는 전문 에이전트입니다. 히어로 + 가치 + 기능 +
임베드 아키텍처 다이어그램 + CTA로 구성된 한 스크롤 페이지를 생성합니다.

## 기본 정보

| 항목 | 값 |
|------|-----|
| **도구** | Read, Write, Edit, Glob, Grep, Bash, AskUserQuestion |
| **모델** | sonnet |
| **연동 스킬** | `brochure`, `architecture-diagram` |
| **출력물** | 자기완결 `.html` (CSS 인라인) + 아키텍처 `.svg` |

## 트리거 키워드

- "brochure", "online brochure", "landing page", "marketing one-pager"
- "product overview page", "solution showcase"
- "브로셔", "브로셔 만들어", "온라인 브로셔", "랜딩 페이지", "소개 페이지"

## 대상과 경계

브로셔는 **이중 독자(의사결정자 + 엔지니어)를 위한 설득 + 명료성**입니다. 의사결정자는 가치를
몇 초 만에 파악하고, 엔지니어는 페이지를 떠나지 않고 기능·아키텍처를 파고들 수 있어야 합니다.
한 스크롤 — 슬라이드 덱도, 문서 사이트도 아닙니다.

| 상황 | 사용 |
|------|------|
| 제품/솔루션 랜딩 페이지, 한 페이지 개요, 공개 쇼케이스 | **brochure** (이 에이전트) |
| 슬라이드 덱 / 발표 / 교육 | `reactive-presentation-agent` |
| 다중 페이지 문서 사이트 | `gitbook-agent` |

## 필수 규칙

1. **사실 우선** — 작성 전 제품 사실(핵심 메시지·지표·기능·아키텍처)을 repo/README/사용자에서 확보. 지표·기능 수·서비스명을 지어내지 않음.
2. **자기완결 HTML** — 단일 `.html`, CSS는 `<style>` 인라인. 폰트 CDN은 system 폴백 필수. 빌드 도구·프레임워크 금지.
3. **3-tier 반응형** — 모바일(~375px)·태블릿(~768px)·PC(~1280px) 검증. 모바일에서 표는 카드로 재배치.
4. **접근성** — skip-link, `:focus-visible`, `prefers-reduced-motion`, WCAG-AA 대비.
5. **다이어그램 일관성** — 아키텍처는 `architecture-diagram` 스킬로 생성(SVG 임베드), 카피와 동일한 컴포넌트·수치 유지.

## 워크플로우

```
brochure-agent → 제품 사실 수집 → (architecture-diagram 스킬 → SVG)
  → 자기완결 HTML 작성 → 자기검증 스크립트 → content-review-agent (≥85)
  → GitHub Pages 공개 배포
```
