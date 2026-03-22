# GitBook Component Patterns

Ready-to-use patterns for GitBook's rich content components.

---

## Hints (Callouts)

Four styles available:

```markdown
{% hint style="info" %}
**Tip**: General information or helpful tip.
{% endhint %}

{% hint style="success" %}
**Done**: Confirmation that an action succeeded.
{% endhint %}

{% hint style="warning" %}
**Warning**: Something to be cautious about.
{% endhint %}

{% hint style="danger" %}
**Critical**: Breaking change or security concern.
{% endhint %}
```

---

## Tabs

Group related content into switchable tabs:

```markdown
{% tabs %}
{% tab title="Linux" %}
```bash
sudo apt install kubectl
curl -LO https://dl.k8s.io/release/stable.txt
```
{% endtab %}

{% tab title="macOS" %}
```bash
brew install kubectl
```
{% endtab %}

{% tab title="Windows" %}
```powershell
choco install kubernetes-cli
```
{% endtab %}
{% endtabs %}
```

---

## Code Blocks

### Basic

````markdown
```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-service
```
````

### With Title and Line Numbers

```markdown
{% code title="deployment.yaml" lineNumbers="true" %}
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
spec:
  replicas: 3
```
{% endcode %}
```

### With Highlighted Lines

```markdown
{% code lineNumbers="true" %}
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config    # This line is important
data:
  key: value
```
{% endcode %}
```

---

## Images

### Standard

```markdown
![Architecture Diagram](.gitbook/assets/architecture.png)
```

### With Caption

```markdown
<figure><img src=".gitbook/assets/diagram.png" alt="System Architecture"><figcaption><p>Figure 1: System Architecture Overview</p></figcaption></figure>
```

### Sized Image

```markdown
<figure><img src=".gitbook/assets/screenshot.png" alt="Dashboard" width="600"><figcaption><p>Monitoring Dashboard</p></figcaption></figure>
```

---

## Expandable Sections

```markdown
<details>
<summary>Advanced Configuration Options</summary>

You can configure additional parameters:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `timeout` | `30s` | Request timeout |
| `retries` | `3` | Max retry attempts |

</details>
```

---

## Embedded Content

### Files (Downloadable)

```markdown
{% file src=".gitbook/assets/template.yaml" %}
Download the CloudFormation template
{% endfile %}
```

### Videos

```markdown
{% embed url="https://www.youtube.com/watch?v=dQw4w9WgXcQ" %}
Demo walkthrough video
{% endembed %}
```

### External Pages

```markdown
{% embed url="https://aws.amazon.com/lambda/" %}
AWS Lambda Documentation
{% endembed %}
```

---

## Tables

### Standard

```markdown
| Service | Purpose | Cost Model |
|---------|---------|------------|
| Lambda | Compute | Per-invocation |
| S3 | Storage | Per-GB stored |
| DynamoDB | Database | Per-RCU/WCU |
```

### With Alignment

```markdown
| Left | Center | Right |
|:-----|:------:|------:|
| Text | Text | 100 |
| Text | Text | 200 |
```

---

## Diagrams

### Embed Draw.io PNG (Static)

```markdown
![VPC Architecture](.gitbook/assets/vpc-architecture.png)
```

### Embed Animated SVG (Interactive)

For animated diagrams created by animated-diagram-agent, use an iframe:

```html
<iframe src="../.gitbook/assets/traffic-flow.html" width="100%" height="500" frameborder="0" style="border-radius: 8px; border: 1px solid #3d4f5f;"></iframe>
```

### Mermaid (Inline)

GitBook supports Mermaid diagrams natively:

````markdown
```mermaid
graph LR
    A[Client] --> B[ALB]
    B --> C[ECS Service]
    C --> D[(RDS)]

    style A fill:#e1f5fe
    style B fill:#945DF2,color:#fff
    style C fill:#F78E04,color:#fff
    style D fill:#4D72F3,color:#fff
```
````

---

## Page Templates

### Overview Page

```markdown
---
description: High-level overview of the system architecture
---

# Architecture Overview

## Context

Brief description of the system and its purpose.

{% hint style="info" %}
This architecture supports up to 10,000 concurrent users.
{% endhint %}

## Components

![Architecture Diagram](.gitbook/assets/architecture.png)

| Component | Service | Purpose |
|-----------|---------|---------|
| Frontend | CloudFront + S3 | Static hosting |
| API | API Gateway + Lambda | REST API |
| Database | DynamoDB | Data storage |

## Data Flow

1. User requests are routed through CloudFront
2. API calls are handled by API Gateway
3. Lambda functions process business logic
4. Data is persisted in DynamoDB

## Next Steps

* [Component Details](components.md)
* [Deployment Guide](../operations/deployment.md)
```

### How-To Page

```markdown
# Deploy to Production

## Prerequisites

* AWS CLI configured
* Terraform installed (v1.5+)
* Access to the production AWS account

## Steps

### 1. Initialize Terraform

```bash
cd infrastructure/
terraform init
```

### 2. Review Plan

```bash
terraform plan -var-file=prod.tfvars
```

{% hint style="warning" %}
Always review the plan before applying to production.
{% endhint %}

### 3. Apply Changes

```bash
terraform apply -var-file=prod.tfvars
```

### 4. Verify Deployment

```bash
aws ecs list-services --cluster production
```

## Troubleshooting

<details>
<summary>Terraform state lock error</summary>

If you get a state lock error, check if another deployment is in progress:

```bash
terraform force-unlock <LOCK_ID>
```

</details>
```
