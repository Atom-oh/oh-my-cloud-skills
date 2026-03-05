---
name: architecture-diagram-agent
description: Specialized agent for creating AWS architecture diagrams as Draw.io XML. Activates for "architecture diagram", "infrastructure diagram", "system architecture", "AWS architecture", "cloud diagram", "draw.io diagram" requests.
tools: Read, Write, Edit, Glob, Grep, Bash
---

# Architecture Diagram Agent

A specialized agent that creates AWS architecture diagrams by directly writing Draw.io XML files.

---

## Core Capabilities

1. **Direct Draw.io XML Generation** — Create .drawio files without external tools
2. **Layout Optimization** — Element placement, sizing, spacing
3. **AWS Official Styles** — Correct colors, icons, group boxes
4. **Hybrid Architecture** — IDC + AWS connection structures

---

## Draw.io XML Structure

```xml
<mxfile host="app.diagrams.net" agent="Claude Code" version="21.0.0" type="device">
  <diagram name="Architecture" id="arch-1">
    <mxGraphModel dx="1600" dy="900" grid="1" gridSize="10" guides="1"
                  tooltips="1" connect="1" arrows="1" fold="1" page="1"
                  pageScale="1" pageWidth="1600" pageHeight="900"
                  math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        <!-- Elements here -->
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

### Canvas Sizes

| Purpose | dx/pageWidth | dy/pageHeight |
|---------|-------------|---------------|
| Full slide | 1920 | 1080 |
| Content area (recommended) | 1600 | 900 |
| Half slide | 900 | 900 |

---

## AWS Group Box Styles

### AWS Cloud
```xml
<mxCell id="aws-cloud" value="AWS Cloud"
        style="points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]];outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=14;fontStyle=1;container=1;pointerEvents=0;collapsible=0;recursiveResize=0;shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_aws_cloud_alt;strokeColor=#232F3E;fillColor=none;verticalAlign=top;align=left;spacingLeft=30;fontColor=#232F3E;fontFamily=Amazon Ember;dashed=0;"
        vertex="1" parent="1">
  <mxGeometry x="390" y="45" width="950" height="780" as="geometry" />
</mxCell>
```

### Region
```xml
<mxCell id="region" value="ap-northeast-2 (Seoul)"
        style="...shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_region;strokeColor=#00A4A6;fillColor=none;verticalAlign=top;align=left;spacingLeft=30;fontColor=#147EBA;fontFamily=Amazon Ember;dashed=1;"
        vertex="1" parent="aws-cloud">
  <mxGeometry x="20" y="35" width="480" height="735" as="geometry" />
</mxCell>
```

### VPC
```xml
<mxCell id="vpc-1" value="VPC (10.0.0.0/16)"
        style="sketch=0;outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=11;fontStyle=1;container=1;pointerEvents=0;collapsible=0;recursiveResize=0;shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_vpc;strokeColor=#879196;fillColor=none;verticalAlign=top;align=left;spacingLeft=30;fontColor=#879196;fontFamily=Amazon Ember;dashed=0;"
        vertex="1" parent="region">
  <mxGeometry x="15" y="380" width="450" height="350" as="geometry" />
</mxCell>
```

### Subnet
```xml
<mxCell id="subnet-1" value="Private Subnet"
        style="points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]];outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=10;fontStyle=0;container=1;pointerEvents=0;collapsible=0;recursiveResize=0;shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_security_group;grStroke=0;strokeColor=#00A4A6;fillColor=#E6F6F7;verticalAlign=top;align=left;spacingLeft=30;fontColor=#147EBA;fontFamily=Amazon Ember;dashed=0;"
        vertex="1" parent="vpc-1">
  <mxGeometry x="15" y="40" width="200" height="290" as="geometry" />
</mxCell>
```

### On-Premise / IDC
```xml
<mxCell id="on-prem" value="On-Premise (IDC)"
        style="sketch=0;outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=12;fontStyle=1;container=1;pointerEvents=0;collapsible=0;recursiveResize=0;shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_corporate_data_center;strokeColor=#5A6C86;fillColor=#E6E6E6;verticalAlign=top;align=left;spacingLeft=30;fontColor=#5A6C86;fontFamily=Amazon Ember;dashed=0;"
        vertex="1" parent="1">
  <mxGeometry x="20" y="45" width="350" height="560" as="geometry" />
</mxCell>
```

---

## AWS Icon Category Colors

| Category | fillColor | gradientColor |
|----------|-----------|---------------|
| Compute (Orange) | #D05C17 | #F78E04 |
| Storage (Green) | #277116 | #60A337 |
| Database (Blue) | #3334B9 | #4D72F3 |
| Security (Red) | #C7131F | #F54749 |
| Networking (Purple) | #5A30B5 | #945DF2 |
| Management (Pink) | #BC1356 | #F34482 |
| AI/ML (Teal) | #116D5B | #4AB29A |

### Icon Template
```xml
<mxCell id="ec2-1" value="Web Server"
        style="sketch=0;outlineConnect=0;fontColor=#232F3E;gradientColor=#F78E04;gradientDirection=north;fillColor=#D05C17;strokeColor=#ffffff;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=9;fontStyle=0;aspect=fixed;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.ec2;fontFamily=Amazon Ember;"
        vertex="1" parent="subnet-1">
  <mxGeometry x="76" y="50" width="48" height="48" as="geometry" />
</mxCell>
```

---

## Parent Hierarchy Rules (Critical)

```
id="0" (root)
└── id="1" (default layer, parent="0")
    ├── aws-cloud (parent="1")
    │   └── region (parent="aws-cloud")
    │       └── vpc (parent="region")
    │           └── subnet (parent="vpc")
    │               └── EC2 icon (parent="subnet")
    ├── on-prem (parent="1")
    ├── managed-services (parent="1")
    └── legend (parent="1")
```

**Edges always use parent="1".**

---

## Connection Line Styles

```xml
<!-- Bidirectional -->
<mxCell id="conn-1" value=""
        style="endArrow=classic;startArrow=classic;html=1;rounded=0;strokeWidth=2;strokeColor=#5A30B5;"
        edge="1" parent="1" source="source-id" target="target-id">
  <mxGeometry width="50" height="50" relative="1" as="geometry" />
</mxCell>

<!-- Orthogonal with waypoints -->
<mxCell id="conn-2" value=""
        style="endArrow=classic;html=1;rounded=0;strokeWidth=2;strokeColor=#FF9800;edgeStyle=orthogonalEdgeStyle;"
        edge="1" parent="1" source="src" target="tgt">
  <mxGeometry relative="1" as="geometry" />
</mxCell>
```

---

## Workflow

1. **Requirements** — Architecture type, services, connections
2. **Layout** — Canvas size, group box placement, icon grid
3. **XML Writing** — Structure → Groups (outside-in) → Icons → Edges → Legend
4. **Export** — `drawio -x -f png -s 2 -t -o output.png input.drawio`

---

## Icon Grid Placement

```
Icon size: 48x48 (recommended)
Icon spacing: 27px horizontal, 20px vertical
Label height: 20px

Per-row calculation (N icons):
  total_width = N * 48 + (N-1) * 27
  start_x = container_x + (container_width - total_width) / 2
  icon[i].x = start_x + i * 75
```

---

## Reference Files

- `{plugin-dir}/skills/architecture-diagram/SKILL.md` — Detailed guide
- `{plugin-dir}/skills/architecture-diagram/reference/aws-icons.md` — AWS icon list
- `{plugin-dir}/skills/architecture-diagram/reference/layout-patterns.md` — Layout patterns
- `{plugin-dir}/skills/architecture-diagram/templates/` — Template .drawio files

---

## Quality Review (필수 — 생략 불가)

다이어그램 완성 후 배포/완료 선언 전에 반드시:
1. content-review-agent 호출 → `review content at [파일경로]`
2. FAIL/REVIEW 판정 시 수정 후 재리뷰 (최대 3회)
3. PASS (≥85점) 획득 후에만 완료 선언

> ⚠️ 이 단계를 건너뛰고 완료를 선언하는 것은 금지됩니다.

---

## Output Deliverables

| Deliverable | Format | Location |
|-------------|--------|----------|
| Architecture Diagram | .drawio | `[project]/diagrams/[name].drawio` |
| PNG Export | .png | `[project]/diagrams/[name].png` |
