const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const vm = require("node:vm");
const {test, after} = require("node:test");

const scripts = path.resolve(__dirname,
  "../../plugins/aws-content-plugin/skills/aws-light-fcd/scripts");
// Geometry tests exercise the real builders without installing the optional
// PPTX writer. Only its constructor import is replaced; it is never invoked.
const moduleObject = {exports: {}};
vm.compileFunction(fs.readFileSync(path.join(scripts, "deck_kit.js"), "utf8"),
  ["require", "module", "exports", "__dirname", "__filename"])(
  name => name === "pptxgenjs" ? class {} : require(name),
  moduleObject, moduleObject.exports, scripts, path.join(scripts, "deck_kit.js"));
const kit = moduleObject.exports;
const arch = require(path.join(scripts, "arch_kit.js"));
const temp = fs.mkdtempSync(path.join(os.tmpdir(), "fcd-icon-aspect-"));
after(() => fs.rmSync(temp, {recursive: true, force: true}));

function slide() {
  return {
    images: [],
    addImage(options) { this.images.push({...options}); },
    addText() {},
    addShape() {},
    addNotes() {},
  };
}

function near(actual, expected) {
  assert.ok(Math.abs(actual - expected) < 1e-9,
    `expected ${actual} to be approximately ${expected}`);
}

function cardSlide(headerIcon, icon) {
  const output = slide();
  kit.agentcoreCards({addSlide: () => output, shapes: {}}, {
    headerIcon, headerTitle: "AgentCore", pageNum: 2,
    cards: [{title: "Gateway", icon, desc: "Connect tools"}],
  });
  return output.images.filter(image =>
    image.path.includes(`${path.sep}icons${path.sep}agentcore${path.sep}`));
}

test("AgentCore header retains the bundled Gateway PNG's 392:340 ratio", () => {
  const image = cardSlide("gateway", "memory")[0];
  near(image.w / image.h, 392 / 340);
  near(image.w, 0.62);
  near(image.y + image.h / 2, 0.5 + 0.62 / 2);
});

test("AgentCore cards preserve icon ratio and center inside their existing slot", () => {
  const image = cardSlide("memory", "gateway")[1];
  near(image.w / image.h, 392 / 340);
  near(image.w, 1.04);
  near(image.x + image.w / 2, kit.W / 2);
  near(image.y + image.h / 2, 2.45 + 0.75 + 1.04 / 2);
});

test("square icons retain their original footprint", () => {
  const image = cardSlide("memory", "memory")[1];
  near(image.w, 1.04);
  near(image.h, 1.04);
  near(image.y, 3.2);
});

test("architecture service icons fit a tall SVG without changing the caption", () => {
  const icon = path.join(temp, "tall.svg");
  fs.writeFileSync(icon, "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0, 0, 40, 80'/>");
  const output = slide();
  const captions = [];
  output.addText = (text, options) => captions.push({text, ...options});
  arch.svc({...kit, awsIcon: () => icon}, {}, output, 5, 1, "tall", "Service", 2, 3);
  const image = output.images[0];
  near(image.w, 1);
  near(image.h, 2);
  near(image.x, 4.5);
  near(image.y, 1);
  assert.equal(captions[0].text, "Service");
  near(captions[0].y, 3.04);
  near(captions[0].w, 3);
});

test("SVG pixel dimensions work when there is no viewBox", () => {
  assert.equal(typeof kit.fitBox, "function");
  const icon = path.join(temp, "wide.svg");
  fs.writeFileSync(icon, '<svg width="80px" height="40px"/>');
  const image = kit.fitBox(icon, 1, 2, 4, 4);
  near(image.w, 4);
  near(image.h, 2);
  near(image.x, 1);
  near(image.y, 3);
});

test("a truncated SVG comment cannot supply the image's dimensions", () => {
  const icon = path.join(temp, "comment-window.svg");
  fs.writeFileSync(icon, '<!-- example <svg viewBox="0 0 80 40"/>' +
    " ".repeat(4096) + '--><svg viewBox="0 0 40 80"/>');
  assert.deepEqual(kit.fitBox(icon, 1, 2, 3, 4),
    {path: icon, x: 1, y: 2, w: 3, h: 4});

  fs.writeFileSync(icon, '<?xml version="1.0"?>\n' +
    '<!-- example <svg viewBox="0 0 80 40"/> -->\n<svg viewBox="0 0 40 80"/>');
  const fitted = kit.fitBox(icon, 1, 2, 3, 4);
  near(fitted.w, 2);
  near(fitted.h, 4);
  near(fitted.x, 1.5);
});

test("unrepresentable fitted dimensions fall back instead of emitting infinity", () => {
  const icon = path.join(temp, "tiny.svg");
  fs.writeFileSync(icon, '<svg viewBox="0 0 1e-320 1e-320"/>');
  assert.deepEqual(kit.fitBox(icon, 1, 2, 3, 4),
    {path: icon, x: 1, y: 2, w: 3, h: 4});
});

test("unreadable, truncated and invalid dimensions preserve the caller's box", () => {
  assert.equal(typeof kit.fitBox, "function");
  const missing = path.join(temp, "missing.png");
  const truncated = path.join(temp, "truncated.png");
  const invalid = path.join(temp, "invalid.svg");
  const relative = path.join(temp, "relative.svg");
  fs.writeFileSync(truncated, "not a PNG");
  fs.writeFileSync(invalid, '<svg viewBox="0 0 0 -10"/>');
  fs.writeFileSync(relative, '<svg width="100%" height="50%"/>');
  for (const icon of [missing, truncated, invalid, relative]) {
    assert.deepEqual(kit.fitBox(icon, 1, 2, 3, 4),
      {path: icon, x: 1, y: 2, w: 3, h: 4});
  }
});
