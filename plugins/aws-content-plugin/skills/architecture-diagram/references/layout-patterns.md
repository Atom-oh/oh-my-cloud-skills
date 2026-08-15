# Draw.io Layout Patterns and Editing Techniques

Layout patterns and XML editing techniques validated on real architecture diagram work.

> 💡 **The spec generator implements these patterns automatically.** `scripts/layout_aws.py`
> deterministically generates the layout principles described here (Multi-AZ mirroring, VPC nesting,
> left-to-right tiers, edge anchors) from a YAML spec (`examples/`). Use this document to understand what
> rules the generator follows, or as a reference when hand-editing a generated diagram further.

---

## Editing box styles

### Adjusting corner rounding (arcSize)

**Problem**: the default rounded box's curvature is too large and clips text near the corners

```xml
<!-- Problem: default rounded has a large arcSize -->
style="rounded=1;..."

<!-- Fix: set arcSize explicitly smaller -->
style="rounded=1;arcSize=5;..."
```

| arcSize value | Effect |
|-----------|------|
| 0 | square corners |
| 5 | slightly rounded corners (recommended) |
| 10 | moderately rounded corners |
| 20+ | heavily rounded corners |

### Internal spacing

**Problem**: text sits too close to the box edge

```xml
<!-- Fix: add spacingTop, spacingLeft -->
style="verticalAlign=top;spacingTop=8;spacingLeft=10;..."
```

| Attribute | Use | Recommended value |
|------|------|--------|
| spacingTop | top margin | 5-10 |
| spacingLeft | left margin | 5-10 |
| spacingRight | right margin | 5-10 |
| spacingBottom | bottom margin | 5-10 |

### Text alignment

```xml
<!-- Group box title in the top-left -->
style="verticalAlign=top;align=left;spacingTop=8;spacingLeft=30;..."

<!-- Content centered -->
style="verticalAlign=middle;align=center;..."
```

---

## Icon grid placement

### Basic grid pattern

```
Place 4-5 icons per row:

┌──────────────────────────────────────────────────────────┐
│ [icon1] [icon2] [icon3] [icon4] [icon5]         │
│  label1    label2     label3     label4     label5            │
│                                                          │
│ [icon6] [icon7] [icon8] [icon9]                   │
│  label6    label7     label8     label9                      │
└──────────────────────────────────────────────────────────┘
```

### Coordinate calculation

> **The single source of truth for icon size is `references/design-tokens.md`: standard 78×78** (dense
> exception 48×48). The figures below are for illustrating the calculation method only — actual sizes
> should use 78.

```
Icon size: 78x78 (standard, per design-tokens.md) — 48x48 only as a dense exception
Label height: 25px
Row spacing: icon height + label height + margin = 78 + 25 + 17 = 120px

Example (starting point x=914, y=162):
- Row 1 icon: y=162, label: y=202
- Row 2 icon: y=230, label: y=270
- Row 3 icon: y=322, label: y=362 (if a section divider is included)
- Row 4 icon: y=390, label: y=430

Column spacing (based on 40px icons):
- Column 1: x=914
- Column 2: x=989 (+75)
- Column 3: x=1064 (+75)
- Column 4: x=1139 (+75)
- Column 5: x=1214 (+75)
```

### Icon + label pair

```xml
<!-- Icon -->
<mxCell id="secrets-mgr" value=""
        style="sketch=0;outlineConnect=0;fontColor=#FFFFFF;gradientColor=#F54749;gradientDirection=north;fillColor=#C7131F;strokeColor=#ffffff;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=9;fontStyle=0;aspect=fixed;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.secrets_manager;fontFamily=Amazon Ember;"
        vertex="1" parent="1">
  <mxGeometry x="914" y="162" width="40" height="40" as="geometry" />
</mxCell>

<!-- Label (below the icon) -->
<mxCell id="secrets-mgr-label" value="Secrets&#xa;Manager"
        style="text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=top;whiteSpace=wrap;rounded=0;fontFamily=Amazon Ember;fontSize=8;fontColor=#FFFFFF;"
        vertex="1" parent="1">
  <mxGeometry x="904" y="202" width="60" height="25" as="geometry" />
</mxCell>
```

**Label coordinate calculation**:
- label x = icon x - (label width - icon width) / 2
- example: icon x=914, icon width=40, label width=60 → label x = 914 - 10 = 904
- label y = icon y + icon height = 162 + 40 = 202

---

## Adjusting related elements together

### When resizing a parent box

```
mgmt-box height: 340 → 360 (+20)

Affected child elements:
- mapping-box: y=465 → y=485 (+20)
- mapping-title: y=468 → y=488 (+20)
- legend: y=560 → y=580 (+20)
- all elements inside the legend: y += 20
- footer: y=665 → y=685 (+20)
```

### Bulk edit pattern

```
Bulk-editing y coordinates with the Edit tool:
1. Identify affected elements
2. Apply the same delta to each element's y coordinate
3. Verify the parent-child hierarchy
```

---

## Adjusting group scope

### Region should contain only VPCs

**Principle**: the Region box should contain only resources that actually belong to the Region (VPCs)

```
┌─ AWS Cloud ───────────────────────────────────────────┐
│  ┌─ Region (VPCs only) ─┐  ┌─ Management services (separate) ─┐  │
│  │  ┌────┐ ┌────┐       │  │  icons...        │  │
│  │  │VPC1│ │VPC2│       │  │                     │  │
│  │  └────┘ └────┘       │  └─────────────────────┘  │
│  │  ┌────────────────┐  │                           │
│  │  │    VPC3        │  │  ┌─ Legend ──────────────┐  │
│  │  └────────────────┘  │  │                     │  │
│  └──────────────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

**Width calculation**:
```
VPCs end at x=880
Region start: x=410
Region end (with margin): x=890
Region width = 890 - 410 = 480
```

---

## Legend layout

### Two-row legend pattern

```
┌─ Legend ────────────────────────────────────────────────────────┐
│ [IDC server] IDC solution  [EC2] compute  [S3] storage  [Aurora] DB │
│ [Shield] security  [TGW] networking  [━━▶] Direct Connect  BYOL     │
└───────────────────────────────────────────────────────────────┘
```

### Legend element placement

```xml
<!-- Row 1 -->
<mxCell id="leg-1" ... vertex="1" parent="1">
  <mxGeometry x="905" y="610" width="20" height="20" as="geometry" />
</mxCell>
<mxCell id="leg-1-text" value="IDC solution" ...>
  <mxGeometry x="928" y="607" width="65" height="25" as="geometry" />
</mxCell>

<mxCell id="leg-2" ... vertex="1" parent="1">
  <mxGeometry x="998" y="608" width="24" height="24" as="geometry" />
</mxCell>
<mxCell id="leg-2-text" value="Compute" ...>
  <mxGeometry x="1025" y="607" width="45" height="25" as="geometry" />
</mxCell>

<!-- Row 2 (y += 30) -->
<mxCell id="leg-5" ... vertex="1" parent="1">
  <mxGeometry x="905" y="640" width="24" height="24" as="geometry" />
</mxCell>
```

### Direct Connect legend arrow

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

## Color reference

### AWS service category colors

| Category | fillColor | gradientColor | strokeColor |
|----------|-----------|---------------|-------------|
| Compute | #D05C17 | #F78E04 | #ffffff |
| Storage | #277116 | #60A337 | #ffffff |
| Database | #3334B9 | #4D72F3 | #ffffff |
| Security | #C7131F | #F54749 | #ffffff |
| Networking | #5A30B5 | #945DF2 | #ffffff |
| Management | #BC1356 | #F34482 | #ffffff |
| AI/ML | #116D5B | #4AB29A | #ffffff |

### Group box colors

> **The single source of truth is `references/design-tokens.md`.** Public=green (#7AA116), Private=teal
> (#00A4A6) — matches the Web Tier (green)/App·Data Tier (teal) in `templates/*.drawio`. Don't swap them.

| Group | strokeColor | fillColor | fontColor |
|------|-------------|-----------|-----------|
| AWS Cloud | #232F3E | none | #232F3E |
| Region | #00A4A6 | none | #147EBA |
| VPC | #879196 | none | #879196 |
| Public Subnet | #7AA116 | #F2F6E8 | #248814 |
| Private Subnet | #00A4A6 | #E6F6F7 | #147EBA |
| Security Group | #C7131F | #FEE7E7 | #C62828 |
| IDC | #5A6C86 | #E6E6E6 | #5A6C86 |

### Custom box colors

| Use | fillColor | strokeColor | fontColor |
|------|-----------|-------------|-----------|
| Management services (Dark) | #263238 | #FF9900 | #FF9900 |
| Hybrid advantage | #1B5E20 | #4CAF50 | #A5D6A7 |
| Legend box | #FAFAFA | #E0E0E0 | #424242 |
| BYOL badge | #FFF9C4 | #F57F17 | #F57F17 |

---

## Connector styles

### Basic connector

```xml
style="endArrow=classic;html=1;strokeWidth=1;strokeColor=#545B64;"
```

### Bidirectional connector

```xml
style="endArrow=classic;startArrow=classic;html=1;strokeWidth=2;strokeColor=#5A30B5;"
```

### Direct Connect (thick orange)

```xml
style="endArrow=classic;startArrow=classic;html=1;rounded=0;strokeWidth=4;strokeColor=#FF9800;edgeStyle=orthogonalEdgeStyle;"
```

### Elbow connector (Orthogonal)

```xml
style="edgeStyle=orthogonalEdgeStyle;..."
<Array as="points">
  <mxPoint x="400" y="530" />
  <mxPoint x="400" y="220" />
</Array>
```

---

## Frequently used editing patterns

### 1. Fixing clipped text

```xml
<!-- Before -->
style="rounded=1;..."

<!-- After -->
style="rounded=1;arcSize=5;spacingTop=8;spacingLeft=10;..."
```

### 2. Increasing box height + moving child elements

```
1. Calculate the box height increase (e.g. +20)
2. y += 20 for all elements below the box
3. Expand the parent container too, if needed
```

### 3. Adding an icon row

```
new row y = previous row y + 68 (icon 40 + label 25 + spacing 3)
or
new row y = previous row y + 92 (if a section label is included)
```

### 4. Shrinking Region scope

```
1. Check the max x + width across the VPCs
2. Region width = (VPC end x) - (Region start x) + margin (10)
```
