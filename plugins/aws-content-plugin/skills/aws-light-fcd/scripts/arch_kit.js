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
  const cw = capW;   // caller-supplied width (default 1.8"); archFlow passes its slotW
  s.addImage({ path: iconPath, x: cx - iconSz / 2, y, w: iconSz, h: iconSz });
  s.addText(label, { x: cx - cw / 2, y: y + iconSz + 0.04, w: cw, h: 0.54, fontFace: kit.FONT, fontSize: 10.5, color: kit.C.body, align: "center", valign: "top", lineSpacingMultiple: 1.0, margin: 0 });
}

// small labeled chip (oval + text) — endpoints (users/agents/programs), never emoji.
// `maxW` caps the total footprint (oval + gap + text) so the label never bleeds into a
// neighboring column or the legend rail; archFlow passes its computed slotW.
function chip(kit, pres, s, x, y, label, d = 0.2, maxW = 1.33) {
  const textW = Math.max(0.3, Math.min(1.05, maxW - d - 0.08));
  s.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: kit.C.blueTint }, line: { color: kit.C.blue, width: 1 } });
  s.addText(label, { x: x + d + 0.08, y: y - (0.34 - d) / 2, w: textW, h: 0.34, fontFace: kit.FONT, fontSize: 11, color: kit.C.body, align: "left", valign: "middle", margin: 0 });
}

// horizontal arrow
function arrow(kit, pres, s, x, y, w) {
  s.addShape(pres.shapes.LINE, { x, y, w, h: 0, line: { color: kit.C.muted, width: 1.5, endArrowType: "triangle" } });
}

// far-right numbered step legend. Text width is clamped to the canvas right edge
// (W - PAD margin would waste the rail; 0.05 keeps it just inside 13.333).
// Rows must stay above the footer band (6.8") — same fail-loud contract as the
// column capacity guard: too many rows throws instead of silently bleeding.
function stepLegend(kit, pres, s, steps, lx = 11.45, lyTop = 1.55, lrow = 0.6) {
  const lastBottom = lyTop + (steps.length - 1) * lrow + 0.36;
  if (lastBottom > 6.8) {
    const maxRows = Math.floor((6.8 - 0.36 - lyTop) / lrow) + 1;
    throw new Error(`arch.stepLegend: ${steps.length} rows from y=${lyTop} reach ${lastBottom.toFixed(2)}" ` +
      `(footer band starts at 6.8"). Max ${maxRows} rows at this position — shorten the legend or split the slide.`);
  }
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
const CAPTION_H = 0.54;    // svc caption box height
const ICON_GAP = 0.04;     // gap between icon and caption
const CELL_PAD = 0.04;     // slack below the caption before the next item
const CHIP_CELL = 0.45;
// vertical space one item needs, derived from ITS icon size (a bigger iconSz needs a
// taller cell) — not a flat constant that a large icon would silently overflow.
function itemCellH(it) {
  if (it.chip != null) return CHIP_CELL;
  const iconSz = it.iconSz || 0.62;
  return iconSz + ICON_GAP + CAPTION_H + CELL_PAD;
}
const COL_GAP = 0.6;       // horizontal gap between columns (arrow room). Kept modest so
                           // columns stay wide enough for a 2-line group label to fit.
const GROUP_PAD_TOP = 0.62; // room for a 2-line centered group label above the content
const GROUP_PAD = 0.2;

function archFlow(kit, pres, opts) {
  const s = archSlide(kit, pres, { title: opts.title, subtitle: opts.subtitle, bg: opts.bg });
  const columns = opts.columns || [];
  const n = columns.length;
  const hasLegend = !!(opts.legend && opts.legend.length);

  const declaredSteps = columns.flatMap(c => (c.items || [])
    .map(it => it.step).filter(v => v != null));
  // A step marker with no legend would render an unexplained numbered badge — reject the
  // combination (fail-loud, matching the other archFlow guards).
  if (declaredSteps.length && !hasLegend) {
    throw new Error(`arch.archFlow: ${declaredSteps.length} item(s) set a 'step' but no 'legend' ` +
      `was given — a step marker with no legend row is an unexplained badge. Add a legend or drop the steps.`);
  }
  // Every step must point at a real legend row: integer in 1..legend.length, used at most
  // once. (Not required to COVER the whole legend — callers add markers by hand via
  // arch.stepMarker off the returned geometry, e.g. the demo's GPU/monitoring stages.)
  if (hasLegend) {
    for (const v of declaredSteps) {
      if (!Number.isInteger(v) || v < 1 || v > opts.legend.length) {
        throw new Error(`arch.archFlow: step ${v} is not a valid legend index (legend has ` +
          `${opts.legend.length} entries; steps must be integers in 1..${opts.legend.length}).`);
      }
    }
    if (new Set(declaredSteps).size !== declaredSteps.length) {
      throw new Error(`arch.archFlow: duplicate step number(s) in columns — each step value must be used once.`);
    }
  }

  const x0 = kit.PAD;
  const x1 = hasLegend ? 11.2 : kit.W - kit.PAD;
  const y0 = opts.subtitle ? 1.95 : 1.55;
  const y1 = 6.8;
  const slotW = (x1 - x0 - COL_GAP * Math.max(0, n - 1)) / Math.max(1, n);

  // Fail loudly instead of emitting a broken diagram that only check_pptx catches later.
  const MIN_SLOT = 0.7;
  if (slotW < MIN_SLOT) {
    throw new Error(`arch.archFlow: ${n} columns leave only ${slotW.toFixed(2)}" per column ` +
      `(min ${MIN_SLOT}"). Use fewer columns, split across slides, or drop the legend.`);
  }
  const capacity = y1 - y0;
  columns.forEach((col, i) => {
    const items = col.items || [];
    const stackH = items.reduce((a, it) => a + itemCellH(it), 0);
    const need = stackH + (col.label ? GROUP_PAD_TOP + GROUP_PAD : 0);
    if (items.length && need > capacity) {
      throw new Error(`arch.archFlow: column ${i} needs ${need.toFixed(2)}" for ${items.length} ` +
        `items but only ${capacity.toFixed(2)}" is available. Use fewer items per column ` +
        `or split across slides.`);
    }
  });

  const cols = columns.map((col, i) => {
    const cx = x0 + i * (slotW + COL_GAP);
    const items = col.items || [];
    const cellH = items.map(itemCellH);
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
      let cy = itemY + h / 2;
      let itemCx = icx;
      if (it.chip != null) {
        // anchor the oval inside the column (never left of cx) and let its label fill the
        // rest of the slot width — keeps the whole chip within [cx, cx+slotW].
        const ovalD = 0.2;
        const ovalX = cx + 0.06;
        const ovalY = itemY + (h - ovalD) / 2;
        chip(kit, pres, s, ovalX, ovalY, it.chip, ovalD, slotW - 0.06);
        // the documented contract is "the item's {cx,cy} center" — for a chip that's the
        // oval's visual center, not the slot center (which lands on the label text)
        itemCx = ovalX + ovalD / 2;
        cy = ovalY + ovalD / 2;
      } else {
        svc(kit, pres, s, icx, itemY, it.icon, it.label, it.iconSz, slotW);
      }
      // anchor the step marker at the item's actual visual anchor: icon corner for svc
      // items, the oval for chips (icx would float the badge over the chip's label text)
      if (it.step != null) stepMarker(kit, pres, s, itemCx + 0.14, itemY - 0.1, it.step);
      itemY += h;
      return { cx: itemCx, cy };
    });
    return { x: cx, y: boxY, w: slotW, h: boxH, items: placed };
  });

  // arrows: "auto" connects adjacent columns at the mean vertical center of both
  // stacks; an explicit [[i,j],...] list connects arbitrary column pairs. Bad input
  // throws (fail-loud, matching the step/slot/capacity guards) — a silently dropped
  // arrow is worse than an error because check_pptx can't detect a missing connector.
  let pairs;
  if (opts.arrows === "auto") {
    pairs = cols.slice(0, -1).map((_, i) => [i, i + 1]);
  } else if (opts.arrows == null) {
    pairs = [];
  } else if (Array.isArray(opts.arrows)) {
    pairs = opts.arrows;
  } else {
    throw new Error(`arch.archFlow: 'arrows' must be "auto" or an array of [from,to] pairs — got ${JSON.stringify(opts.arrows)}.`);
  }
  pairs.forEach(([i, j]) => {
    if (!cols[i] || !cols[j]) {
      throw new Error(`arch.archFlow: arrow [${i},${j}] references a column that doesn't exist (${n} columns).`);
    }
    if (j !== i + 1) {
      // a straight horizontal line between non-adjacent columns would cut right through
      // the content of every column in between (and check_pptx doesn't inspect LINE
      // shapes, so nothing downstream would catch it). Reject rather than draw it wrong;
      // route long hops manually via the returned cols[] geometry if truly needed.
      throw new Error(`arch.archFlow: arrow [${i},${j}] spans non-adjacent columns — a straight ` +
        `connector would cross the columns in between. Chain adjacent pairs ([${i},${i + 1}], …) ` +
        `or draw a routed connector by hand using the returned cols[] geometry.`);
    }
    const midY = ((cols[i].y + cols[i].h / 2) + (cols[j].y + cols[j].h / 2)) / 2;
    const fromX = cols[i].x + cols[i].w + 0.12;
    const toX = cols[j].x - 0.12;
    if (toX <= fromX) {
      throw new Error(`arch.archFlow: arrow [${i},${j}] leaves no horizontal gap to draw in.`);
    }
    arrow(kit, pres, s, fromX, midY, toX - fromX);
  });

  if (hasLegend) stepLegend(kit, pres, s, opts.legend, 11.45, y0);  // y0 tracks the subtitle offset
  if (opts.pageNum != null) kit.addFooter(pres, s, opts.pageNum);
  if (opts.notes) s.addNotes(opts.notes);
  return { s, cols };
}

module.exports = { renderIcon, stepMarker, groupBox, svc, chip, arrow, stepLegend, archSlide, archFlow };
