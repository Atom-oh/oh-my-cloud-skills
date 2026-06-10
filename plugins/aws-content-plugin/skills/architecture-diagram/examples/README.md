# Golden Exemplars — spec-driven AWS diagrams

These are the reference outputs of `scripts/layout_aws.py`. Each is a **spec (`.yaml`) +
generated diagram (`.drawio`)** pair that passes both gates at **100/100
[geometry · design]**. Copy a spec as the starting point for a new diagram — edit
structure/labels/flows, never coordinates.

| Spec | Pattern | Demonstrates |
|------|---------|--------------|
| `multi-az-3tier.yaml` | Multi-AZ Web 3-Tier (CloudFront → ALB → ECS → RDS) | `vpc` engine: mirrored 2-AZ columns, public/private subnets, cross-AZ flows |
| `eks-multi-az.yaml` | EKS Multi-AZ cluster | `vpc` engine: multi-service subnet rows (EKS Node + Worker), Aurora data tier |
| `serverless-api.yaml` | Serverless REST API (API GW → Lambda → DynamoDB/S3 + EventBridge) | `stages` engine: left→right stage columns, no VPC, sync + async flows |

## Regenerate / verify

```bash
cd ..                          # skill root
python3 scripts/layout_aws.py examples/multi-az-3tier.yaml -o /tmp/out.drawio
python3 scripts/validate_drawio.py /tmp/out.drawio
python3 scripts/lint_layout.py /tmp/out.drawio          # expect 100/100
xvfb-run -a drawio -x -f png -s 2 -o /tmp/out.png /tmp/out.drawio
```

## Spec shape (no coordinates)

The Region's shape selects the layout engine: **`vpc`** (Multi-AZ / tier) or **`stages`**
(serverless / pipeline). `external`, `edge`, `title`, and `flows` are shared.

### `vpc` engine — Multi-AZ / tiered

```yaml
title: "..."
external: [{id, icon, label}]          # left column, outside AWS (users, on-prem)
edge:     [{id, icon, label}]          # between external and Region (CloudFront/Route53/WAF/ALB)
region:
  label: "AWS Region (...)"
  vpc:
    label: "VPC ..."
    azs: ["AZ-a", "AZ-c"]              # >=1; rendered as equal-size mirrored columns
    tiers:                             # top→bottom rows; one subnet per (tier × az)
      - {name, kind: public|private, services: [{id, icon, label}, ...]}
flows: [{from, to, label, kind: sync|async|highlight}]
```

Service ids are instanced per AZ: `alb` → `alb_0` (AZ-0), `alb_1` (AZ-1). A flow naming a
bare id binds to the AZ-0 instance.

### `stages` engine — serverless / pipeline

```yaml
region:
  label: "AWS Region (...)"
  stages:                              # left→right columns, no VPC/subnets
    - {name: "Compute", services: [{id: fn, icon: lambda, label: "OrderFn"}, ...]}
    - {name: "Data",    services: [{id: ddb, icon: dynamodb, label: "DynamoDB"}, ...]}
flows: [{from: client, to: fn}, {from: fn, to: ddb}]   # ids used directly (no AZ suffix)
```

Icon short-names are in `layout_aws.py` (`ICONS`).

> Why this beats hand-placed XML and general auto-layout engines: see the top of
> `../SKILL.md` and the bake-off report (drawio won fidelity; ELK/Graphviz broke AWS
> Multi-AZ symmetry; the gap was LLM coordinate-guessing, which this removes).
