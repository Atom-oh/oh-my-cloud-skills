#!/usr/bin/env python3
"""Test suite for the spec-driven layout engine + gates.

Runs standalone (no pytest needed):  python3 scripts/test_layout_aws.py
Also pytest-compatible:               pytest scripts/test_layout_aws.py

Covers: every committed exemplar passes both gates (validate clean + lint 100/100),
generation is idempotent (regenerated XML == committed .drawio), the dispatcher picks
the right engine per spec shape, id schemes (AZ-instancing, region prefixes, bare
aliases), grid-snapping, edge anchors, the icon registry, and graceful failure on a
malformed spec.
"""
import os
import sys
import glob

try:                                    # match the rest of the skill's XML hardening
    import defusedxml.ElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET  # self-generated XML only; lint adds an XXE guard

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
EXAMPLES = os.path.join(SKILL, "examples")
sys.path.insert(0, HERE)

import layout_aws        # noqa: E402
import lint_layout       # noqa: E402
import validate_drawio   # noqa: E402

try:
    import yaml
except ImportError:
    yaml = None


def _load(spec_path):
    with open(spec_path, encoding="utf-8") as f:
        return yaml.safe_load(f.read())


def _gen(spec):
    cells, parent, cw, ch = layout_aws.build(spec)
    return layout_aws.to_xml(cells, parent, cw, ch, spec.get("title", "A")), cells


def _vertex_ids(cells):
    return {c.cid for c in cells if c.vertex and not c.edge}


def _edges(cells):
    return [(c.src, c.tgt) for c in cells if c.edge]


# --- per-exemplar gate tests (parametrised manually for standalone runs) ---
EXEMPLAR_SPECS = sorted(glob.glob(os.path.join(EXAMPLES, "*.yaml")))


def test_exemplars_exist():
    assert EXEMPLAR_SPECS, "no example specs found"
    assert yaml is not None, "pyyaml required for tests"


def test_exemplars_pass_validate_gate():
    for sp in EXEMPLAR_SPECS:
        xml, _ = _gen(_load(sp))
        issues = validate_drawio.lint_raw(xml)
        assert not issues, f"{os.path.basename(sp)}: validate found {issues}"


def test_exemplars_lint_100():
    for sp in EXEMPLAR_SPECS:
        xml, _ = _gen(_load(sp))
        r = lint_layout.analyze(xml)
        assert r["score"] == 100, f"{os.path.basename(sp)}: score {r['score']} {r['findings']}"
        assert r["subscores"]["geometry"] == 100 and r["subscores"]["design"] == 100, \
            f"{os.path.basename(sp)}: subscores {r['subscores']}"


def test_generation_idempotent():
    """Regenerating a committed exemplar reproduces it byte-for-byte (no hidden state)."""
    for sp in EXEMPLAR_SPECS:
        committed = os.path.splitext(sp)[0] + ".drawio"
        if not os.path.exists(committed):
            continue
        xml, _ = _gen(_load(sp))
        with open(committed, encoding="utf-8") as f:
            assert xml == f.read(), f"{os.path.basename(sp)}: regenerated XML != committed .drawio"


def test_dispatcher_picks_engine():
    # vpc
    _, cells = _gen(_load(os.path.join(EXAMPLES, "multi-az-3tier.yaml")))
    ids = _vertex_ids(cells)
    assert "vpc" in ids and "az_0" in ids and "az_1" in ids
    # stages
    _, cells = _gen(_load(os.path.join(EXAMPLES, "serverless-api.yaml")))
    ids = _vertex_ids(cells)
    assert "stage_0" in ids and "vpc" not in ids
    # multi-region
    _, cells = _gen(_load(os.path.join(EXAMPLES, "multi-region-dr.yaml")))
    ids = _vertex_ids(cells)
    assert "region_0" in ids and "region_1" in ids
    # hybrid
    _, cells = _gen(_load(os.path.join(EXAMPLES, "hybrid-dx.yaml")))
    ids = _vertex_ids(cells)
    assert "onprem" in ids and "region" in ids


def test_az_instancing_and_alias():
    spec = _load(os.path.join(EXAMPLES, "multi-az-3tier.yaml"))
    _, cells = _gen(spec)
    ids = _vertex_ids(cells)
    assert "alb_0" in ids and "alb_1" in ids, "services must be instanced per AZ"
    # bare id in a flow resolves to AZ-0; the edge must reference alb_0
    srcs_tgts = {x for e in _edges(cells) for x in e}
    assert "alb_0" in srcs_tgts


def test_region_prefix_namespacing():
    spec = _load(os.path.join(EXAMPLES, "multi-region-dr.yaml"))
    _, cells = _gen(spec)
    ids = _vertex_ids(cells)
    assert "r0_alb_0" in ids and "r1_alb_0" in ids, "regions must namespace ids r0_/r1_"
    # cross-region replicate edge must connect r0_rds_0 -> r1_rds_0
    assert any(s == "r0_rds_0" and t == "r1_rds_0" for s, t in _edges(cells)), \
        "cross-region flow did not resolve prefixed ids"


def test_all_coords_on_10px_grid():
    for sp in EXEMPLAR_SPECS:
        xml, _ = _gen(_load(sp))
        root = ET.fromstring(xml)
        for g in root.iter("mxGeometry"):
            for k in ("x", "y"):
                v = g.get(k)
                if v is not None:
                    assert float(v) % 10 == 0, f"{os.path.basename(sp)}: {k}={v} off 10px grid"


def test_anchors_vertical_and_horizontal():
    # same column (vertical): exit bottom / enter top
    a = layout_aws._anchors((0, 0, 78, 78), (0, 300, 78, 78))
    assert "exitX=0.5;exitY=1;" in a and "entryX=0.5;entryY=0;" in a
    # different column to the right (horizontal): exit right / enter left
    a = layout_aws._anchors((0, 0, 78, 78), (400, 0, 78, 78))
    assert "exitX=1;exitY=0.5;" in a and "entryX=0;entryY=0.5;" in a


def test_icon_registry_shape_vs_resourceicon():
    s_users = layout_aws.icon_style("users")
    assert "shape=mxgraph.aws4.users" in s_users and "resIcon=" not in s_users
    s_rds = layout_aws.icon_style("rds")
    assert "resIcon=mxgraph.aws4.rds" in s_rds and "resourceIcon" in s_rds
    # unknown icon falls back to a resourceIcon (never crashes)
    s_unknown = layout_aws.icon_style("totally_made_up")
    assert "resIcon=mxgraph.aws4.totally_made_up" in s_unknown


def test_malformed_spec_raises():
    # a region with neither vpc nor stages -> vpc path -> missing 'vpc' key
    raised = False
    try:
        layout_aws.build({"title": "bad", "region": {"label": "x"}})
    except (KeyError, TypeError):
        raised = True
    assert raised, "malformed spec should raise (caught by main() -> exit 2)"


def test_title_present_when_specified():
    xml, cells = _gen(_load(os.path.join(EXAMPLES, "multi-az-3tier.yaml")))
    assert "title" in _vertex_ids(cells)
    assert "fontSize=18" in xml


# --- standalone runner ---
def _run():
    tests = sorted((n, f) for n, f in globals().items()
                   if n.startswith("test_") and callable(f))
    passed = failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"  ✅ {name}")
            passed += 1
        except Exception as e:  # noqa: BLE001
            print(f"  ❌ {name}: {type(e).__name__}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed ({len(tests)} total)")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(_run())
