---
sidebar_position: 2
title: "Architecture Diagram Agent"
---

# Architecture Diagram Agent

AWS 아키텍처 다이어그램을 Draw.io XML 파일로 직접 생성하는 전문 에이전트입니다.

## 기본 정보

| 항목 | 값 |
|------|-----|
| **모델** | sonnet |
| **도구** | Read, Write, Edit, Glob, Grep, Bash |

## 트리거 키워드

다음 키워드가 감지되면 자동으로 활성화됩니다:

| 키워드 | 설명 |
|--------|------|
| "architecture diagram", "infrastructure diagram" | 아키텍처 다이어그램 생성 |
| "system architecture", "AWS architecture" | 시스템/AWS 아키텍처 |
| "cloud diagram", "draw.io" | 클라우드 다이어그램 |

## 핵심 기능

1. **Direct Draw.io XML Generation** — 외부 도구 없이 .drawio 파일 직접 생성
2. **Layout Optimization** — 요소 배치, 크기, 간격 최적화
3. **AWS Official Styles** — 공식 색상, 아이콘, 그룹 박스 사용
4. **Hybrid Architecture** — IDC + AWS 연결 구조 지원

## 캔버스 크기

| 용도 | dx/pageWidth | dy/pageHeight |
|------|--------------|---------------|
| 전체 슬라이드 | 1920 | 1080 |
| 콘텐츠 영역 (권장) | 1600 | 900 |
| 절반 슬라이드 | 900 | 900 |

## AWS 그룹 박스 스타일

### AWS Cloud

```xml
<mxCell id="aws-cloud" value="AWS Cloud"
        style="...shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_aws_cloud_alt;strokeColor=#232F3E;fillColor=none;..."
        vertex="1" parent="1">
  <mxGeometry x="390" y="45" width="950" height="780" as="geometry" />
</mxCell>
```

### Region

```xml
<mxCell id="region" value="ap-northeast-2 (Seoul)"
        style="...shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_region;strokeColor=#00A4A6;fillColor=none;..."
        vertex="1" parent="aws-cloud">
  <mxGeometry x="20" y="35" width="480" height="735" as="geometry" />
</mxCell>
```

### VPC

```xml
<mxCell id="vpc-1" value="VPC (10.0.0.0/16)"
        style="...shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_vpc;strokeColor=#879196;fillColor=none;..."
        vertex="1" parent="region">
  <mxGeometry x="15" y="380" width="450" height="350" as="geometry" />
</mxCell>
```

## AWS 아이콘 카테고리 색상

| 카테고리 | fillColor | gradientColor |
|----------|-----------|---------------|
| Compute (Orange) | #D05C17 | #F78E04 |
| Storage (Green) | #277116 | #60A337 |
| Database (Blue) | #3334B9 | #4D72F3 |
| Security (Red) | #C7131F | #F54749 |
| Networking (Purple) | #5A30B5 | #945DF2 |
| Management (Pink) | #BC1356 | #F34482 |
| AI/ML (Teal) | #116D5B | #4AB29A |

## Parent 계층 규칙

```
id="0" (root)
└── id="1" (default layer, parent="0")
    ├── aws-cloud (parent="1")
    │   └── region (parent="aws-cloud")
    │       └── vpc (parent="region")
    │           └── subnet (parent="vpc")
    │               └── EC2 icon (parent="subnet")
    ├── on-prem (parent="1")
    └── legend (parent="1")
```

:::warning 중요
Edge(연결선)는 항상 `parent="1"`을 사용합니다.
:::

## 워크플로우

1. **Requirements** — 아키텍처 타입, 서비스, 연결 파악
2. **Layout** — 캔버스 크기, 그룹 박스 배치, 아이콘 그리드
3. **XML Writing** — 구조 → 그룹 (바깥에서 안으로) → 아이콘 → Edge → 범례
4. **Export** — `drawio -x -f png -s 2 -t -o output.png input.drawio`

## 아이콘 그리드 배치

```
아이콘 크기: 48x48 (권장)
아이콘 간격: 27px 수평, 20px 수직
라벨 높이: 20px

행당 계산 (N개 아이콘):
  total_width = N * 48 + (N-1) * 27
  start_x = container_x + (container_width - total_width) / 2
  icon[i].x = start_x + i * 75
```

## 출력물

| 산출물 | 형식 | 위치 |
|--------|------|------|
| Architecture Diagram | .drawio | `[project]/diagrams/[name].drawio` |
| PNG Export | .png | `[project]/diagrams/[name].png` |

## 사용 예시

```
사용자: "3-tier 웹 애플리케이션 아키텍처 다이어그램 그려줘"

에이전트:
1. 요구사항 분석 (VPC, Public/Private Subnet, ALB, EC2, RDS)
2. 캔버스 크기 설정 (1600x900)
3. Draw.io XML 생성
4. PNG 내보내기
5. content-review-agent로 품질 검토
```

## 협업 워크플로우

```mermaid
flowchart LR
    A[architecture-diagram-agent] --> B[.drawio 파일]
    B --> C[PNG export]
    C --> D[프레젠테이션/문서에 삽입]
```
