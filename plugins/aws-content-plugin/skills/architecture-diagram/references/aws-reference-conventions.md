# AWS Reference-Architecture Conventions — placement "taste"

> The biggest gap between an LLM diagram and a hand-made PowerPoint one isn't draw.io
> knowledge — it's the **unwritten placement rules** AWS reference architectures follow.
> Apply these so the diagram reads the way an AWS Solutions Architect would draw it.
> Sizes/colors come from `design-tokens.md`; this file is about WHERE things go.

## 1. Flow direction (decide once, keep it)

- **Data / request flow: left → right.** User on the far left, data store on the far right.
- **Control / management flow: top → bottom.** CI/CD, IAM, monitoring sit above or below
  the data path, never woven through it.
- Pick one primary axis and never reverse it mid-diagram. Arrows that double back read as messy.

## 2. What goes INSIDE the VPC vs OUTSIDE

A frequent mistake is putting managed/edge services inside the VPC box.

**Outside the VPC** — in a "Managed Services" / "AWS Cloud" band above or beside the VPC:
- Edge & global: CloudFront, Route 53, WAF, Global Accelerator
- Serverless & managed data: S3, DynamoDB, SQS, SNS, Lambda (unless VPC-attached), API
  Gateway, Cognito, Secrets Manager, ECR, SES
- These connect INTO the VPC via arrows; they are not drawn inside a subnet.

**Inside the VPC** (in subnets): EC2, RDS, ElastiCache, EKS/ECS nodes, ALB/NLB, NAT
Gateway, VPC-attached Lambda, ENIs, interface endpoints.

## 3. Canonical positions (so every diagram looks familiar)

| Element | Position |
|---------|----------|
| Internet / users | far left (or top-left), outside AWS Cloud |
| Internet Gateway (IGW) | VPC top edge, centered or top-left |
| Public subnet | top row of the VPC |
| NAT Gateway | in the **public** subnet (left side) |
| ALB / NLB | public subnet (or dedicated ELB subnet), above the app tier |
| Private/app subnet | middle row |
| Data/DB subnet | bottom row (RDS/Aurora here, often Multi-AZ) |
| Availability Zones | **side by side** (columns), never stacked vertically |
| Region label | dashed container wrapping the AZs |
| Managed-services band | above or to the right of the VPC (orange `#FF9900` frame) |
| Legend / title | bottom-right or top-center (see §6) |

## 4. Multi-AZ & multi-tier

- Show **2 AZs side by side** as parallel columns; mirror the tier structure in each.
- Tiers stack top→bottom **within** an AZ: public (web) → private (app) → data.
- If both AZs are identical, draw both but you may de-emphasize the second (70% opacity)
  to keep focus — or show one AZ in detail and a compact "AZ-b (mirror)" box.

## 5. Subnet semantics (color carries meaning — see design-tokens.md)

- **Public subnet = green `#7AA116`** (internet-routable: ALB, NAT, bastion).
- **Private subnet = teal `#00A4A6`** (app/data: EC2, RDS, EKS nodes).
- Don't put a database in a public subnet — reviewers read that as a security error even
  in a diagram.

## 6. Framing, legend, title

- **Canvas margin ≥ 40px** on all sides — never let a box touch the edge.
- Every diagram gets a **title** (top-center or bottom-left) and, if it has >1 edge style,
  a **legend** (bottom-right) explaining sync vs async vs management lines.
- A numbered-flow diagram (see `snippets.md` → numbered flow) gets a **step legend**:
  `① User → CloudFront  ② → ALB  ③ → ECS  ④ → RDS`.

## 7. When to STOP drawing connections

- Edge budget is **≤ 12** (design-tokens.md). Past that, switch to the numbered-flow
  pattern: draw only the primary path as arrows, express secondary relationships with
  numbered badges + the step legend. This is the single biggest readability win on busy
  diagrams (and what `lint_layout.py` nudges you toward).

## 8. Quick self-check before export

- Does data flow one direction? Are managed services outside the VPC? Are AZs side by
  side? Is the DB in a private subnet? Is there a title + legend + margin?
- Then run `validate_drawio.py` and `lint_layout.py` (≥ 80) — mechanical confirmation.
