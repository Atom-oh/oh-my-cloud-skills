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
| `multi-region-dr.yaml` | Multi-Region Active/DR (Route 53 → 2 regions, Aurora replication) | `regions:` list, per-region id prefixes (`r0_`/`r1_`), cross-region async flow |
| `hybrid-dx.yaml` | Hybrid (On-prem IDC ↔ AWS via Direct Connect, DMS migration) | `onprem:` block + DX edge + Multi-AZ VPC |

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

### Multi-region — `regions:` (a list)

Replace `region:` with `regions:` (each entry is a full `vpc` or `stages` region). Ids are
namespaced per region: `r<i>_<id>` (vpc instances: `r<i>_<id>_<az>`).

```yaml
edge: [{id: r53, icon: route53, label: "Route 53"}]
regions:
  - {label: "Primary (us-east-1)", vpc: {azs: ["AZ-1a"], tiers: [...]}}
  - {label: "DR (us-west-2)",      vpc: {azs: ["AZ-2a"], tiers: [...]}}
flows: [{from: r0_rds, to: r1_rds, label: "replicate", kind: async}]
```

### Hybrid — `onprem:` block

Adds a corporate-DC container left of the Region, connected via a Direct Connect / VPN edge.

```yaml
onprem: {label: "On-Premises (IDC)", services: [{id: app_srv, icon: ec2, label: "App"}]}
edge:   [{id: dx, icon: directconnect, label: "Direct Connect"}]
region: {vpc: {...}}
flows:  [{from: app_srv, to: dx}, {from: dx, to: ec2_0}]
```

Blocks compose left→right: **[external] [onprem] [edge] [region(s)]**. Icon short-names
are in `layout_aws.py` (`ICONS`).

> Why this beats hand-placed XML and general auto-layout engines: see the top of
> `../SKILL.md` and the bake-off report (drawio won fidelity; ELK/Graphviz broke AWS
> Multi-AZ symmetry; the gap was LLM coordinate-guessing, which this removes).
