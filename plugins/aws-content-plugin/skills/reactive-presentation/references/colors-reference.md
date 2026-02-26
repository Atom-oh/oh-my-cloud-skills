# AWS Color Palette Reference

AWS 브랜드 공식 색상 팔레트와 PPT에서의 활용 가이드.

## Primary Colors

### Brand Core

| 이름 | Hex | RGB | 용도 |
|------|-----|-----|------|
| Squid Ink | #232F3E | [35, 47, 62] | 주 배경 (Dark Theme) |
| Smile Orange | #FF9900 | [255, 153, 0] | 강조, CTA |
| White | #FFFFFF | [255, 255, 255] | 텍스트 (Dark), 배경 (Light) |
| Black | #000000 | [0, 0, 0] | 텍스트 (Light) |

### Secondary

| 이름 | Hex | RGB | 용도 |
|------|-----|-----|------|
| Amazon Blue | #146EB4 | [20, 110, 180] | 링크, 보조 강조 |
| Deep Blue | #16191F | [22, 25, 31] | 더 어두운 배경 |
| Light Gray | #D5DBDB | [213, 219, 219] | 테두리, 구분선 |
| Warm Gray | #545B64 | [84, 91, 100] | 보조 텍스트 |

---

## Service Category Colors

AWS 서비스 카테고리별 공식 색상.

### Compute (Orange)

| 이름 | Hex | RGB | 서비스 |
|------|-----|-----|--------|
| Compute Orange | #ED7100 | [237, 113, 0] | EC2, Lambda, ECS |
| Compute Light | #F78E04 | [247, 142, 4] | 그라데이션용 |
| Compute Dark | #D05C17 | [208, 92, 23] | 그라데이션용 |

### Storage (Green)

| 이름 | Hex | RGB | 서비스 |
|------|-----|-----|--------|
| Storage Green | #3B48CC | [59, 72, 204] | S3, EBS, EFS |
| Storage Dark | #1F8476 | [31, 132, 118] | Glacier |

### Database (Blue)

| 이름 | Hex | RGB | 서비스 |
|------|-----|-----|--------|
| Database Blue | #527FFF | [82, 127, 255] | RDS, DynamoDB |
| Database Purple | #3B48CC | [59, 72, 204] | Aurora |

### Networking (Purple)

| 이름 | Hex | RGB | 서비스 |
|------|-----|-----|--------|
| Networking Purple | #8C4FFF | [140, 79, 255] | VPC, CloudFront |
| Networking Dark | #5A30B5 | [90, 48, 181] | Route 53 |

### Security (Red)

| 이름 | Hex | RGB | 서비스 |
|------|-----|-----|--------|
| Security Red | #DD344C | [221, 52, 76] | IAM, WAF |
| Security Dark | #BF0816 | [191, 8, 22] | GuardDuty |

### Analytics (Purple)

| 이름 | Hex | RGB | 서비스 |
|------|-----|-----|--------|
| Analytics Purple | #8C4FFF | [140, 79, 255] | Kinesis, Athena |
| Analytics Blue | #4D27AA | [77, 39, 170] | Redshift |

### Machine Learning (Green)

| 이름 | Hex | RGB | 서비스 |
|------|-----|-----|--------|
| ML Green | #01A88D | [1, 168, 141] | SageMaker |
| ML Teal | #055F4E | [5, 95, 78] | Bedrock |

### Integration (Pink)

| 이름 | Hex | RGB | 서비스 |
|------|-----|-----|--------|
| Integration Pink | #E7157B | [231, 21, 123] | SQS, SNS |
| Integration Dark | #C2185B | [194, 24, 91] | EventBridge |

---

## Architecture Diagram Colors

### Container Borders

| 요소 | Hex | RGB | strokeColor |
|------|-----|-----|-------------|
| AWS Cloud | #232F3E | [35, 47, 62] | #232F3E |
| Region | #00A4A6 | [0, 164, 166] | #00A4A6 |
| VPC | #879196 | [135, 145, 150] | #879196 |
| Availability Zone | #147EBA | [20, 126, 186] | #147EBA |
| Security Group | #DF3312 | [223, 51, 18] | #DF3312 |

### Subnet Fill Colors

| 요소 | Hex | RGB | fillColor |
|------|-----|-----|-----------|
| Public Subnet | #F2F6E8 | [242, 246, 232] | #F2F6E8 |
| Private Subnet | #E6F6F7 | [230, 246, 247] | #E6F6F7 |

### Subnet Stroke Colors

| 요소 | Hex | RGB | strokeColor |
|------|-----|-----|-------------|
| Public Subnet | #7AA116 | [122, 161, 22] | #7AA116 |
| Private Subnet | #00A4A6 | [0, 164, 166] | #00A4A6 |

### Text Colors

| 요소 | Hex | RGB | fontColor |
|------|-----|-----|-----------|
| AWS Cloud Label | #232F3E | [35, 47, 62] | #232F3E |
| Region Label | #147EBA | [20, 126, 186] | #147EBA |
| VPC Label | #879196 | [135, 145, 150] | #879196 |
| Public Subnet | #248814 | [36, 136, 20] | #248814 |
| Private Subnet | #147EBA | [20, 126, 186] | #147EBA |

---

## Template Theme Colors (layout_sample.pptx)

AWS Dark Template에서 정의된 테마 색상입니다. layout_sample.pptx의 theme1.xml에서 추출한 실제 값입니다.

### Theme Color Scheme

| Scheme Color | Hex | RGB | 용도 |
|--------------|-----|-----|------|
| dk1 (Dark 1) | #000000 | [0, 0, 0] | 기본 텍스트 (Light 배경) |
| dk2 (Dark 2) | #161D26 | [22, 29, 38] | 진한 배경, 테이블 헤더 |
| lt1 (Light 1) | #FFFFFF | [255, 255, 255] | 기본 텍스트 (Dark 배경) |
| lt2 (Light 2) | #F3F3F7 | [243, 243, 247] | 밝은 배경, 테이블 본문 |
| accent1 | #41B3FF | [65, 179, 255] | 강조 (Blue) |
| accent2 | #AD5CFF | [173, 92, 255] | 강조 (Purple) |
| accent3 | #00E500 | [0, 229, 0] | 강조 (Green) |
| accent4 | #FF5C85 | [255, 92, 133] | 강조 (Pink) |
| accent5 | #FF693C | [255, 105, 60] | 강조 (Orange) |
| accent6 | #FBD332 | [251, 211, 50] | 강조 (Yellow) |

### Table Formatting (Slide 89 Reference)

layout_sample.pptx Slide 89에서 추출한 실제 테이블 포맷입니다.

**Table 8 (Comparison Table):**
| 요소 | 값 | 설명 |
|------|-----|------|
| 위치 | left=0.93", top=2.05" | 853,441 EMU, 1,872,143 EMU |
| 크기 | width=11.45", height=2.20" | 10,472,928 EMU |
| Fill | schemeClr=tx1 | 테마 색상 (Dark) |
| Font Size | 16pt | 헤더/본문 동일 |
| Header | Bold | 첫 행 굵게 |
| First Column | Bold | 첫 열 굵게 |

**Table 9 (Tips Table):**
| 요소 | 값 | 설명 |
|------|-----|------|
| 위치 | left=0.93", top=4.48" | 853,440 EMU, 4,094,791 EMU |
| 크기 | width=11.45", height=2.12" | 10,472,928 EMU |
| Fill | schemeClr=bg2 | 테마 색상 (Light) |
| Font Size | 16pt | 헤더/본문 동일 |
| Header | Bold | 첫 행 굵게 |
| First Column | Bold | 첫 열 굵게 |

### Theme Color to RGB Mapping (MCP 도구용)

MCP 도구는 테마 색상을 직접 지원하지 않으므로 RGB로 변환하여 사용합니다:

| Theme Scheme | Dark Theme RGB | Light Theme RGB | MCP 사용 값 |
|--------------|----------------|-----------------|-------------|
| tx1 (Text 1) | [22, 29, 38] | [0, 0, 0] | Dark: [22, 29, 38] |
| bg2 (Background 2) | [243, 243, 247] | [243, 243, 247] | [243, 243, 247] |
| Text on tx1 fill | [255, 255, 255] | - | [255, 255, 255] |
| Text on bg2 fill | [22, 29, 38] | - | [22, 29, 38] |

### Table Color Recommendation (Dark Theme)

**권장 조합 (layout_sample.pptx 기반):**

```yaml
# 어두운 테이블 (tx1 스타일)
mcp__ppt__add_table:
  header_bg_color: [22, 29, 38]     # dk2
  body_bg_color: [22, 29, 38]       # dk2
  header_font_size: 16
  body_font_size: 16

mcp__ppt__format_table_cell:
  color: [255, 255, 255]            # 흰색 텍스트
  font_size: 16
  bold: true                        # 헤더와 첫 열

# 밝은 테이블 (bg2 스타일)
mcp__ppt__add_table:
  header_bg_color: [243, 243, 247]  # lt2
  body_bg_color: [243, 243, 247]    # lt2
  header_font_size: 16
  body_font_size: 16

mcp__ppt__format_table_cell:
  color: [22, 29, 38]               # 어두운 텍스트
  font_size: 16
  bold: true                        # 헤더와 첫 열
```

**대안 조합 (SKILL.md 기존 권장 - Dark Slate):**

```yaml
mcp__ppt__add_table:
  header_bg_color: [55, 75, 100]    # Slate Blue
  body_bg_color: [40, 55, 75]       # Dark Slate
  header_font_size: 16
  body_font_size: 16

mcp__ppt__format_table_cell:
  color: [255, 255, 255]            # 흰색 텍스트
  font_size: 16
```

---

## PPT Color Schemes

MCP에서 사용 가능한 색상 스킴.

### modern_blue

```
Primary: #0066CC (Blue)
Accent: #FF6B35 (Orange)
Background: #1A1A2E (Dark)
Text: #FFFFFF (White)
```

### corporate_gray

```
Primary: #545B64 (Gray)
Accent: #FF9900 (Orange)
Background: #232F3E (Squid Ink)
Text: #FFFFFF (White)
```

### elegant_green

```
Primary: #01A88D (Teal)
Accent: #FF9900 (Orange)
Background: #FFFFFF (White)
Text: #232F3E (Dark)
```

### warm_red

```
Primary: #DD344C (Red)
Accent: #FF9900 (Orange)
Background: #232F3E (Dark)
Text: #FFFFFF (White)
```

---

## Usage Examples

### Dark Theme Slide

```
mcp__ppt__manage_text:
  color: [255, 255, 255]      # White text

mcp__ppt__add_table:
  header_bg_color: [35, 47, 62]     # Squid Ink
  header_font_color: [255, 255, 255] # White
```

### Accent Elements

```
mcp__ppt__add_shape:
  fill_color: [255, 153, 0]   # Smile Orange
  line_color: [35, 47, 62]    # Squid Ink
```

### Chart Colors

```
mcp__ppt__add_chart:
  # Series colors are auto-assigned based on color_scheme
  # To customize, use chart-specific color settings
```

---

## Accessibility Notes

1. **대비율**: 텍스트와 배경 간 최소 4.5:1 대비율 유지
2. **색맹 고려**: 빨강-초록 조합 피하기
3. **일관성**: 동일한 의미에 동일한 색상 사용

### Safe Color Combinations

| 배경 | 텍스트 | 대비율 |
|------|--------|--------|
| #232F3E | #FFFFFF | 12.6:1 ✓ |
| #232F3E | #FF9900 | 6.8:1 ✓ |
| #FFFFFF | #232F3E | 12.6:1 ✓ |
| #FFFFFF | #545B64 | 7.1:1 ✓ |
