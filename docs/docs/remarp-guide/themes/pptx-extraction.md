---
sidebar_position: 1
title: PPTX 테마 추출
---

# PPTX 테마 추출

기업 PowerPoint 템플릿에서 색상, 폰트, 로고를 추출하여 Remarp 프레젠테이션에 적용할 수 있습니다.

## 빠른 시작

```bash
# PPTX에서 테마 추출
python3 scripts/extract_pptx_theme.py template.pptx -o common/pptx-theme/

# 출력 구조:
# common/pptx-theme/
# ├── theme-manifest.json    # 추출된 모든 메타데이터
# ├── theme-override.css     # CSS 변수 오버라이드
# └── images/
#     ├── logo_1.png         # 추출된 로고
#     └── bg_1.png           # 배경 이미지 (있는 경우)
```

## CLI 옵션

| 옵션 | 기본값 | 설명 |
|------|--------|------|
| `<pptx_path>` | 필수 | PPTX 템플릿 파일 경로 |
| `-o, --output` | `./pptx-theme` | 출력 디렉토리 |
| `--master N` | `0` | 슬라이드 마스터 인덱스 (멀티 마스터 템플릿용) |
| `--list-masters` | - | 모든 슬라이드 마스터 목록 출력 후 종료 |
| `--json-only` | - | JSON 매니페스트만 생성, CSS 스킵 |
| `--css-file` | `theme-override.css` | 출력 CSS 파일명 |

## Frontmatter에서 테마 지정

```yaml
---
remarp: true
title: "My Presentation"

theme:
  source: "./company-template.pptx"  # PPTX/PDF 파일 또는 추출된 디렉토리
  footer: auto                        # 자동 추출 또는 직접 지정
  pagination: true                    # 페이지 번호 표시
  logo: auto                          # 자동 추출 또는 경로 지정
---
```

## 테마 소스 타입

| 소스 타입 | 예시 | 동작 |
|----------|------|------|
| PPTX 파일 | `./template.pptx` | `_theme/` 디렉토리로 테마 추출 |
| PDF 파일 | `./template.pdf` | 색상과 이미지 추출 |
| 디렉토리 | `./_theme/template/` | 이미 추출된 테마 사용 |

## 색상 매핑

PPTX 테마 색상은 reactive-presentation CSS 변수로 매핑됩니다:

| PPTX 색상 | CSS 변수 | 용도 |
|----------|---------|------|
| `dk2` | `--bg-primary` | 메인 배경 (충분히 어두운 경우에만) |
| `accent1` | `--accent` | 기본 강조색 (버튼, 링크, 하이라이트) |
| `accent2` | `--accent-light` | 보조 강조색 (그라데이션, 호버) |
| `accent3` | `--green` | 성공 표시 |
| `accent4` | `--red` | 오류/위험 표시 |
| `accent5` | `--orange` | 경고 표시 |
| `accent6` | `--yellow` | 주의 표시 |
| `hlink` | `--cyan` | 하이퍼링크 색상 |
| `lt1` | `--text-primary` | 기본 텍스트 색상 (충분히 밝은 경우) |

## 로고 감지

로고는 크기 휴리스틱으로 식별됩니다:

- 슬라이드 마스터에서 슬라이드 너비의 20% 미만인 이미지 → 로고
- 20% 이상인 이미지 → 장식용/배경 (무시)

위치는 EMU에서 CSS 퍼센트로 변환됩니다:
- 슬라이드 크기: 12,192,000 x 6,858,000 EMU (16:9)
- EMU → % = `(emu_value / slide_dimension) * 100`

## 로고 통합

```javascript
// SlideFramework에서 로고 자동 적용
const deck = new SlideFramework({
  logoSrc: '../common/pptx-theme/images/logo_1.png',
  footer: '© 2025, Amazon Web Services'
});
```

## 푸터 추출

- **푸터 텍스트**: 슬라이드 마스터의 placeholder idx=3에서 추출
- **슬라이드 번호 형식**: placeholder idx=4에서 추출 (예: `‹#›`)
- **날짜 형식**: placeholder idx=2에서 추출

푸터 텍스트는 `theme-manifest.json`의 `footer_text` 필드에서 확인하고 SlideFramework에 전달합니다.

## 배경 타입

| PPTX 채우기 타입 | CSS 출력 |
|----------------|----------|
| BACKGROUND (상속) | 오버라이드 없음 (theme.css 기본값 사용) |
| SOLID | `:root`에 `background-color` |
| PICTURE | `::before` 가상 요소에 어두운 오버레이 |
| GRADIENT | 추출된 색상으로 `linear-gradient()` |

## 테마 매니페스트

`theme-manifest.json`에는 추출된 모든 메타데이터가 포함됩니다:

```json
{
  "source": "template.pptx",
  "master_index": 0,
  "master_name": "Slide Master Name",
  "colors": {
    "dk1": "#000000",
    "lt1": "#FFFFFF",
    "dk2": "#161D26",
    "lt2": "#F3F3F7",
    "accent1": "#41B3FF",
    "accent2": "#AD5CFF",
    "accent3": "#00E500",
    "accent4": "#FF5C85",
    "accent5": "#FF693C",
    "accent6": "#FBD332"
  },
  "fonts": {
    "heading": "Calibri Light",
    "body": "Calibri"
  },
  "logos": [
    {
      "file": "images/logo_1.png",
      "position_pct": { "left": "4.88%", "top": "92.42%" }
    }
  ],
  "footer_text": "© 2025, Amazon Web Services, Inc.",
  "layout_details": [
    { "index": 0, "name": "Title Slide", "background": { "type": "picture" } },
    { "index": 1, "name": "Title and Content", "background": { "type": "inherited" } }
  ]
}
```

## 멀티 마스터 템플릿

일부 템플릿에는 여러 슬라이드 마스터가 있습니다. `--list-masters`로 확인하고 `--master N`으로 특정 마스터를 선택합니다:

```bash
# 모든 마스터 목록 확인
python3 scripts/extract_pptx_theme.py template.pptx --list-masters

# 특정 마스터에서 추출
python3 scripts/extract_pptx_theme.py template.pptx --master 1 -o theme-alt/
```

## 트러블슈팅

### 색상이 잘못 표시되는 경우

스크립트는 dk2가 어두운 경우(휘도 < 0.2)에만 배경색으로 적용합니다. 밝은 테마 PPTX의 경우 기본 어두운 배경을 유지하고 강조색만 적용됩니다.

### 로고가 표시되지 않는 경우

1. `theme-manifest.json`의 `logos` 배열 확인
2. `images/` 디렉토리에 이미지 파일 존재 확인
3. SlideFramework의 `logoSrc` 경로가 파일 위치와 일치하는지 확인

### 폰트가 로드되지 않는 경우

PPTX 폰트는 시스템 폰트일 수 있습니다. 브라우저에 해당 폰트가 설치되어 있거나 웹 폰트 import가 필요합니다:

```css
@import url('https://fonts.googleapis.com/css2?family=...');
```
