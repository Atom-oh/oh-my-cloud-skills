---
name: architecture-diagram
description: AWS 아키텍처 다이어그램(draw.io/.drawio → PNG·SVG)을 생성. 사용자가 "아키텍처 다이어그램 그려줘", "AWS 구성도 만들어줘", "인프라 다이어그램", "시스템 아키텍처", "클라우드 아키텍처", 또는 AWS/클라우드 구성을 draw.io/비표준 손그림 다이어그램으로 그려달라고 요청할 때 활성화(AWS·클라우드 무관한 일반 draw.io 작도는 대상 아님). 표준 패턴은 YAML 스펙 생성기(layout_aws.py)로 좌표 없이 생성하고, 비정형 도형은 손으로 .drawio를 작성하는 두 경로를 지원 — draw.io MCP는 선택적 대화형 편집용.
allowed-tools:
  - Read
  - Write
  - Bash
---

# Architecture Diagram Skill

A skill that generates AWS architecture diagrams. **Goal**: a diagram that a first-time viewer can read left-to-right as data flow, where group boundaries match the actual network hierarchy, with uniform alignment and spacing — ready to drop straight into a slide deck. **Supports four modes**:

| Mode | Approach | Advantages | When to use |
|------|------|------|----------|
| **Spec generator (recommended)** | `scripts/layout_aws.py` turns a YAML spec into .drawio | **Automatic coordinate calculation** · guarantees Multi-AZ mirror symmetry · always passes the gate | VPC/Multi-AZ/tier · serverless/pipeline patterns (the most common case) |
| **Hand-written XML** | Create a .drawio file directly with the Write tool | Complete freedom | Irregular structures that don't fit the generator's patterns |
| **Draw.io MCP** | Live editing via MCP | Interactive edits, real-time preview | Optional (setup: `references/mcp-setup-guide.md`) |
| **Sketch (Excalidraw)** | `scripts/excalidraw_gen.py` turns a YAML spec into a local `.excalidraw` | Hand-drawn/whiteboard aesthetic, same shared icons (including AgentCore) | Brainstorming, concept diagrams, casual feel (drawio is recommended for formal infrastructure diagrams) |

> **Why the spec generator**: the root cause of the quality gap versus a slide deck is *hand-placing pixel coordinates*.
> Even general-purpose auto-layout engines (D2/ELK, Python diagrams/Graphviz) don't know AWS conventions
> (AZ left-right mirroring, VPC nesting, left-to-right tiers) and break them. `layout_aws.py` only requires you
> to declare **structure, labels, and flow**, and it deterministically computes AWS-convention coordinates and
> emits drawio — which then passes the validate/lint gates as-is.

---

## Spec-Driven Generation — the recommended path

For VPC / Multi-AZ / tiered architectures, **don't write coordinates by hand** — declare them as a high-level YAML spec.

```bash
# 1) Write the spec (copy examples/multi-az-3tier.yaml as a starting point) — no coordinates, structure only
#    external (outside actors) → edge (CDN/DNS/WAF) → region.vpc.{azs, tiers[].services} + flows
# 2) Generate
python3 scripts/layout_aws.py my-spec.yaml -o output.drawio
# 3) Gates (required)
python3 scripts/validate_drawio.py output.drawio
python3 scripts/lint_layout.py output.drawio
# 4) export
xvfb-run -a drawio -x -f png -s 2 -o output.png output.drawio
```

**Block composition** — arranged left-to-right as `[external] [onprem] [edge] [region(s)]`. Supports 4 patterns:
- **`vpc`** — Multi-AZ/tiered. AZs are auto-**mirrored** (identical size, left-right symmetric); service ids are instantiated per AZ as `id_0`/`id_1`.
- **`stages`** — serverless/pipeline. `region.stages` lays out left-to-right stage columns with no VPC. Ids are used as-is.
- **Multi-region** — a `regions:` list. Per-region id prefixes `r0_`/`r1_` (e.g. `{from: r0_rds, to: r1_rds, kind: async}`).
- **Hybrid** — an `onprem:` block (corporate DC container) connected to the Region via a Direct Connect/VPN edge.

- Icon registry, colors, and spacing all follow the canonical `design-tokens.md` (baked into the generator).
- Golden examples: **`examples/`** — `multi-az-3tier` and `eks-multi-az` (vpc), `serverless-api` (stages), `multi-region-dr` (regions), `hybrid-dx` (onprem). Each is a spec+drawio pair — copy and modify.
- Use hand-written XML mode only for irregular structures that don't fit the 4 patterns above (e.g. a Transit Gateway mesh) — start from a template (`templates/`), with syntax covered in `references/drawio-xml-guide.md` + `references/snippets.md`.

### Sketch output (Excalidraw) — whiteboard aesthetic

If you need a hand-drawn/whiteboard feel, output the same `stages` spec as a local `.excalidraw` (no server required):
```bash
python3 scripts/excalidraw_gen.py my-spec.yaml -o output.excalidraw
# → open and edit in excalidraw.com / the VSCode Excalidraw extension / Obsidian
```
- Embeds icons from the shared icon library (reactive-presentation/icons — official Service icons plus **AgentCore**) as images → self-contained.
- The `icon:` vocabulary is identical to layout_aws.py (`agentcore`, `arch:Amazon-Bedrock`, common short names). Excalidraw has no built-in AWS shapes, so **every icon is an embedded image**.
- For formal infrastructure diagrams (where fidelity matters most), drawio (`layout_aws.py`) is recommended — sketches are for brainstorming and conceptual explanation.

---

## Clarify the input (before drawing)

Guessing from just "draw me an EKS diagram" produces an overcrowded, spaghetti-edge diagram. Before drawing, pin down from the request: the component list, logical grouping (VPC/subnet/account), the **primary data flow**, points to emphasize, the environment (single region / Multi-AZ / multi-region / DR), external actors, and purpose (full slide vs. security review) — and use `AskUserQuestion` only for items the request leaves unanswered where the diagram would actually differ depending on the answer. Don't invent the service list; take it from a source (the request, code, or docs).

Placement rules (inside/outside VPC, AZs side by side, DB in private subnet, etc.): **`references/aws-reference-conventions.md`**.

---

## Canvas size for slides (16:9 baseline)

| Use | Size (px) |
|------|-----------|
| Full slide | 1920 x 1080 |
| Content area (recommended) | 1600 x 900 |
| Half slide | 900 x 900 |

Every AWS icon gets a service-name label below it (`verticalLabelPosition=bottom`, `fontFamily=Amazon Ember`) — an unlabeled icon costs design points in the lint gate.

---

## AWS Icons

| Category | Example services |
|----------|-------------|
| Compute | EC2, Lambda, ECS, EKS |
| Storage | S3, EBS, EFS, Glacier |
| Database | RDS, DynamoDB, ElastiCache, Aurora |
| Networking | VPC, CloudFront, Route 53, ALB/NLB |
| Security | IAM, WAF, Shield, KMS |
| Integration | SQS, SNS, EventBridge, Step Functions |

> Full icon list: **`references/aws-icons.md`**. Canonical colors/sizes/spacing: **`references/design-tokens.md`** (values are not restated here — restating them would just cause drift).

**New/product icons not in mxgraph (e.g. AgentCore):** in the spec, use `icon: agentcore` or
`icon: "arch:<Service-Name>"` (e.g. `arch:Amazon-Bedrock`) to pull the icon from
`reactive-presentation`'s shared icon library and embed it as base64 (keeping the `.drawio` self-contained). Details: `references/aws-icons.md` → "Shared icons".

---

## ⚠️ Validate before export (required — prevents silent failure)

> **The drawio CLI "succeeds" with exit 0 even on malformed XML, while silently dropping 90% of cells** —
> the leading cause of "looks finished but the PNG is empty." **Always validate before export.**

```bash
# 0) Auto grid-snap — snaps coordinates off by 1-5px onto a 10px grid (preserves the 78px icon size)
python3 scripts/snap_grid.py output.drawio --in-place

# 1) Structural validation — catches XML silent killers / truncation
python3 scripts/validate_drawio.py output.drawio
# ✅ On pass, prints cells/vertices/edges/icons/groups counts → compare against the intended count (detects omissions)
# ❌ On failure, do not export — fix it first

# 2) Layout gate — geometry (alignment, overflow, overlap, spacing, edges) + design (icon size, labels, margins, title, font)
python3 scripts/lint_layout.py output.drawio
# ✅ layout score must be ≥ 80 before export (use --json for the detailed breakdown; canonical thresholds live in design-tokens.md)
```

**Most common silent killers (never do these when generating):**
- `&` inside an XML comment (e.g. `<!-- EDGE & AUTH -->`) and `--` inside a comment (e.g. `<!-- ----- -->`) — both are illegal XML and cause every subsequent cell to be dropped
- Unescaped `&`, `<`, `>` inside labels/values → must be `&amp;` `&lt;` `&gt;`
- Decorative comments are best **omitted entirely** (debugging value < risk of breaking the render)

## PNG export

CLI path: Linux `/usr/bin/drawio` · macOS Homebrew `/opt/homebrew/bin/drawio`

```bash
# High-resolution PNG (recommended for slides) — transparent background: -t; SVG: -f svg
drawio -x -f png -s 2 -o output.png input.drawio
# Headless Linux — requires xvfb. dbus/GPU stderr warnings are safe to ignore.
xvfb-run -a drawio -x -f png -s 2 -o output.png input.drawio
```

> **Check after export**: if the PNG is abnormally small (<10KB) or cells appear missing, suspect truncation — cross-check the validator's cell count against the actual render.

---

## Layout principles

1. **Outside to inside**: user/internet → AWS Cloud → Region → VPC → Subnet
2. **Left to right**: the direction of data flow
3. **Tier separation**: presentation → application → data
4. **Icons at the same level get the same size** (standard 78×78; only tightly nested subnets use 48) — mixing sizes looks cluttered
5. Keep legend/caption boxes from overlapping the VPC area

## Edge routing (the key to quality — the main cause of an "ugly" diagram)

Spaghetti edges are the #1 thing that ruins a diagram:

1. **Group same-kind resources into a single column (vertical line)** — the single most effective fix, since it eliminates the case where auto-routing cuts through a neighboring icon.
2. **Pin edges to orthogonal routing**: `edgeStyle=orthogonalEdgeStyle;rounded=0;`. If edges still cut through, pin explicit entry/exit anchors: `exitX/exitY` (departure point), `entryX/entryY` (arrival point).
3. **Use waypoint lanes for dense bands**: `scripts/route_edges.py --from <id> --to <id> --via-x <X>` computes clean orthogonal waypoints plus anchors (no manual coordinates needed). Separate incoming (async) and outgoing (sync) edges into different channels.
4. **Color/style edges by kind, with a legend**: synchronous API calls (solid black), asynchronous events (dashed pink), AI calls (green), etc.
5. **When too many connections make things cluttered, compress with a "numbered flow" pattern** (snippets.md #33): don't draw every connection — draw only the handful of key data flows as arrows, each in a single color with a numbered badge (①②③). Show secondary connections only as text in the numbered legend. Professional AWS diagrams look clean precisely because they don't draw every connection.

---

## Reference documents

| File | Content |
|------|------|
| `references/design-tokens.md` | **Single source of truth** — icon size (78×78), container colors, edges, fonts, spacing |
| `references/aws-reference-conventions.md` | **Placement rules** — inside/outside VPC, flow direction, AZs side by side, DB in private subnet, legend/title |
| `references/aws-icons.md` | AWS icon shape names and styles, shared-icon embedding |
| `references/best-practices.md` | Architecture diagram best practices |
| `references/layout-patterns.md` | Layout patterns such as 3-Tier and hybrid |
| `references/snippets.md` | Copy-paste XML code snippets |
| `references/drawio-xml-guide.md` | Syntax guide for hand-writing XML |
| `references/mcp-setup-guide.md` | Draw.io MCP setup and tool usage |
| `scripts/layout_aws.py` | **Spec generator (recommended)** — YAML spec → auto-computed AWS-convention coordinates → .drawio |
| `examples/` | **Golden exemplar library** — spec+drawio pairs that pass the gate, starting points for new diagrams |
| `scripts/snap_grid.py` | Pre-export step 0 — snaps coordinates to a 10px grid (`--in-place`/`--report`) |
| `scripts/validate_drawio.py` | Pre-export validation 1 — detects silent killers + reports cell counts (`--coords`) |
| `scripts/lint_layout.py` | Pre-export validation 2 — layout gate, score ≥ 80 (`--json`) |
| `scripts/route_edges.py` | Auto-computes edge waypoints — orthogonal channel routing + anchors (`--list`) |

---

## Quality Review

Requires a content-review-agent PASS before deployment/declaring completion — per the Quality Gate rule in the plugin's CLAUDE.md (Draw.io is Visual-Testing-exempt → judged on the 90-point scale; minor touch-ups can be applied without a re-review).
