# AWS Icon Reference

Guide to AWS icon shape names and styles available in Draw.io.

## Shape naming convention

AWS icon shape name format:
```
shape=mxgraph.aws4.[service_name]
```

## Shared icons — new/product icons not in mxgraph (AgentCore, etc.)

Draw.io's built-in `mxgraph.aws4.*` shape set is **fixed**, so it lacks new/product icons
(e.g. **Bedrock AgentCore**). These icons are pulled from the `reactive-presentation` skill's
**shared icon library** (`skills/reactive-presentation/icons/` — official Architecture-Service-Icons
SVGs + AgentCore and other product PNGs) and **embedded as base64 images**. `layout_aws.py`
handles this automatically — you only need to specify the `icon:` value in the spec.

| Spec `icon:` value | Behavior |
|------|------|
| `ec2`, `lambda`, `s3` … | built-in `mxgraph.aws4.*` shape (vector, default) |
| `agentcore` | embeds the AgentCore PNG from the shared library (registered in `EMBED_ICONS`) |
| `arch:Amazon-Bedrock` | finds `Arch_Amazon-Bedrock_48.svg` in the official Service set and embeds it |
| `arch:<Service-Name>` | embeds an arbitrary official service icon (`Arch_<Service-Name>_48.svg`) |

```yaml
# Example: AgentCore reference (stages pattern)
stages:
  - {name: "Inference", services: [{id: br, icon: "arch:Amazon-Bedrock", label: "Bedrock"}]}
  - {name: "Agent",     services: [{id: ac, icon: agentcore, label: "AgentCore"},
                                    {id: fn, icon: lambda,    label: "Tools"}]}
```

- The embedding format follows the draw.io convention `image=data:<mime>,<base64>` (comma form — avoids
  colliding with the `;` in style strings). Both PNG and SVG render fine in exports.
- `.drawio` is **self-contained** (icons are baked into the file), so it can be shared and exported to PNG
  without external dependencies.
- To add a new product icon: place the file in the shared library (`reactive-presentation/icons/`) and
  register `"shortname": "<relative-path>"` in `layout_aws.py`'s `EMBED_ICONS`. The `arch:` prefix works
  immediately without registration, but only for the official Service set.

> This shared library is the **same source** used by reactive-presentation (AWS icons in slides) — icons stay
> consistent across content skills.

## Mandatory rule: show icon labels

**Whenever you add an AWS icon, you must label it with the icon's name.**

```
┌─────────────┐
│   [icon]    │
│             │
│ SecretManager│  ← service name required below the icon
└─────────────┘
```

### Label style settings

```
labelPosition=center;      # horizontal label position
verticalLabelPosition=bottom;  # place label below the icon
align=center;              # center text horizontally
verticalAlign=top;         # align text to top
fontFamily=Amazon Ember;   # AWS font
fontSize=12;               # font size
fontColor=#FFFFFF;         # white for Dark theme
```

### Label examples

| Icon | Label text |
|--------|------------|
| Secrets Manager | `Secrets Manager` |
| Lambda | `Lambda` |
| API Gateway | `API Gateway` |
| DynamoDB | `DynamoDB` |
| CloudWatch | `CloudWatch` |

---

## Icons by category

### Compute

| Service | Shape name | Description |
|--------|-----------|------|
| EC2 | `mxgraph.aws4.ec2` | Elastic Compute Cloud |
| Lambda | `mxgraph.aws4.lambda_function` | Serverless function |
| ECS | `mxgraph.aws4.ecs` | Elastic Container Service |
| EKS | `mxgraph.aws4.eks` | Elastic Kubernetes Service |
| Fargate | `mxgraph.aws4.fargate` | Serverless containers |
| Batch | `mxgraph.aws4.batch` | Batch computing |
| Elastic Beanstalk | `mxgraph.aws4.elastic_beanstalk` | App deployment |
| Lightsail | `mxgraph.aws4.lightsail` | Simplified VPS |
| App Runner | `mxgraph.aws4.app_runner` | Containerized apps |

### Storage

| Service | Shape name | Description |
|--------|-----------|------|
| S3 | `mxgraph.aws4.s3` | Simple Storage Service |
| S3 Bucket | `mxgraph.aws4.bucket` | S3 bucket |
| EBS | `mxgraph.aws4.elastic_block_store` | Block storage |
| EFS | `mxgraph.aws4.elastic_file_system` | File system |
| FSx | `mxgraph.aws4.fsx` | High-performance file system |
| Glacier | `mxgraph.aws4.glacier` | Archival storage |
| Storage Gateway | `mxgraph.aws4.storage_gateway` | Hybrid storage |

### Database

| Service | Shape name | Description |
|--------|-----------|------|
| RDS | `mxgraph.aws4.rds` | Relational Database Service |
| Aurora | `mxgraph.aws4.aurora` | High-performance relational DB |
| DynamoDB | `mxgraph.aws4.dynamodb` | NoSQL database |
| ElastiCache | `mxgraph.aws4.elasticache` | In-memory cache |
| Redshift | `mxgraph.aws4.redshift` | Data warehouse |
| DocumentDB | `mxgraph.aws4.documentdb` | MongoDB-compatible DB |
| Neptune | `mxgraph.aws4.neptune` | Graph database |
| Timestream | `mxgraph.aws4.timestream` | Time-series database |
| QLDB | `mxgraph.aws4.qldb` | Ledger database |
| MemoryDB | `mxgraph.aws4.memorydb` | Redis-compatible |

### Networking & Content Delivery

| Service | Shape name | Description |
|--------|-----------|------|
| VPC | `mxgraph.aws4.vpc` | Virtual Private Cloud |
| CloudFront | `mxgraph.aws4.cloudfront` | CDN |
| Route 53 | `mxgraph.aws4.route_53` | DNS service |
| API Gateway | `mxgraph.aws4.api_gateway` | API management |
| ELB/ALB | `mxgraph.aws4.application_load_balancer` | Load balancer |
| NLB | `mxgraph.aws4.network_load_balancer` | Network LB |
| NAT Gateway | `mxgraph.aws4.nat_gateway` | NAT gateway |
| Internet Gateway | `mxgraph.aws4.internet_gateway` | IGW |
| VPN Gateway | `mxgraph.aws4.vpn_gateway` | VPN |
| Direct Connect | `mxgraph.aws4.direct_connect` | Dedicated line |
| Transit Gateway | `mxgraph.aws4.transit_gateway` | Network hub |
| PrivateLink | `mxgraph.aws4.privatelink` | Private connectivity |
| Global Accelerator | `mxgraph.aws4.global_accelerator` | Global acceleration |

### Security, Identity & Compliance

| Service | Shape name | Description |
|--------|-----------|------|
| IAM | `mxgraph.aws4.identity_and_access_management` | Access management |
| Cognito | `mxgraph.aws4.cognito` | User authentication |
| WAF | `mxgraph.aws4.waf` | Web firewall |
| Shield | `mxgraph.aws4.shield` | DDoS protection |
| KMS | `mxgraph.aws4.key_management_service` | Key management |
| Secrets Manager | `mxgraph.aws4.secrets_manager` | Secrets management |
| Certificate Manager | `mxgraph.aws4.certificate_manager` | SSL/TLS certificates |
| GuardDuty | `mxgraph.aws4.guardduty` | Threat detection |
| Inspector | `mxgraph.aws4.inspector` | Vulnerability scanning |
| Macie | `mxgraph.aws4.macie` | Data security |
| Security Hub | `mxgraph.aws4.security_hub` | Security hub |

### Application Integration

| Service | Shape name | Description |
|--------|-----------|------|
| SQS | `mxgraph.aws4.sqs` | Message queue |
| SNS | `mxgraph.aws4.sns` | Notification service |
| EventBridge | `mxgraph.aws4.eventbridge` | Event bus |
| Step Functions | `mxgraph.aws4.step_functions` | Workflow orchestration |
| AppSync | `mxgraph.aws4.appsync` | GraphQL API |
| MQ | `mxgraph.aws4.mq` | Message broker |

### Analytics

| Service | Shape name | Description |
|--------|-----------|------|
| Kinesis | `mxgraph.aws4.kinesis` | Streaming data |
| Athena | `mxgraph.aws4.athena` | S3 query engine |
| EMR | `mxgraph.aws4.emr` | Big data processing |
| Glue | `mxgraph.aws4.glue` | ETL service |
| QuickSight | `mxgraph.aws4.quicksight` | BI visualization |
| OpenSearch Service | `mxgraph.aws4.opensearch_service` | search/analytics (newer OpenSearch glyph — preferred) |
| OpenSearch (legacy) | `mxgraph.aws4.elasticsearch_service` | fallback for older draw.io versions (old ES icon) |
| Data Pipeline | `mxgraph.aws4.data_pipeline` | Data movement |
| Lake Formation | `mxgraph.aws4.lake_formation` | Data lake |
| MSK | `mxgraph.aws4.managed_streaming_for_kafka` | Kafka |

### Machine Learning

| Service | Shape name | Description |
|--------|-----------|------|
| SageMaker | `mxgraph.aws4.sagemaker` | ML platform |
| Bedrock | `mxgraph.aws4.bedrock` | Generative AI |
| Rekognition | `mxgraph.aws4.rekognition` | Image/video analysis |
| Comprehend | `mxgraph.aws4.comprehend` | NLP |
| Lex | `mxgraph.aws4.lex` | Chatbot |
| Polly | `mxgraph.aws4.polly` | TTS |
| Transcribe | `mxgraph.aws4.transcribe` | STT |
| Translate | `mxgraph.aws4.translate` | Translation |
| Textract | `mxgraph.aws4.textract` | Document analysis |

### Management & Governance

| Service | Shape name | Description |
|--------|-----------|------|
| CloudWatch | `mxgraph.aws4.cloudwatch` | Monitoring |
| CloudTrail | `mxgraph.aws4.cloudtrail` | Audit logging |
| CloudFormation | `mxgraph.aws4.cloudformation` | IaC |
| Systems Manager | `mxgraph.aws4.systems_manager` | Operations management |
| Config | `mxgraph.aws4.config` | Resource configuration |
| Organizations | `mxgraph.aws4.organizations` | Account management |
| Control Tower | `mxgraph.aws4.control_tower` | Landing zone |
| Service Catalog | `mxgraph.aws4.service_catalog` | Service catalog |

### Developer Tools

| Service | Shape name | Description |
|--------|-----------|------|
| CodeCommit | `mxgraph.aws4.codecommit` | Git repository |
| CodeBuild | `mxgraph.aws4.codebuild` | Build service |
| CodeDeploy | `mxgraph.aws4.codedeploy` | Deployment automation |
| CodePipeline | `mxgraph.aws4.codepipeline` | CI/CD |
| Cloud9 | `mxgraph.aws4.cloud9` | Cloud IDE |
| X-Ray | `mxgraph.aws4.xray` | Distributed tracing |

## AWS Groups (container/group shapes)

Containers for logically grouping resources in architecture diagrams.

### Basic infrastructure groups

| Element | Shape name | Color | Description |
|------|-----------|------|------|
| AWS Cloud | `mxgraph.aws4.group_aws_cloud` | #242F3E | overall AWS Cloud boundary |
| AWS Cloud (Alt) | `mxgraph.aws4.group_aws_cloud_alt` | #242F3E | AWS Cloud (alternate style) |
| Region | `mxgraph.aws4.group_region` | #147EBA | Region boundary |
| Availability Zone | `mxgraph.aws4.group_availability_zone` | #147EBA | Availability Zone (AZ) |

### Network groups

| Element | Shape name | Color | Description |
|------|-----------|------|------|
| VPC | `mxgraph.aws4.group_vpc` | #248814 | Virtual Private Cloud |
| VPC (alt) | `mxgraph.aws4.group_vpc2` | #248814 | VPC alternate style |
| Public Subnet | `mxgraph.aws4.group_public_subnet` | #248814 | public subnet (solid line) |
| Private Subnet | `mxgraph.aws4.group_private_subnet` | #147EBA | private subnet (dashed line) |
| Security Group | `mxgraph.aws4.group_security_group` | #DF3312 | security group |
| Network ACL | `mxgraph.aws4.group_nacl` | #248814 | network ACL |

### Compute groups

| Element | Shape name | Color | Description |
|------|-----------|------|------|
| Auto Scaling Group | `mxgraph.aws4.group_auto_scaling` | #ED7100 | Auto Scaling group |
| EC2 Instance Contents | `mxgraph.aws4.group_ec2_instance_contents` | #ED7100 | inside an EC2 instance |
| Spot Fleet | `mxgraph.aws4.group_spot_fleet` | #ED7100 | Spot fleet |
| ECS Cluster | `mxgraph.aws4.group_ecs_cluster` | #ED7100 | ECS cluster |
| EKS Cluster | `mxgraph.aws4.group_eks_cluster` | #ED7100 | EKS cluster |

### Service/feature groups

| Element | Shape name | Color | Description |
|------|-----------|------|------|
| AWS Account | `mxgraph.aws4.group_aws_account` | #242F3E | AWS account boundary |
| Corporate Data Center | `mxgraph.aws4.group_corporate_data_center` | #7D8998 | on-premises data center |
| Elastic Beanstalk Container | `mxgraph.aws4.group_elastic_beanstalk` | #248814 | EB environment |
| Step Functions | `mxgraph.aws4.group_step_functions` | #CD2264 | Step Functions workflow |
| Generic Group | `mxgraph.aws4.group_generic` | #7D8998 | generic group |
| Generic Group (alt) | `mxgraph.aws4.group_generic_alt` | #7D8998 | generic group (alternate) |

### Group style guide

```
# Basic group style
shape=mxgraph.aws4.group_[type];
strokeWidth=2;
dashed=0;               # solid line (public subnet)
dashed=1;               # dashed line (private subnet)
rounded=1;
arcSize=10;
fillColor=none;         # transparent background recommended
fontFamily=Amazon Ember;
fontStyle=1;            # Bold
fontSize=14;
verticalAlign=top;
spacingTop=10;
spacingLeft=10;
```

### Group nesting order (outer → inner)

```
1. AWS Cloud
   └── 2. Region
       └── 3. Availability Zone
           └── 4. VPC
               └── 5. Subnet (Public/Private)
                   └── 6. Security Group
                       └── 7. EC2 Instance / Auto Scaling Group
```

### Group color palette

> **The single source of truth for colors is `references/design-tokens.md`.** Values below match it (Public=green #7AA116, Private=teal #00A4A6).

| Group type | Border Color | Fill Color | Use |
|----------|--------------|------------|------|
| AWS Cloud | #232F3E | none | overall cloud |
| Region/AZ | #00A4A6 | none | region/availability zone |
| VPC | #879196 | none | network (solid line) |
| Public Subnet | #7AA116 | #F2F6E8 | public (green) |
| Private Subnet | #00A4A6 | #E6F6F7 | private (teal) |
| Security Group | #C7131F | #FEE7E7 | security |
| Compute (ASG/EC2) | #ED7100 | none | compute |
| Generic | #7D8998 | none | generic |

## General icons

| Element | Shape name | Description |
|------|-----------|------|
| User | `mxgraph.aws4.user` | user |
| Users | `mxgraph.aws4.users` | user group |
| Client | `mxgraph.aws4.client` | client |
| Mobile Client | `mxgraph.aws4.mobile_client` | mobile |
| Traditional Server | `mxgraph.aws4.traditional_server` | on-premises server |
| Corporate Data Center | `mxgraph.aws4.corporate_data_center` | data center |
| Internet | `mxgraph.aws4.internet` | internet |
| Cloud | `mxgraph.aws4.cloud` | generic cloud |

## Service icon color codes (fillColor / gradientColor)

AWS icons are **color-coded by service category**. Using these colors keeps the diagram consistent with official AWS style.

### Category-to-color mapping

| Category | fillColor | gradientColor | Representative services |
|----------|-----------|---------------|-------------|
| **Compute** (Orange) | `#D05C17` | `#F78E04` | EC2, Lambda, ECS, EKS |
| **Storage** (Green) | `#277116` | `#60A337` | S3, EBS, EFS, Glacier |
| **Database** (Blue) | `#3334B9` | `#4D72F3` | RDS, DynamoDB, Aurora |
| **Security** (Red) | `#C7131F` | `#F54749` | IAM, WAF, GuardDuty |
| **Networking** (Purple) | `#5A30B5` | `#945DF2` | VPC, CloudFront, Route53 |
| **Management** (Pink) | `#BC1356` | `#F34482` | CloudWatch, CloudTrail |
| **AI/ML** (Teal) | `#116D5B` | `#4AB29A` | SageMaker, Bedrock |
| **Integration** (Magenta) | `#BC1356` | `#F34482` | SQS, SNS, EventBridge |
| **Analytics** (Purple) | `#5A30B5` | `#945DF2` | Kinesis, Athena, Glue |
| **Developer** (Blue) | `#3334B9` | `#4D72F3` | CodePipeline, CodeBuild |

### Example XML with color applied

```xml
<!-- Compute (EC2) -->
<mxCell id="ec2" value="EC2"
  style="sketch=0;outlineConnect=0;fontColor=#232F3E;
         gradientColor=#F78E04;gradientDirection=north;
         fillColor=#D05C17;strokeColor=#ffffff;
         dashed=0;verticalLabelPosition=bottom;verticalAlign=top;
         align=center;html=1;fontSize=9;fontStyle=0;aspect=fixed;
         shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.ec2;
         fontFamily=Amazon Ember;"
  vertex="1" parent="1">
  <mxGeometry x="100" y="100" width="48" height="48" as="geometry" />
</mxCell>

<!-- Database (RDS) -->
<mxCell id="rds" value="RDS"
  style="sketch=0;outlineConnect=0;fontColor=#232F3E;
         gradientColor=#4D72F3;gradientDirection=north;
         fillColor=#3334B9;strokeColor=#ffffff;
         dashed=0;verticalLabelPosition=bottom;verticalAlign=top;
         align=center;html=1;fontSize=9;fontStyle=0;aspect=fixed;
         shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.rds;
         fontFamily=Amazon Ember;"
  vertex="1" parent="1">
  <mxGeometry x="200" y="100" width="48" height="48" as="geometry" />
</mxCell>

<!-- Security (WAF) -->
<mxCell id="waf" value="WAF"
  style="sketch=0;outlineConnect=0;fontColor=#232F3E;
         gradientColor=#F54749;gradientDirection=north;
         fillColor=#C7131F;strokeColor=#ffffff;
         dashed=0;verticalLabelPosition=bottom;verticalAlign=top;
         align=center;html=1;fontSize=9;fontStyle=0;aspect=fixed;
         shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.waf;
         fontFamily=Amazon Ember;"
  vertex="1" parent="1">
  <mxGeometry x="300" y="100" width="48" height="48" as="geometry" />
</mxCell>
```

### Connector color guide

| Connection type | strokeColor | strokeWidth | Description |
|----------|-------------|-------------|------|
| Direct Connect | `#FF9800` | 4 | dedicated line connection |
| PrivateLink | `#5A30B5` | 2 | private connection between VPCs |
| VPN | `#7D8998` | 2 | VPN tunnel |
| General connection | `#545B64` | 2 | default arrow |
| Data flow | `#3334B9` | 2 | data movement |

---

## Style templates

### Basic AWS icon style

```
shape=mxgraph.aws4.[service];
fontFamily=Amazon Ember;
fontSize=12;
labelPosition=center;
verticalLabelPosition=bottom;
align=center;
verticalAlign=top;
```

### Group/container style

```
shape=mxgraph.aws4.group_[type];
fontFamily=Amazon Ember;
fontSize=14;
fontStyle=1;
verticalAlign=top;
spacingTop=10;
strokeColor=#[color];
fillColor=#[background];
dashed=0;
```

## Icon size guide

> **The single source of truth is `references/design-tokens.md`: standard 78×78** (uniform across all icons), with a dense exception of 48×48 (only when ≥16 icons). 40/60 are retired.

| Type | Size | Use |
|------|------|------|
| Service/resource icon (standard) | **78x78** | default — all icons the same |
| Dense exception | 48x48 | only when ≥16 icons, uniform within a diagram |

## Searching icons via MCP

```
# Check AWS category
mcp__drawio__get-shape-categories

# List all shapes in the AWS category
mcp__drawio__get-shapes-in-category
→ category: "AWS"

# Search for a specific service
mcp__drawio__get-shape-by-name
→ name: "ec2"
```
