# Draw.io 레이아웃 패턴 및 수정 기법

실제 아키텍처 다이어그램 작업에서 검증된 레이아웃 패턴과 XML 수정 기법.

---

## 박스 스타일 수정

### 라운딩 곡률 조정 (arcSize)

**문제**: 기본 rounded 박스의 곡률이 너무 커서 모서리의 텍스트가 잘림

```xml
<!-- 문제: 기본 rounded는 arcSize가 크다 -->
style="rounded=1;..."

<!-- 해결: arcSize를 명시적으로 작게 설정 -->
style="rounded=1;arcSize=5;..."
```

| arcSize 값 | 효과 |
|-----------|------|
| 0 | 직각 모서리 |
| 5 | 약간 둥근 모서리 (권장) |
| 10 | 보통 둥근 모서리 |
| 20+ | 많이 둥근 모서리 |

### 내부 여백 (Spacing)

**문제**: 텍스트가 박스 가장자리에 너무 붙음

```xml
<!-- 해결: spacingTop, spacingLeft 추가 -->
style="verticalAlign=top;spacingTop=8;spacingLeft=10;..."
```

| 속성 | 용도 | 권장값 |
|------|------|--------|
| spacingTop | 상단 여백 | 5-10 |
| spacingLeft | 좌측 여백 | 5-10 |
| spacingRight | 우측 여백 | 5-10 |
| spacingBottom | 하단 여백 | 5-10 |

### 텍스트 정렬

```xml
<!-- 그룹 박스 제목을 좌상단에 -->
style="verticalAlign=top;align=left;spacingTop=8;spacingLeft=30;..."

<!-- 내용을 중앙에 -->
style="verticalAlign=middle;align=center;..."
```

---

## 아이콘 그리드 배치

### 기본 그리드 패턴

```
행당 4-5개 아이콘 배치:

┌──────────────────────────────────────────────────────────┐
│ [아이콘1] [아이콘2] [아이콘3] [아이콘4] [아이콘5]         │
│  라벨1    라벨2     라벨3     라벨4     라벨5            │
│                                                          │
│ [아이콘6] [아이콘7] [아이콘8] [아이콘9]                   │
│  라벨6    라벨7     라벨8     라벨9                      │
└──────────────────────────────────────────────────────────┘
```

### 좌표 계산

```
아이콘 크기: 40x40 (작은 그리드) 또는 48x48 (표준)
라벨 높이: 25px
행 간격: 아이콘높이 + 라벨높이 + 여백 = 40 + 25 + 3 = 68px

예시 (시작점 x=914, y=162):
- Row 1 아이콘: y=162, 라벨: y=202
- Row 2 아이콘: y=230, 라벨: y=270
- Row 3 아이콘: y=322, 라벨: y=362 (섹션 구분자 포함 시)
- Row 4 아이콘: y=390, 라벨: y=430

열 간격 (40px 아이콘 기준):
- Column 1: x=914
- Column 2: x=989 (+75)
- Column 3: x=1064 (+75)
- Column 4: x=1139 (+75)
- Column 5: x=1214 (+75)
```

### 아이콘 + 라벨 쌍

```xml
<!-- 아이콘 -->
<mxCell id="secrets-mgr" value=""
        style="sketch=0;outlineConnect=0;fontColor=#FFFFFF;gradientColor=#F54749;gradientDirection=north;fillColor=#C7131F;strokeColor=#ffffff;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=9;fontStyle=0;aspect=fixed;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.secrets_manager;fontFamily=Amazon Ember;"
        vertex="1" parent="1">
  <mxGeometry x="914" y="162" width="40" height="40" as="geometry" />
</mxCell>

<!-- 라벨 (아이콘 아래) -->
<mxCell id="secrets-mgr-label" value="Secrets&#xa;Manager"
        style="text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=top;whiteSpace=wrap;rounded=0;fontFamily=Amazon Ember;fontSize=8;fontColor=#FFFFFF;"
        vertex="1" parent="1">
  <mxGeometry x="904" y="202" width="60" height="25" as="geometry" />
</mxCell>
```

**라벨 좌표 계산**:
- 라벨 x = 아이콘 x - (라벨너비 - 아이콘너비) / 2
- 예: 아이콘 x=914, 아이콘너비=40, 라벨너비=60 → 라벨 x = 914 - 10 = 904
- 라벨 y = 아이콘 y + 아이콘높이 = 162 + 40 = 202

---

## 연관 요소 동시 조정

### 부모 박스 크기 변경 시

```
mgmt-box height: 340 → 360 (+20)

영향받는 하위 요소들:
- mapping-box: y=465 → y=485 (+20)
- mapping-title: y=468 → y=488 (+20)
- legend: y=560 → y=580 (+20)
- 범례 내 모든 요소: y += 20
- footer: y=665 → y=685 (+20)
```

### 일괄 수정 패턴

```
Edit 도구로 y 좌표 일괄 수정:
1. 영향받는 요소 식별
2. 각 요소의 y 좌표에 동일한 delta 적용
3. 계층 구조 확인 (부모-자식 관계)
```

---

## 그룹 범위 조정

### Region은 VPC만 포함

**원칙**: Region 박스는 실제 Region에 속하는 리소스(VPC)만 포함

```
┌─ AWS Cloud ───────────────────────────────────────────┐
│  ┌─ Region (VPC만 포함) ─┐  ┌─ 관리 서비스 (별도) ─┐  │
│  │  ┌────┐ ┌────┐       │  │  아이콘들...        │  │
│  │  │VPC1│ │VPC2│       │  │                     │  │
│  │  └────┘ └────┘       │  └─────────────────────┘  │
│  │  ┌────────────────┐  │                           │
│  │  │    VPC3        │  │  ┌─ 범례 ──────────────┐  │
│  │  └────────────────┘  │  │                     │  │
│  └──────────────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

**Width 계산**:
```
VPC들이 x=880에서 끝남
Region 시작: x=410
Region 끝 (여백 포함): x=890
Region width = 890 - 410 = 480
```

---

## 범례 레이아웃

### 2줄 범례 패턴

```
┌─ 범례 ────────────────────────────────────────────────────────┐
│ [IDC서버] IDC 솔루션  [EC2] 컴퓨팅  [S3] 스토리지  [Aurora] DB │
│ [Shield] 보안  [TGW] 네트워킹  [━━▶] Direct Connect  BYOL     │
└───────────────────────────────────────────────────────────────┘
```

### 범례 요소 배치

```xml
<!-- Row 1 -->
<mxCell id="leg-1" ... vertex="1" parent="1">
  <mxGeometry x="905" y="610" width="20" height="20" as="geometry" />
</mxCell>
<mxCell id="leg-1-text" value="IDC 솔루션" ...>
  <mxGeometry x="928" y="607" width="65" height="25" as="geometry" />
</mxCell>

<mxCell id="leg-2" ... vertex="1" parent="1">
  <mxGeometry x="998" y="608" width="24" height="24" as="geometry" />
</mxCell>
<mxCell id="leg-2-text" value="컴퓨팅" ...>
  <mxGeometry x="1025" y="607" width="45" height="25" as="geometry" />
</mxCell>

<!-- Row 2 (y += 30) -->
<mxCell id="leg-5" ... vertex="1" parent="1">
  <mxGeometry x="905" y="640" width="24" height="24" as="geometry" />
</mxCell>
```

### Direct Connect 범례 화살표

```xml
<mxCell id="leg-7" value=""
        style="endArrow=classic;startArrow=classic;html=1;rounded=0;strokeWidth=3;strokeColor=#FF9800;"
        edge="1" parent="1">
  <mxGeometry width="50" height="50" relative="1" as="geometry">
    <mxPoint x="1059" y="652" as="sourcePoint" />
    <mxPoint x="1109" y="652" as="targetPoint" />
  </mxGeometry>
</mxCell>
```

---

## 색상 참조

### AWS 서비스 카테고리 색상

| 카테고리 | fillColor | gradientColor | strokeColor |
|----------|-----------|---------------|-------------|
| 컴퓨팅 | #D05C17 | #F78E04 | #ffffff |
| 스토리지 | #277116 | #60A337 | #ffffff |
| 데이터베이스 | #3334B9 | #4D72F3 | #ffffff |
| 보안 | #C7131F | #F54749 | #ffffff |
| 네트워킹 | #5A30B5 | #945DF2 | #ffffff |
| 관리 | #BC1356 | #F34482 | #ffffff |
| AI/ML | #116D5B | #4AB29A | #ffffff |

### 그룹 박스 색상

| 그룹 | strokeColor | fillColor | fontColor |
|------|-------------|-----------|-----------|
| AWS Cloud | #232F3E | none | #232F3E |
| Region | #00A4A6 | none | #147EBA |
| VPC | #879196 | none | #879196 |
| Public Subnet | #00A4A6 | #E6F6F7 | #147EBA |
| Private Subnet | #7AA116 | #F2F6E8 | #248814 |
| Security Group | #DD344C | #FBE9E7 | #C62828 |
| IDC | #5A6C86 | #E6E6E6 | #5A6C86 |

### 커스텀 박스 색상

| 용도 | fillColor | strokeColor | fontColor |
|------|-----------|-------------|-----------|
| 관리 서비스 (Dark) | #263238 | #FF9900 | #FF9900 |
| 하이브리드 장점 | #1B5E20 | #4CAF50 | #A5D6A7 |
| 범례 박스 | #FAFAFA | #E0E0E0 | #424242 |
| BYOL 배지 | #FFF9C4 | #F57F17 | #F57F17 |

---

## 연결선 스타일

### 기본 연결선

```xml
style="endArrow=classic;html=1;strokeWidth=1;strokeColor=#545B64;"
```

### 양방향 연결선

```xml
style="endArrow=classic;startArrow=classic;html=1;strokeWidth=2;strokeColor=#5A30B5;"
```

### Direct Connect (두꺼운 오렌지)

```xml
style="endArrow=classic;startArrow=classic;html=1;rounded=0;strokeWidth=4;strokeColor=#FF9800;edgeStyle=orthogonalEdgeStyle;"
```

### 꺾인 연결선 (Orthogonal)

```xml
style="edgeStyle=orthogonalEdgeStyle;..."
<Array as="points">
  <mxPoint x="400" y="530" />
  <mxPoint x="400" y="220" />
</Array>
```

---

## 자주 사용하는 수정 패턴

### 1. 텍스트 잘림 수정

```xml
<!-- Before -->
style="rounded=1;..."

<!-- After -->
style="rounded=1;arcSize=5;spacingTop=8;spacingLeft=10;..."
```

### 2. 박스 높이 증가 + 하위 요소 이동

```
1. 박스 height 증가량 계산 (예: +20)
2. 박스 아래 모든 요소의 y += 20
3. 부모 컨테이너도 필요시 확장
```

### 3. 아이콘 행 추가

```
새 행 y = 이전 행 y + 68 (아이콘40 + 라벨25 + 간격3)
또는
새 행 y = 이전 행 y + 92 (섹션 라벨 포함 시)
```

### 4. Region 범위 축소

```
1. VPC들의 최대 x + width 확인
2. Region width = (VPC 끝 x) - (Region 시작 x) + 여백(10)
```
