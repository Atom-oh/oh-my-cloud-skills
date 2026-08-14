---
name: architecture-diagram
description: Generates AWS architecture diagrams (draw.io/.drawio → PNG/SVG). Activates when the user asks to "draw an architecture diagram," "create an AWS diagram," "infrastructure diagram," "system architecture," "cloud architecture," or requests an AWS/cloud configuration drawn as a draw.io/non-standard hand-drawn diagram (general draw.io drawing unrelated to AWS/cloud is out of scope). Standard patterns are generated coordinate-free via the YAML spec generator (layout_aws.py); irregular shapes are hand-authored as .drawio — two supported paths. The draw.io MCP is optional, for interactive editing.
allowed-tools:
  - Read
  - Write
  - Bash
---

# Architecture Diagram Skill

A skill for generating AWS architecture diagrams. Supports **three modes**:

| Mode | Approach | Advantages | When to use |
|------|------|------|----------|
| **Spec generator (recommended)** | `scripts/layout_aws.py` — YAML spec → .drawio | **Automatic coordinate calculation** · guarantees Multi-AZ mirror symmetry · always passes the gate | VPC/Multi-AZ/tiered · serverless/pipeline patterns (most common) |
| **Direct XML authoring** | Write tool creates a .drawio file directly | Full freedom | Irregular structures that don't fit generator patterns |
| **Draw.io MCP** | Real-time editing via MCP | Interactive edits, live preview | Optional (requires setup) |
| **Sketch (Excalidraw)** | `scripts/excalidraw_gen.py` — YAML spec → local `.excalidraw` | Hand-drawn/whiteboard aesthetic, same shared icons (including AgentCore) | Brainstorming/concept diagrams/casual feel (drawio is recommended for formal infra diagrams) |

> **Why a spec generator**: The root cause of the quality gap versus PPT is *the LLM placing pixel coordinates
> directly* (the weakest spatial-layout skill for an LLM). General-purpose auto-layout engines (D2/ELK,
> Python diagrams/Graphviz) don't know AWS conventions (AZ left-right mirroring, VPC nesting, left-to-right
> tiers) and break them. `layout_aws.py` lets the LLM **declare only structure, labels, and flow**, then
> deterministically computes AWS-convention coordinates and outputs drawio → passes the existing
> validate/lint gates as-is. Empirical basis: `examples/` + bake-off.
>
> See **`references/mcp-setup-guide.md`** for MCP setup instructions

---

## Spec-Driven Generation — recommended path

For VPC/Multi-AZ/tiered architectures, declare a high-level YAML spec **instead of writing coordinates directly**.

```bash
# 1) Write the spec (copy examples/multi-az-3tier.yaml as a starting point) — no coordinates, structure only
#    external(external actor) → edge(CDN/DNS/WAF) → region.vpc.{azs, tiers[].services} + flows
# 2) Generate
python3 scripts/layout_aws.py my-spec.yaml -o output.drawio
# 3) Gates (mandatory)
python3 scripts/validate_drawio.py output.drawio
python3 scripts/lint_layout.py output.drawio    # generator output is designed for 100/100 [geometry · design]
# 4) export
xvfb-run -a drawio -x -f png -s 2 -o output.png output.drawio
```

**Block composition** — arranged left-to-right as `[external] [onprem] [edge] [region(s)]`. Supports 4 patterns:
- **`vpc`** — Multi-AZ/tiered. AZs are automatically **mirrored** (equal size, left-right symmetric); service ids are instantiated per-AZ as `id_0`/`id_1`.
- **`stages`** — serverless/pipeline. `region.stages` lays out left-to-right stage columns without a VPC. ids are used as-is.
- **Multi-region** — a `regions:` list. Region ids get prefixes `r0_`/`r1_` (e.g. `{from: r0_rds, to: r1_rds, kind: async}`).
- **Hybrid** — an `onprem:` block (corporate DC container) + Direct Connect/VPN edge connecting to the Region.

- Icon registry, colors, and spacing all follow `design-tokens.md` as the single source of truth (built into the generator).
- Golden examples: **`examples/`** — `multi-az-3tier`, `eks-multi-az` (vpc), `serverless-api` (stages), `multi-region-dr` (regions), `hybrid-dx` (onprem). Spec+drawio pairs; copy and modify.
- Use direct XML authoring mode only for irregular structures that don't fit the 4 patterns above, such as a Transit Gateway mesh.

### Sketch output (Excalidraw) — whiteboard aesthetic

If you need a hand-drawn/whiteboard feel, output the same `stages` spec as a local `.excalidraw` (no server required):
```bash
python3 scripts/excalidraw_gen.py my-spec.yaml -o output.excalidraw
# → open in excalidraw.com / the VSCode Excalidraw extension / Obsidian for editing
```
- Embeds images from the shared icon library (reactive-presentation/icons — official Service icons + **AgentCore**) → self-contained.
- The `icon:` vocabulary is identical to layout_aws.py (`agentcore`, `arch:Amazon-Bedrock`, common short names). Excalidraw has no built-in AWS shapes, so **all icons are embedded images**.
- For formal infrastructure diagrams (where fidelity matters), drawio (`layout_aws.py`) is recommended — drawio wins per the bake-off. Sketches are for brainstorming/concept explanation.

---

## Diagram workflow for PPT

Diagrams for insertion into PPT **must** have their canvas size set.

### Canvas size (based on PPT 16:9)

| Use | Size (px) | Ratio |
|------|-----------|------|
| Full slide | 1920 x 1080 | 16:9 |
| Content area (recommended) | 1600 x 900 | 16:9 |
| Half slide | 900 x 900 | 1:1 |
| 2/3 slide | 1200 x 900 | 4:3 |

### Mandatory: show AWS icon labels

**Every** AWS icon **must** show its service name underneath:

```
┌─────────────┐
│   [icon]    │
│             │
│ Lambda      │  ← service name required
└─────────────┘
```

Label settings: `verticalLabelPosition=bottom`, `fontFamily=Amazon Ember`, `fontSize=12`

---

## AWS icon categories

| Category | Example services |
|----------|-------------|
| Compute | EC2, Lambda, ECS, EKS |
| Storage | S3, EBS, EFS, Glacier |
| Database | RDS, DynamoDB, ElastiCache, Aurora |
| Networking | VPC, CloudFront, Route 53, ALB/NLB |
| Security | IAM, WAF, Shield, KMS |
| Analytics | Kinesis, Athena, EMR, Redshift |
| Integration | SQS, SNS, EventBridge, Step Functions |

> See **`references/aws-icons.md`** for the full icon list

**New/product icons not in mxgraph (AgentCore, etc.):** In the spec, use `icon: agentcore` or
`icon: "arch:<Service-Name>"` (e.g. `arch:Amazon-Bedrock`) to pull it from `reactive-presentation`'s shared
icon library and embed it as base64 (`.drawio` stays self-contained). Details: `references/aws-icons.md` → "Shared icons".

---

## Color guide

> **The single source of truth is `references/design-tokens.md`** — container colors/icon sizes/edges/fonts/spacing are
> all defined there. Values are not restated here (restating them causes drift).

---

## Validate before exporting (mandatory — prevents silent failure)

> **The drawio CLI can "succeed" with exit 0 on malformed XML while silently dropping 90% of cells** —
> this is the main cause of "looks finished but the PNG is empty." **Always validate before exporting.**

```bash
# 0) Auto grid-snap — snaps coordinates off by 1-5px onto a 10px grid (preserves icon size 78)
python3 scripts/snap_grid.py output.drawio --in-place

# 1) Structural validation — catches silent XML killers / truncation
python3 scripts/validate_drawio.py output.drawio
# ✅ On pass, prints cells/vertices/edges/icons/groups counts → compare against the intended count (detects omissions)
# ❌ On failure, do not export — fix first

# 2) Layout gate — QA for "does this look like PPT?" Scored across two layers:
#    · geometry: grid alignment · out-of-container elements · icon overlap · spacing · edge budget
#    · design:   icon size discipline (78 + 48 for nesting; 40/60 retired) · missing labels · margins · title · font
python3 scripts/lint_layout.py output.drawio
# ✅ layout score must be ≥ 80 to export. Output: score/100 [geometry · design]
# ❌ If below threshold, fix the [geometry]/[design] findings and rerun (use --json for detailed scores)
# (canonical numbers: references/design-tokens.md)
```

**Most common silent killers (never do these when generating):**
- `&` inside an XML comment (must be `&amp;`) — e.g. `<!-- EDGE & AUTH -->` ❌ → best to avoid comments entirely
- `--` inside an XML comment (e.g. `<!-- ----- -->`) — illegal XML, drops all subsequent cells
- Unescaped `&`, `<`, `>` in labels/values → use `&amp;` `&lt;` `&gt;`
- Decorative comments are best **omitted** (their debugging value is lower than the render-breaking risk)

## PNG export

CLI path: Linux `/usr/bin/drawio` · macOS Homebrew `/opt/homebrew/bin/drawio`

```bash
# High-resolution PNG (for PPT, recommended)
drawio -x -f png -s 2 -o output.png input.drawio

# Headless Linux (no display) — requires xvfb. dbus/GPU stderr warnings can be ignored.
xvfb-run -a drawio -x -f png -s 2 -o output.png input.drawio

# Transparent background (for Dark theme PPT)
drawio -x -f png -s 2 -t -o output.png input.drawio

# SVG (vector, stays sharp when scaled)
drawio -x -f svg -o output.svg input.drawio
```

> **After export, check**: if the PNG size is abnormally small (<10KB) or cells are missing, suspect truncation.
> Cross-check the validator's cell count against the actual render.

### CLI options

| Option | Description | Recommended value |
|------|------|--------|
| `-x` | export mode | required |
| `-f <format>` | output format | png |
| `-s <scale>` | zoom factor | 2 |
| `-t` | transparent background | for Dark PPT |
| `-b <color>` | background color | #232F3E |

---

## Templates

| File | Purpose |
|------|------|
| `templates/aws-basic.drawio` | Basic VPC, Subnet, AZ structure |
| `templates/aws-samples.drawio` | Data Lake architecture sample, for copying icons |

### Using templates

1. Open `templates/aws-samples.drawio` in draw.io
2. Select the icon you need → copy (Cmd+C)
3. Paste into the new diagram (Cmd+V)
4. Adjust position and labels

---

## Workflow

### Step 0 — gather requirements up front (mandatory, before drawing)

Guessing from just "draw me EKS" produces a cluttered, spaghetti diagram. PPT-quality results come from
**structured input**. Ask via `AskUserQuestion` for anything missing (skip if already clear).

| # | Question | Reason | Default |
|---|------|------|--------|
| 1 | Component list | prevents hallucinated services | required |
| 2 | Logical groupings (VPC/subnet/account) | determines container hierarchy | inferred from components |
| 3 | **Primary data flows (up to 5 paths)** | determines the edge set | required |
| 4 | Emphasis points ("lead actor" of this diagram) | visual hierarchy | none (uniform) |
| 5 | Environment (single region / Multi-AZ / multi-region / DR) | layout strategy | single region, 2-AZ |
| 6 | External actors (users, on-prem, SaaS) | left-side placement | internet users |
| 7 | Canvas/purpose (full slide, security review vs. dev overview) | abstraction level | 1600×900, technical review |

> If there are more than 5 flows, use the **numbered flow pattern** (snippets.md #33) — arrows only for the
> primary path, the rest as ①②③ badges + legend.
> For placement rules (inside/outside VPC, AZs side by side, DB in private, etc.), see
> **`references/aws-reference-conventions.md`**.

### When using MCP

1. Open the Draw.io app
2. Confirm the MCP server connection (`/mcp`)
3. `get-shape-categories` → check the AWS category
4. `add-cell-of-shape` → add an AWS icon
5. `add-edge` → add a connecting line
6. `edit-cell` → adjust styling

### When authoring XML directly

1. Copy a template file or write the base structure
2. Add AWS icon shapes
3. Add connecting lines (edges)
4. Export PNG

> See **`references/drawio-xml-guide.md`** for detailed XML syntax

---

## Layout principles

1. **Outside to inside**: users/internet → AWS Cloud → Region → VPC → Subnet
2. **Left to right**: direction of data flow
3. **Tier separation**: presentation → application → data
4. **Show AZs**: clearly separate availability zones when depicting high availability
5. **Avoid element overlap**: place legend/description boxes so they don't overlap the VPC area

## Edge routing (the crux of quality — the #1 cause of "ugly" diagrams)

Spaghetti edges are the number-one thing that ruins a diagram. Follow these rules:

1. **Group same-kind resources into a single column (vertical row)**. Stacking multiple Lambdas vertically
   in one group eliminates the problem of auto-routing cutting through neighboring icons (the most effective fix).
2. **Pin orthogonal edges**: `edgeStyle=orthogonalEdgeStyle;rounded=0;`. If auto-routing still cuts through an
   icon, pin the entry/exit points with **explicit anchors**: `exitX/exitY` (departure), `entryX/entryY`
   (arrival) — e.g. to exit from the right-center: `exitX=1;exitY=0.5;exitDx=0;exitDy=0;`.
3. **Use waypoint lanes for dense bands**: when there are many edges, group them into common vertical/horizontal
   channels (lanes) to reduce crossings. **`scripts/route_edges.py --from <id> --to <id> --via-x <X>`**
   (or `--via-y`) computes clean orthogonal waypoints + exit/entry anchors for you (no manual absolute-coordinate
   math needed). Separate incoming (async) and outgoing (sync) edges into **different X channels**.
4. **Distinguish edge types by color/style + add a legend**: synchronous API (solid black), WebSocket (dashed
   blue), async event (dashed pink), AI call (green), auth (dashed red), etc. Place the legend in an empty
   corner without overlap.
5. **Adjust edge label position** so labels don't overlap borders/icons.
6. **If there are many edges (>~15), reduce them — the "numbered flow" pattern** (the decisive technique for
   making dense diagrams look clean): instead of drawing every connection, compress to **around 5 core data
   flows**, each with a single color + numbered badge (①②③④⑤). Secondary connections (auth JWKS, authorizer,
   static assets, etc.) are shown **only as text in the numbered legend**. Information density is the root
   cause of clutter — professional AWS diagrams look clean because they don't draw every connection.

## Icon sizing (uniformity)

| Level | Size | Use |
|------|------|------|
| Standard service icon | **78x78** | most AWS services (default) |
| Nested resource | 48-52 | only when packing multiple resources into a narrow subnet |

> Icons at the same level within one diagram **must** be the same size. Mixing sizes looks cluttered.

> See **`references/layout-patterns.md`** for layout pattern details

---

## Reference documents

| File | Content |
|------|------|
| `references/design-tokens.md` | **Single source of truth** — icon size (78×78), container colors, edges, fonts, spacing. Other docs must match these values |
| `references/aws-reference-conventions.md` | **Placement rules** — inside/outside VPC, flow direction, AZs side by side, DB in private, legend/title (closes the PPT "taste" gap) |
| `references/aws-icons.md` | AWS icon shape names and style |
| `references/best-practices.md` | Best practices for architecture diagrams |
| `references/layout-patterns.md` | Layout patterns: 3-Tier, hybrid, etc. |
| `references/snippets.md` | Copy-and-use XML code snippets |
| `references/drawio-xml-guide.md` | Direct XML authoring syntax guide |
| `references/mcp-setup-guide.md` | Draw.io MCP setup and tool usage |
| `scripts/layout_aws.py` | **Spec generator (recommended)** — YAML spec (structure/labels/flow) → AWS-convention coordinate calculation → .drawio. Built-in Multi-AZ mirroring, VPC nesting, tier placement, edge anchors. See `examples/` |
| `examples/` | **Golden exemplar library** — spec+drawio pairs that pass the gate at 100/100 (multi-az-3tier, eks-multi-az). Starting point for new diagrams |
| `scripts/snap_grid.py` | **Pre-export step 0** — auto-snaps all coordinates to a 10px grid (preserves icon size 78). `--in-place`/`--report` |
| `scripts/validate_drawio.py` | **Pre-export validation 1** — detects silent killers (`&`/`--` in comments, unescaped characters, DOCTYPE) + reports cell counts (detects truncation) + `--coords` for absolute coordinates |
| `scripts/lint_layout.py` | **Pre-export validation 2 (layout gate)** — scores geometry (alignment/overflow/overlap/spacing/edges) + design (icon size discipline/labels/margins/title/fonts). `score/100 [geometry · design]`, score must be ≥ 80 to export |
| `scripts/route_edges.py` | **Auto-computes edge waypoints** — given `--from/--to`, generates a clean orthogonal path (channel routing) + entry/exit anchors. The key tool for cleaning up messy arrows. Use `--list` to check absolute cell coordinates |

---

## Quality Review (mandatory before declaring deployment/completion)

Applies to new diagrams and substantive revisions — minor touch-ups like typo fixes or one-line edits don't need re-review.

1. Call content-review-agent → `review content at [file path]`
2. On a FAIL/REVIEW verdict, fix and re-review (up to 3 times)
3. Declare completion only after obtaining a PASS on the applicable scale (100-point scale: ≥85 / non-HTML 90-point scale: ≥77 — see content-review-agent's Verdict table)

---

## Verification checklist

- [ ] **Passes `scripts/validate_drawio.py`** (mandatory before export — prevents silent truncation)
- [ ] **`scripts/lint_layout.py` layout score ≥ 80** (mandatory before export — geometry: alignment/overlap/spacing/edges · design: icon size/labels/margins/title/fonts)
- [ ] Cell/icon counts match intent (cross-check against validator output)
- [ ] No `&`/`--` in XML comments (or comments not used at all)
- [ ] Icon size unified to 78×78 (design-tokens.md)
- [ ] Amazon Ember font set on all text
- [ ] Using official AWS colors (Public=green/Private=teal, design-tokens.md)
- [ ] Hierarchy is clear (Cloud > Region > VPC > Subnet)
- [ ] Data flow direction is consistent (left→right)
- [ ] Edges are orthogonal and don't cut through icons
- [ ] Edge types are distinguished by color/style with a legend
- [ ] Icon sizes at the same level are uniform (standard 78x78)
- [ ] Labels are placed below icons
