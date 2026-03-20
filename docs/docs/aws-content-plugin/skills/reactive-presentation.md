---
sidebar_position: 1
title: "Reactive Presentation"
---

# Reactive Presentation Skill

인터랙티브 HTML 프레젠테이션 슬라이드쇼를 빌드하는 스킬입니다. Canvas 애니메이션, 퀴즈, 다크 테마, 키보드 네비게이션을 지원하며 GitHub Pages로 배포합니다.

## 트리거 키워드

다음 키워드로 활성화됩니다:
- "create slides", "build a presentation", "make a slideshow"
- "training slides", "interactive presentation"
- "Canvas animation slides", "reactive presentation"

## 제공 리소스

### assets/

프레임워크 파일 (`common/`에 복사):

| 파일 | 설명 |
|------|------|
| `theme.css` | 다크 테마, Pretendard 폰트, 16:9 레이아웃, 모든 컴포넌트 스타일 |
| `theme-override-template.css` | PPTX 추출 CSS 오버라이드용 템플릿 |
| `slide-framework.js` | SlideFramework 클래스 (키보드, 터치, 진행 표시, 프레젠터 뷰) |
| `slide-renderer.js` | SlideRenderer 클래스: JSON → HTML 동적 렌더링 |
| `presenter-view.js` | PresenterView 클래스 (드래그 가능 분할, BroadcastChannel 동기화) |
| `animation-utils.js` | Canvas 프리미티브, AnimationLoop, TimelineAnimation, Colors, Ease |
| `quiz-component.js` | QuizManager (자동 채점, 피드백) |
| `export-utils.js` | ExportUtils (PDF 내보내기, ZIP 다운로드) |

### scripts/

| 스크립트 | 설명 |
|----------|------|
| `extract_pptx_theme.py` | PPTX 테마 추출 → CSS 오버라이드 + 이미지 |
| `remarp_to_slides.py` | Remarp 마크다운 → HTML 슬라이드 변환 |
| `marp_to_slides.py` | Marp 마크다운 → HTML 슬라이드 변환 (레거시) |
| `extract_aws_icons.py` | AWS Architecture Icons 추출 |

### references/

| 참조 문서 | 설명 |
|----------|------|
| `framework-guide.md` | CSS 클래스, JS 함수, HTML 템플릿 API 레퍼런스 |
| `slide-patterns.md` | 슬라이드 타입별 HTML 패턴, Canvas 애니메이션 패턴 |
| `remarp-format-guide.md` | Remarp 마크다운 포맷 명세 (권장) |
| `marp-format-guide.md` | Marp 마크다운 포맷 명세 (레거시) |
| `pptx-theme-guide.md` | PPTX 테마 추출 사용법, 색상 매핑, 트러블슈팅 |
| `aws-icons-guide.md` | AWS Architecture Icons 사용법, 네이밍 규약 |
| `canvas-animation-prompt.md` | Canvas prompt → JS 코드 생성 가이드 |
| `interactive-patterns-guide.md` | 인터랙티브 슬라이드 패턴 (시뮬레이터, 대시보드 등) |
| `colors-reference.md` | AWS 색상 팔레트 |

### icons/

AWS Architecture Icons (4,224개 파일):

| 디렉토리 | 설명 |
|----------|------|
| `Architecture-Service-Icons_07312025/` | 서비스 레벨 아이콘 (121개 카테고리) |
| `Architecture-Group-Icons_07312025/` | 그룹 아이콘 (Cloud, VPC, Region, Subnet) |
| `Category-Icons_07312025/` | 카테고리 레벨 아이콘 (4개 크기) |
| `Resource-Icons_07312025/` | 리소스 레벨 아이콘 (22개 카테고리) |
| `others/` | 서드파티 아이콘 (LangChain, Grafana 등) |

## 주요 기능

### Remarp 포맷 (권장)

프래그먼트 애니메이션, Canvas DSL, 스피커 노트, 슬라이드 전환을 마크다운에서 직접 제어:

```markdown
---
remarp: true
title: My Presentation
theme: aws-dark
---

# Slide Title
@type: content

This is a paragraph {.click}

:::click
This appears on click
:::

:::notes
{timing: 2min}
Speaker notes here
:::
```

### PPTX 테마 추출

```bash
python3 scripts/extract_pptx_theme.py <pptx_path> -o {repo}/common/pptx-theme/
```

생성물:
- `theme-manifest.json` — 추출된 색상, 폰트, 로고, 푸터
- `theme-override.css` — CSS 변수 오버라이드
- `images/` — 로고, 배경 이미지

### 슬라이드 타입

| 콘텐츠 타입 | 패턴 | 인터랙티브 요소 |
|-------------|------|-----------------|
| 단순 흐름 (박스 ≤4) | Canvas Animation | `:::canvas` DSL, step ↑↓ 내비게이션 |
| 복잡 아키텍처 (박스 5+) | HTML Architecture | `:::html` + `:::css` (flow-h, flow-group) |
| A vs B 비교 | Compare Toggle | `.compare-toggle` 버튼 |
| 설정 변형 | Tab Content | `.tab-bar` + YAML 코드 |
| 단계별 프로세스 | Timeline | `.timeline` 애니메이션 |
| 모니터링/대시보드 (박스 5+) | HTML Dashboard | `:::html` + `:::script` |
| 베스트 프랙티스 | Checklist | `.checklist` 토글 |
| 블록 요약 | Quiz | `data-quiz` 퀴즈 |

### Canvas vs HTML 선택 기준

:::warning STOP Gate
Canvas 사용 전 반드시 박스/아이콘 개수를 확인하세요:
- **≤4개**: `:::canvas` 사용 가능
- **5개 이상**: `:::canvas` 금지 → `:::html` + `:::css` 필수
:::

### 키보드 단축키

| 키 | 동작 |
|----|------|
| ← → | 이전/다음 슬라이드 |
| ↑ ↓ | 탭/비교 옵션 순환 |
| F | 전체 화면 |
| P | 프레젠터 뷰 |
| N | 스피커 노트 패널 |
| O | 개요 모드 |

## 사용 예시

```
사용자: "EKS 입문 프레젠테이션 만들어줘"

1. presentation-agent 호출
2. Remarp 콘텐츠 작성
3. HTML 빌드: python3 scripts/remarp_to_slides.py build {slug}/
4. content-review-agent 검토
5. GitHub Pages 배포
```

## Quality Review (필수)

콘텐츠 완성 후 배포 전에 반드시:
1. `content-review-agent` 호출
2. PASS (85점 이상) 획득 후에만 배포

:::warning 필수
이 단계를 건너뛰고 배포하는 것은 금지됩니다.
:::
