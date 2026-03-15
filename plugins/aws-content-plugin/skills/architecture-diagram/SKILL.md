---
name: architecture-diagram
description: AWS 아키텍처 다이어그램을 draw.io MCP로 생성. 사용자가 "아키텍처 다이어그램 그려줘", "AWS 구성도 만들어줘", "인프라 다이어그램", "시스템 아키텍처", "클라우드 아키텍처"를 요청할 때 활성화.
model: sonnet
allowed-tools:
  - Read
  - Write
  - Bash
---

# Architecture Diagram Skill

AWS 아키텍처 다이어그램을 생성하는 스킬. **두 가지 모드**를 지원합니다:

| 모드 | 방식 | 장점 | 사용 시점 |
|------|------|------|----------|
| **XML 직접 작성** | Write 도구로 .drawio 파일 생성 | 의존성 없음, 안정적 | 기본 (항상 사용 가능) |
| **Draw.io MCP** | MCP로 실시간 편집 | 대화형 수정, 실시간 미리보기 | 선택적 (설정 필요) |

> MCP 설정 방법은 **`reference/mcp-setup-guide.md`** 참조

---

## PPT용 다이어그램 워크플로우

PPT 삽입용 다이어그램은 **캔버스 크기 설정이 필수**입니다.

### 캔버스 크기 (PPT 16:9 기준)

| 용도 | 크기 (px) | 비율 |
|------|-----------|------|
| 전체 슬라이드 | 1920 x 1080 | 16:9 |
| 콘텐츠 영역 (권장) | 1600 x 900 | 16:9 |
| 절반 슬라이드 | 900 x 900 | 1:1 |
| 2/3 슬라이드 | 1200 x 900 | 4:3 |

### 필수: AWS 아이콘 라벨 표시

모든 AWS 아이콘 아래에 서비스 이름을 **반드시** 표시:

```
┌─────────────┐
│   [아이콘]   │
│             │
│ Lambda      │  ← 서비스 이름 필수
└─────────────┘
```

라벨 설정: `verticalLabelPosition=bottom`, `fontFamily=Amazon Ember`, `fontSize=12`

---

## AWS 아이콘 카테고리

| 카테고리 | 서비스 예시 |
|----------|-------------|
| Compute | EC2, Lambda, ECS, EKS |
| Storage | S3, EBS, EFS, Glacier |
| Database | RDS, DynamoDB, ElastiCache, Aurora |
| Networking | VPC, CloudFront, Route 53, ALB/NLB |
| Security | IAM, WAF, Shield, KMS |
| Analytics | Kinesis, Athena, EMR, Redshift |
| Integration | SQS, SNS, EventBridge, Step Functions |

> 전체 아이콘 목록은 **`reference/aws-icons.md`** 참조

---

## 색상 가이드 (AWS 공식)

| 용도 | 색상 코드 | 설명 |
|------|-----------|------|
| AWS Cloud | #232F3E | 다크 네이비 (배경) |
| Region | #147EBA | 블루 |
| VPC | #248814 | 그린 |
| Public Subnet | #E7F4E8 | 라이트 그린 |
| Private Subnet | #E6F2F8 | 라이트 블루 |
| Security Group | #DF3312 | 레드 (보더) |
| 화살표 | #545B64 | 그레이 |
| Direct Connect | #F58536 | 오렌지 |
| PrivateLink | #5A30B5 | 퍼플 |

---

## PNG 내보내기

macOS Homebrew CLI: `/opt/homebrew/bin/drawio`

```bash
# 기본 PNG
drawio -x -f png -o output.png input.drawio

# 고해상도 PNG (PPT용, 권장)
drawio -x -f png -s 2 -o output.png input.drawio

# 투명 배경 (Dark 테마 PPT)
drawio -x -f png -s 2 -t -o output.png input.drawio

# SVG (벡터, 확대해도 선명)
drawio -x -f svg -o output.svg input.drawio
```

### CLI 옵션

| 옵션 | 설명 | 권장값 |
|------|------|--------|
| `-x` | 내보내기 모드 | 필수 |
| `-f <format>` | 출력 형식 | png |
| `-s <scale>` | 확대 배율 | 2 |
| `-t` | 투명 배경 | Dark PPT용 |
| `-b <color>` | 배경색 | #232F3E |

---

## 템플릿

| 파일 | 용도 |
|------|------|
| `templates/aws-basic.drawio` | VPC, Subnet, AZ 기본 구조 |
| `templates/aws-samples.drawio` | Data Lake 아키텍처 샘플, 아이콘 복사용 |

### 템플릿 활용

1. `templates/aws-samples.drawio`를 draw.io에서 열기
2. 필요한 아이콘 선택 → 복사 (Cmd+C)
3. 새 다이어그램에 붙여넣기 (Cmd+V)
4. 위치와 라벨 수정

---

## 워크플로우

### MCP 활용 시

1. Draw.io 앱 열기
2. MCP 서버 연결 확인 (`/mcp`)
3. `get-shape-categories` → AWS 카테고리 확인
4. `add-cell-of-shape` → AWS 아이콘 추가
5. `add-edge` → 연결선 추가
6. `edit-cell` → 스타일 조정

### XML 직접 작성 시

1. 템플릿 파일 복사 또는 기본 구조 작성
2. AWS 아이콘 shape 추가
3. 연결선 (edge) 추가
4. PNG 내보내기

> XML 문법 상세는 **`reference/drawio-xml-guide.md`** 참조

---

## 레이아웃 원칙

1. **외부에서 내부로**: 사용자/인터넷 → AWS Cloud → Region → VPC → Subnet
2. **왼쪽에서 오른쪽으로**: 데이터 흐름 방향
3. **계층 구분**: 프레젠테이션 → 애플리케이션 → 데이터
4. **AZ 표시**: 고가용성 설계 시 가용영역 명확히 구분
5. **요소 겹침 방지**: 범례/설명 박스는 VPC 영역과 겹치지 않도록 배치

> 레이아웃 패턴 상세는 **`reference/layout-patterns.md`** 참조

---

## 참조 문서

| 파일 | 내용 |
|------|------|
| `reference/aws-icons.md` | AWS 아이콘 shape 이름 및 스타일 |
| `reference/best-practices.md` | 아키텍처 다이어그램 모범사례 |
| `reference/layout-patterns.md` | 3-Tier, 하이브리드 등 레이아웃 패턴 |
| `reference/snippets.md` | 복사해서 사용할 XML 코드 조각 |
| `reference/drawio-xml-guide.md` | XML 직접 작성 문법 가이드 |
| `reference/mcp-setup-guide.md` | Draw.io MCP 설정 및 도구 사용법 |

---

## Quality Review (필수)

다이어그램 완성 후 배포/완료 선언 전에 **반드시**:

1. content-review-agent 호출 → `review content at [파일경로]`
2. FAIL/REVIEW 판정 시 수정 후 재리뷰 (최대 3회)
3. PASS (≥85점) 획득 후에만 완료 선언

> 이 단계를 건너뛰고 완료를 선언하는 것은 금지됩니다.

---

## 검증 체크리스트

- [ ] Amazon Ember 폰트가 모든 텍스트에 설정되었는가
- [ ] AWS 공식 색상을 사용하고 있는가
- [ ] 계층 구조가 명확한가 (Cloud > Region > VPC > Subnet)
- [ ] 데이터 흐름 방향이 일관성 있는가
- [ ] 아이콘 크기가 균일한가 (권장: 60x60)
- [ ] 라벨이 아이콘 아래에 배치되었는가
