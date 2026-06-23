#!/usr/bin/env python3
"""embed_fonts.py — embed TTF fonts into a .pptx so it renders identically everywhere.

Usage:
    python embed_fonts.py <deck.pptx> [--fonts-dir DIR] [--family NAME]

By default embeds every Regular/Bold TTF found in <skill>/assets/fonts/ for the family
"Pretendard". The deck is modified in place (a .bak copy is kept next to it).

PowerPoint font embedding (OOXML) requires four things inside the pptx zip:
  1. ppt/fonts/fontN.fntdata          — the raw TTF bytes
  2. [Content_Types].xml              — a Default entry for the "fntdata" extension
  3. ppt/_rels/presentation.xml.rels  — a relationship per font part
  4. ppt/presentation.xml             — <p:embeddedFontLst> mapping typeface→part,
                                        and embedTrueTypeFonts="1" on <p:presentation>

This embeds the regular + bold faces of one family (enough for our decks, which only
use bold/non-bold). Extend FACE_MAP if you add italic or more weights.
"""
import sys, os, re, shutil, zipfile, tempfile, argparse, glob

REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
FONT_REL_TYPE = REL_NS + "/font"


def find_faces(fonts_dir):
    """Return {'regular': path, 'bold': path, ...} from TTFs in fonts_dir."""
    faces = {}
    for p in glob.glob(os.path.join(fonts_dir, "*.ttf")):
        name = os.path.basename(p).lower()
        if "bolditalic" in name or ("bold" in name and "italic" in name):
            faces["boldItalic"] = p
        elif "bold" in name:
            faces["bold"] = p
        elif "italic" in name:
            faces["italic"] = p
        elif "regular" in name:
            faces["regular"] = p
    return faces


def embed(pptx_path, fonts_dir, family):
    faces = find_faces(fonts_dir)
    if "regular" not in faces:
        print("ERROR: no Regular TTF found in", fonts_dir)
        return 1
    print("fonts:", {k: os.path.basename(v) for k, v in faces.items()})

    tmp = tempfile.mkdtemp()
    with zipfile.ZipFile(pptx_path) as z:
        z.extractall(tmp)

    # 1) copy font bytes into ppt/fonts/
    fonts_out = os.path.join(tmp, "ppt", "fonts")
    os.makedirs(fonts_out, exist_ok=True)
    # order matters: regular, bold, italic, boldItalic -> font1..fontN
    order = [k for k in ("regular", "bold", "italic", "boldItalic") if k in faces]
    part_for = {}
    for i, key in enumerate(order, start=1):
        part = f"font{i}.fntdata"
        shutil.copy(faces[key], os.path.join(fonts_out, part))
        part_for[key] = part

    # 2) [Content_Types].xml — add Default for fntdata
    ct_path = os.path.join(tmp, "[Content_Types].xml")
    ct = open(ct_path, encoding="utf-8").read()
    if "fntdata" not in ct:
        ins = '<Default Extension="fntdata" ContentType="application/x-fontdata"/>'
        ct = ct.replace("<Default", ins + "<Default", 1)
        open(ct_path, "w", encoding="utf-8").write(ct)

    # 3) ppt/_rels/presentation.xml.rels — one relationship per font part
    rels_path = os.path.join(tmp, "ppt", "_rels", "presentation.xml.rels")
    rels = open(rels_path, encoding="utf-8").read()
    existing_ids = [int(m) for m in re.findall(r'Id="rId(\d+)"', rels)]
    next_id = (max(existing_ids) + 1) if existing_ids else 1
    rid_for = {}
    new_rels = ""
    for key in order:
        rid = f"rId{next_id}"
        rid_for[key] = rid
        new_rels += f'<Relationship Id="{rid}" Type="{FONT_REL_TYPE}" Target="fonts/{part_for[key]}"/>'
        next_id += 1
    rels = rels.replace("</Relationships>", new_rels + "</Relationships>")
    open(rels_path, "w", encoding="utf-8").write(rels)

    # 4) ppt/presentation.xml — embedTrueTypeFonts + <p:embeddedFontLst>
    pres_path = os.path.join(tmp, "ppt", "presentation.xml")
    pres = open(pres_path, encoding="utf-8").read()

    # ensure embedTrueTypeFonts attribute on <p:presentation ...> (don't touch saveSubsetFonts if present)
    if "embedTrueTypeFonts" not in pres:
        pres = re.sub(r"(<p:presentation\b)", r'\1 embedTrueTypeFonts="1"', pres, count=1)
    if "saveSubsetFonts" not in pres:
        pres = re.sub(r"(<p:presentation\b)", r'\1 saveSubsetFonts="0"', pres, count=1)

    # build embeddedFontLst
    tag_for = {"regular": "p:regular", "bold": "p:bold", "italic": "p:italic", "boldItalic": "p:boldItalic"}
    faces_xml = ""
    for key in order:
        faces_xml += f'<{tag_for[key]} r:id="{rid_for[key]}"/>'
    font_block = (
        f'<p:embeddedFontLst><p:embeddedFont>'
        f'<p:font typeface="{family}"/>{faces_xml}'
        f'</p:embeddedFont></p:embeddedFontLst>'
    )

    # embeddedFontLst must sit in schema order: after <p:notesSz>, before <p:custShowLst>/<p:defaultTextStyle>.
    if "<p:embeddedFontLst>" not in pres:
        m = re.search(r"<p:notesSz[^>]*/>", pres)
        if m:
            pres = pres[:m.end()] + font_block + pres[m.end():]
        elif "<p:defaultTextStyle" in pres:
            pres = pres.replace("<p:defaultTextStyle", font_block + "<p:defaultTextStyle", 1)
        else:
            pres = pres.replace("</p:presentation>", font_block + "</p:presentation>", 1)
    open(pres_path, "w", encoding="utf-8").write(pres)

    # repack
    shutil.copy(pptx_path, pptx_path + ".bak")
    if os.path.exists(pptx_path):
        os.remove(pptx_path)
    with zipfile.ZipFile(pptx_path, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(tmp):
            for f in files:
                full = os.path.join(root, f)
                z.write(full, os.path.relpath(full, tmp))
    shutil.rmtree(tmp)
    print(f"embedded {len(order)} face(s) of '{family}' into {pptx_path}")
    print(f"(backup: {pptx_path}.bak)")
    return 0


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    default_fonts = os.path.join(here, "..", "assets", "fonts")
    ap = argparse.ArgumentParser()
    ap.add_argument("pptx")
    ap.add_argument("--fonts-dir", default=default_fonts)
    ap.add_argument("--family", default="Pretendard")
    a = ap.parse_args()
    sys.exit(embed(a.pptx, a.fonts_dir, a.family))
