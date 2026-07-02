---
sidebar_position: 1
title: Remarp 소개
---

# Remarp 소개

Remarp는 **reactive-presentation** 프레임워크를 위한 차세대 마크다운 포맷입니다. 사람이 읽고 편집할 수 있는 `.md` 파일 하나가 프레젠테이션의 **단일 소스**가 됩니다.

:::tip 파일 확장자
`.md` 확장자를 사용하고 frontmatter에 `remarp: true`를 추가합니다. 이전의 `.remarp.md` 확장자도 하위호환 지원됩니다.
:::

## 왜 Remarp인가?

기존 프레젠테이션 제작 방식에는 각각 장단점이 있습니다:

- **Marp**: 마크다운 기반으로 편집이 쉽지만, 애니메이션이나 인터랙티브 기능이 제한적
- **JSON + Renderer**: 인터랙티브 기능은 강력하지만, JSON을 직접 편집하기 어려움

Remarp는 두 방식의 장점을 결합합니다.

## 비교표

| 항목 | Marp (기존) | JSON+Renderer | **Remarp (신규)** |
|---|---|---|---|
| 소스 포맷 | Markdown | JSON | **Markdown** |
| 사람이 읽기 | 쉬움 | 어려움 | **쉬움** |
| 프래그먼트 애니메이션 | 불가 | 수동 HTML | **`{.click}` 한 줄** |
| Canvas 애니메이션 | 불가 (수동 JS) | 별도 JS 모듈 | **`:::canvas` DSL** |
| 인터랙티브 패턴 | 불가 | 수동 구현 | **`:::html` + `:::script`** |
| 스피커 노트 | `<!-- notes: -->` | JSON 필드 | **`:::notes` + 타이밍/큐** |
| 컬럼 레이아웃 | 불가 | 수동 HTML | **`::: left`/`::: right`** |
| 슬라이드 전환 효과 | 불가 | 불가 | **`@transition fade`** |
| 키보드 커스텀 | 불가 | 불가 | **`keys:` frontmatter** |
| 블록별 증분 빌드 | 불가 | 해당 없음 | **`sync` 명령** |
| 비주얼 편집 | 불가 | 불가 | **VSCode Visual Edit** |
| Canvas 비주얼 편집 | 불가 | 불가 | **VSCode Canvas Editor** |
| 하위 호환 | - | - | **`marp: true` 지원** |

## 핵심 장점

### 1. 사람이 읽을 수 있는 마크다운

Remarp 파일은 일반 마크다운처럼 읽고 편집할 수 있습니다. 복잡한 JSON 구조나 HTML 태그 없이도 풍부한 프레젠테이션을 만들 수 있습니다.

### 2. 프래그먼트 애니메이션

클릭할 때마다 요소가 순차적으로 나타나는 애니메이션을 `{.click}` 한 줄로 구현합니다:

```markdown
- 첫 번째 포인트{.click}
- 두 번째 포인트{.click}
- 세 번째 포인트{.click animation=fade-up}
```

### 3. Canvas DSL

복잡한 아키텍처 다이어그램을 코드로 작성할 수 있습니다:

```markdown
:::canvas width=960 height=400
box apigw "API GW" at 50,170 size 130,60 color #FF9900
box lambda "Lambda" at 260,170 size 130,60 color #4CAF50
arrow apigw -> lambda "invoke" step 1
:::
```

### 4. 스피커 노트 + 타이밍

발표자 노트에 타이밍과 큐 마커를 추가할 수 있습니다:

```markdown
:::notes
{timing: 3min}
**핵심 포인트** 설명.
{cue: demo} 대시보드 보여주기.
{cue: question} "경험 있으신 분?"
:::
```

### 5. PPTX 테마 통합

기업 PPTX 템플릿에서 색상, 로고, 폰트를 자동으로 추출하여 적용합니다:

```yaml
theme:
  source: "./company-template.pptx"
  footer: auto
  logo: auto
```

### 6. 멀티파일 프로젝트

30분 이상의 긴 세션은 블록별로 파일을 분리하여 관리할 수 있습니다:

```
aws-scaling/
├── _presentation.md          # 글로벌 설정
├── 01-fundamentals.md        # Block 1
├── 02-advanced.md            # Block 2
└── build/                    # 생성된 HTML
```

### 7. 인터랙티브 패턴

슬라이더, 계산기, 시뮬레이터 등 복잡한 인터랙션은 `:::html` + `:::script` 블록으로 구현합니다:

```markdown
:::html
<div class="slider-group">
  <input type="range" id="cpu" min="50" max="2000" value="250">
  <span id="cpu-val">250m</span>
</div>
:::

:::script
document.getElementById('cpu').oninput = e => {
  document.getElementById('cpu-val').textContent = e.target.value + 'm';
};
:::
```

### 8. VSCode Visual Edit

Remarp VSCode 확장의 Visual Edit 모드로 슬라이드를 직접 드래그/리사이즈할 수 있습니다:

- 요소 드래그 -> 소스 `.md`의 `:::css` 블록에 자동 반영 (CSS Writeback)
- Canvas 요소 이동 -> `:::canvas` DSL 좌표 자동 업데이트 (Canvas Writeback)
- 화살표 waypoint 편집 -> 경로 조정
- Property Panel -> 선택한 요소의 폰트, 색상, 여백 등 속성 편집
- 실시간 양방향 동기화

## 하위 호환성

기존 `marp: true` 파일도 Remarp 파서가 그대로 처리합니다. 점진적으로 Remarp 기능을 도입할 수 있습니다.

## 다음 단계

- [빠른 시작](./quick-start.md)으로 5분 만에 첫 프레젠테이션 만들기
- [Frontmatter](./syntax/frontmatter.md)로 프레젠테이션 설정 알아보기
- [VSCode 확장](./vscode-extension.md)으로 편집 환경 구성하기
- [Canvas DSL](./syntax/canvas-dsl.md)로 다이어그램 작성하기
