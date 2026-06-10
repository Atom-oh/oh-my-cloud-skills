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
def build(spec):
    cells = []
    pos = {}  # id -> (abs_x, abs_y, w, h) for flow anchoring

    azs = spec["region"]["vpc"].get("azs") or ["AZ"]
    tiers = spec["region"]["vpc"]["tiers"]
    n_az = len(azs)

    # --- pass 1: uniform sizing (mirror all AZs) ---
    # subnet width = widest service row across all tiers; subnet height per tier.
    def row_w(services):
        n = max(1, len(services))
        return n * ICON + (n - 1) * ICON_GAP

    subnet_inner_w = max(row_w(t.get("services", [])) for t in tiers)
    subnet_w = subnet_inner_w + 2 * PAD
    tier_h = []
    for t in tiers:
        rows = 1  # v1: single row of services per subnet
        h = LABEL_TOP + rows * ICON + ICON_LABEL + PAD
        tier_h.append(h)

    az_inner_w = subnet_w
    az_content_h = sum(tier_h) + (len(tiers) - 1) * GAP
    az_w = az_inner_w + 2 * PAD
    az_h = LABEL_TOP + az_content_h + PAD

    vpc_inner_w = n_az * az_w + (n_az - 1) * GAP
    vpc_w = vpc_inner_w + 2 * PAD
    vpc_h = LABEL_TOP + az_h + PAD

    region_w = vpc_w + 2 * PAD
    region_h = LABEL_TOP + vpc_h + PAD

    external = spec.get("external", [])
    edge_actors = spec.get("edge", [])

    def col_h(items):
        if not items:
            return 0
        return len(items) * ICON + (len(items) - 1) * (ICON_GAP + ICON_LABEL)

    left_h = max(col_h(external), col_h(edge_actors), region_h)
    content_h = max(region_h, left_h)

    has_title = bool(spec.get("title"))
    title_h = 40 if has_title else 0

    # --- pass 2: absolute placement ---
    x0 = MARGIN                                   # external column
    x1 = x0 + (ICON if external else 0) + (FLOW_GAP if external else 0)   # edge column
    x2 = x1 + (ICON if edge_actors else 0) + (FLOW_GAP if edge_actors else 0)  # region
    top = MARGIN + title_h

    def place_col(items, cx):
        ch = col_h(items)
        cy = top + (content_h - ch) / 2
        step = ICON + ICON_GAP + ICON_LABEL
        for k, it in enumerate(items):
            ax, ay = snap(cx), snap(cy + k * step)
            cells.append(Cell(it["id"], esc(it.get("label", it["id"])),
                              icon_style(it.get("icon", "ec2")),
                              ax, ay, ICON, ICON))
            pos[it["id"]] = (ax, ay, ICON, ICON)

    place_col(external, x0)
    place_col(edge_actors, x1)

    # region container (absolute, parent=1)
    rx, ry = snap(x2), snap(top + (content_h - region_h) / 2)
    cells.append(Cell("region", esc(spec["region"].get("label", "AWS Region")),
                      container_style("group_region", C["region_stroke"], C["region_font"], dashed=1),
                      rx, ry, region_w, region_h))
    # vpc (child of region)
    vx, vy = rx + PAD, ry + LABEL_TOP
    cells.append(Cell("vpc", esc(spec["region"]["vpc"].get("label", "VPC")),
                      container_style("group_vpc", C["vpc_stroke"], C["vpc_font"]),
                      snap(vx - rx), snap(vy - ry), vpc_w, vpc_h, ))
    # mark parents via a parallel list
    parent = {"region": "1", "vpc": "region"}

    for j, az_name in enumerate(azs):
        ax = vx + PAD + j * (az_w + GAP)
        ay = vy + LABEL_TOP
        az_id = f"az_{j}"
        cells.append(Cell(az_id, esc(az_name), az_style(),
                          snap(ax - vx), snap(ay - vy), az_w, az_h))
        parent[az_id] = "vpc"
        # tiers stacked
        ty = ay + LABEL_TOP
        for ti, t in enumerate(tiers):
            kind = t.get("kind", "private")
            if kind == "public":
                gi, st, fi, fo = "group_public_subnet", C["pub_stroke"], C["pub_fill"], C["pub_font"]
            else:
                gi, st, fi, fo = "group_private_subnet", C["prv_stroke"], C["prv_fill"], C["prv_font"]
            sx = ax + PAD
            sub_id = f"subnet_{j}_{ti}"
            cells.append(Cell(sub_id, esc(t.get("name", "Subnet")),
                              container_style(gi, st, fo, fill=fi),
                              snap(sx - ax), snap(ty - ay), subnet_w, tier_h[ti]))
            parent[sub_id] = az_id
            # services row, centered
            services = t.get("services", [])
            rw = row_w(services)
            startx = sx + (subnet_w - rw) / 2
            icy = ty + LABEL_TOP
            for si, svc in enumerate(services):
                icx = startx + si * (ICON + ICON_GAP)
                inst_id = f"{svc['id']}_{j}"
                cells.append(Cell(inst_id, esc(svc.get("label", svc["id"])),
                                  icon_style(svc.get("icon", "ec2")),
                                  snap(icx - sx), snap(icy - ty), ICON, ICON))
                parent[inst_id] = sub_id
                pos[inst_id] = (snap(icx), snap(icy), ICON, ICON)
                if j == 0:
                    pos[svc["id"]] = pos[inst_id]   # bare id -> AZ-0 instance
            ty += tier_h[ti] + GAP

    # title
    canvas_w = x2 + region_w + MARGIN
    canvas_h = top + content_h + MARGIN
    if has_title:
        cells.append(Cell("title", esc(spec["title"]),
                          (f"text;html=1;strokeColor=none;fillColor=none;align=left;"
                           f"verticalAlign=middle;fontSize=18;fontStyle=1;"
                           f"fontColor={C['title']};fontFamily=Amazon Ember;"),
                          MARGIN, MARGIN, 600, 30))
        parent["title"] = "1"

    # flows
    def resolve(ref):
        return ref if ref in pos else (f"{ref}_0" if f"{ref}_0" in pos else ref)

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
