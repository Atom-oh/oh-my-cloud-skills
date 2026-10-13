#!/usr/bin/env python3
"""Generate a hand-drawn (sketch) **.excalidraw** diagram from a YAML/JSON spec.

Writes a LOCAL ``.excalidraw`` file (no server) that opens directly in Excalidraw
(excalidraw.com, the VSCode Excalidraw extension, or Obsidian). The whiteboard /
hand-drawn aesthetic is Excalidraw's native strength — use this when you want a
sketch-style overview rather than the PPT-grade drawio output (layout_aws.py).

AWS icons (incl. **AgentCore** and any official service) come from the SHARED icon
library in the reactive-presentation skill and are embedded as image elements, so
the file is self-contained. Excalidraw has no built-in AWS shapes, so every icon is
an embedded image (standard ``data:<mime>;base64,`` dataURL in the ``files`` map).

Spec (stages pattern — left-to-right pipeline of labelled groups):

    title: "Inference Platform"
    region: { label: "us-east-1" }          # optional outer label
    stages:
      - name: "Edge"
        services: [{id: cf, icon: cloudfront, label: "CloudFront"}]
      - name: "Agent"
        services:
          - {id: ac, icon: agentcore, label: "AgentCore"}
          - {id: fn, icon: lambda,    label: "Tools"}

`icon:` accepts the same vocabulary as layout_aws.py: common short names
(ec2/lambda/s3/...), `agentcore` (+ component variants), or `arch:<Service-Name>`.

    python3 excalidraw_gen.py spec.yaml -o out.excalidraw
    python3 excalidraw_gen.py spec.yaml            # writes <spec>.excalidraw

Deterministic output (fixed seeds/timestamps) — re-running the same spec is idempotent.
"""
import sys
import os
import json
import base64
import glob
import hashlib

# Reuse the shared-icon resolver (canonical lib + agentcore/arch: handling).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from layout_aws import _SHARED_ICONS, _SERVICE_SET, _resolve_embed  # noqa: E402

# ---- common short name -> official Service-icon base name (Excalidraw has no
# built-in AWS shapes, so even standard services resolve to an embedded image). ----
SERVICE_NAME = {
    "ec2": "Amazon-EC2", "lambda": "AWS-Lambda", "ecs": "Amazon-Elastic-Container-Service",
    "eks": "Amazon-Elastic-Kubernetes-Service", "fargate": "AWS-Fargate",
    "s3": "Amazon-Simple-Storage-Service", "rds": "Amazon-RDS", "aurora": "Amazon-Aurora",
    "dynamodb": "Amazon-DynamoDB", "elasticache": "Amazon-ElastiCache",
    "cloudfront": "Amazon-CloudFront", "route53": "Amazon-Route-53",
    "apigateway": "Amazon-API-Gateway", "alb": "Elastic-Load-Balancing",
    "elb": "Elastic-Load-Balancing", "vpc": "Amazon-Virtual-Private-Cloud",
    "sqs": "Amazon-Simple-Queue-Service", "sns": "Amazon-Simple-Notification-Service",
    "eventbridge": "Amazon-EventBridge", "secrets": "AWS-Secrets-Manager",
    "cloudwatch": "Amazon-CloudWatch", "waf": "AWS-WAF", "bedrock": "Amazon-Bedrock",
    "sagemaker": "Amazon-SageMaker", "kinesis": "Amazon-Kinesis-Data-Streams",
    "stepfunctions": "AWS-Step-Functions", "iam": "AWS-Identity-and-Access-Management",
    "kms": "AWS-Key-Management-Service",
}

# ---- canonical metrics (sketch layout) ----
ICON = 56
LABEL_H = 22
SVC_GAP = 28
STAGE_PAD = 22
STAGE_LABEL_H = 30
STAGE_GAP = 76        # room for the arrow between stages
TITLE_H = 52
MARGIN = 48
STAGE_MIN_W = 168

# Excalidraw default sticky palette — cycled per stage for a whiteboard feel.
STAGE_FILLS = ["#fff9db", "#ebfbee", "#e7f5ff", "#fff0f6", "#f3f0ff", "#fff4e6"]
STAGE_STROKES = ["#f08c00", "#2f9e44", "#1971c2", "#e64980", "#7048e8", "#e8590c"]
INK = "#1e1e1e"


def _resolve_service_icon(short):
    """Map any icon short name to a shared-library file path (relative to
    _SHARED_ICONS), or None. Order: agentcore/arch: (layout_aws) → common service map."""
    rel = _resolve_embed(short)
    if rel:
        return rel
    name = SERVICE_NAME.get(short)
    if name:
        hits = glob.glob(os.path.join(
            _SHARED_ICONS, _SERVICE_SET, "*", "48", f"Arch_{name}_48.svg"))
        if hits:
            return os.path.relpath(hits[0], _SHARED_ICONS)
    # last resort: treat the short name itself as an official Service base name
    hits = glob.glob(os.path.join(
        _SHARED_ICONS, _SERVICE_SET, "*", "48", f"Arch_{short}_48.svg"))
    return os.path.relpath(hits[0], _SHARED_ICONS) if hits else None


def _data_url(rel_path):
    """Standard data URL (``data:<mime>;base64,<b64>``) for an Excalidraw files entry."""
    full = os.path.join(_SHARED_ICONS, rel_path)
    with open(full, "rb") as fh:
        raw = fh.read()
    ext = os.path.splitext(full)[1].lower()
    mime = {".svg": "image/svg+xml", ".png": "image/png",
            ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}.get(ext, "image/png")
    return mime, "data:%s;base64,%s" % (mime, base64.b64encode(raw).decode("ascii"))


class Builder:
    """Accumulates Excalidraw elements + the files map with deterministic ids."""

    def __init__(self):
        self.elements = []
        self.files = {}
        self._n = 0

    def _next(self):
        self._n += 1
        return self._n

    def _base(self, type_, x, y, w, h, **extra):
        n = self._next()
        el = {
            "id": "el%d" % n, "type": type_,
            "x": round(x, 2), "y": round(y, 2), "width": round(w, 2), "height": round(h, 2),
            "angle": 0, "strokeColor": INK, "backgroundColor": "transparent",
            "fillStyle": "hachure", "strokeWidth": 1.5, "strokeStyle": "solid",
            "roughness": 1, "opacity": 100, "groupIds": [], "frameId": None,
            "roundness": None, "seed": 1000 + n * 7, "version": 1,
            "versionNonce": 2000 + n * 13, "isDeleted": False, "boundElements": None,
            "updated": 1, "link": None, "locked": False,
        }
        el.update(extra)
        self.elements.append(el)
        return el

    def rect(self, x, y, w, h, stroke, fill, group=None):
        return self._base("rectangle", x, y, w, h, strokeColor=stroke,
                          backgroundColor=fill, fillStyle="hachure", strokeWidth=2,
                          roundness={"type": 3}, groupIds=([group] if group else []))

    def text(self, x, y, w, s, size=16, align="center", color=INK, group=None):
        return self._base("text", x, y, w, size * 1.25, text=s, fontSize=size,
                          fontFamily=1, textAlign=align, verticalAlign="top",
                          strokeColor=color, containerId=None, originalText=s,
                          lineHeight=1.25, groupIds=([group] if group else []))

    def image(self, x, y, w, h, rel_path, group=None):
        fid = "icon_" + hashlib.md5(rel_path.encode()).hexdigest()[:16]
        if fid not in self.files:
            mime, url = _data_url(rel_path)
            self.files[fid] = {"mimeType": mime, "id": fid, "dataURL": url,
                               "created": 1, "lastRetrieved": 1}
        return self._base("image", x, y, w, h, fileId=fid, status="saved",
                          scale=[1, 1], groupIds=([group] if group else []))

    def arrow(self, x1, y1, x2, y2):
        w, h = x2 - x1, y2 - y1
        return self._base("arrow", x1, y1, w, h, points=[[0, 0], [round(w, 2), round(h, 2)]],
                          strokeWidth=2, lastCommittedPoint=None, startBinding=None,
                          endBinding=None, startArrowhead=None, endArrowhead="arrow")

    def dump(self, source="excalidraw_gen.py"):
        return {"type": "excalidraw", "version": 2, "source": source,
                "elements": self.elements, "files": self.files,
                "appState": {"viewBackgroundColor": "#ffffff", "gridSize": None}}


def _svc_block_h(services):
    n = max(1, len(services))
    return n * (ICON + LABEL_H) + (n - 1) * SVC_GAP


def build(spec):
    stages = spec.get("stages") or (spec.get("region") or {}).get("stages") or []
    if not stages:
        raise ValueError("spec needs `stages:` (a left-to-right list of {name, services})")
    b = Builder()
    title = spec.get("title")
    region_label = (spec.get("region") or {}).get("label")

    top = MARGIN
    if title:
        b.text(MARGIN, top, 600, title, size=28, align="left")
        top += TITLE_H
    if region_label:
        b.text(MARGIN, top, 600, region_label, size=16, align="left", color="#1971c2")
        top += 30

    stage_h = STAGE_LABEL_H + max(_svc_block_h(s.get("services", [])) for s in stages) + 2 * STAGE_PAD
    x = MARGIN
    centers = []  # (right_x, left_x, mid_y) per stage for arrows
    for i, st in enumerate(stages):
        svcs = st.get("services", [])
        stage_w = max(STAGE_MIN_W, ICON + 2 * STAGE_PAD + 40)
        gid = "stage%d" % i
        stroke = STAGE_STROKES[i % len(STAGE_STROKES)]
        b.rect(x, top, stage_w, stage_h, stroke, STAGE_FILLS[i % len(STAGE_FILLS)], group=gid)
        b.text(x, top + 8, stage_w, st.get("name", ""), size=15, color=stroke, group=gid)
        # services: vertically centered block under the stage label
        block_h = _svc_block_h(svcs)
        sy = top + STAGE_LABEL_H + (stage_h - STAGE_LABEL_H - block_h) / 2
        icx = x + (stage_w - ICON) / 2
        for sv in svcs:
            sgid = "svc_%s_%d" % (sv.get("id", "x"), b._n)
            rel = _resolve_service_icon(sv.get("icon", ""))
            if rel:
                b.image(icx, sy, ICON, ICON, rel, group=sgid)
            else:  # icon missing → sketchy placeholder box so it never breaks
                b.rect(icx, sy, ICON, ICON, INK, "transparent", group=sgid)
            b.text(x + STAGE_PAD, sy + ICON + 4, stage_w - 2 * STAGE_PAD,
                   sv.get("label", sv.get("id", "")), size=13, group=sgid)
            sy += ICON + LABEL_H + SVC_GAP
        centers.append((x + stage_w, x, top + stage_h / 2))
        x += stage_w + STAGE_GAP

    for i in range(len(centers) - 1):
        rx, _, my = centers[i]
        _, lx, _ = centers[i + 1]
        b.arrow(rx + 12, my, lx - 12, my)
    return b.dump()


def main():
    args = [a for a in sys.argv[1:]]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    spec_path = args[0]
    out = None
    if "-o" in args:
        out = args[args.index("-o") + 1]
    out = out or (os.path.splitext(spec_path)[0] + ".excalidraw")
    with open(spec_path, "r", encoding="utf-8") as fh:
        text = fh.read()
    if spec_path.endswith((".yaml", ".yml")):
        import yaml
        spec = yaml.safe_load(text)
    else:
        spec = json.loads(text)
    doc = build(spec)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=2)
    print("✅ wrote %s  (%d elements, %d embedded icons). Open in Excalidraw / VSCode Excalidraw."
          % (out, len(doc["elements"]), len(doc["files"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
