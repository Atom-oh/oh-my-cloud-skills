# AWS Architecture Icons Guide

Official AWS Architecture Icons for use in reactive presentations. Source: [AWS Architecture Icons](https://aws.amazon.com/architecture/icons/)

## Setup

Extract icons into the presentation repo's `common/aws-icons/` directory:

```bash
# Extract all 48px SVGs (recommended)
python3 {skill-dir}/scripts/extract_aws_icons.py -o {repo}/common/aws-icons/

# Extract specific categories only
python3 {skill-dir}/scripts/extract_aws_icons.py -o {repo}/common/aws-icons/ -c Containers,Management-Governance

# List available categories
python3 {skill-dir}/scripts/extract_aws_icons.py --list-categories

# Extract 64px for 4K presentations
python3 {skill-dir}/scripts/extract_aws_icons.py -o {repo}/common/aws-icons/ -s 64
```

## Directory Structure After Extraction

```
common/aws-icons/
├── services/          # Architecture Service Icons (main service logos)
│   ├── Arch_Amazon-Elastic-Kubernetes-Service_48.svg
│   ├── Arch_Amazon-Managed-Grafana_48.svg
│   ├── Arch_Amazon-Managed-Service-for-Prometheus_48.svg
│   ├── Arch_AWS-Lambda_48.svg
│   └── ...
├── categories/        # Category Icons (group-level)
│   ├── Arch-Category_Containers_48.svg
│   ├── Arch-Category_Compute_48.svg
│   └── ...
├── resources/         # Resource Icons (sub-service components)
│   ├── Res_Amazon-EC2_Instance_48.svg
│   ├── Res_Amazon-EKS_EKS-on-Outposts_48.svg
│   └── ...
├── groups/            # Group Icons (VPC, Subnet, Region, etc.)
│   ├── Virtual-private-cloud-VPC_32.svg
│   ├── Private-subnet_32.svg
│   └── ...
└── icon-index.txt     # Auto-generated index of all extracted icons
```

## Naming Conventions

| Type | Pattern | Example |
|------|---------|---------|
| Service | `Arch_{Service-Name}_{size}.svg` | `Arch_Amazon-Elastic-Kubernetes-Service_48.svg` |
| Category | `Arch-Category_{Category}_{size}.svg` | `Arch-Category_Containers_48.svg` |
| Resource | `Res_{Service}_{Resource}_{size}.svg` | `Res_Amazon-EC2_Instance_48.svg` |
| Group | `{Group-Name}_{size}.svg` | `Virtual-private-cloud-VPC_32.svg` |
| Dark variant | `{name}_{size}_Dark.svg` | `Arch-Category_Containers_48_Dark.svg` |

## Using Icons in Slides

### As `<img>` tags (recommended for most cases)

```html
<!-- Inline with text -->
<img src="../common/aws-icons/services/Arch_Amazon-Elastic-Kubernetes-Service_48.svg"
     alt="EKS" style="width: 1.5rem; vertical-align: middle;" />

<!-- In a card header -->
<div class="card">
  <div class="card-title" style="display: flex; align-items: center; gap: 8px;">
    <img src="../common/aws-icons/services/Arch_Amazon-Managed-Grafana_48.svg"
         alt="Grafana" style="width: 2rem;" />
    Amazon Managed Grafana
  </div>
</div>
```

### In Canvas animations

For canvas-based architecture diagrams, load icons as Image objects:

```javascript
// Preload icon
const eksIcon = new Image();
eksIcon.src = '../common/aws-icons/services/Arch_Amazon-Elastic-Kubernetes-Service_48.svg';

// Draw on canvas (after icon loads)
eksIcon.onload = () => {
  // Draw at BASE coordinate space (scales automatically with ctx.scale)
  const iconSize = 32; // in BASE_W/BASE_H coordinate space
  ctx.drawImage(eksIcon, x - iconSize/2, y - iconSize/2, iconSize, iconSize);
};
```

### In column layouts with icon + label

```html
<div class="col-3">
  <div class="card" style="text-align: center; padding: 16px;">
    <img src="../common/aws-icons/services/Arch_Amazon-Elastic-Kubernetes-Service_48.svg"
         alt="EKS" style="width: 3rem; margin-bottom: 8px;" />
    <div class="card-title">Amazon EKS</div>
    <p style="font-size: 0.85rem;">Managed Kubernetes</p>
  </div>
  <div class="card" style="text-align: center; padding: 16px;">
    <img src="../common/aws-icons/services/Arch_AWS-Fargate_48.svg"
         alt="Fargate" style="width: 3rem; margin-bottom: 8px;" />
    <div class="card-title">AWS Fargate</div>
    <p style="font-size: 0.85rem;">Serverless Compute</p>
  </div>
</div>
```

## Commonly Used Icons by Topic

### EKS & Containers
| Icon | Filename |
|------|----------|
| EKS | `services/Arch_Amazon-Elastic-Kubernetes-Service_48.svg` |
| EKS Cloud | `services/Arch_Amazon-EKS-Cloud_48.svg` |
| EKS Anywhere | `services/Arch_Amazon-EKS-Anywhere_48.svg` |
| ECS | `services/Arch_Amazon-Elastic-Container-Service_48.svg` |
| ECR | `services/Arch_Amazon-Elastic-Container-Registry_48.svg` |
| Fargate | `services/Arch_AWS-Fargate_48.svg` |

### Observability & Monitoring
| Icon | Filename |
|------|----------|
| CloudWatch | `services/Arch_Amazon-CloudWatch_48.svg` |
| Managed Grafana | `services/Arch_Amazon-Managed-Grafana_48.svg` |
| Managed Prometheus | `services/Arch_Amazon-Managed-Service-for-Prometheus_48.svg` |
| X-Ray | `services/Arch_AWS-X-Ray_48.svg` |
| CloudTrail | `services/Arch_AWS-CloudTrail_48.svg` |

### Compute
| Icon | Filename |
|------|----------|
| EC2 | `services/Arch_Amazon-EC2_48.svg` |
| Lambda | `services/Arch_AWS-Lambda_48.svg` |
| Auto Scaling | `services/Arch_Amazon-EC2-Auto-Scaling_48.svg` |

### Networking
| Icon | Filename |
|------|----------|
| VPC | `services/Arch_Amazon-Virtual-Private-Cloud_48.svg` |
| ELB | `services/Arch_Elastic-Load-Balancing_48.svg` |
| Route 53 | `services/Arch_Amazon-Route-53_48.svg` |
| CloudFront | `services/Arch_Amazon-CloudFront_48.svg` |

### Database & Storage
| Icon | Filename |
|------|----------|
| RDS | `services/Arch_Amazon-RDS_48.svg` |
| DynamoDB | `services/Arch_Amazon-DynamoDB_48.svg` |
| S3 | `services/Arch_Amazon-Simple-Storage-Service_48.svg` |
| ElastiCache | `services/Arch_Amazon-ElastiCache_48.svg` |

### Security
| Icon | Filename |
|------|----------|
| IAM | `services/Arch_AWS-Identity-and-Access-Management_48.svg` |
| Secrets Manager | `services/Arch_AWS-Secrets-Manager_48.svg` |
| KMS | `services/Arch_AWS-Key-Management-Service_48.svg` |

## Dark Theme Tips

- Default SVG icons use AWS brand colors on transparent backgrounds — they work well on the dark theme
- Some icons have `_Dark` variants with lighter outlines — prefer these if the standard version is hard to see
- For canvas drawings, add a subtle glow or white circle behind icons for better contrast:

```javascript
// White circle backdrop for dark backgrounds
ctx.beginPath();
ctx.arc(x, y, iconSize/2 + 4, 0, Math.PI * 2);
ctx.fillStyle = 'rgba(255, 255, 255, 0.1)';
ctx.fill();
ctx.drawImage(icon, x - iconSize/2, y - iconSize/2, iconSize, iconSize);
```

## Sizing Guidelines

| Context | Recommended Size | CSS |
|---------|-----------------|-----|
| Inline with text | 48px SVG | `width: 1.2rem` |
| Card header | 48px SVG | `width: 2rem` |
| Architecture node | 48px SVG | `width: 3rem` |
| Hero/feature icon | 64px SVG | `width: 4rem` |
| Canvas icon | 48px SVG | `drawImage(..., 28-36px)` in BASE coords |

SVGs scale to any size, so 48px source works everywhere. Use 64px source only if you need crisp detail at very large display sizes.
