// ════════════════════════════════════════════════════════════════
// arch_kit.js — AWS architecture-diagram primitives for the AWS Light deck
// require alongside deck_kit.js:
//   const kit = require("./deck_kit.js");
//   const arch = require("./arch_kit.js");
//
// PREFERRED — declarative auto-layout (no coordinates from the caller):
//   arch.archFlow(kit, pres, { title, pageNum, columns: [...], arrows: "auto" });
//
// Primitives — for the topologies archFlow's column model doesn't fit
// (Transit Gateway mesh, non-linear flows). Manual coordinate placement is the
// exception path, not the default — an LLM hand-placing pixel coordinates is the
// #1 cause of amateur-looking output (see the architecture-diagram skill's
// design-tokens.md, which archFlow's constants below are aligned with):
//   const s = arch.archSlide(kit, pres, { title, pageNum });
//   arch.groupBox(kit, pres, s, x,y,w,h, "스토리지");
//   arch.svc(kit, pres, s, cx, y, "ecr", "Amazon ECR");
//   arch.stepMarker(kit, pres, s, x, y, 1);
//   arch.arrow(kit, pres, s, x, y, w);
//   arch.stepLegend(kit, pres, s, ["...","..."]);
// All coords in inches on a 13.333 x 7.5 canvas.
// ════════════════════════════════════════════════════════════════
const fs = require("fs");
const path = require("path");

// Render a react-icons component to a base64 PNG (for agenda tiles etc.)
//   const data = await renderFiIcon(require("react-icons/fi").FiZap, "#3B82F6");
// react/react-dom/sharp are lazy-required here (not at module load) so the rest of the
// kit — the layout math in archFlow, the primitives — loads and is testable without the
// image-render deps installed.
async function renderIcon(IconComponent, hexColor, size = 256) {
  const React = require("react");
  const ReactDOMServer = require("react-dom/server");
  const sharp = require("sharp");
  const svg = ReactDOMServer.renderToStaticMarkup(
    React.createElement(IconComponent, { color: hexColor, size: String(size) })
  );
  const buf = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + buf.toString("base64");
}

// step marker: accent circle + white number (the AWS diagram motif)
function stepMarker(kit, pres, s, x, y, n, d = 0.34) {
  s.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: kit.C.magenta }, line: { type: "none" } });
  s.addText(String(n), { x, y, w: d, h: d, fontFace: kit.FONT, fontSize: d > 0.3 ? 12 : 10, bold: true, color: "FFFFFF", align: "center", valign: "middle", margin: 0 });
}

// dashed group container with centered top label
function groupBox(kit, pres, s, x, y, w, h, label) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.08, fill: { type: "none" }, line: { color: kit.C.hairline, width: 1, dashType: "dash" } });
  if (label) s.addText(label, { x, y: y - 0.04, w, h: 0.6, fontFace: kit.FONT, fontSize: 12, bold: true, color: kit.C.body, align: "center", valign: "top" });
}

// Curated bundled icon names (assets/icons/aws/*.png) — used to build "did you mean"
// suggestions when a typo'd name falls through to the shared library and misses there too.
function _curatedNames(kit) {
  const dir = path.join(kit.ASSETS, "icons", "aws");
  try { return fs.readdirSync(dir).filter(f => f.endsWith(".png")).map(f => f.slice(0, -4)); }
  catch { return []; }
}

// AWS service icon (centered on cx) + caption below.
// `iconName` may be a curated bundled name ("ecr", "eks", "s3") OR any key from the
// shared library ("Amazon-EKS", "AWS-Lambda"); the curated PNG wins when present,
// otherwise it resolves from the shared reactive-presentation icon set. A typo'd name
// that matches neither throws with near-match suggestions instead of a bare crash.
// `capW` caps the caption text-box width so it never bleeds past a narrow column;
// defaults to 1.8" (roomy) but archFlow passes its computed slotW for tight layouts.
function svc(kit, pres, s, cx, y, iconName, label, iconSz = 0.62, capW = 1.8) {
  if (typeof iconName !== "string" || !iconName) {
    throw new Error(`arch.svc: item needs an 'icon' name (or use {chip: "..."} for endpoints) — got ${JSON.stringify(iconName)} for label '${label}'.`);
  }
  const curated = kit.awsIcon(iconName);
  let iconPath;
  if (fs.existsSync(curated)) {
    iconPath = curated;
  } else {
    try {
      iconPath = kit.icon(iconName);
    } catch (e) {
      const names = _curatedNames(kit);
      const needle = iconName.toLowerCase().replace(/[^a-z0-9]/g, "");
      const near = names.filter(n => n.toLowerCase().replace(/[^a-z0-9]/g, "").includes(needle) ||
        needle.includes(n.toLowerCase().replace(/[^a-z0-9]/g, "")));
      const hint = near.length ? ` Did you mean: ${near.join(", ")}?` : "";
      throw new Error(`arch.svc: unknown icon '${iconName}' (checked curated aws/ set and the ` +
        `shared 811-icon library).${hint} See references/icons.md.`);
    }
  }
  const cw = Math.min(1.8, capW);
  s.addImage({ path: iconPath, x: cx - iconSz / 2, y, w: iconSz, h: iconSz });
  s.addText(label, { x: cx - cw / 2, y: y + iconSz + 0.04, w: cw, h: 0.54, fontFace: kit.FONT, fontSize: 10.5, color: kit.C.body, align: "center", valign: "top", lineSpacingMultiple: 1.0, margin: 0 });
}

// small labeled chip (oval + text) — endpoints (users/agents/programs), never emoji.
// `maxW` caps the total footprint (oval + gap + text) so the label never bleeds into a
// neighboring column or the legend rail; archFlow passes its computed slotW.
function chip(kit, pres, s, x, y, label, d = 0.2, maxW = 1.33) {
  const textW = Math.min(1.05, maxW - d - 0.08);
  s.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: kit.C.blueTint }, line: { color: kit.C.blue, width: 1 } });
  s.addText(label, { x: x + d + 0.08, y: y - (0.34 - d) / 2, w: textW, h: 0.34, fontFace: kit.FONT, fontSize: 11, color: kit.C.body, align: "left", valign: "middle", margin: 0 });
}

// horizontal arrow
function arrow(kit, pres, s, x, y, w) {
  s.addShape(pres.shapes.LINE, { x, y, w, h: 0, line: { color: kit.C.muted, width: 1.5, endArrowType: "triangle" } });
}

// far-right numbered step legend. Text width is clamped to the canvas right edge
// (W - PAD margin would waste the rail; 0.05 keeps it just inside 13.333).
function stepLegend(kit, pres, s, steps, lx = 11.45, lyTop = 1.55, lrow = 0.6) {
  const textW = kit.W - 0.05 - (lx + 0.38);
  steps.forEach((t, i) => {
    stepMarker(kit, pres, s, lx, lyTop + i * lrow, i + 1, 0.28);
    s.addText(t, { x: lx + 0.38, y: lyTop + i * lrow - 0.04, w: textW, h: 0.36, fontFace: kit.FONT, fontSize: 10.5, color: kit.C.body, align: "left", valign: "middle", margin: 0 });
  });
}

// create an architecture slide shell (title + footer)
function archSlide(kit, pres, opts) {
  const s = pres.addSlide();
  kit.applyBg(s, opts.bg || "plain");
  kit.addHeader(pres, s, opts.title, opts.subtitle);
  if (opts.pageNum != null) kit.addFooter(pres, s, opts.pageNum);
  return s;
}

// ════════════════════════════════════════════════════════════════
// archFlow — declarative column-flow architecture diagram (PREFERRED).
// The caller declares WHAT (columns of icons/chips, optional group labels,
// a legend) and archFlow computes WHERE. No coordinates from the caller —
// see the module header for why (design-tokens.md rationale, shared with
// the architecture-diagram skill).
//
//   arch.archFlow(kit, pres, {
//     title, subtitle, pageNum, bg,
//     columns: [
//       { items: [{ icon:"model_registry", label:"모델 레지스트리", step:3 }] },
//       { label:"스토리지", items: [{icon:"efs",label:"Amazon EFS"},{icon:"s3",label:"Amazon S3"}] },
//       { items: [{ chip:"사용자" }, { chip:"에이전트" }] },
//     ],
//     arrows: "auto",              // adjacent columns, left-to-right; or [[0,1],[1,2]]
//     legend: ["1단계 설명", "2단계 설명", ...],   // reserves the right rail, step:N -> legend[N-1]
//   });
//
// Returns { s, cols } — cols[i] = { x, y, w, h, items:[{cx,cy}] } — the computed
// geometry, so callers can drop in extra primitives for the irregular 10% of a
// diagram that doesn't fit the column model (escape hatch, not the common case).
// ════════════════════════════════════════════════════════════════
const ITEM_CELL = 1.2;     // icon (0.62) + gap (0.04) + caption box (0.5) = 1.16, +slack
const CHIP_CELL = 0.45;
const COL_GAP = 0.6;       // horizontal gap between columns (arrow room). Kept modest so
                           // columns stay wide enough for a 2-line group label to fit.
const GROUP_PAD_TOP = 0.62; // room for a 2-line centered group label above the content
const GROUP_PAD = 0.2;

function archFlow(kit, pres, opts) {
  const s = archSlide(kit, pres, { title: opts.title, subtitle: opts.subtitle, bg: opts.bg });
  const columns = opts.columns || [];
  const n = columns.length;
  const hasLegend = !!(opts.legend && opts.legend.length);

  const x0 = kit.PAD;
  const x1 = hasLegend ? 11.2 : kit.W - kit.PAD;
  const y0 = opts.subtitle ? 1.95 : 1.55;
  const y1 = 6.8;
  const slotW = (x1 - x0 - COL_GAP * Math.max(0, n - 1)) / Math.max(1, n);

  const cols = columns.map((col, i) => {
    const cx = x0 + i * (slotW + COL_GAP);
    const items = col.items || [];
    const cellH = items.map(it => (it.chip != null ? CHIP_CELL : ITEM_CELL));
    const stackH = cellH.reduce((a, b) => a + b, 0);
    const grouped = !!col.label;
    // An empty column (items: []) is a reserved slot the caller fills via the returned
    // geometry (e.g. demo's GPU fan-out). It spans the FULL region — collapsing it to
    // h=0 at mid-region put callers' anchored content off-canvas. Non-empty columns
    // size to their stack and center vertically.
    const boxH = items.length ? stackH + (grouped ? GROUP_PAD_TOP + GROUP_PAD : 0) : (y1 - y0);
    const boxY = items.length ? y0 + (y1 - y0 - boxH) / 2 : y0;
    if (grouped) groupBox(kit, pres, s, cx, boxY, slotW, boxH, col.label);

    let itemY = boxY + (grouped ? GROUP_PAD_TOP : 0);
    const placed = items.map((it, k) => {
      const h = cellH[k];
      const icx = cx + slotW / 2;
      const icy = itemY + h / 2;
      if (it.chip != null) {
        // cap the chip footprint at the column's right edge (oval starts at icx-0.5)
        chip(kit, pres, s, icx - 0.5, itemY + (h - CHIP_CELL) / 2, it.chip, 0.2, slotW / 2 + 0.5);
      } else {
        svc(kit, pres, s, icx, itemY, it.icon, it.label, it.iconSz, slotW);
      }
      if (it.step != null) stepMarker(kit, pres, s, icx + 0.14, itemY - 0.1, it.step);
      itemY += h;
      return { cx: icx, cy: icy };
    });
    return { x: cx, y: boxY, w: slotW, h: boxH, items: placed };
  });

  // arrows: "auto" connects adjacent columns at the mean vertical center of both
  // stacks; an explicit [[i,j],...] list connects arbitrary column pairs.
  const pairs = opts.arrows === "auto"
    ? cols.slice(0, -1).map((_, i) => [i, i + 1])
    : (opts.arrows || []);
  pairs.forEach(([i, j]) => {
    if (!cols[i] || !cols[j]) return;
    const midY = ((cols[i].y + cols[i].h / 2) + (cols[j].y + cols[j].h / 2)) / 2;
    const fromX = cols[i].x + cols[i].w + 0.12;
    const toX = cols[j].x - 0.12;
    if (toX > fromX) arrow(kit, pres, s, fromX, midY, toX - fromX);
  });

  if (hasLegend) stepLegend(kit, pres, s, opts.legend);
  if (opts.pageNum != null) kit.addFooter(pres, s, opts.pageNum);
  if (opts.notes) s.addNotes(opts.notes);
  return { s, cols };
}

module.exports = { renderIcon, stepMarker, groupBox, svc, chip, arrow, stepLegend, archSlide, archFlow };
