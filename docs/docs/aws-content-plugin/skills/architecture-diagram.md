---
sidebar_position: 2
title: "Architecture Diagram"
---

# Architecture Diagram Skill

Create AWS architecture diagrams using Draw.io. The recommended path is the **spec-driven layout engine** (`layout_aws.py`): a compact YAML spec → a clean `.drawio` with auto-computed coordinates, Multi-AZ mirror symmetry, VPC nesting, tier placement, and edge anchors — so it always passes the layout/design gate. Hand-authored XML and Draw.io MCP remain available for non-standard shapes and live editing, and a sketch-style `.excalidraw` generator (`excalidraw_gen.py`) reuses the same shared AWS icon vocabulary for whiteboard-style concept diagrams.

## Trigger Keywords

Activated by the following keywords:
- "architecture diagram", "draw architecture"
- "AWS diagram", "create infrastructure diagram"
- "system architecture", "cloud architecture"

## Supported Modes

| Mode | Method | Advantages | When to Use |
|------|--------|------------|-------------|
| **Spec generator (recommended)** | `scripts/layout_aws.py` — YAML/JSON spec → .drawio | Auto-computed coordinates, Multi-AZ mirror symmetry, always passes the gate | VPC/Multi-AZ/tier, serverless & pipeline patterns (most common) |
| **XML Direct Writing** | Create .drawio file with Write tool | No dependencies, stable | Non-standard shapes / full manual control |
| **Draw.io MCP** | Real-time editing via MCP | Interactive, live preview | Optional (requires setup) |
| **Sketch (Excalidraw)** | `scripts/excalidraw_gen.py` — same spec → local `.excalidraw` | Hand-drawn/whiteboard aesthetic, same shared icons (incl. AgentCore) | Brainstorming / concept diagrams (use drawio for formal infra) |

The spec engine ships extra composition engines — serverless `stages`, multi-region, and hybrid block composition — and `lint_layout.py` scores geometry + design as a gate.

## Provided Resources

### references/

| Reference Doc | Description |
|---------------|-------------|
| `aws-icons.md` | AWS icon shape names and styles |
| `best-practices.md` | Architecture diagram best practices |
| `layout-patterns.md` | Layout patterns |
| `drawio-xml-guide.md` | XML direct writing syntax guide |
| `mcp-setup-guide.md` | Draw.io MCP setup and tool usage |
| `snippets.md` | Copy-paste XML code snippets |

### templates/

| Template | Description |
|----------|-------------|
| `aws-basic.drawio` | VPC, Subnet, AZ basic structure |
| `aws-samples.drawio` | Data Lake architecture sample |

### scripts/

| Script | Description |
|--------|-------------|
| `layout_aws.py` | Spec-driven layout engine (YAML/JSON spec → .drawio); VPC/Multi-AZ/tier + serverless `stages`, multi-region, hybrid engines |
| `excalidraw_gen.py` | Sketch-style `.excalidraw` generator reusing the shared AWS icon vocabulary (local, offline) |
| `lint_layout.py` | Layout/design gate — scores geometry + design, exit code drives PASS/FAIL |
| `validate_drawio.py` | Validate `.drawio` XML structure |
| `route_edges.py` / `snap_grid.py` | Edge routing and grid snapping helpers |

---

## Canvas Size (For PPT)

| Purpose | Canvas Size (px) | Ratio |
|---------|------------------|-------|
| Full slide | 1920 x 1080 | 16:9 |
| Content area (recommended) | 1600 x 900 | 16:9 |
| Half slide | 900 x 900 | 1:1 |
| 2/3 slide | 1200 x 900 | 4:3 |

---

## Draw.io XML Code Examples

### Empty Canvas (PPT 1600x900)

```xml
<mxfile host="app.diagrams.net" agent="Claude Code" version="21.0.0">
  <diagram name="Architecture" id="arch-1">
    <mxGraphModel dx="1600" dy="900" grid="1" gridSize="10" guides="1"
                  tooltips="1" connect="1" arrows="1" fold="1" page="1"
                  pageScale="1" pageWidth="1600" pageHeight="900">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        <!-- Add elements here -->
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

### AWS Cloud Container

```xml
<mxCell id="aws-cloud" value="AWS Cloud"
        style="points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]];outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=14;fontStyle=1;container=1;pointerEvents=0;collapsible=0;recursiveResize=0;shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_aws_cloud_alt;strokeColor=#232F3E;fillColor=none;verticalAlign=top;align=left;spacingLeft=30;fontColor=#232F3E;fontFamily=Amazon Ember;dashed=0;"
        vertex="1" parent="1">
  <mxGeometry x="20" y="20" width="1560" height="860" as="geometry" />
</mxCell>
```

### VPC Container

```xml
<mxCell id="vpc-1" value="Production VPC (10.0.0.0/16)"
        style="sketch=0;outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=11;fontStyle=1;container=1;pointerEvents=0;collapsible=0;recursiveResize=0;shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_vpc;strokeColor=#879196;fillColor=none;verticalAlign=top;align=left;spacingLeft=30;fontColor=#879196;fontFamily=Amazon Ember;dashed=0;"
        vertex="1" parent="region">
  <mxGeometry x="20" y="40" width="500" height="400" as="geometry" />
</mxCell>
```

### Public Subnet (Green)

```xml
<mxCell id="public-subnet" value="Public Subnet (10.0.1.0/24)"
        style="points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]];outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=10;fontStyle=0;container=1;pointerEvents=0;collapsible=0;recursiveResize=0;shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_security_group;grStroke=0;strokeColor=#7AA116;fillColor=#F2F6E8;verticalAlign=top;align=left;spacingLeft=30;fontColor=#248814;fontFamily=Amazon Ember;dashed=0;"
        vertex="1" parent="vpc-1">
  <mxGeometry x="20" y="45" width="220" height="150" as="geometry" />
</mxCell>
```

### Private Subnet (Blue)

```xml
<mxCell id="private-subnet" value="Private Subnet (10.0.10.0/24)"
        style="points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]];outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=10;fontStyle=0;container=1;pointerEvents=0;collapsible=0;recursiveResize=0;shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_security_group;grStroke=0;strokeColor=#00A4A6;fillColor=#E6F6F7;verticalAlign=top;align=left;spacingLeft=30;fontColor=#147EBA;fontFamily=Amazon Ember;dashed=0;"
        vertex="1" parent="vpc-1">
  <mxGeometry x="20" y="210" width="220" height="170" as="geometry" />
</mxCell>
```

### EC2 Instance Icon

```xml
<mxCell id="ec2-1" value="Web Server"
        style="sketch=0;outlineConnect=0;fontColor=#232F3E;gradientColor=#F78E04;gradientDirection=north;fillColor=#D05C17;strokeColor=#ffffff;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=9;fontStyle=0;aspect=fixed;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.ec2;fontFamily=Amazon Ember;"
        vertex="1" parent="private-subnet">
  <mxGeometry x="86" y="60" width="48" height="48" as="geometry" />
</mxCell>
```

### Lambda Function Icon

```xml
<mxCell id="lambda-1" value="Lambda"
        style="sketch=0;outlineConnect=0;fontColor=#232F3E;gradientColor=#F78E04;gradientDirection=north;fillColor=#D05C17;strokeColor=#ffffff;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=9;fontStyle=0;aspect=fixed;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.lambda;fontFamily=Amazon Ember;"
        vertex="1" parent="1">
  <mxGeometry x="200" y="200" width="48" height="48" as="geometry" />
</mxCell>
```

### Aurora Database Icon

```xml
<mxCell id="aurora-1" value="Aurora"
        style="sketch=0;outlineConnect=0;fontColor=#232F3E;gradientColor=#4D72F3;gradientDirection=north;fillColor=#3334B9;strokeColor=#ffffff;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=9;fontStyle=0;aspect=fixed;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.aurora;fontFamily=Amazon Ember;"
        vertex="1" parent="1">
  <mxGeometry x="400" y="200" width="48" height="48" as="geometry" />
</mxCell>
```

### Connection Arrow

```xml
<mxCell id="conn-1" value=""
        style="endArrow=classic;startArrow=classic;html=1;rounded=0;strokeWidth=2;strokeColor=#545B64;"
        edge="1" parent="1" source="source-id" target="target-id">
  <mxGeometry width="50" height="50" relative="1" as="geometry" />
</mxCell>
```

---

## Layout Patterns Detail

### 3-Tier Architecture Pattern

```
┌─────────────────────────────────────────────────────────────┐
│                     Presentation Tier                        │
│  CloudFront → ALB → Web Servers                              │
├─────────────────────────────────────────────────────────────┤
│                      Application Tier                        │
│  API Gateway → Lambda/ECS → Application Logic                │
├─────────────────────────────────────────────────────────────┤
│                         Data Tier                            │
│  RDS/Aurora → DynamoDB → ElastiCache → S3                   │
└─────────────────────────────────────────────────────────────┘
```

**Layout coordinates:**
- Presentation Tier: y = 50-200
- Application Tier: y = 250-400
- Data Tier: y = 450-600
- Horizontal spacing between icons: 150px

### Hybrid Cloud Pattern

```
┌─ On-Premise (IDC) ───────┐    ┌─ AWS Cloud ─────────────────┐
│                          │    │  ┌─ Region ───────────────┐ │
│  ┌────────┐  ┌────────┐  │    │  │  ┌─ VPC ────────────┐  │ │
│  │ Server │  │Firewall│  │════│  │  │ Private Subnet   │  │ │
│  └────────┘  └────────┘  │ DX │  │  │  ┌────┐ ┌────┐  │  │ │
│                          │    │  │  │  │EC2 │ │RDS │  │  │ │
│  Legacy Apps             │    │  │  │  └────┘ └────┘  │  │ │
│                          │    │  │  └──────────────────┘  │ │
└──────────────────────────┘    │  └────────────────────────┘ │
                                └─────────────────────────────┘
```

**Key elements:**
- IDC box: x=20, width=350
- AWS Cloud box: x=400, width=rest
- Direct Connect arrow: thick orange (#FF9800), strokeWidth=4

### Serverless Architecture Pattern

```
┌─────────────────────────────────────────────────────────────┐
│  Client → API Gateway → Lambda → DynamoDB                    │
│              ↓                                               │
│          Cognito ←─────────────────────────────────┐        │
│              ↓                                     │        │
│         Step Functions → Lambda → S3 → EventBridge │        │
└─────────────────────────────────────────────────────────────┘
```

**Recommended icon sizes:**
- API Gateway, Lambda, DynamoDB: 48x48
- Cognito, Step Functions: 48x48
- Arrows: strokeWidth=2, color=#545B64

---

## AWS Icon Label Rules

:::warning Required
Display service name below all AWS icons.
:::

```
┌─────────────┐
│   [Icon]    │
│             │
│ Lambda      │  ← Service name required
└─────────────┘
```

Label settings:
- `verticalLabelPosition=bottom`
- `fontFamily=Amazon Ember`
- `fontSize=12`
- `fontColor=#FFFFFF` (Dark theme)

---

## AWS Color Guide

| Purpose | Color Code | Description |
|---------|------------|-------------|
| AWS Cloud | #232F3E | Dark navy (background) |
| Region | #147EBA | Blue |
| VPC | #248814 | Green |
| Public Subnet | #E7F4E8 | Light green |
| Private Subnet | #E6F2F8 | Light blue |
| Security Group | #DF3312 | Red (border) |

### Service Category Colors

| Category | fillColor | gradientColor |
|----------|-----------|---------------|
| Compute | #D05C17 | #F78E04 |
| Storage | #277116 | #60A337 |
| Database | #3334B9 | #4D72F3 |
| Security | #C7131F | #F54749 |
| Networking | #5A30B5 | #945DF2 |
| Management | #BC1356 | #F34482 |
| AI/ML | #116D5B | #4AB29A |

---

## Best Practices Checklist

### Layout
- [ ] Clear hierarchy (Cloud > Region > VPC > Subnet)
- [ ] Consistent data flow direction (left to right)
- [ ] Uniform icon sizes (recommended: 60x60)
- [ ] Appropriate spacing maintained

### Colors & Style
- [ ] AWS official colors used
- [ ] Amazon Ember font applied
- [ ] Container colors are correct

### Connections
- [ ] Arrow directions are correct
- [ ] Sync/async distinguished (solid/dashed)
- [ ] No unnecessary line crossings

### Completeness
- [ ] All major components included
- [ ] Legend present
- [ ] Title and version info present
- [ ] Labels below all AWS icons

---

## PNG Export

```bash
# Basic PNG export
drawio -x -f png -o output.png input.drawio

# High-resolution PNG (2x scale, recommended for PPT)
drawio -x -f png -s 2 -o output.png input.drawio

# Transparent background (for dark theme PPT)
drawio -x -f png -s 2 -t -o output.png input.drawio
```

---

## Usage Example

```
User: "Draw a 3-tier web architecture diagram"

1. architecture-diagram-agent called
2. Requirements analysis (VPC, Subnet, EC2, RDS, etc.)
3. Draw.io XML generation
4. PNG export
5. content-review-agent review
```

---

## Draw.io MCP Setup (Optional)

Draw.io MCP enables real-time editing:

```json
{
  "mcpServers": {
    "drawio": {
      "type": "http",
      "url": "http://localhost:3000/mcp"
    }
  }
}
```

Prerequisites:
1. drawio-mcp-server running in HTTP mode
2. Browser Extension installed and connected
3. Draw.io app open

---

## Quality Review (Required)

After diagram completion:
1. Call `content-review-agent`
2. Achieve PASS (85+ score) before completion

## Validation Checklist

- [ ] Amazon Ember font set for all text
- [ ] AWS official colors used
- [ ] Clear hierarchy (Cloud > Region > VPC > Subnet)
- [ ] Consistent data flow direction
- [ ] Uniform icon sizes (recommended: 60x60)
- [ ] Labels placed below icons
