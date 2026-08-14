---
name: architecture-diagram
description: AWS 아키텍처 다이어그램(draw.io/.drawio → PNG·SVG)을 생성. 사용자가 "아키텍처 다이어그램 그려줘", "AWS 구성도 만들어줘", "인프라 다이어그램", "시스템 아키텍처", "클라우드 아키텍처", 또는 AWS/클라우드 구성을 draw.io/비표준 손그림 다이어그램으로 그려달라고 요청할 때 활성화(AWS·클라우드 무관한 일반 draw.io 작도는 대상 아님). 표준 패턴은 YAML 스펙 생성기(layout_aws.py)로 좌표 없이 생성하고, 비정형 도형은 손으로 .drawio를 작성하는 두 경로를 지원 — draw.io MCP는 선택적 대화형 편집용.
allowed-tools:
  - Read
  - Write
  - Bash
---

# Architecture Diagram Skill

AWS 아키텍처 다이어그램을 생성하는 스킬. **목표**: 처음 보는 사람이 데이터 흐름을 좌→우로 따라 읽을 수 있고, 그룹 경계가 실제 네트워크 위계와 일치하며, 정렬·간격이 균일한 — PPT에 바로 넣을 수 있는 다이어그램. **네 가지 모드**를 지원합니다:

| 모드 | 방식 | 장점 | 사용 시점 |
|------|------|------|----------|
| **스펙 생성기 (권장)** | `scripts/layout_aws.py` 로 YAML 스펙 → .drawio | **좌표 자동계산** · Multi-AZ 미러 대칭 보장 · 항상 게이트 통과 | VPC/Multi-AZ/티어 · 서버리스/파이프라인 패턴 (가장 흔함) |
| **XML 직접 작성** | Write 도구로 .drawio 파일 생성 | 완전한 자유도 | 생성기 패턴에 안 맞는 비정형 구조 |
| **Draw.io MCP** | MCP로 실시간 편집 | 대화형 수정, 실시간 미리보기 | 선택적 (설정: `references/mcp-setup-guide.md`) |
| **스케치 (Excalidraw)** | `scripts/excalidraw_gen.py` 로 YAML 스펙 → 로컬 `.excalidraw` | 손그림/화이트보드 미학, 같은 공유 아이콘(AgentCore 포함) | 브레인스토밍·개념도·캐주얼 느낌 (정식 인프라도는 drawio 권장) |

> **왜 스펙 생성기인가**: PPT 대비 품질 격차의 근본 원인은 *픽셀 좌표를 손으로 찍는 것*입니다.
> 범용 자동배치 엔진(D2/ELK, Python diagrams/Graphviz)도 AWS 관례(AZ 좌우 미러·VPC 중첩·좌→우
> 티어)를 몰라 깨뜨립니다. `layout_aws.py`는 **구조·라벨·흐름만 선언**하면 AWS 관례 좌표를
> 결정적으로 계산해 drawio로 출력합니다 → validate/lint 게이트를 그대로 통과.

---

## 스펙 생성기 (Spec-Driven Generation) — 권장 경로

VPC·Multi-AZ·티어형 아키텍처는 **좌표를 직접 쓰지 말고** 고수준 YAML 스펙으로 선언하세요.

```bash
# 1) 스펙 작성 (examples/multi-az-3tier.yaml 를 출발점으로 복사) — 좌표 없음, 구조만
#    external(외부 행위자) → edge(CDN/DNS/WAF) → region.vpc.{azs, tiers[].services} + flows
# 2) 생성
python3 scripts/layout_aws.py my-spec.yaml -o output.drawio
# 3) 게이트 (필수)
python3 scripts/validate_drawio.py output.drawio
python3 scripts/lint_layout.py output.drawio
# 4) export
xvfb-run -a drawio -x -f png -s 2 -o output.png output.drawio
```

**블록 합성** — 좌→우로 `[external] [onprem] [edge] [region(s)]` 배치. 4가지 패턴 지원:
- **`vpc`** — Multi-AZ/티어형. AZ 자동 **미러**(동일 크기·좌우 대칭), 서비스 id는 AZ별 `id_0`/`id_1` 인스턴스화.
- **`stages`** — 서버리스/파이프라인. `region.stages`로 VPC 없이 좌→우 스테이지 컬럼. id 그대로 사용.
- **멀티리전** — `regions:` 리스트. 리전별 id 접두사 `r0_`/`r1_` (예: `{from: r0_rds, to: r1_rds, kind: async}`).
- **하이브리드** — `onprem:` 블록(기업 DC 컨테이너) + Direct Connect/VPN 엣지로 Region 연결.

- 아이콘 레지스트리·색상·간격은 전부 `design-tokens.md` 정본을 따름 (생성기에 내장).
- 골든 예시: **`examples/`** — `multi-az-3tier`·`eks-multi-az`(vpc), `serverless-api`(stages), `multi-region-dr`(regions), `hybrid-dx`(onprem). 스펙+drawio 쌍, 복사해서 수정.
- Transit Gateway 메시 등 위 4패턴에 안 맞는 비정형 구조만 XML 직접 작성 모드를 사용 — 템플릿(`templates/`)에서 시작하고 문법은 `references/drawio-xml-guide.md` + `references/snippets.md`.

### 스케치 출력 (Excalidraw) — 화이트보드 미학

손그림/화이트보드 느낌이 필요하면 같은 `stages` 스펙을 로컬 `.excalidraw`로 출력합니다 (서버 불필요):
```bash
python3 scripts/excalidraw_gen.py my-spec.yaml -o output.excalidraw
# → excalidraw.com / VSCode Excalidraw 확장 / Obsidian 에서 열어 편집
```
- 공유 아이콘 라이브러리(reactive-presentation/icons — 공식 Service + **AgentCore**)를 image로 임베드 → 자체완결.
- `icon:` 어휘는 layout_aws.py와 동일 (`agentcore`, `arch:Amazon-Bedrock`, 공통 short names). Excalidraw는 내장 AWS 셰이프가 없어 **모든 아이콘이 임베드 이미지**입니다.
- 정식 인프라 다이어그램(충실도 우선)은 drawio(`layout_aws.py`)를 권장 — 스케치는 브레인스토밍·개념 설명용.

---

## 입력 정리 (그리기 전에)

"EKS 그려줘"만으로 추측하면 과밀·스파게티 다이어그램이 됩니다. 그리기 전에 컴포넌트 목록, 논리 그룹(VPC/서브넷/계정), **주 데이터 흐름**, 강조 포인트, 환경(단일 리전/Multi-AZ/멀티리전/DR), 외부 행위자, 용도(전체 슬라이드 vs 보안 리뷰)를 요청에서 정리하고 — 요청이 답하지 않아 다이어그램이 달라지는 항목만 `AskUserQuestion`으로 확인합니다. 서비스 목록은 지어내지 말고 소스(요청/코드/문서)에서 가져옵니다.

배치 규칙(VPC 안/밖, AZ 나란히, DB는 private 등): **`references/aws-reference-conventions.md`**.

---

## PPT용 캔버스 크기 (16:9 기준)

| 용도 | 크기 (px) |
|------|-----------|
| 전체 슬라이드 | 1920 x 1080 |
| 콘텐츠 영역 (권장) | 1600 x 900 |
| 절반 슬라이드 | 900 x 900 |

모든 AWS 아이콘은 아래에 서비스 이름 라벨 (`verticalLabelPosition=bottom`, `fontFamily=Amazon Ember`) — 라벨 없는 아이콘은 lint의 design 감점 대상.

---

## AWS 아이콘

| 카테고리 | 서비스 예시 |
|----------|-------------|
| Compute | EC2, Lambda, ECS, EKS |
| Storage | S3, EBS, EFS, Glacier |
| Database | RDS, DynamoDB, ElastiCache, Aurora |
| Networking | VPC, CloudFront, Route 53, ALB/NLB |
| Security | IAM, WAF, Shield, KMS |
| Integration | SQS, SNS, EventBridge, Step Functions |

> 전체 아이콘 목록: **`references/aws-icons.md`**. 색상·크기·간격 정본: **`references/design-tokens.md`** (여기서 값을 재기술하지 않음 — 재기술은 곧 drift).

**mxgraph에 없는 신규/제품 아이콘 (AgentCore 등):** 스펙에서 `icon: agentcore` 또는
`icon: "arch:<Service-Name>"`(예: `arch:Amazon-Bedrock`)를 쓰면 `reactive-presentation`의 공유
아이콘 라이브러리에서 가져와 base64로 임베드합니다(`.drawio` 자체완결). 상세: `references/aws-icons.md` → "공유 아이콘".

---

## ⚠️ 내보내기 전 검증 (필수 — 침묵 실패 방지)

> **drawio CLI는 잘못된 XML에서도 exit 0으로 "성공"하면서 셀의 90%를 조용히 누락시킵니다** —
> "완성된 듯하지만 텅 빈 PNG"의 주범입니다. **export 전에 반드시 검증**하세요.

```bash
# 0) 그리드 자동 정렬 — 좌표 1~5px 어긋남을 10px 그리드로 스냅 (아이콘 크기 78은 보존)
python3 scripts/snap_grid.py output.drawio --in-place

# 1) 구조 검증 — XML 침묵 킬러 / truncation
python3 scripts/validate_drawio.py output.drawio
# ✅ 통과 시 cells/vertices/edges/icons/groups 개수 출력 → 의도한 개수와 비교(누락 감지)
# ❌ 실패 시 export 금지하고 먼저 수정

# 2) 레이아웃 게이트 — geometry(정렬·이탈·겹침·간격·엣지) + design(아이콘 크기·라벨·여백·제목·폰트)
python3 scripts/lint_layout.py output.drawio
# ✅ layout score ≥ 80 이어야 export (--json 으로 세부 점수; 수치 정본: design-tokens.md)
```

**가장 흔한 침묵 킬러 (생성 시 절대 금지):**
- XML 주석 안의 `&` (예: `<!-- EDGE & AUTH -->`) 와 `--` (예: `<!-- ----- -->`) — XML 불법, 이후 모든 셀 누락
- 라벨/값 안의 미이스케이프 `&`, `<`, `>` → `&amp;` `&lt;` `&gt;`
- 장식용 주석은 **생략** 권장 (디버깅 가치 < 렌더 파괴 위험)

## PNG 내보내기

CLI 경로: Linux `/usr/bin/drawio` · macOS Homebrew `/opt/homebrew/bin/drawio`

```bash
# 고해상도 PNG (PPT용, 권장) — 투명 배경은 -t, SVG는 -f svg
drawio -x -f png -s 2 -o output.png input.drawio
# Headless Linux — xvfb 필요. dbus/GPU stderr 경고는 무시 가능.
xvfb-run -a drawio -x -f png -s 2 -o output.png input.drawio
```

> **export 후 확인**: PNG 용량이 비정상적으로 작거나(<10KB) 셀이 비면 truncation 의심 — validator의 cell 개수와 실제 렌더를 대조.

---

## 레이아웃 원칙

1. **외부에서 내부로**: 사용자/인터넷 → AWS Cloud → Region → VPC → Subnet
2. **왼쪽에서 오른쪽으로**: 데이터 흐름 방향
3. **계층 구분**: 프레젠테이션 → 애플리케이션 → 데이터
4. **같은 레벨 아이콘은 동일 크기** (표준 78×78; 좁은 subnet 중첩만 48) — 섞으면 산만해 보임
5. 범례/설명 박스는 VPC 영역과 겹치지 않게

## 엣지 라우팅 (품질의 핵심 — "안 이쁨"의 주원인)

스파게티 엣지가 다이어그램을 망치는 1순위입니다:

1. **같은 종류 리소스는 단일 컬럼(세로 일렬)으로 묶기** — 자동 라우팅이 옆 아이콘을 관통하는 문제가 사라지는 가장 효과적인 수정.
2. **직교 엣지 고정**: `edgeStyle=orthogonalEdgeStyle;rounded=0;`. 관통이 남으면 명시적 앵커로 출입점 고정: `exitX/exitY`(출발), `entryX/entryY`(도착).
3. **조밀한 밴드는 웨이포인트 레인**: `scripts/route_edges.py --from <id> --to <id> --via-x <X>`가 깨끗한 직교 웨이포인트 + 앵커를 계산 (수동 좌표 불필요). 들어오는(async)/나가는(sync) 엣지는 서로 다른 채널로 분리.
4. **엣지 종류별 색상/스타일 + 범례**: 동기 API(검정 실선), 비동기 이벤트(분홍 점선), AI 호출(초록) 등.
5. **연결이 많아 혼잡해지면 "번호 플로우" 패턴으로 압축** (snippets.md #33): 모든 연결을 다 그리지 말고 핵심 데이터 플로우 몇 개만 화살표로, 각각 단일 색 + 번호 배지(①②③)로. 부수적 연결은 번호 범례의 텍스트로만. 전문 AWS 다이어그램이 깔끔한 이유는 모든 연결을 그리지 않기 때문입니다.

---

## 참조 문서

| 파일 | 내용 |
|------|------|
| `references/design-tokens.md` | **정본(SINGLE SOURCE)** — 아이콘 크기(78×78)·컨테이너 색상·엣지·폰트·간격 |
| `references/aws-reference-conventions.md` | **배치 규칙** — VPC 안/밖, 흐름 방향, AZ 나란히, DB는 private, 범례/제목 |
| `references/aws-icons.md` | AWS 아이콘 shape 이름 및 스타일, 공유 아이콘 임베드 |
| `references/best-practices.md` | 아키텍처 다이어그램 모범사례 |
| `references/layout-patterns.md` | 3-Tier, 하이브리드 등 레이아웃 패턴 |
| `references/snippets.md` | 복사해서 사용할 XML 코드 조각 |
| `references/drawio-xml-guide.md` | XML 직접 작성 문법 가이드 |
| `references/mcp-setup-guide.md` | Draw.io MCP 설정 및 도구 사용법 |
| `scripts/layout_aws.py` | **스펙 생성기 (권장)** — YAML 스펙 → AWS 관례 좌표 자동계산 → .drawio |
| `examples/` | **골든 exemplar 라이브러리** — 게이트 통과하는 스펙+drawio 쌍, 새 다이어그램의 출발점 |
| `scripts/snap_grid.py` | export 전 0단계 — 좌표 10px 그리드 스냅 (`--in-place`/`--report`) |
| `scripts/validate_drawio.py` | export 전 검증 1 — 침묵 킬러 검출 + 셀 개수 리포트 (`--coords`) |
| `scripts/lint_layout.py` | export 전 검증 2 — 레이아웃 게이트, score ≥ 80 (`--json`) |
| `scripts/route_edges.py` | 엣지 웨이포인트 자동계산 — 직교 채널 라우팅 + 앵커 (`--list`) |

---

## Quality Review

배포/완료 선언 전 content-review-agent PASS — plugin CLAUDE.md의 Quality Gate 규칙 (Draw.io는 Visual-Testing 면제 → 90점 스케일; 사소한 손질은 재리뷰 없이 반영).
