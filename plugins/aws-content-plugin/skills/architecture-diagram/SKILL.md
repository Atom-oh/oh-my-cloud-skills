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

> MCP 설정 방법은 **`references/mcp-setup-guide.md`** 참조

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

> 전체 아이콘 목록은 **`references/aws-icons.md`** 참조

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

## ⚠️ 내보내기 전 검증 (필수 — 침묵 실패 방지)

> **drawio CLI는 잘못된 XML에서도 exit 0으로 "성공"하면서 셀의 90%를 조용히 누락시킵니다** —
> "완성된 듯하지만 텅 빈 PNG"의 주범입니다. **export 전에 반드시 검증**하세요.

```bash
python3 scripts/validate_drawio.py output.drawio
# ✅ 통과 시 cells/vertices/edges/icons/groups 개수 출력 → 의도한 개수와 비교(누락 감지)
# ❌ 실패 시 export 금지하고 먼저 수정
```

**가장 흔한 침묵 킬러 (생성 시 절대 금지):**
- XML 주석 안의 `&` (반드시 `&amp;`) — 예: `<!-- EDGE & AUTH -->` ❌ → 주석을 아예 쓰지 말 것
- XML 주석 안의 `--` (예: `<!-- ----- -->`) — XML 불법, 이후 모든 셀 누락
- 라벨/값 안의 미이스케이프 `&`, `<`, `>` → `&amp;` `&lt;` `&gt;`
- 장식용 주석은 **생략**을 권장 (디버깅 가치 < 렌더 파괴 위험)

## PNG 내보내기

CLI 경로: Linux `/usr/bin/drawio` · macOS Homebrew `/opt/homebrew/bin/drawio`

```bash
# 고해상도 PNG (PPT용, 권장)
drawio -x -f png -s 2 -o output.png input.drawio

# Headless Linux (디스플레이 없음) — xvfb 필요. dbus/GPU stderr 경고는 무시 가능.
xvfb-run -a drawio -x -f png -s 2 -o output.png input.drawio

# 투명 배경 (Dark 테마 PPT)
drawio -x -f png -s 2 -t -o output.png input.drawio

# SVG (벡터, 확대해도 선명)
drawio -x -f svg -o output.svg input.drawio
```

> **export 후 확인**: PNG 용량이 비정상적으로 작거나(<10KB) 셀이 비면 truncation 의심.
> validator의 cell 개수와 실제 렌더를 대조하세요.

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

> XML 문법 상세는 **`references/drawio-xml-guide.md`** 참조

---

## 레이아웃 원칙

1. **외부에서 내부로**: 사용자/인터넷 → AWS Cloud → Region → VPC → Subnet
2. **왼쪽에서 오른쪽으로**: 데이터 흐름 방향
3. **계층 구분**: 프레젠테이션 → 애플리케이션 → 데이터
4. **AZ 표시**: 고가용성 설계 시 가용영역 명확히 구분
5. **요소 겹침 방지**: 범례/설명 박스는 VPC 영역과 겹치지 않도록 배치

## 엣지 라우팅 (품질의 핵심 — "안 이쁨"의 주원인)

스파게티 엣지가 다이어그램을 망치는 1순위입니다. 다음을 지키세요:

1. **같은 종류 리소스는 단일 컬럼(세로 일렬)으로 묶기**. 여러 Lambda를 한 그룹에 세로로 쌓으면, 자동 라우팅이 옆 아이콘을 관통하는 문제가 사라집니다(가장 효과적인 수정).
2. **직교 엣지 고정**: `edgeStyle=orthogonalEdgeStyle;rounded=0;`. 자동 라우팅이 아이콘을 관통하면 **명시적 앵커**로 출입점을 고정: `exitX/exitY`(출발), `entryX/entryY`(도착) — 예: 오른쪽 중앙에서 나가려면 `exitX=1;exitY=0.5;exitDx=0;exitDy=0;`.
3. **조밀한 밴드는 웨이포인트 레인 사용**: 엣지가 많으면 공통 수직/수평 채널(레인)로 묶어 교차를 줄입니다. **`scripts/route_edges.py --from <id> --to <id> --via-x <X>`** (또는 `--via-y`)가 깨끗한 직교 웨이포인트 + exit/entry 앵커를 계산해 줍니다(절대좌표 수동 계산 불필요). 들어오는(async) 엣지와 나가는(sync) 엣지는 **서로 다른 X 채널**로 분리하세요.
4. **엣지 종류별 색상/스타일 구분 + 범례**: 동기 API(검정 실선), WebSocket(파랑 점선), 비동기 이벤트(분홍 점선), AI 호출(초록), 인증(빨강 점선) 등. 범례는 빈 코너에 겹치지 않게.
5. **라벨이 보더/아이콘과 겹치지 않게** 엣지 라벨 위치 조정.
6. **엣지가 많으면(>~15) 줄여라 — "번호 플로우" 패턴** (밀집 다이어그램을 이쁘게 만드는 결정적 기법): 모든 연결을 다 그리지 말고 **핵심 데이터 플로우 5개 내외**로 압축하고 각 플로우에 단일 색상 + 번호 배지(①②③④⑤)를 붙입니다. 부수적 연결(인증 JWKS, authorizer, static 등)은 **번호 범례의 텍스트**로만 표기합니다. 정보 밀도가 혼잡의 근본 원인 — 전문 AWS 다이어그램이 깔끔한 이유는 모든 연결을 그리지 않기 때문입니다.

## 아이콘 사이징 (균일성)

| 레벨 | 크기 | 용도 |
|------|------|------|
| 표준 서비스 아이콘 | **78x78** | 대부분의 AWS 서비스 (기본값) |
| 중첩 리소스 | 48~52 | 좁은 subnet 안에 여러 리소스를 넣을 때만 |

> 한 다이어그램 안에서 같은 레벨 아이콘은 **반드시 동일 크기**. 섞으면 산만해 보입니다.

> 레이아웃 패턴 상세는 **`references/layout-patterns.md`** 참조

---

## 참조 문서

| 파일 | 내용 |
|------|------|
| `references/aws-icons.md` | AWS 아이콘 shape 이름 및 스타일 |
| `references/best-practices.md` | 아키텍처 다이어그램 모범사례 |
| `references/layout-patterns.md` | 3-Tier, 하이브리드 등 레이아웃 패턴 |
| `references/snippets.md` | 복사해서 사용할 XML 코드 조각 |
| `references/drawio-xml-guide.md` | XML 직접 작성 문법 가이드 |
| `references/mcp-setup-guide.md` | Draw.io MCP 설정 및 도구 사용법 |
| `scripts/validate_drawio.py` | **export 전 검증** — 침묵 킬러(주석 `&`/`--`, 미이스케이프 문자, DOCTYPE) 검출 + 셀 개수 리포트(truncation 감지) + `--coords` 절대좌표 |
| `scripts/route_edges.py` | **엣지 웨이포인트 자동계산** — `--from/--to`로 깨끗한 직교 경로(채널 라우팅) + exit/entry 앵커 생성. 어지러운 화살표 정리의 핵심 도구. `--list`로 셀 절대좌표 확인 |

---

## Quality Review (필수)

다이어그램 완성 후 배포/완료 선언 전에 **반드시**:

1. content-review-agent 호출 → `review content at [파일경로]`
2. FAIL/REVIEW 판정 시 수정 후 재리뷰 (최대 3회)
3. PASS (≥85점) 획득 후에만 완료 선언

> 이 단계를 건너뛰고 완료를 선언하는 것은 금지됩니다.

---

## 검증 체크리스트

- [ ] **`scripts/validate_drawio.py`로 검증 통과** (export 전 필수 — 침묵 truncation 방지)
- [ ] 셀/아이콘 개수가 의도와 일치하는가 (validator 출력 대조)
- [ ] XML 주석에 `&`/`--` 없음 (또는 주석 미사용)
- [ ] Amazon Ember 폰트가 모든 텍스트에 설정되었는가
- [ ] AWS 공식 색상을 사용하고 있는가
- [ ] 계층 구조가 명확한가 (Cloud > Region > VPC > Subnet)
- [ ] 데이터 흐름 방향이 일관성 있는가 (왼쪽→오른쪽)
- [ ] 엣지가 직교(orthogonal)이고 아이콘을 관통하지 않는가
- [ ] 엣지 종류가 색상/스타일로 구분되고 범례가 있는가
- [ ] 같은 레벨 아이콘 크기가 균일한가 (표준 78x78)
- [ ] 라벨이 아이콘 아래에 배치되었는가
