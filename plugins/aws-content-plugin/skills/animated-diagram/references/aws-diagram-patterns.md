# AWS Diagram Patterns

Color coding, layout conventions, and common architectural patterns for animated diagrams.

---

## AWS Color Palette

### Service Category Colors

| Category | Primary | Accent | Services |
|----------|---------|--------|----------|
| Compute | `#D05C17` | `#F78E04` | EC2, Lambda, ECS, EKS |
| Storage | `#277116` | `#60A337` | S3, EBS, EFS |
| Database | `#3334B9` | `#4D72F3` | RDS, DynamoDB, Aurora, ElastiCache |
| Security | `#C7131F` | `#F54749` | IAM, Cognito, KMS, WAF |
| Networking | `#5A30B5` | `#945DF2` | VPC, Route 53, CloudFront, ALB |
| AI/ML | `#116D5B` | `#4AB29A` | Bedrock, SageMaker |
| Management | `#BC1356` | `#F34482` | CloudWatch, CloudFormation |

### Traffic Flow Colors

| Type | Color | Hex | Dot Size |
|------|-------|-----|----------|
| User → AWS (Inbound) | Blue | `#147EBA` | r=5 |
| AWS → External (Outbound) | Red | `#DD344C` | r=5 |
| Internal (AWS ↔ AWS) | Orange | `#FF9900` | r=4 |
| Success path | Green | `#1B660F` | r=4 |
| Degraded path | Yellow | `#F2C94C` | r=4 |

### Background & UI

| Element | Color | Use |
|---------|-------|-----|
| Dark background | `#232F3E` | Squid Ink (page background) |
| Light background | `#FFFFFF` | Light theme alternative |
| Border accent | `#FF9900` | Orange highlights, legends |
| Text on dark | `#FFFFFF` | Labels on dark backgrounds |
| Text on light | `#232F3E` | Labels on light backgrounds |

---

## Common Architecture Patterns

### 1. Web Application (ALB → Lambda → DynamoDB)

```
User → CloudFront → ALB → Lambda → DynamoDB
                              ↓
                           S3 (logs)
```

Animation plan:
- Inbound path: User → CloudFront → ALB (Blue dots)
- Internal path: ALB → Lambda → DynamoDB (Orange dots)
- Log path: Lambda → S3 (Orange dots, slower)

### 2. Hybrid Architecture (IDC → AWS)

```
IDC Server → Direct Connect → Transit Gateway → VPC → Services
```

Animation plan:
- Cross-boundary: IDC → DX Gateway (Red dots, thick)
- Internal routing: TGW → VPC (Orange dots)
- Service mesh: VPC services (Orange dots, multiple paths)

### 3. Event-Driven Pipeline

```
S3 Upload → EventBridge → Lambda → Step Functions → SNS
                                        ↓
                                    DynamoDB
```

Animation plan:
- Trigger: S3 → EventBridge (Green dots)
- Processing: EventBridge → Lambda → Step Functions (Orange dots)
- Notification: Step Functions → SNS (Orange dots)
- Storage: Step Functions → DynamoDB (Orange dots)

### 4. Multi-AZ High Availability

```
ALB ──┬── AZ-a: EC2 → RDS Primary
      └── AZ-b: EC2 → RDS Standby
              RDS Primary ←sync→ RDS Standby
```

Animation plan:
- Load distribution: ALB → EC2 in each AZ (Blue dots, alternating)
- Sync replication: RDS Primary ↔ Standby (Orange dots, bidirectional)
- Health check: Pulsing glow on active instances (Green)

---

## Layout Conventions

### ViewBox Standard

Use `viewBox="0 0 1600 900"` for 16:9 aspect ratio matching Draw.io canvas.

### Zone Placement

| Zone | X Range | Y Range | Content |
|------|---------|---------|---------|
| Left (IDC/External) | 20-350 | 20-880 | On-premise, users |
| Center (AWS) | 380-1200 | 20-780 | AWS services |
| Right (AWS Managed) | 880-1580 | 20-780 | Managed services, global |
| Bottom | 20-1580 | 800-880 | Legend, footer |

### Label Placement

- Service labels: Below icons (y + 55px from icon center)
- Group labels: Top-left inside group box
- Path labels: Centered on path midpoint
- Legend: Bottom-right corner with semi-transparent background

---

## SVG Static Elements

### Service Box (for inline SVG backgrounds)

```xml
<!-- Service box with icon placeholder -->
<g transform="translate(500,200)">
  <rect x="-50" y="-30" width="100" height="60" rx="8"
        fill="#232F3E" stroke="#F78E04" stroke-width="2" />
  <text x="0" y="5" text-anchor="middle" fill="#FFFFFF"
        font-family="Amazon Ember, sans-serif" font-size="12">Lambda</text>
</g>
```

### Group Box (for inline SVG backgrounds)

```xml
<!-- VPC group box -->
<rect x="380" y="100" width="500" height="400" rx="0"
      fill="none" stroke="#879196" stroke-width="2" stroke-dasharray="none" />
<text x="395" y="125" fill="#879196"
      font-family="Amazon Ember, sans-serif" font-size="13" font-weight="bold">
  VPC (10.0.0.0/16)
</text>
```

### Arrow Label

```xml
<text x="350" y="290" text-anchor="middle" fill="#AAAAAA"
      font-family="Amazon Ember, sans-serif" font-size="10">
  HTTPS
</text>
```
