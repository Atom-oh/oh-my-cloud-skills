#!/usr/bin/env python3
"""AWS-aware deterministic layout engine: a compact spec -> a clean .drawio diagram.

WHY THIS EXISTS
---------------
The bake-off (~/diagram-bakeoff) showed the quality gap vs hand-crafted PPT is NOT a
tool problem — drawio renders beautifully. It is that the LLM hand-places pixel
coordinates, which is the one thing LLMs are weakest at (2D spatial reasoning). General
auto-layout engines (D2/ELK, Graphviz) don't help either: they optimize edge-crossing,
not the AWS *conventions* (mirrored AZ columns, nested VPC, left->right tiers) that make
AWS diagrams look professional.

So: the author declares STRUCTURE + LABELS + FLOWS (never coordinates). This engine
computes every coordinate bottom-up with AWS conventions baked in — uniform 78px icons,
mirrored equal-size AZ columns, tiered subnets, breathing room, a title — and emits
drawio using the skill's canonical styles (design-tokens.md). The output is meant to
pass `validate_drawio.py` and `lint_layout.py` (geometry AND design) with no edits.

SPEC (YAML or JSON)
-------------------
    title: "Multi-AZ Web 3-Tier"
    external:                       # left column, top-to-bottom (outside AWS)
      - {id: users, icon: users, label: "Users"}
    edge:                           # between external actors and the Region (CDN/DNS/WAF)
      - {id: cf, icon: cloudfront, label: "Amazon CloudFront"}
    region:
      label: "AWS Region (us-east-1)"
      vpc:
        label: "VPC 10.0.0.0/16"
        azs: ["Availability Zone A", "Availability Zone C"]   # >=1; rendered mirrored
        tiers:                      # top-to-bottom rows; one subnet per (tier x az)
          - {name: "Public Subnet",  kind: public,  services: [{id: alb, icon: alb, label: "ALB"}]}
          - {name: "Private App",    kind: private, services: [{id: ecs, icon: ecs, label: "ECS Fargate"}]}
          - {name: "Private Data",   kind: private, services: [{id: rds, icon: rds, label: "RDS"}]}
    flows:                          # ids are suffixed per AZ: alb_0 (AZ A), alb_1 (AZ C).
      - {from: users, to: cf, label: "HTTPS"}              # a base id == AZ-0 instance
      - {from: cf,    to: alb_0, label: "origin"}
      - {from: alb_0, to: ecs_0, label: "route"}
      - {from: rds_0, to: rds_1, label: "replicate", kind: async}

Service / actor ids are unique handles for flows. Inside a tier, each service is
instantiated once per AZ; instance id = "<id>_<az-index>". A flow endpoint that names a
bare base id resolves to the AZ-0 instance.

PATTERN 2 — serverless / stages (no VPC). Replace `region.vpc` with `region.stages`:
a left-to-right row of labelled groups, each a vertical column of services. For
serverless / event-driven / pipeline shapes (API -> compute -> data). Service ids are
NOT AZ-instanced here (they are unique as written), so flows use the ids directly.

    region:
      label: "AWS Region (us-east-1)"
      stages:
        - {name: "Compute", services: [{id: fn, icon: lambda, label: "OrderFn"}]}
        - {name: "Data",    services: [{id: ddb, icon: dynamodb, label: "DynamoDB"}]}
    flows:
      - {from: client, to: fn, label: "invoke"}
      - {from: fn, to: ddb, label: "put"}

The Region's shape selects the engine: `vpc` -> Multi-AZ/tier; `stages` -> serverless.

PATTERN 3 — multi-region. Use `regions:` (a list) instead of `region:`. Each entry is a
full region (vpc or stages) and is laid out left-to-right. Ids are namespaced per region:
`r<region-index>_<id>` (and `r<i>_<id>_<az>` for vpc instances). So a flow to the DR
region's database is `{from: r0_rds, to: r1_rds, kind: async}`.

    regions:
      - {label: "Primary (us-east-1)", vpc: {azs: ["AZ-1a"], tiers: [...]}}
      - {label: "DR (us-west-2)",      vpc: {azs: ["AZ-2a"], tiers: [...]}}
    flows: [{from: r0_rds, to: r1_rds, label: "replicate", kind: async}]

PATTERN 4 — hybrid. Add an `onprem:` block (a corporate-DC container with a column of
servers) placed left of the Region; connect it via a Direct Connect / VPN edge actor.

    onprem: {label: "On-Premises (IDC)", services: [{id: app_srv, icon: ec2, label: "App"}]}
    edge:   [{id: dx, icon: directconnect, label: "Direct Connect"}]
    region: { vpc: {...} }
    flows:  [{from: app_srv, to: dx}, {from: dx, to: ec2_0}]

Blocks compose left→right in this order: [external] [onprem] [edge] [region(s)].

Usage:
    python3 layout_aws.py spec.yaml -o out.drawio
    python3 layout_aws.py spec.yaml            # writes <spec>.drawio next to the spec
Then ALWAYS gate before export:
    python3 validate_drawio.py out.drawio && python3 lint_layout.py out.drawio
"""
import sys
import os
import json
import html
import base64
import glob
import functools

# ---- canonical metrics (design-tokens.md) ----
ICON = 78
ICON_LABEL = 26     # label rendered below the icon
PAD = 24            # container inner padding (sides/bottom)
LABEL_TOP = 34      # container top band for its own label
GAP = 36            # gap between sibling containers (subnets, AZ columns)
ICON_GAP = 46       # gap between sibling icons in a subnet row
MARGIN = 40         # canvas margin
FLOW_GAP = 70       # horizontal gap between external | edge | region columns

# ---- color palette (design-tokens.md) ----
C = {
    "region_stroke": "#00A4A6", "region_font": "#147EBA",
    "vpc_stroke": "#879196", "vpc_font": "#879196",
    "az_stroke": "#00A4A6", "az_font": "#147EBA",
    "pub_stroke": "#7AA116", "pub_fill": "#F2F6E8", "pub_font": "#248814",
    "prv_stroke": "#00A4A6", "prv_fill": "#E6F6F7", "prv_font": "#147EBA",
    "edge_sync": "#545B64", "edge_async": "#545B64", "edge_hi": "#FF9900",
    "title": "#232F3E",
}

# ---- icon registry: short name -> (resIcon, fill, gradient) ----
# fill/gradient follow AWS category coloring (compute=orange, db=blue/purple, net=purple).
_ORANGE = ("#D05C17", "#F78E04")
_PURPLE = ("#5A30B5", "#945DF2")
_BLUE = ("#3334B9", "#4D72F3")
_PINK = ("#C7131F", "#F34482")
_GREEN = ("#1B660F", "#6CAE3E")
ICONS = {
    "users":      ("users", None, None),            # shape, not resourceIcon
    "user":       ("user", None, None),
    "cloudfront": ("cloudfront", *_PURPLE),
    "route53":    ("route_53", *_PURPLE),
    "directconnect": ("direct_connect", *_PURPLE),
    "tgw":        ("transit_gateway", *_PURPLE),
    "vpngateway": ("vpn_gateway", *_PURPLE),
    "waf":        ("waf", *_PINK),
    "apigateway": ("api_gateway", *_PURPLE),
    "alb":        ("application_load_balancer", *_PURPLE),
    "elb":        ("elastic_load_balancing", *_PURPLE),
    "ec2":        ("ec2", *_ORANGE),
    "ecs":        ("elastic_container_service", *_ORANGE),
    "eks":        ("eks", *_ORANGE),
    "lambda":     ("lambda", *_ORANGE),
    "fargate":    ("fargate", *_ORANGE),
    "rds":        ("rds", *_BLUE),
    "aurora":     ("aurora", *_BLUE),
    "dynamodb":   ("dynamodb", *_BLUE),
    "elasticache":("elasticache", *_BLUE),
    "s3":         ("s3", *_GREEN),
    "sqs":        ("sqs", *_PINK),
    "sns":        ("sns", *_PINK),
    "eventbridge":("eventbridge", *_PINK),
    "secrets":    ("secrets_manager", *_PINK),
    "cloudwatch": ("cloudwatch", *_PINK),
    "bedrock":    ("bedrock", *_GREEN),
    "sagemaker":  ("sagemaker", *_GREEN),
}

# ---- shared service-name vocabulary (ADR-020) ----
# Consumed by reactive-presentation/scripts/archify_icons.py to resolve Archify diagram
# node ids to official AWS icons, so the two diagram paths (this static .drawio engine and
# the interactive Archify path) name AWS services identically and never grow a second,
# divergent vocabulary. Keys are a subset of the ICONS short names above; values are keys
# of reactive-presentation/icons/index-lite.json's ["icons"] sub-dict (official
# Architecture-Service-Icons stems). "users"/"user" are deliberately omitted: they are
# draw.io shapes, not AWS services, and neither is an index key.
ARCH_STEMS = {
    "cloudfront":    "Amazon-CloudFront",
    "route53":       "Amazon-Route-53",
    "directconnect": "AWS-Direct-Connect",
    "tgw":           "AWS-Transit-Gateway",
    "vpngateway":    "AWS-Site-to-Site-VPN",
    "waf":           "AWS-WAF",
    "apigateway":    "Amazon-API-Gateway",
    "alb":           "Elastic-Load-Balancing",
    "elb":           "Elastic-Load-Balancing",
    "ec2":           "Amazon-EC2",
    "ecs":           "Amazon-Elastic-Container-Service",
    "eks":           "Amazon-Elastic-Kubernetes-Service",
    "lambda":        "AWS-Lambda",
    "fargate":       "AWS-Fargate",
    "rds":           "Amazon-RDS",
    "aurora":        "Amazon-Aurora",
    "dynamodb":      "Amazon-DynamoDB",
    "elasticache":   "Amazon-ElastiCache",
    "s3":            "Amazon-Simple-Storage-Service",
    "sqs":           "Amazon-Simple-Queue-Service",
    "sns":           "Amazon-Simple-Notification-Service",
    "eventbridge":   "Amazon-EventBridge",
    "secrets":       "AWS-Secrets-Manager",
    "cloudwatch":    "Amazon-CloudWatch",
    "bedrock":       "Amazon-Bedrock",
    "sagemaker":     "Amazon-SageMaker",
}

# ---- shared AWS icon library (canonical: reactive-presentation/icons) ----
# draw.io's built-in mxgraph.aws4 shape set is fixed and omits new / product icons
# (e.g. Bedrock AgentCore). Those live in the sibling reactive-presentation skill's
# icon library and are SHARED: when a service isn't a built-in shape we embed the
# official icon as a base64 data URI (shape=image), so the .drawio stays portable.
_SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SHARED_ICONS = os.path.normpath(
    os.path.join(_SKILL_DIR, "..", "reactive-presentation", "icons"))
_SERVICE_SET = "Architecture-Service-Icons_07312025"

# Short name -> path (relative to _SHARED_ICONS) for icons NOT in mxgraph.aws4.
# Anything here renders as an embedded image instead of a built-in shape.
# Bedrock AgentCore product icons + its component icons (Runtime/Gateway/Memory/…).
_AC = "AgentCore/dark-purple"
EMBED_ICONS = {
    "agentcore":                  f"{_AC}/Agentcore.png",
    "agentcore-runtime":          f"{_AC}/Runtime.png",
    "agentcore-gateway":          f"{_AC}/Gateway.png",
    "agentcore-memory":           f"{_AC}/Memory.png",
    "agentcore-identity":         f"{_AC}/Identity.png",
    "agentcore-browser":          f"{_AC}/Browser-Tool.png",
    "agentcore-code-interpreter": f"{_AC}/Code-Interpreter.png",
    "agentcore-observability":    f"{_AC}/Observability.png",
    "agentcore-policy":           f"{_AC}/Policy-Engine.png",
    "agentcore-evaluations":      f"{_AC}/Evaluations.png",
    "ai-agent":                   f"{_AC}/AI-Agent.png",
}


@functools.lru_cache(maxsize=None)
def _icon_data_uri(rel_path):
    """Read a shared icon file and return a draw.io-ready data URI, or None.

    draw.io stores embedded images as `data:<mime>,<base64>` (comma form, no
    `;base64`) so the URI never contains a `;` that would break style parsing.
    """
    full = os.path.join(_SHARED_ICONS, rel_path)
    if not os.path.isfile(full):
        return None
    with open(full, "rb") as fh:
        raw = fh.read()
    ext = os.path.splitext(full)[1].lower()
    mime = {".svg": "image/svg+xml", ".png": "image/png",
            ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}.get(ext, "image/png")
    return f"data:{mime},{base64.b64encode(raw).decode('ascii')}"


@functools.lru_cache(maxsize=None)
def _resolve_embed(short):
    """Map a service short name to a shared-icon relative path, or None.

    - explicit EMBED_ICONS entries (e.g. ``agentcore``)
    - ``arch:<Service-Name>`` pulls the 48px SVG from the official Service set,
      e.g. ``arch:Amazon-Bedrock`` -> Arch_Amazon-Bedrock_48.svg
    """
    if short in EMBED_ICONS:
        return EMBED_ICONS[short]
    if short.startswith("arch:"):
        name = short[5:]
        hits = glob.glob(os.path.join(
            _SHARED_ICONS, _SERVICE_SET, "*", "48", f"Arch_{name}_48.svg"))
        if hits:
            return os.path.relpath(hits[0], _SHARED_ICONS)
    return None


def esc(s):
    return html.escape(str(s), quote=True)


def snap(v):
    return int(round(v / 10.0) * 10)


class Cell:
    __slots__ = ("cid", "value", "style", "x", "y", "w", "h", "vertex", "edge",
                 "src", "tgt")

    def __init__(self, cid, value, style, x=0, y=0, w=0, h=0, vertex=True,
                 edge=False, src=None, tgt=None):
        self.cid, self.value, self.style = cid, value, style
        self.x, self.y, self.w, self.h = x, y, w, h
        self.vertex, self.edge, self.src, self.tgt = vertex, edge, src, tgt


# ---------- style builders (canonical, design-tokens.md) ----------
def container_style(grIcon, stroke, font, fill="none", dashed=0):
    return (f"sketch=0;outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;"
            f"fontSize=12;fontStyle=0;container=1;pointerEvents=0;collapsible=0;"
            f"recursiveResize=0;shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.{grIcon};"
            f"grStroke=0;strokeColor={stroke};fillColor={fill};verticalAlign=top;"
            f"align=left;spacingLeft=30;fontColor={font};fontFamily=Amazon Ember;"
            f"dashed={dashed};")


def az_style():
    return (f"fillColor=none;strokeColor={C['az_stroke']};dashed=1;verticalAlign=top;"
            f"fontStyle=0;fontSize=12;align=left;spacingLeft=12;html=1;"
            f"fontColor={C['az_font']};fontFamily=Amazon Ember;")


def icon_style(short):
    # Shared-library icons not in mxgraph.aws4 (AgentCore, arch:<Service>) → embed
    # the official icon as a base64 image so the .drawio stays self-contained.
    rel = _resolve_embed(short)
    if rel:
        uri = _icon_data_uri(rel)
        if uri:
            return (f"sketch=0;outlineConnect=0;fontColor={C['title']};dashed=0;"
                    f"verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;"
                    f"fontSize=10;fontFamily=Amazon Ember;shape=image;imageAspect=1;"
                    f"aspect=fixed;image={uri};")
    res, fill, grad = ICONS.get(short, (short, *_ORANGE))
    if fill is None:  # plain shape (users/user) — no resourceIcon frame
        return (f"sketch=0;outlineConnect=0;fontColor={C['title']};gradientColor=none;"
                f"fillColor={C['title']};strokeColor=none;dashed=0;verticalLabelPosition=bottom;"
                f"verticalAlign=top;align=center;html=1;fontSize=10;fontFamily=Amazon Ember;"
                f"shape=mxgraph.aws4.{res};")
    return (f"sketch=0;outlineConnect=0;fontColor={C['title']};gradientColor={grad};"
            f"gradientDirection=north;fillColor={fill};strokeColor=#ffffff;dashed=0;"
            f"verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=10;"
            f"fontFamily=Amazon Ember;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.{res};")


def edge_style(kind, anchors=""):
    base = "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=block;"
    if kind == "highlight":
        return base + f"strokeColor={C['edge_hi']};strokeWidth=2.5;{anchors}fontSize=9;fontFamily=Amazon Ember;"
    if kind == "async":
        return (base + f"dashed=1;dashPattern=8 8;strokeColor={C['edge_async']};{anchors}"
                f"fontSize=9;fontFamily=Amazon Ember;")
    return base + f"strokeColor={C['edge_sync']};{anchors}fontSize=9;fontFamily=Amazon Ember;"


def _anchors(src_box, tgt_box):
    """Fixed exit/entry points so orthogonal routing leaves/enters cleanly instead of
    cutting across a neighbouring icon. Vertical when the two cells share a column,
    horizontal otherwise."""
    sx, sy, sw, sh = src_box
    tx, ty, tw, th = tgt_box
    scx, scy, tcx, tcy = sx + sw / 2, sy + sh / 2, tx + tw / 2, ty + th / 2
    if abs(tcx - scx) <= max(sw, tw):  # same column → vertical
        if tcy >= scy:
            ex, ey, nx, ny = 0.5, 1, 0.5, 0   # exit bottom, enter top
        else:
            ex, ey, nx, ny = 0.5, 0, 0.5, 1
    else:  # different column → horizontal
        if tcx >= scx:
            ex, ey, nx, ny = 1, 0.5, 0, 0.5   # exit right, enter left
        else:
            ex, ey, nx, ny = 0, 0.5, 1, 0.5
    return (f"exitX={ex};exitY={ey};exitDx=0;exitDy=0;"
            f"entryX={nx};entryY={ny};entryDx=0;entryDy=0;")


# ---------- layout engine ----------
def col_h(items):
    """Visual height of a vertical column of icons (icon spans only, label-gapped)."""
    if not items:
        return 0
    return len(items) * ICON + (len(items) - 1) * (ICON_GAP + ICON_LABEL)


def stage_style():
    """A serverless 'stage' group — a light neutral box, not a VPC/subnet container."""
    return ("rounded=1;arcSize=4;whiteSpace=wrap;html=1;container=1;collapsible=0;"
            "pointerEvents=0;fillColor=#F7F8FA;strokeColor=#B0B7BF;fontColor=#5A6C86;"
            "verticalAlign=top;align=left;spacingLeft=12;spacingTop=8;fontSize=12;"
            "fontStyle=1;fontFamily=Amazon Ember;dashed=0;")


TITLE_STYLE = ("text;html=1;strokeColor=none;fillColor=none;align=left;"
               "verticalAlign=middle;fontSize=18;fontStyle=1;"
               f"fontColor={C['title']};fontFamily=Amazon Ember;")


def _region_size(region):
    """Bounding box of one Region — `vpc` (Multi-AZ/tier) or `stages` (serverless)."""
    if "stages" in region:
        stages = region["stages"]
        stage_w = max(ICON + 2 * PAD, 150)
        stage_h = LABEL_TOP + max(col_h(s.get("services", [])) + ICON_LABEL for s in stages) + PAD
        return (len(stages) * stage_w + (len(stages) - 1) * GAP + 2 * PAD, LABEL_TOP + stage_h + PAD)
    vpc = region["vpc"]
    azs = vpc.get("azs") or ["AZ"]
    tiers = vpc["tiers"]

    def row_w(s):
        n = max(1, len(s))
        return n * ICON + (n - 1) * ICON_GAP

    subnet_w = max(row_w(t.get("services", [])) for t in tiers) + 2 * PAD
    tier_h = LABEL_TOP + ICON + ICON_LABEL + PAD
    az_w = subnet_w + 2 * PAD
    az_h = LABEL_TOP + len(tiers) * tier_h + (len(tiers) - 1) * GAP + PAD
    vpc_w = len(azs) * az_w + (len(azs) - 1) * GAP + 2 * PAD
    return (vpc_w + 2 * PAD, LABEL_TOP + (LABEL_TOP + az_h + PAD) + PAD)


def _render_region(region, rx, ry, prefix, rid, cells, parent, pos, alias):
    """Draw one Region box at absolute (rx, ry) + its interior. `prefix` namespaces ids so
    multiple regions don't collide (e.g. r0_, r1_). Returns (w, h)."""
    rx, ry = snap(rx), snap(ry)
    region_w, region_h = _region_size(region)
    cells.append(Cell(rid, esc(region.get("label", "AWS Region")),
                      container_style("group_region", C["region_stroke"], C["region_font"], dashed=1),
                      rx, ry, region_w, region_h))
    parent[rid] = "1"
    if "stages" in region:
        _fill_stages(region, rx, ry, rid, prefix, cells, parent, pos)
    else:
        _fill_vpc(region, rx, ry, rid, prefix, cells, parent, pos, alias)
    return region_w, region_h


def _fill_vpc(region, rx, ry, rid, prefix, cells, parent, pos, alias):
    vpc = region["vpc"]
    azs = vpc.get("azs") or ["AZ"]
    tiers = vpc["tiers"]

    def row_w(s):
        n = max(1, len(s))
        return n * ICON + (n - 1) * ICON_GAP

    subnet_w = max(row_w(t.get("services", [])) for t in tiers) + 2 * PAD
    tier_h = [LABEL_TOP + ICON + ICON_LABEL + PAD for _ in tiers]
    az_w = subnet_w + 2 * PAD
    az_h = LABEL_TOP + sum(tier_h) + (len(tiers) - 1) * GAP + PAD
    vpc_w = len(azs) * az_w + (len(azs) - 1) * GAP + 2 * PAD
    vpc_h = LABEL_TOP + az_h + PAD
    vpc_id = f"{prefix}vpc"
    vx, vy = rx + PAD, ry + LABEL_TOP
    cells.append(Cell(vpc_id, esc(vpc.get("label", "VPC")),
                      container_style("group_vpc", C["vpc_stroke"], C["vpc_font"]),
                      snap(vx - rx), snap(vy - ry), vpc_w, vpc_h))
    parent[vpc_id] = rid
    for j, az_name in enumerate(azs):
        ax, ay = vx + PAD + j * (az_w + GAP), vy + LABEL_TOP
        az_id = f"{prefix}az_{j}"
        cells.append(Cell(az_id, esc(az_name), az_style(),
                          snap(ax - vx), snap(ay - vy), az_w, az_h))
        parent[az_id] = vpc_id
        ty = ay + LABEL_TOP
        for ti, t in enumerate(tiers):
            if t.get("kind", "private") == "public":
                gi, st, fi, fo = "group_public_subnet", C["pub_stroke"], C["pub_fill"], C["pub_font"]
            else:
                gi, st, fi, fo = "group_private_subnet", C["prv_stroke"], C["prv_fill"], C["prv_font"]
            sx = ax + PAD
            sub_id = f"{prefix}subnet_{j}_{ti}"
            cells.append(Cell(sub_id, esc(t.get("name", "Subnet")),
                              container_style(gi, st, fo, fill=fi),
                              snap(sx - ax), snap(ty - ay), subnet_w, tier_h[ti]))
            parent[sub_id] = az_id
            services = t.get("services", [])
            startx = sx + (subnet_w - row_w(services)) / 2
            icy = ty + LABEL_TOP
            for si, svc in enumerate(services):
                icx = startx + si * (ICON + ICON_GAP)
                inst_id = f"{prefix}{svc['id']}_{j}"
                cells.append(Cell(inst_id, esc(svc.get("label", svc["id"])),
                                  icon_style(svc.get("icon", "ec2")),
                                  snap(icx - sx), snap(icy - ty), ICON, ICON))
                parent[inst_id] = sub_id
                pos[inst_id] = (snap(icx), snap(icy), ICON, ICON)
                if j == 0:
                    # bare (prefixed) id -> the real AZ-0 CELL id, so a flow naming
                    # `rds` / `r0_rds` connects to the actual `rds_0` / `r0_rds_0` cell.
                    alias[f"{prefix}{svc['id']}"] = inst_id
            ty += tier_h[ti] + GAP


def _fill_stages(region, rx, ry, rid, prefix, cells, parent, pos):
    stages = region["stages"]
    stage_w = max(ICON + 2 * PAD, 150)
    stage_h = LABEL_TOP + max(col_h(s.get("services", [])) + ICON_LABEL for s in stages) + PAD
    for i, stg in enumerate(stages):
        stx, sty = rx + PAD + i * (stage_w + GAP), ry + LABEL_TOP
        sid = f"{prefix}stage_{i}"
        cells.append(Cell(sid, esc(stg.get("name", "")), stage_style(),
                          snap(stx - rx), snap(sty - ry), stage_w, stage_h))
        parent[sid] = rid
        svcs = stg.get("services", [])
        avail = stage_h - LABEL_TOP - PAD
        cy = sty + LABEL_TOP + max(0, (avail - (col_h(svcs) + ICON_LABEL)) / 2)
        step = ICON + ICON_GAP + ICON_LABEL
        icx = stx + (stage_w - ICON) / 2
        for k, svc in enumerate(svcs):
            icy = cy + k * step
            svc_id = f"{prefix}{svc['id']}"
            cells.append(Cell(svc_id, esc(svc.get("label", svc["id"])),
                              icon_style(svc.get("icon", "ec2")),
                              snap(icx - stx), snap(icy - sty), ICON, ICON))
            parent[svc_id] = sid
            pos[svc_id] = (snap(icx), snap(icy), ICON, ICON)


def _onprem_size(o):
    svcs = o.get("services", [])
    return (max(ICON + 2 * PAD, 160), LABEL_TOP + col_h(svcs) + ICON_LABEL + PAD)


def _render_onprem(o, ax, ay, cells, parent, pos):
    """On-premises / corporate data center block (hybrid). A grey DC container with a
    vertical column of servers, placed left of the Region (connected via DX/VPN flows)."""
    ax, ay = snap(ax), snap(ay)
    w, h = _onprem_size(o)
    cells.append(Cell("onprem", esc(o.get("label", "On-Premises (IDC)")),
                      container_style("group_corporate_data_center", "#5A6C86", "#5A6C86", fill="#E6E6E6"),
                      ax, ay, w, h))
    parent["onprem"] = "1"
    svcs = o.get("services", [])
    avail = h - LABEL_TOP - PAD
    cy = ay + LABEL_TOP + max(0, (avail - (col_h(svcs) + ICON_LABEL)) / 2)
    step = ICON + ICON_GAP + ICON_LABEL
    icx = ax + (w - ICON) / 2
    for k, svc in enumerate(svcs):
        icy = cy + k * step
        cells.append(Cell(svc["id"], esc(svc.get("label", svc["id"])),
                          icon_style(svc.get("icon", "ec2")),
                          snap(icx - ax), snap(icy - ay), ICON, ICON))
        parent[svc["id"]] = "onprem"
        pos[svc["id"]] = (snap(icx), snap(icy), ICON, ICON)
    return w, h


def build(spec):
    """Compose blocks left→right: [external] [onprem] [edge] [region(s)].

    Handles every pattern via one frame — single region (`region:` vpc|stages),
    multi-region (`regions:` list, ids prefixed r0_/r1_), and hybrid (`onprem:` block
    connected to the region). Flows are wired last by id."""
    cells, parent, pos = [], {}, {}
    alias = {}   # bare/AZ-0 handle -> real cell id (e.g. rds -> rds_0, r0_rds -> r0_rds_0)

    def emit_column(items, ax, ay):
        step = ICON + ICON_GAP + ICON_LABEL
        for k, it in enumerate(items):
            ix, iy = snap(ax), snap(ay + k * step)
            cells.append(Cell(it["id"], esc(it.get("label", it["id"])),
                              icon_style(it.get("icon", "ec2")), ix, iy, ICON, ICON))
            parent[it["id"]] = "1"
            pos[it["id"]] = (ix, iy, ICON, ICON)

    blocks = []  # each: (w, h, render(ax, ay))
    external = spec.get("external", [])
    if external:
        blocks.append((ICON, col_h(external), lambda ax, ay, it=external: emit_column(it, ax, ay)))
    onprem = spec.get("onprem")
    if onprem:
        ow, oh = _onprem_size(onprem)
        blocks.append((ow, oh, lambda ax, ay, o=onprem: _render_onprem(o, ax, ay, cells, parent, pos)))
    edge_actors = spec.get("edge", [])
    if edge_actors:
        blocks.append((ICON, col_h(edge_actors), lambda ax, ay, it=edge_actors: emit_column(it, ax, ay)))

    if spec.get("regions"):
        for ri, rg in enumerate(spec["regions"]):
            rw, rh = _region_size(rg)
            blocks.append((rw, rh, lambda ax, ay, rg=rg, ri=ri:
                           _render_region(rg, ax, ay, f"r{ri}_", f"region_{ri}", cells, parent, pos, alias)))
    elif "region" in spec:
        rg = spec["region"]
        rw, rh = _region_size(rg)
        blocks.append((rw, rh, lambda ax, ay, rg=rg:
                       _render_region(rg, ax, ay, "", "region", cells, parent, pos, alias)))

    has_title = bool(spec.get("title"))
    top = MARGIN + (40 if has_title else 0)
    content_h = max([h for _, h, _ in blocks] + [0])

    x = MARGIN
    for w, h, render in blocks:
        render(x, top + (content_h - h) / 2)
        x += w + FLOW_GAP
    canvas_w = x - FLOW_GAP + MARGIN
    canvas_h = top + content_h + MARGIN

    if has_title:
        cells.append(Cell("title", esc(spec["title"]), TITLE_STYLE, MARGIN, MARGIN, 600, 30))
        parent["title"] = "1"

    def resolve(ref):
        if ref in pos:                 # explicit real cell (alb_0, r0_rds_0, ddb, users)
            return ref
        if ref in alias:               # AZ-0 handle (rds -> rds_0, r0_rds -> r0_rds_0)
            return alias[ref]
        for cand in (f"{ref}_0", f"r0_{ref}"):   # bare convenience fallbacks
            if cand in pos:
                return cand
            if cand in alias:
                return alias[cand]
        return ref

    for i, fl in enumerate(spec.get("flows", [])):
        s, tg = resolve(fl["from"]), resolve(fl["to"])
        anchors = _anchors(pos[s], pos[tg]) if (s in pos and tg in pos) else ""
        cells.append(Cell(f"e{i}", esc(fl.get("label", "")),
                          edge_style(fl.get("kind", "sync"), anchors),
                          vertex=False, edge=True, src=s, tgt=tg))
        parent[f"e{i}"] = "1"

    return cells, parent, snap(canvas_w), snap(canvas_h)


def to_xml(cells, parent, cw, ch, name="Architecture"):
    out = ['<mxfile host="app.diagrams.net" agent="layout_aws.py">',
           f'  <diagram id="arch" name="{esc(name)}">',
           f'    <mxGraphModel dx="{cw}" dy="{ch}" grid="1" gridSize="10" guides="1" '
           f'page="1" pageWidth="{cw}" pageHeight="{ch}" math="0" shadow="0">',
           '      <root>', '        <mxCell id="0" />',
           '        <mxCell id="1" parent="0" />']
    for c in cells:
        p = parent.get(c.cid, "1")
        if c.edge:
            out.append(f'        <mxCell id="{c.cid}" value="{c.value}" style="{c.style}" '
                       f'edge="1" parent="{p}" source="{c.src}" target="{c.tgt}">')
            out.append('          <mxGeometry relative="1" as="geometry" />')
            out.append('        </mxCell>')
        else:
            out.append(f'        <mxCell id="{c.cid}" value="{c.value}" style="{c.style}" '
                       f'vertex="1" parent="{p}">')
            out.append(f'          <mxGeometry x="{c.x}" y="{c.y}" width="{c.w}" '
                       f'height="{c.h}" as="geometry" />')
            out.append('        </mxCell>')
    out += ['      </root>', '    </mxGraphModel>', '  </diagram>', '</mxfile>', '']
    return "\n".join(out)


def main():
    args = [a for a in sys.argv[1:]]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return 2
    spec_path = args[0]
    out = None
    if "-o" in args:
        out = args[args.index("-o") + 1]
    elif "--out" in args:
        out = args[args.index("--out") + 1]
    if not out:
        out = os.path.splitext(spec_path)[0] + ".drawio"

    try:
        with open(spec_path, encoding="utf-8") as f:
            text = f.read()
    except OSError as e:
        print(f"❌ cannot read {spec_path}: {e}")
        return 2
    try:
        import yaml
        spec = yaml.safe_load(text)
    except ImportError:
        spec = json.loads(text)
    except Exception as e:  # noqa
        print(f"❌ spec parse error: {e}")
        return 2

    try:
        cells, parent, cw, ch = build(spec)
    except (KeyError, TypeError) as e:
        print(f"❌ spec is missing a required field: {e}")
        return 2

    xml = to_xml(cells, parent, cw, ch, spec.get("title", "Architecture"))
    with open(out, "w", encoding="utf-8") as f:
        f.write(xml)
    print(f"✅ wrote {out}  ({cw}x{ch}, {len(cells)} cells). "
          f"Now gate: validate_drawio.py {out} && lint_layout.py {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
