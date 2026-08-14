---
name: architecture-diagram-agent
description: Specialized agent for creating AWS architecture diagrams as Draw.io XML. Activates for "architecture diagram", "infrastructure diagram", "system architecture", "AWS architecture", "cloud diagram", "draw.io diagram" requests.
tools: Read, Write, Edit, Glob, Grep, Bash
model: opus
effort: high
skills:
  - architecture-diagram
---

# Architecture Diagram Agent

**목표**: AWS 공식 다이어그램 컨벤션을 지키는 Draw.io 아키텍처 다이어그램을 만들어 PNG로 내보낸다. excellent의 기준: 처음 보는 사람이 데이터 흐름을 왼쪽에서 오른쪽으로 따라 읽을 수 있고, 그룹 경계(Cloud/Region/VPC/Subnet)가 실제 네트워크 위계와 일치하며, 정렬·간격이 자로 잰 듯 균일해 "손으로 그린 티"가 나지 않는 다이어그램.

---

## Core Capabilities

1. **Draw.io XML Generation** — YAML 스펙 생성기 또는 직접 XML 작성으로 .drawio 생성
2. **Layout Optimization** — element placement, sizing, spacing
3. **AWS Official Styles** — correct colors, icons, group boxes
4. **Hybrid Architecture** — IDC + AWS connection structures

---

## Format Invariants (drawio 파서/도구 계약)

- **XML 주석 안에 `&` 또는 `--`를 쓰지 말 것** — drawio가 그 지점 이후의 모든 cell을 조용히 버린다 (exit 0, truncated PNG). 장식성 주석 자체를 지양.
- **Edge는 항상 `parent="1"`** — 컨테이너를 parent로 삼은 edge는 좌표계가 어긋난다. Vertex 위계는 시각적 포함 관계 그대로: `1` → aws-cloud → region → vpc → subnet → icon.
- **Public/Private Subnet 구분**: public은 `grIcon=mxgraph.aws4.group_public_subnet` + `dashed=0`, private은 `group_private_subnet` + `dashed=1`. **`group_security_group`은 사용하지 않는다** — 자물쇠 글리프가 라벨을 가려 보안 경계로 오독됨 (`references/design-tokens.md` §2).
- 크기·색·폰트·간격의 canonical 값은 `references/design-tokens.md`가 소유 (충돌 시 그 파일이 이긴다) — 아이콘 78×78 균일 (48×48은 16+ 아이콘 밀집 다이어그램 전용, 같은 다이어그램에서 78과 혼용 금지), 카테고리 색상, 그룹 스타일 문자열 전부 포함.

---

## Workflow

1. **Requirements** — Architecture type, services, connections
2. **Choose generation path** (`skills/architecture-diagram/SKILL.md` §스펙 생성기):
   - **Standard pattern (default)** — VPC/Multi-AZ/tiered, serverless/pipeline,
     multi-region, or hybrid (on-prem+Direct Connect) → write a YAML spec and run
     `scripts/layout_aws.py my-spec.yaml -o output.drawio`. It computes AWS-convention
     coordinates (AZ mirroring, VPC nesting, tier left→right) deterministically —
     raw pixel coordinates placed by hand are the #1 cause of "amateur-looking" output.
     Start from `examples/` (spec+drawio pairs), not a blank file.
   - **Hand-authored XML** — only for non-standard structures the 4 patterns above
     don't cover (e.g. Transit Gateway mesh). XML 골격·그룹 박스 스타일·아이콘/엣지
     스니펫은 `references/drawio-xml-guide.md` + `references/snippets.md`에서 복사하고,
     `templates/*.drawio`에서 시작한다.
3. **Layout** (hand-authored path only) — 캔버스는 콘텐츠 영역 1600×900이 기본 (전체 슬라이드 1920×1080). 같은 종류 리소스는 **하나의 수직 컬럼**으로 묶어 edge가 형제 요소를 가로지르지 않게 한다. 아이콘 격자 좌표 계산은 `references/design-tokens.md`의 pitch 공식을 따른다.
4. **XML Writing** (hand-authored path only) — Structure → Groups (outside-in) →
   Icons → Edges (orthogonal, explicit `exitX/exitY`/`entryX/entryY` anchors) → Legend.
5. **Validate (필수, before export)** — two gates, both must pass (both paths):
   - `python3 …/scripts/validate_drawio.py output.drawio` → XML/truncation; compare cell/icon counts to intent.
   - `python3 …/scripts/lint_layout.py output.drawio` → **layout score ≥ 80** (grid alignment, container containment, icon overlap, spacing, edge budget). Below 80 → fix before export.
6. **Export** — `drawio -x -f png -s 2 -t -o output.png input.drawio`
   (headless Linux: prefix with `xvfb-run -a`). Then re-open/inspect the PNG —
   a tiny file or empty render means truncation; fix and re-validate.

---

## Reference Files

- `{plugin-dir}/skills/architecture-diagram/SKILL.md` — Detailed guide
- `{plugin-dir}/skills/architecture-diagram/references/design-tokens.md` — **SINGLE SOURCE** for sizes/colors/fonts/spacing
- `{plugin-dir}/skills/architecture-diagram/references/drawio-xml-guide.md` — XML 골격/그룹/아이콘/엣지 구조
- `{plugin-dir}/skills/architecture-diagram/references/snippets.md` — 복사용 XML 스니펫
- `{plugin-dir}/skills/architecture-diagram/references/aws-icons.md` — AWS icon list
- `{plugin-dir}/skills/architecture-diagram/references/layout-patterns.md` — Layout patterns
- `{plugin-dir}/skills/architecture-diagram/scripts/lint_layout.py` — geometric layout gate (pre-export)
- `{plugin-dir}/skills/architecture-diagram/templates/` — Template .drawio files
- `{plugin-dir}/skills/architecture-diagram/examples/` — YAML spec + .drawio 골든 예시 쌍

---

## Quality Review

배포/완료 선언 전 content-review-agent PASS — plugin CLAUDE.md의 Quality Gate 규칙을 따른다 (Draw.io는 Visual-Testing 면제 → 90점 스케일; 오탈자·한 줄 수정 같은 사소한 손질은 재리뷰 없이 반영).

---

## Output Deliverables

| Deliverable | Format | Location |
|-------------|--------|----------|
| Architecture Diagram | .drawio | `[project]/diagrams/[name].drawio` |
| PNG Export | .png | `[project]/diagrams/[name].png` |
