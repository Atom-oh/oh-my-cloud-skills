# AWS Architecture Diagram Best Practices

Guidelines and best practices to follow when authoring AWS architecture diagrams.

> 💡 **Consider the spec generator first.** For VPC/Multi-AZ, serverless, multi-region, or hybrid patterns,
> don't place coordinates by hand — generate from a YAML spec with **`scripts/layout_aws.py`**. The best
> practices below (78px uniformity, mirror symmetry, margins, orthogonal edges) are applied automatically
> and pass the gate. Examples: `examples/`. This document is the reference for hand-drawing irregular
> structures that don't fit the generator.

## 1. Layout principles

### Hierarchy (Outside-In)

Clearly express the hierarchy from outside to inside:

```
1. Users/Internet (outermost)
   └── 2. AWS Cloud
       └── 3. Region
           └── 4. VPC
               └── 5. Availability Zone
                   └── 6. Subnet
                       └── 7. Services
```

### Data flow direction

- **Left → Right**: request flow (recommended)
- **Top → Bottom**: tier separation
- **Stay consistent**: keep one direction throughout a diagram

### 3-Tier architecture layout

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

## 2. Color guide (official AWS)

### AWS brand colors

| Element | Color code | RGB | Use |
|------|-----------|-----|------|
| Squid Ink | #232F3E | 35, 47, 62 | AWS Cloud background |
| Smile Orange | #FF9900 | 255, 153, 0 | emphasis, CTA |
| Anchor | #147EBA | 20, 126, 186 | Region |
| Cosmos | #C7511F | 199, 81, 31 | security-related |

### Container colors

> **The single source of truth is `references/design-tokens.md`** (based on the actual `templates/*.drawio`
> files). The table below must match those values. **Public=green (#7AA116), Private=teal (#00A4A6)** —
> do not swap them.

| Container | Border | Fill | Text |
|----------|--------|------|--------|
| AWS Cloud | #232F3E | none | #232F3E |
| Region | #00A4A6 | none | #147EBA |
| VPC | #879196 | none | #879196 |
| Public Subnet | #7AA116 | #F2F6E8 | #248814 |
| Private Subnet | #00A4A6 | #E6F6F7 | #147EBA |
| Security Group | #C7131F | #FEE7E7 | #C62828 |
| Availability Zone | #00A4A6 | none | #147EBA |
| Corporate / IDC | #5A6C86 | #E6E6E6 | #5A6C86 |

### Arrow colors

| Type | Color | Use |
|------|------|------|
| Data flow | #545B64 | general connection |
| Synchronous call | #232F3E (solid) | API calls, etc. |
| Asynchronous call | #232F3E (dashed) | events, messages |
| Security connection | #DF3312 | security group, etc. |

## 3. Font guide

### Amazon Ember (recommended)

The official AWS brand font:

```
fontFamily=Amazon Ember;
```

Font stack (fallback):
```
Amazon Ember, Arial, Helvetica, sans-serif
```

### Recommended font sizes

| Element | Size | Weight |
|------|------|------|
| Diagram title | 24px | Bold |
| Container label (Cloud, Region) | 16px | Bold |
| Subnet/AZ label | 14px | Regular |
| Service label | 12px | Regular |
| Detail text | 10px | Regular |

### Text placement

- Icon labels: below the icon (verticalLabelPosition=bottom)
- Container labels: top-left (verticalAlign=top)
- Arrow labels: centered (align=center)

## 4. Icon usage guide

### Icon size consistency

> **The single source of truth is `references/design-tokens.md`.** Standard **78×78** (uniform across all
> icons), dense exception **48×48** (only when ≥16 icons, never mixed within one diagram). 40/60 are retired.

```
Standard size: 78x78px      (icon.standard — default)
Dense exception: 48x48px    (icon.dense — only when ≥16 icons)
```

### Icon spacing

```
Minimum spacing: 20px
Recommended spacing: 40px
Spacing within a group: 30px
```

### Icon alignment

- Horizontal alignment: services at the same tier
- Vertical alignment: direction of data flow
- Grid alignment recommended (gridSize=10)

## 5. Edge (connection) guide

### Edge style

```xml
<!-- Orthogonal connection (recommended) -->
style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;"

<!-- Curved connection -->
style="edgeStyle=elbowEdgeStyle;rounded=1;"

<!-- Straight connection -->
style="edgeStyle=none;"
```

### Arrow types

| Type | Style | Use |
|------|--------|------|
| One-way | `endArrow=classic;startArrow=none;` | request flow |
| Two-way | `endArrow=classic;startArrow=classic;` | synchronous communication |
| None | `endArrow=none;startArrow=none;` | association only |

### Dashed vs. solid

```xml
<!-- Solid line (synchronous call) -->
style="dashed=0;"

<!-- Dashed line (asynchronous, optional) -->
style="dashed=1;dashPattern=8 8;"
```

## 6. Common architecture patterns

### Pattern 1: Simple web application

```
Internet → CloudFront → ALB → EC2 (ASG) → RDS
                                    ↘ ElastiCache
```

### Pattern 2: Serverless architecture

```
Client → API Gateway → Lambda → DynamoDB
              ↓
         Cognito (auth)
```

### Pattern 3: Microservices

```
ALB → ECS/EKS Services → RDS/DynamoDB
  ↓
Service Mesh (App Mesh)
  ↓
X-Ray (tracing)
```

### Pattern 4: Event-driven architecture

```
Producer → EventBridge/SNS → SQS → Lambda → Consumer
                  ↓
           Step Functions (orchestration)
```

### Pattern 5: Data lake

```
Sources → Kinesis → S3 (Raw) → Glue ETL → S3 (Processed) → Athena/QuickSight
                                    ↓
                              Redshift (analytics)
```

## 7. Depicting high availability

### Multi-AZ placement

```
┌─────────────────────────────────────────────────┐
│                      VPC                         │
│  ┌───────────────────┐  ┌───────────────────┐   │
│  │    AZ-a           │  │    AZ-c           │   │
│  │  ┌─────────────┐  │  │  ┌─────────────┐  │   │
│  │  │ Public      │  │  │  │ Public      │  │   │
│  │  │  ALB        │  │  │  │  ALB        │  │   │
│  │  └─────────────┘  │  │  └─────────────┘  │   │
│  │  ┌─────────────┐  │  │  ┌─────────────┐  │   │
│  │  │ Private     │  │  │  │ Private     │  │   │
│  │  │  EC2        │  │  │  │  EC2        │  │   │
│  │  └─────────────┘  │  │  └─────────────┘  │   │
│  └───────────────────┘  └───────────────────┘   │
│                    ↕ RDS Multi-AZ ↕              │
└─────────────────────────────────────────────────┘
```

### Active-Standby vs. Active-Active

- **Active-Standby**: only one side's arrow active, the other dashed
- **Active-Active**: both sides use solid arrows

## 8. Depicting security

### Security Group representation

```xml
<!-- Red dashed border -->
style="rounded=1;dashed=1;strokeColor=#DF3312;fillColor=none;"
```

### Encryption representation

- Add a KMS icon
- A lock icon or an "Encrypted" label

### Network boundaries

- Distinguish Public/Private subnets by color
- Explicitly show NAT Gateway, Internet Gateway
- Show VPC Endpoints (PrivateLink)

## 9. Annotations and descriptions

### Adding a legend

Place the legend in the bottom-right of the diagram:
- Color meanings
- Arrow type explanations
- Abbreviation glossary

### Version information

Information to include in a diagram:
- Diagram title
- Creation/revision date
- Version number
- Author

## 10. Checklist

### Layout
- [ ] Is the hierarchy clear (Cloud > Region > VPC > Subnet)?
- [ ] Is the data flow direction consistent?
- [ ] Are icon sizes uniform?
- [ ] Is appropriate spacing maintained?

### Color and style
- [ ] Are official AWS colors used?
- [ ] Is the Amazon Ember font applied?
- [ ] Are container colors correct?

### Connections
- [ ] Are arrow directions correct?
- [ ] Is sync/async distinguished (solid/dashed)?
- [ ] Are unnecessary edge crossings avoided?

### Completeness
- [ ] Are all key components included?
- [ ] Is there a legend?
- [ ] Are title and version info present?

## 11. Anti-patterns (things to avoid)

### Things to avoid

1. **Over-detailing**: don't show every single resource
2. **Inconsistent icon sizes**: same type should be the same size
3. **Arrow crossings**: minimize where possible
4. **Color overuse**: don't use color without purpose
5. **Excess text**: label only with essential information
6. **Ignoring hierarchy**: don't list services without containers

### Recommendations

1. **Simplify**: abstract to a level appropriate for the audience
2. **Consistency**: keep style uniform within one diagram
3. **Clarity**: aim for at-a-glance comprehension
4. **Follow standards**: use official AWS architecture icon standards
