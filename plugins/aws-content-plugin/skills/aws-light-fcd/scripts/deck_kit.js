// ════════════════════════════════════════════════════════════════
// deck_kit.js — AWS Light deck design system (Pretendard)
// Shared tokens + layout builders. require() this from your build script.
//
//   const kit = require("./deck_kit.js");
//   const pres = kit.newDeck();
//   kit.cover(pres, {...});
//   kit.agenda(pres, {...});
//   ...
//   await pres.writeFile({ fileName: "out.pptx" });
//
// Then run scripts/check_pptx.py to QA (score >= 80) and scripts/embed_fonts.py to
// finish. Icons & backgrounds live under assets/.
// ════════════════════════════════════════════════════════════════
const pptxgen = require("pptxgenjs");
const path = require("path");
const fs = require("fs");

const ASSETS = path.join(__dirname, "..", "assets");
const LOGO = path.join(ASSETS, "logo", "aws_logo.png");
const LOGO_WHITE = path.join(ASSETS, "logo", "aws_logo_white.png");
const LOGO_AR = 412 / 247;
const BG_COVER = path.join(ASSETS, "backgrounds", "cover_glow.png");
const BG_GLOW = path.join(ASSETS, "backgrounds", "content_glow.png");
const BG_SECTION = path.join(ASSETS, "backgrounds", "section_grad.png");
const GRAD_PILL = path.join(ASSETS, "backgrounds", "grad_pill.png");

const FONT = "Pretendard";
const W = 13.333, H = 7.5, PAD = 0.92;

// ─── Design tokens (extracted from Amazon Bedrock reference deck) ───
const C = {
  bg: "FFFFFF", card: "F4F4F8", cardSoft: "F7F7FB", hairline: "D2D2D5",
  ink: "161D26", body: "3F4858", muted: "6B7280", faint: "999999",
  gradPurple: "AD5CFF", gradBlue: "41B3FF", gradGreen: "00E500",
  purple: "8B5CF6", blue: "3B82F6", blueBright: "007DFF", magenta: "E91E63", green: "00B341",
  purpleTint: "F2EEFF", blueTint: "EAF2FF", grayTint: "F2F2F4",
};

const COPYRIGHT = "© 2026, Amazon Web Services, Inc. or its affiliates. All rights reserved.";

function newDeck() {
  const pres = new pptxgen();
  pres.defineLayout({ name: "W16x9", width: W, height: H });
  pres.layout = "W16x9";
  pres.author = "AWS Korea";
  return pres;
}

function mkShadow() {
  return { type: "outer", color: "9AA0B0", blur: 10, offset: 3, angle: 90, opacity: 0.18 };
}

// Cap an array to a builder's supported item count, warning instead of silently
// dropping the rest — a builder that just does opts.items.slice(0,6) hides overflow
// from the caller until someone notices a missing item in the rendered deck.
function cap(arr, n, what) {
  if (arr.length > n) {
    console.warn(`[deck_kit] ${what}: got ${arr.length} items, this layout shows only ${n} — split into another slide if the rest matters.`);
  }
  return arr.slice(0, n);
}

// CJK-aware text width estimate, in inches, at font size `fs` (pt). Used to center a
// text run against a fixed-width neighbor (e.g. an icon) without a real text-metrics
// pass. Same per-character factors as check_pptx.py's est_w_pt — keep them in sync if
// either changes (CJK glyphs are ~1em wide; Latin/digits/punctuation ~0.55em).
function estTextW(text, fs) {
  let w = 0;
  for (const ch of text) w += fs * (ch.codePointAt(0) > 0x2E80 ? 1.0 : 0.55);
  return w / 72;
}

const agentcoreIcon = (n) => path.join(ASSETS, "icons", "agentcore", n + ".png");
const awsIcon = (n) => path.join(ASSETS, "icons", "aws", n + ".png");
const toolIcon = (n) => path.join(ASSETS, "icons", "tools", n + ".png");

// ─── Shared AWS icon library (the official 811-icon set used by the sibling
//     reactive-presentation skill — not duplicated here, referenced in place) ───
const RP_ICONS = path.join(__dirname, "..", "..", "reactive-presentation", "icons");
let _rpIndex = null;
function rpIndex() {
  if (_rpIndex) return _rpIndex;
  const f = path.join(RP_ICONS, "index-lite.json");
  if (!fs.existsSync(f)) {
    throw new Error(
      "Shared icon library not found at " + RP_ICONS + ". This skill expects the " +
      "sibling reactive-presentation skill to be installed alongside it. Use the " +
      "bundled curated icons (kit.awsIcon / kit.agentcoreIcon) instead."
    );
  }
  _rpIndex = JSON.parse(fs.readFileSync(f, "utf8")).icons;
  return _rpIndex;
}

// Resolve any icon from the shared library by its index-lite key, e.g.
//   kit.icon("Amazon-EKS")  ·  kit.icon("AWS-Lambda")  ·  kit.icon("Amazon-S3")
// Returns a pptx-safe absolute path: prefers the PNG sibling (PowerPoint renders
// PNG reliably; SVG support is flaky), falling back to the indexed file otherwise.
// Discover names with:  grep -o '"[A-Za-z0-9_-]*":' icons/index-lite.json
function icon(name) {
  const idx = rpIndex();
  const meta = idx[name];
  if (!meta) {
    throw new Error(
      "Unknown icon '" + name + "'. Search names in " +
      path.join(RP_ICONS, "index-lite.json") + " (key = icon name)."
    );
  }
  const abs = path.join(RP_ICONS, meta.path);
  if (abs.toLowerCase().endsWith(".svg")) {
    const png = abs.slice(0, -4) + ".png";
    if (fs.existsSync(png)) return png;
    console.warn("[icon] '" + name + "' has no PNG sibling — returning SVG (" +
      meta.path + "); PowerPoint may not render it. Rasterize with sharp if needed.");
  }
  return abs;
}

// True if `name` exists in the shared library (without throwing).
function hasIcon(name) {
  try { return !!rpIndex()[name]; } catch { return false; }
}

// ─── footer: copyright (left) · small AWS logo + page num (right) ───
//   variant 'dark' (default, for light slides) or 'light' (white text+logo, for gradient slides)
function addFooter(pres, s, pageNum, withLogo = true, variant = "dark") {
  const white = variant === "light";
  const txtColor = white ? "FFFFFF" : C.faint;
  s.addText(COPYRIGHT, {
    x: PAD, y: 7.06, w: 8.2, h: 0.3, fontFace: FONT, fontSize: 8,
    color: txtColor, align: "left", valign: "middle", transparency: white ? 25 : 0,
  });
  if (withLogo) {
    const lh = 0.26, lw = lh * LOGO_AR;
    s.addImage({ path: white ? LOGO_WHITE : LOGO, x: 11.55, y: 6.96, w: lw, h: lh });
  }
  if (pageNum != null) {
    s.addText(String(pageNum), {
      x: 12.5, y: 7.06, w: 0.4, h: 0.3, fontFace: FONT, fontSize: 9,
      color: txtColor, align: "right", valign: "middle", transparency: white ? 25 : 0,
    });
  }
}

// ─── content header: title (+ optional subtitle) ───
function addHeader(pres, s, title, subtitle) {
  s.addText(title, {
    x: PAD - 0.02, y: 0.55, w: 11.4, h: 0.8, fontFace: FONT, fontSize: 30, bold: true,
    color: C.ink, charSpacing: -0.8, align: "left", valign: "top",
  });
  if (subtitle) {
    s.addText(subtitle, {
      x: PAD, y: 1.32, w: 11.4, h: 0.5, fontFace: FONT, fontSize: 14,
      color: C.muted, align: "left", valign: "top",
    });
  }
}

// background helper: 'plain' (white) | 'glow' (subtle top-right glow)
function applyBg(s, mode) {
  if (mode === "glow") s.background = { path: BG_GLOW };
  else s.background = { color: C.bg };
}

// ════════════════════════════════════════════════════════════════
// LAYOUT: COVER
//   opts: { product, subtitle, date, presenter:{name,title,org} }
// ════════════════════════════════════════════════════════════════
function cover(pres, opts) {
  const s = pres.addSlide();
  s.background = { path: BG_COVER };
  s.addText(opts.product, {
    x: PAD - 0.04, y: 2.45, w: 11.5, h: 1.1, fontFace: FONT, fontSize: 54, bold: true,
    color: C.ink, charSpacing: -1, align: "left", valign: "top",
  });
  if (opts.subtitle) {
    s.addText(opts.subtitle, {
      x: PAD, y: 3.62, w: 11, h: 1.0, fontFace: FONT, fontSize: 22, color: C.body,
      lineSpacingMultiple: 1.18, align: "left", valign: "top",
    });
  }
  if (opts.date) {
    s.addText(opts.date, {
      x: PAD, y: 4.95, w: 6, h: 0.4, fontFace: FONT, fontSize: 13, italic: true,
      color: C.muted, align: "left", valign: "middle",
    });
  }
  if (opts.presenter) {
    const p = opts.presenter;
    s.addText([
      { text: p.name || "", options: { bold: true, color: C.ink, fontSize: 15, breakLine: true } },
      { text: p.title || "", options: { color: C.body, fontSize: 13, breakLine: true } },
      { text: p.org || "", options: { color: C.body, fontSize: 13 } },
    ], { x: PAD, y: 5.5, w: 6, h: 1.0, fontFace: FONT, align: "left", valign: "top", lineSpacingMultiple: 1.18 });
  }
  // big logo bottom-right; cover footer has no small logo
  const h = 0.52, w = h * LOGO_AR;
  s.addImage({ path: LOGO, x: W - PAD - w, y: H - 0.95, w, h });
  addFooter(pres, s, null, false);
  if (opts.notes) s.addNotes(opts.notes);
  return s;
}

// ════════════════════════════════════════════════════════════════
// LAYOUT: AGENDA  (content chapters only — NO "next steps / PoC / thanks")
//   opts: { title='Agenda', items:[{num,title,desc,icon}], pageNum, iconPng(fn) }
//   icon is an already-rendered base64 PNG (use renderFiIcon) or an aws/agentcore path
// ════════════════════════════════════════════════════════════════
function agenda(pres, opts) {
  const s = pres.addSlide();
  applyBg(s, "plain");
  s.addText(opts.title || "Agenda", {
    x: PAD - 0.02, y: 0.62, w: 11, h: 0.85, fontFace: FONT, fontSize: 38, bold: true,
    color: C.ink, charSpacing: -1, align: "left", valign: "top",
  });
  const items = cap(opts.items, 6, "agenda"); // 2-col, up to 6
  const colX = [PAD, 7.05];
  const colW = 5.3;
  const rows = Math.ceil(items.length / 2);
  const yTop = rows <= 2 ? 2.55 : 2.15;
  const rowH = rows <= 2 ? 1.5 : 1.25;

  items.forEach((it, i) => {
    const col = i % 2, row = Math.floor(i / 2);
    const x = colX[col], y = yTop + row * rowH;
    // icon tile
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x, y: y - 0.04, w: 0.66, h: 0.66, rectRadius: 0.12, fill: { color: C.blueTint }, line: { type: "none" },
    });
    if (it.iconData) s.addImage({ data: it.iconData, x: x + 0.16, y: y + 0.12, w: 0.34, h: 0.34 });
    else if (it.iconPath) s.addImage({ path: it.iconPath, x: x + 0.14, y: y + 0.1, w: 0.38, h: 0.38 });
    s.addText(it.num, { x: x + 0.86, y: y - 0.06, w: colW - 0.86, h: 0.3, fontFace: FONT, fontSize: 11, bold: true, color: C.blue, align: "left", valign: "top", margin: 0, charSpacing: 0.5 });
    s.addText(it.title, { x: x + 0.86, y: y + 0.2, w: colW - 0.86, h: 0.4, fontFace: FONT, fontSize: 16, bold: true, color: C.ink, align: "left", valign: "top", margin: 0, charSpacing: -0.3 });
    if (it.desc) s.addText(it.desc, { x: x + 0.86, y: y + 0.62, w: colW - 0.86, h: 0.35, fontFace: FONT, fontSize: 11.5, color: C.muted, align: "left", valign: "top", margin: 0 });
    // hairline under non-bottom rows
    if (row < rows - 1) s.addShape(pres.shapes.LINE, { x, y: y + rowH - 0.16, w: colW, h: 0, line: { color: C.hairline, width: 1 } });
  });
  addFooter(pres, s, opts.pageNum);
  if (opts.notes) s.addNotes(opts.notes);
  return s;
}

// ════════════════════════════════════════════════════════════════
// LAYOUT: AGENTCORE 3-CARD  (gradient pill header + AgentCore icon)
//   opts: { headerIcon='agentcore', headerTitle, subtitle,
//           cards:[{title, icon, desc}], pageNum }
//   card.icon is an agentcore icon name (see references/icons.md)
// ════════════════════════════════════════════════════════════════
function agentcoreCards(pres, opts) {
  const s = pres.addSlide();
  applyBg(s, "plain");
  // centered icon+title group
  const titleText = opts.headerTitle;
  const titleFs = 28;
  const estW = estTextW(titleText, titleFs);
  const iconW = 0.62, iconGap = 0.18;
  const groupW = iconW + iconGap + estW;
  const groupX = (W - groupW) / 2;
  s.addImage({ path: agentcoreIcon(opts.headerIcon || "agentcore"), x: groupX, y: 0.5, w: iconW, h: iconW });
  s.addText(titleText, { x: groupX + iconW + iconGap, y: 0.5, w: estW + 0.6, h: 0.62, fontFace: FONT, fontSize: titleFs, bold: true, color: C.ink, charSpacing: -0.8, align: "left", valign: "middle", margin: 0 });
  if (opts.subtitle) s.addText(opts.subtitle, { x: PAD, y: 1.42, w: 11.5, h: 0.5, fontFace: FONT, fontSize: 14, color: C.muted, align: "center", valign: "top" });

  const cards = cap(opts.cards, 3, "agentcoreCards");
  const cardW = 3.62, gap = 0.42;
  const totalW = cardW * cards.length + gap * (cards.length - 1);
  const startX = (W - totalW) / 2;
  const cardY = 2.45, cardH = 3.35, pillH = 0.72;
  cards.forEach((c, i) => {
    const x = startX + i * (cardW + gap);
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: cardY, w: cardW, h: cardH, rectRadius: 0.14, fill: { color: C.card }, line: { type: "none" }, shadow: mkShadow() });
    s.addImage({ path: GRAD_PILL, x: x + 0.18, y: cardY - 0.28, w: cardW - 0.36, h: pillH });
    s.addText(c.title, { x: x + 0.18, y: cardY - 0.28, w: cardW - 0.36, h: pillH, fontFace: FONT, fontSize: 16, bold: true, color: "FFFFFF", align: "center", valign: "middle", charSpacing: 0.5 });
    s.addImage({ path: agentcoreIcon(c.icon), x: x + cardW / 2 - 0.52, y: cardY + 0.75, w: 1.04, h: 1.04 });
    s.addText(c.desc, { x: x + 0.3, y: cardY + 2.05, w: cardW - 0.6, h: 1.1, fontFace: FONT, fontSize: 14, color: C.body, align: "center", valign: "top", lineSpacingMultiple: 1.25 });
  });
  addFooter(pres, s, opts.pageNum);
  if (opts.notes) s.addNotes(opts.notes);
  return s;
}

// ════════════════════════════════════════════════════════════════
// LAYOUT: BIG STAT  (solid-blue big numbers — NO gradient on text)
//   opts: { title, bg='glow', stats:[{num, lines:[{t,blue?}], source}], pageNum }
// ════════════════════════════════════════════════════════════════
function bigStat(pres, opts) {
  const s = pres.addSlide();
  applyBg(s, opts.bg || "glow");
  addHeader(pres, s, opts.title);
  const stats = cap(opts.stats, 4, "bigStat");
  const n = stats.length;
  const colW = (n <= 2) ? 5.2 : 3.5;
  const gap = (n <= 2) ? 1.6 : 0.4;
  const totalW = colW * n + gap * (n - 1);
  const startX = (W - totalW) / 2;
  const numFs = (n <= 2) ? 96 : 72;
  stats.forEach((st, i) => {
    const x = startX + i * (colW + gap);
    s.addText(st.num, { x, y: 2.25, w: colW, h: 1.5, fontFace: FONT, fontSize: numFs, bold: true, color: C.gradBlue, align: "left", valign: "middle", charSpacing: -2, margin: 0 });
    s.addText(
      st.lines.map((ln, j) => ({ text: ln.t, options: { color: ln.blue ? C.blue : C.body, bold: !!ln.blue, breakLine: j < st.lines.length - 1 } })),
      { x, y: 3.95, w: colW, h: 1.4, fontFace: FONT, fontSize: (n <= 2 ? 18 : 14), align: "left", valign: "top", lineSpacingMultiple: 1.35, margin: 0 }
    );
    if (st.source) s.addText(st.source, { x, y: 5.5, w: colW, h: 0.4, fontFace: FONT, fontSize: 11, color: C.muted, align: "left", valign: "top", margin: 0 });
  });
  addFooter(pres, s, opts.pageNum);
  if (opts.notes) s.addNotes(opts.notes);
  return s;
}

// ════════════════════════════════════════════════════════════════
// LAYOUT: TITLE + VISUAL  (big left emphasis title, right visual region)
//   EKS slide-21 style. The right region is yours to draw into via a
//   callback that receives (pres, s, region) where region = {x,y,w,h}.
//   opts: { title, titleColor=C.blueBright, caption, draw(pres,s,region), pageNum, bg }
// ════════════════════════════════════════════════════════════════
function titleWithVisual(pres, opts) {
  const s = pres.addSlide();
  applyBg(s, opts.bg || "plain");

  // left emphasis title (vertically centered in the left column)
  s.addText(opts.title, {
    x: PAD, y: opts.titleY != null ? opts.titleY : 2.9, w: 4.6, h: 1.7, fontFace: FONT,
    fontSize: opts.titleFs || 32, bold: true, color: opts.titleColor || C.blueBright,
    charSpacing: -0.8, align: "left", valign: "top", lineSpacingMultiple: 1.12,
  });

  // right visual region
  const region = { x: 6.55, y: 1.0, w: 5.85, h: 5.4 };
  if (opts.caption) {
    s.addText(opts.caption, {
      x: region.x, y: region.y, w: region.w, h: 0.4, fontFace: FONT, fontSize: 14, bold: true,
      color: C.ink, align: "center", valign: "middle",
    });
    region.y += 0.55; region.h -= 0.55;
  }
  if (typeof opts.draw === "function") opts.draw(pres, s, region);

  addFooter(pres, s, opts.pageNum);
  if (opts.notes) s.addNotes(opts.notes);
  return s;
}

// ════════════════════════════════════════════════════════════════
// LAYOUT: PIPELINE  (numbered circles + cards + arrows, left→right)
//   opts: { title, subtitle, steps:[{n,title,desc}], pageNum, bg }
// ════════════════════════════════════════════════════════════════
function pipeline(pres, opts) {
  const s = pres.addSlide();
  applyBg(s, opts.bg || "plain");
  addHeader(pres, s, opts.title, opts.subtitle);
  const steps = cap(opts.steps, 4, "pipeline");
  const n = steps.length;
  const cardW = n <= 3 ? 3.3 : 2.7;
  const gap = (W - 2 * PAD - cardW * n) / (n - 1);
  const y = opts.subtitle ? 2.9 : 2.6, cardH = 2.4;
  steps.forEach((st, i) => {
    const x = PAD + i * (cardW + gap);
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: cardW, h: cardH, rectRadius: 0.1, fill: { color: C.card }, line: { type: "none" } });
    s.addShape(pres.shapes.OVAL, { x: x + 0.3, y: y - 0.3, w: 0.66, h: 0.66, fill: { color: C.blueBright }, line: { type: "none" } });
    s.addText(String(st.n), { x: x + 0.3, y: y - 0.3, w: 0.66, h: 0.66, fontFace: FONT, fontSize: 24, bold: true, color: "FFFFFF", align: "center", valign: "middle", margin: 0 });
    s.addText(st.title, { x: x + 0.32, y: y + 0.55, w: cardW - 0.64, h: 0.45, fontFace: FONT, fontSize: 17, bold: true, color: C.ink, align: "left", valign: "top", margin: 0 });
    s.addText(st.desc, { x: x + 0.32, y: y + 1.05, w: cardW - 0.64, h: 1.1, fontFace: FONT, fontSize: 13, color: C.body, align: "left", valign: "top", margin: 0, lineSpacingMultiple: 1.25 });
    if (i < n - 1) s.addShape(pres.shapes.LINE, { x: x + cardW + 0.12, y: y + cardH / 2, w: gap - 0.24, h: 0, line: { color: C.muted, width: 2, endArrowType: "triangle" } });
  });
  addFooter(pres, s, opts.pageNum);
  if (opts.notes) s.addNotes(opts.notes);
  return s;
}

// ════════════════════════════════════════════════════════════════
// LAYOUT: WHY / WHAT  (top WHY panel + arrow + bottom WHAT cards w/ 차별점)
//   opts: { title, subtitle, why:[{dot,t,d}], what:[{n,t,d,diff,dc}], pageNum }
// ════════════════════════════════════════════════════════════════
function whyWhat(pres, opts) {
  const s = pres.addSlide();
  applyBg(s, opts.bg || "plain");
  addHeader(pres, s, opts.title, opts.subtitle);

  const whyY = 2.0, whyH = 1.45;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: PAD, y: whyY, w: W - 2 * PAD, h: whyH, rectRadius: 0.1, fill: { color: C.purpleTint }, line: { type: "none" } });
  s.addText("WHY", { x: PAD + 0.3, y: whyY + 0.16, w: 2, h: 0.35, fontFace: FONT, fontSize: 14, bold: true, color: C.purple, align: "left", valign: "top", charSpacing: 1 });
  const why = cap(opts.why, 3, "whyWhat.why");
  const wcolW = (W - 2 * PAD - 0.6) / 3;
  why.forEach((it, i) => {
    const x = PAD + 0.3 + i * wcolW;
    s.addShape(pres.shapes.OVAL, { x, y: whyY + 0.62, w: 0.16, h: 0.16, fill: { color: it.dot || C.purple }, line: { type: "none" } });
    s.addText(it.t, { x: x + 0.26, y: whyY + 0.55, w: wcolW - 0.4, h: 0.3, fontFace: FONT, fontSize: 13, bold: true, color: C.ink, align: "left", valign: "middle", margin: 0 });
    s.addText(it.d, { x, y: whyY + 0.92, w: wcolW - 0.3, h: 0.5, fontFace: FONT, fontSize: 11, color: C.body, align: "left", valign: "top", margin: 0, lineSpacingMultiple: 1.15 });
  });

  // connector arrow between the two panels
  s.addShape(pres.shapes.DOWN_ARROW, { x: W / 2 - 0.22, y: whyY + whyH + 0.06, w: 0.44, h: 0.32, fill: { color: C.purple }, line: { type: "none" } });

  // WHAT panel (mirrors WHY: label inside a tinted panel that wraps the cards)
  const whatPanelY = whyY + whyH + 0.5;
  const whatLabelH = 0.55;
  const cardTop = whatPanelY + whatLabelH;
  const whatH = 1.95;
  const whatPanelH = whatLabelH + whatH + 0.22;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: PAD, y: whatPanelY, w: W - 2 * PAD, h: whatPanelH, rectRadius: 0.1, fill: { color: C.grayTint }, line: { type: "none" } });
  s.addText("WHAT", { x: PAD + 0.3, y: whatPanelY + 0.16, w: 2, h: 0.35, fontFace: FONT, fontSize: 14, bold: true, color: C.purple, align: "left", valign: "top", charSpacing: 1 });

  const what = cap(opts.what, 3, "whyWhat.what");
  const ccolW = (W - 2 * PAD - 0.6 - 0.4) / 3;
  what.forEach((c, i) => {
    const x = PAD + 0.2 + i * (ccolW + 0.3);
    const dc = c.dc || C.blue;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: cardTop, w: ccolW, h: whatH, rectRadius: 0.08, fill: { color: C.bg }, line: { color: C.hairline, width: 0.75 } });
    s.addText([{ text: c.n + "  ", options: { bold: true, color: dc } }, { text: c.t, options: { bold: true, color: C.ink } }],
      { x: x + 0.22, y: cardTop + 0.15, w: ccolW - 0.44, h: 0.32, fontFace: FONT, fontSize: 14, align: "left", valign: "middle", margin: 0 });
    s.addText(c.d, { x: x + 0.22, y: cardTop + 0.52, w: ccolW - 0.44, h: 0.55, fontFace: FONT, fontSize: 11, color: C.body, align: "left", valign: "top", margin: 0, lineSpacingMultiple: 1.15 });
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: x + 0.18, y: cardTop + 1.2, w: ccolW - 0.36, h: 0.6, rectRadius: 0.05, fill: { type: "none" }, line: { color: dc, width: 0.75 } });
    s.addText([{ text: "차별점  ", options: { bold: true, color: dc } }, { text: c.diff, options: { color: C.body } }],
      { x: x + 0.32, y: cardTop + 1.2, w: ccolW - 0.6, h: 0.6, fontFace: FONT, fontSize: 11.5, align: "left", valign: "middle", margin: 0, lineSpacingMultiple: 1.15 });
  });
  addFooter(pres, s, opts.pageNum);
  if (opts.notes) s.addNotes(opts.notes);
  return s;
}

// ════════════════════════════════════════════════════════════════
// LAYOUT: CHART WITH CALLOUT  (native editable bar/line chart + side callout)
//   opts: { title, subtitle, chartType='bar', series:[{name,labels,values}],
//           callout:{big, lines:[{t,blue?}]}, maxVal, pageNum }
// ════════════════════════════════════════════════════════════════
function chartWithCallout(pres, opts) {
  const s = pres.addSlide();
  applyBg(s, opts.bg || "plain");
  addHeader(pres, s, opts.title, opts.subtitle);
  const chartTypeMap = { bar: pres.charts.BAR, line: pres.charts.LINE };
  s.addChart(chartTypeMap[opts.chartType || "bar"], opts.series, {
    x: PAD, y: 2.1, w: 7.6, h: 4.3, barDir: "col",
    chartColors: opts.chartColors || [C.gradBlue, C.purple, C.green, C.magenta],
    chartArea: { fill: { color: "FFFFFF" } },
    catAxisLabelColor: C.muted, valAxisLabelColor: C.muted,
    catAxisLabelFontFace: FONT, valAxisLabelFontFace: FONT, catAxisLabelFontSize: 11, valAxisLabelFontSize: 10,
    valGridLine: { color: "EEF0F3", size: 0.5 }, catGridLine: { style: "none" },
    showValue: opts.showValue !== false, dataLabelPosition: "outEnd", dataLabelColor: C.ink, dataLabelFontFace: FONT, dataLabelFontSize: 11, dataLabelFontBold: true,
    showLegend: !!opts.showLegend, legendPos: "b", legendColor: C.muted, legendFontFace: FONT,
    showTitle: false,
    valAxisMaxVal: opts.maxVal, valAxisMinVal: 0,
  });
  if (opts.callout) {
    const cx = 9.0, cw = 3.4;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: cx, y: 2.5, w: cw, h: 2.6, rectRadius: 0.1, fill: { color: C.blueTint }, line: { type: "none" } });
    s.addText(opts.callout.big, { x: cx + 0.3, y: 2.75, w: cw - 0.6, h: 1.0, fontFace: FONT, fontSize: 54, bold: true, color: C.blueBright, align: "left", valign: "middle", charSpacing: -1, margin: 0 });
    s.addText(
      opts.callout.lines.map((ln, j) => ({ text: ln.t, options: { color: ln.blue ? C.blue : C.body, bold: !!ln.blue } })),
      { x: cx + 0.3, y: 3.85, w: cw - 0.6, h: 1.1, fontFace: FONT, fontSize: 14, align: "left", valign: "top", margin: 0, lineSpacingMultiple: 1.3 }
    );
  }
  addFooter(pres, s, opts.pageNum);
  if (opts.notes) s.addNotes(opts.notes);
  return s;
}

// ════════════════════════════════════════════════════════════════
// LAYOUT: CHIP GRID  (rows of labeled chips, vendor-colored — EKS-23 style)
//   opts: { title, leftLabel, vendorBoxes:[{name,color,items}],
//           rows:[{label, groups:[{color,chips:[]}], panel?}], pageNum }
// ════════════════════════════════════════════════════════════════
function chipGrid(pres, opts) {
  const s = pres.addSlide();
  applyBg(s, opts.bg || "plain");
  addHeader(pres, s, opts.title);

  if (opts.leftLabel) s.addText(opts.leftLabel, { x: PAD, y: 1.7, w: 3.0, h: 0.6, fontFace: FONT, fontSize: 14, color: C.body, align: "left", valign: "top", lineSpacingMultiple: 1.15 });
  (opts.vendorBoxes || []).forEach((vb, i) => {
    const bx = 4.3 + i * 3.6;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: bx, y: 1.6, w: 3.3, h: 1.0, rectRadius: 0.08, fill: { color: C.card }, line: { type: "none" } });
    s.addText(vb.name, { x: bx, y: 1.72, w: 3.3, h: 0.3, fontFace: FONT, fontSize: 13, bold: true, color: vb.color, align: "center", valign: "top" });
    s.addText(vb.items, { x: bx + 0.1, y: 2.02, w: 3.1, h: 0.5, fontFace: FONT, fontSize: 11, color: C.body, align: "center", valign: "top", lineSpacingMultiple: 1.1 });
  });

  const cw = 0.82, gap = 0.18;
  function chip(x, y, label, color) {
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: cw, h: cw, rectRadius: 0.08, fill: { type: "none" }, line: { color, width: 2 } });
    s.addText(label, { x, y, w: cw, h: cw, fontFace: FONT, fontSize: 13, bold: true, color: C.ink, align: "center", valign: "middle", margin: 0 });
  }
  let rowY = 3.35;
  opts.rows.forEach((row) => {
    if (row.panel) s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: PAD, y: rowY - 0.18, w: W - 2 * PAD, h: 1.25, rectRadius: 0.1, fill: { color: C.grayTint }, line: { type: "none" } });
    s.addText(row.label, { x: PAD + (row.panel ? 0.2 : 0), y: rowY, w: 0.9, h: cw, fontFace: FONT, fontSize: 14, bold: true, color: C.body, align: "left", valign: "middle", margin: 0 });
    let x = 1.7 + (row.panel ? 0.2 : 0);
    row.groups.forEach((g, gi) => {
      if (gi > 0) x += g.gapBefore || 0;
      g.chips.forEach(l => { chip(x, rowY, l, g.color); x += cw + gap; });
    });
    rowY += 1.4;
  });
  addFooter(pres, s, opts.pageNum);
  if (opts.notes) s.addNotes(opts.notes);
  return s;
}

// ════════════════════════════════════════════════════════════════
// LAYOUT: SECTION DIVIDER  (full gradient bg + chapter number + big white title)
//   opts: { num, title, kicker, pageNum }
// ════════════════════════════════════════════════════════════════
function sectionDivider(pres, opts) {
  const s = pres.addSlide();
  s.background = { path: BG_SECTION };
  if (opts.num) {
    s.addText(String(opts.num), {
      x: PAD, y: 1.7, w: 4, h: 1.2, fontFace: FONT, fontSize: 22, bold: true,
      color: "FFFFFF", align: "left", valign: "top", charSpacing: 3, transparency: 35,
    });
  }
  s.addText(opts.title, {
    x: PAD - 0.02, y: 2.95, w: 11, h: 1.4, fontFace: FONT, fontSize: 50, bold: true,
    color: "FFFFFF", charSpacing: -1, align: "left", valign: "top",
  });
  if (opts.kicker) {
    s.addText(opts.kicker, {
      x: PAD, y: 4.25, w: 10.5, h: 0.6, fontFace: FONT, fontSize: 18,
      color: "FFFFFF", align: "left", valign: "top", transparency: 12,
    });
  }
  addFooter(pres, s, opts.pageNum, true, "light");
  if (opts.notes) s.addNotes(opts.notes);
  return s;
}

// ════════════════════════════════════════════════════════════════
// LAYOUT: CLOSING  (full gradient bg + "Thank you." — English by convention)
//   opts: { text="Thank you.", pageNum }
// ════════════════════════════════════════════════════════════════
function closing(pres, opts = {}) {
  const s = pres.addSlide();
  s.background = { path: BG_SECTION };
  s.addText(opts.text || "Thank you.", {
    x: PAD - 0.02, y: 3.0, w: 11, h: 1.3, fontFace: FONT, fontSize: 54, bold: true,
    color: "FFFFFF", charSpacing: -1, align: "left", valign: "middle",
  });
  addFooter(pres, s, opts.pageNum, true, "light");
  if (opts.notes) s.addNotes(opts.notes);
  return s;
}

module.exports = {
  pptxgen, newDeck, FONT, W, H, PAD, C, COPYRIGHT,
  ASSETS, LOGO, LOGO_AR, BG_COVER, BG_GLOW, GRAD_PILL,
  agentcoreIcon, awsIcon, toolIcon, icon, hasIcon, RP_ICONS, mkShadow, cap, estTextW,
  addFooter, addHeader, applyBg,
  cover, agenda, agentcoreCards, bigStat, titleWithVisual,
  pipeline, whyWhat, chartWithCallout, chipGrid,
  sectionDivider, closing,
};
