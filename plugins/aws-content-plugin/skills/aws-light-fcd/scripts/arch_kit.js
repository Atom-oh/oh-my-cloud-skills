// ════════════════════════════════════════════════════════════════
// arch_kit.js — AWS architecture-diagram primitives for the AWS Light deck
// require alongside deck_kit.js:
//   const kit = require("./deck_kit.js");
//   const arch = require("./arch_kit.js");
//   const s = arch.archSlide(kit, pres, { title, pageNum });
//   arch.groupBox(kit, pres, s, x,y,w,h, "스토리지");
//   arch.svc(kit, pres, s, cx, y, "ecr", "Amazon ECR");
//   arch.stepMarker(kit, pres, s, x, y, 1);
//   arch.arrow(kit, pres, s, x, y, w);
//   arch.stepLegend(kit, pres, s, ["...","..."]);
// All coords in inches on a 13.333 x 7.5 canvas.
// ════════════════════════════════════════════════════════════════
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const fs = require("fs");

// Render a react-icons component to a base64 PNG (for agenda tiles etc.)
//   const data = await renderFiIcon(require("react-icons/fi").FiZap, "#3B82F6");
async function renderIcon(IconComponent, hexColor, size = 256) {
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
  if (label) s.addText(label, { x, y: y - 0.04, w, h: 0.5, fontFace: kit.FONT, fontSize: 12, bold: true, color: kit.C.body, align: "center", valign: "top" });
}

// AWS service icon (centered on cx) + caption below.
// `iconName` may be a curated bundled name ("ecr", "eks", "s3") OR any key from the
// shared library ("Amazon-EKS", "AWS-Lambda"); the curated PNG wins when present,
// otherwise it resolves from the shared reactive-presentation icon set.
function svc(kit, pres, s, cx, y, iconName, label, iconSz = 0.62) {
  const curated = kit.awsIcon(iconName);
  const iconPath = fs.existsSync(curated) ? curated : kit.icon(iconName);
  s.addImage({ path: iconPath, x: cx - iconSz / 2, y, w: iconSz, h: iconSz });
  s.addText(label, { x: cx - 0.9, y: y + iconSz + 0.04, w: 1.8, h: 0.5, fontFace: kit.FONT, fontSize: 10.5, color: kit.C.body, align: "center", valign: "top", lineSpacingMultiple: 1.0 });
}

// horizontal arrow
function arrow(kit, pres, s, x, y, w) {
  s.addShape(pres.shapes.LINE, { x, y, w, h: 0, line: { color: kit.C.muted, width: 1.5, endArrowType: "triangle" } });
}

// far-right numbered step legend
function stepLegend(kit, pres, s, steps, lx = 11.45, lyTop = 1.55, lrow = 0.6) {
  steps.forEach((t, i) => {
    stepMarker(kit, pres, s, lx, lyTop + i * lrow, i + 1, 0.28);
    s.addText(t, { x: lx + 0.38, y: lyTop + i * lrow - 0.04, w: 1.55, h: 0.36, fontFace: kit.FONT, fontSize: 10.5, color: kit.C.body, align: "left", valign: "middle", margin: 0 });
  });
}

// create an architecture slide shell (title + footer)
function archSlide(kit, pres, opts) {
  const s = pres.addSlide();
  kit.applyBg(s, opts.bg || "plain");
  kit.addHeader(pres, s, opts.title, opts.subtitle);
  // footer added by caller after content, OR here if pageNum given
  s._archPage = opts.pageNum;
  return s;
}

module.exports = { renderIcon, stepMarker, groupBox, svc, arrow, stepLegend, archSlide };
