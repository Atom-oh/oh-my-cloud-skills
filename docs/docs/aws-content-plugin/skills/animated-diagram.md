---
sidebar_position: 3
title: "Animated Diagram"
---

# Animated Diagram Skill

SVG와 SMIL 애니메이션을 사용한 동적 애니메이션 다이어그램을 생성하는 스킬입니다. 트래픽 흐름 시각화, 펄싱 효과, 인터랙티브 범례, 반응형 스케일링이 포함된 자체 완결형 HTML 파일을 생성합니다.

## 트리거 키워드

다음 키워드로 활성화됩니다:
- "animated diagram", "traffic flow"
- "animated architecture", "dynamic diagram"
- "SMIL animation"

## 사용 케이스

- AWS 서비스를 통한 요청 경로 트래픽 흐름 시각화
- 애니메이션 연결이 있는 서비스 인터랙션 다이어그램
- 단계별 애니메이션이 있는 배포 파이프라인
- 애니메이션 상태 표시기가 있는 실시간 모니터링 대시보드

## 제공 리소스

### references/

| 참조 문서 | 설명 |
|----------|------|
| `smil-animation-guide.md` | SMIL 애니메이션 문법과 패턴 |
| `aws-diagram-patterns.md` | AWS 아키텍처 색상 코딩 및 레이아웃 규약 |

### templates/

| 템플릿 | 설명 |
|--------|------|
| `traffic-flow.html` | 모든 패턴이 포함된 완전한 트래픽 흐름 템플릿 |

## 아키텍처

각 애니메이션 다이어그램은 3개 레이어로 구성된 자체 완결형 HTML 파일입니다:

```
┌─────────────────────────────────────────────┐
│              HTML Wrapper                    │
│  ┌───────────────────────────────────────┐  │
│  │         Background Layer              │  │
│  │   (Draw.io PNG or inline SVG)         │  │
│  ├───────────────────────────────────────┤  │
│  │         Animation Layer               │  │
│  │   (SVG with SMIL animations)          │  │
│  ├───────────────────────────────────────┤  │
│  │         Interactive Legend             │  │
│  │   (JS toggle for animation groups)    │  │
│  └───────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
```

## 색상 표준

| 트래픽 타입 | 색상 | Hex |
|-------------|------|-----|
| Outbound | Red | `#DD344C` |
| Inbound | Blue | `#147EBA` |
| AWS Internal | Orange | `#FF9900` |
| Success/Active | Green | `#1B660F` |
| Warning | Yellow | `#F2C94C` |
| Background | Squid Ink | `#232F3E` |

## SMIL 애니메이션 패턴

### 트래픽 점 (animateMotion)

```xml
<svg viewBox="0 0 1600 900">
  <!-- 경로 정의 -->
  <path id="path-user-to-alb" d="M 100,450 L 300,450 L 300,300 L 500,300"
        fill="none" stroke="none" />

  <!-- 경로를 따라 이동하는 점 -->
  <circle r="5" fill="#147EBA">
    <animateMotion dur="3s" repeatCount="indefinite">
      <mpath href="#path-user-to-alb" />
    </animateMotion>
  </circle>
</svg>
```

### 펄싱 글로우 효과

```xml
<circle cx="500" cy="300" r="30" fill="none" stroke="#FF9900">
  <animate attributeName="r" values="28;35;28" dur="2s" repeatCount="indefinite" />
  <animate attributeName="opacity" values="0.8;0.3;0.8" dur="2s" repeatCount="indefinite" />
</circle>
```

### 순차 스태거

```xml
<!-- Dot 1: 즉시 시작 -->
<circle r="4" fill="#DD344C">
  <animateMotion dur="4s" begin="0s" repeatCount="indefinite">
    <mpath href="#outbound-path" />
  </animateMotion>
</circle>

<!-- Dot 2: 1.3초 후 시작 -->
<circle r="4" fill="#DD344C">
  <animateMotion dur="4s" begin="1.3s" repeatCount="indefinite">
    <mpath href="#outbound-path" />
  </animateMotion>
</circle>
```

## 애니메이션 타이밍

| 애니메이션 타입 | 지속 시간 | 반복 |
|-----------------|----------|------|
| 트래픽 점 (짧은 경로) | 2-3s | indefinite |
| 트래픽 점 (긴 경로) | 4-6s | indefinite |
| 펄싱 글로우 | 2s | indefinite |
| 하이라이트 플래시 | 1s | 3 times |

## 인터랙티브 범례

```html
<div class="legend">
  <label>
    <input type="checkbox" checked onchange="toggleGroup('inbound')">
    <span style="color:#147EBA">● Inbound Traffic</span>
  </label>
  <label>
    <input type="checkbox" checked onchange="toggleGroup('outbound')">
    <span style="color:#DD344C">● Outbound Traffic</span>
  </label>
</div>

<script>
function toggleGroup(group) {
  document.querySelectorAll(`[data-group="${group}"]`).forEach(el => {
    el.style.display = el.style.display === 'none' ? '' : 'none';
  });
}
</script>
```

## 사용 예시

```
사용자: "VPC 트래픽 흐름 애니메이션 만들어줘"

1. animated-diagram-agent 호출
2. 정적 배경 생성 (Draw.io 또는 inline SVG)
3. SMIL 애니메이션 추가
4. 인터랙티브 범례 추가
5. content-review-agent 검토
```

## 출력물 활용

생성된 HTML 파일은 다양한 곳에 삽입 가능:

- **프레젠테이션**: `<iframe>`으로 HTML 슬라이드에 삽입
- **GitBook**: 문서 페이지에 `<iframe>` 임베드
- **단독**: 브라우저에서 직접 열기

## Quality Review (필수)

콘텐츠 완성 후 반드시:
1. `content-review-agent` 호출
2. PASS (85점 이상) 획득 후에만 완료 선언

## 검증 체크리스트

- [ ] 모든 `<animateMotion>` 경로가 유효하고 보임
- [ ] 색상 코딩이 표준과 일치 (Red/Blue/Orange)
- [ ] 범례 토글이 각 애니메이션 그룹에 작동
- [ ] 다양한 뷰포트 크기에서 반응형 스케일링 작동
- [ ] 배경 이미지/SVG가 애니메이션 오버레이와 정렬
- [ ] 애니메이션 요소가 viewBox를 넘지 않음
- [ ] `data-group` 속성이 범례 토글 함수와 일치
