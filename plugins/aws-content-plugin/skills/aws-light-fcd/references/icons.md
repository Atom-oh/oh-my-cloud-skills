# Icon Catalog

Icons come from two tiers:

1. **Curated bundled set** (in this skill's `assets/icons/`) — a small, hand-picked,
   pre-validated set for the most common diagram needs. Helpers `kit.agentcoreIcon(name)`,
   `kit.awsIcon(name)`, `kit.toolIcon(name)` return the path (filename without `.png`).
2. **Shared official library** (811 icons) — the full AWS Architecture Icons set, the
   *same* library the sibling `reactive-presentation` skill ships, referenced in place
   (not duplicated). Helper `kit.icon(name)` resolves it. **Use this whenever the curated
   set doesn't have the service you need** — see "Shared icon library" below.

`arch.svc(kit, pres, s, cx, y, name, label)` accepts a name from *either* tier: a curated
short name (`"ecr"`) wins when bundled, otherwise it resolves from the shared library
(`"Amazon-Elastic-Container-Registry"`).

## AgentCore icons — `assets/icons/agentcore/`

Black + purple line icons on transparent background (designed for white canvas).
Extracted from the official "Amazon AgentCore Icons" deck. Use these whenever a slide
is about AgentCore or one of its components.

| name | represents |
|---|---|
| `agentcore` | Amazon Bedrock AgentCore (brain + sparkle) — use in headers |
| `ai_agent` | AI Agent (brain + neural nodes) |
| `runtime` | Runtime (brain + cloud + clock) — serverless runtime |
| `gateway` | Gateway (brain + gear + connectors) — tool gateway |
| `identity` | Identity (brain + person + shield) |
| `code_interpreter` | Code Interpreter (brain + code window + lock) |
| `observability` | Observability (brain + rising chart) |
| `browser_tool` | Browser Tool (brain + browser window + globe) |
| `memory` | Memory (brain + stacked blocks) |
| `evaluations` | Evaluations (brain + doc + magnifier checklist) |
| `policy_engine` | Policy Engine / Agentic Guardrails (brain + lock + check) |

Typical mapping for a 3-card AgentCore feature slide:
- "가치 실현 시간 단축 / 빠른 구축" → `runtime`
- "유연성 / 어떤 모델·프레임워크" → `ai_agent`
- "신뢰성 / 안전·거버넌스" → `policy_engine`

## AWS service icons — `assets/icons/aws/`

Official AWS service icons (colored square tiles). Use in architecture diagrams via
`arch.svc(kit, pres, s, cx, y, "<name>", "<label>")`.

| name | service | tile color |
|---|---|---|
| `eks` | Amazon EKS | orange |
| `ecr` | Amazon ECR | orange |
| `gpu` | GPU / compute chip | orange outline |
| `s3` | Amazon S3 | green |
| `fsx` | Amazon FSx | green |
| `efs` | Amazon EFS | green |
| `api_gateway` | Amazon API Gateway | purple |
| `load_balancer` | Elastic Load Balancing | pink |
| `cloudwatch` | Amazon CloudWatch | pink |
| `model_registry` | Model registry / HF-style atom | line |
| `aws_cloud` | AWS Cloud / Region mark (square+triangle+circle) | blue |

### Need an AWS icon that isn't here? → use the shared library first

Before extracting/converting anything, check the **shared icon library** (next section) —
it has 800+ official icons and almost always already contains the service you need.
Only fall back to manual extraction (below) if the shared library is unavailable.

This curated set is a small starter pulled from one EKS deck. To add more, extract from any
AWS deck's `ppt/media/*.svg` and convert with sharp:

```js
const sharp = require("sharp"), fs = require("fs");
await sharp(fs.readFileSync("media/imageNN.svg"), { density: 300 })
  .resize(256, 256, { fit: "inside" }).png().toFile("assets/icons/aws/<name>.png");
```

Or use the official AWS Architecture Icons package
(https://aws.amazon.com/architecture/icons/) — download the asset pack, pick the SVGs
you need, and convert the same way. Always verify the icon visually after extraction
(filenames in source decks are not semantic).

## Shared icon library — `kit.icon(name)` (811 official icons)

The full **AWS Architecture Icons** set lives in the sibling `reactive-presentation`
skill at `../reactive-presentation/icons/`. This skill references it in place — nothing
is duplicated, and no download is needed as long as both skills are installed together
(they ship in the same `aws-content-plugin`).

Resolve any icon by its **index key** with `kit.icon(name)`:

```js
arch.svc(kit, pres, s, cx, y, "Amazon-Elastic-Kubernetes-Service", "Amazon EKS");
s.addImage({ path: kit.icon("Amazon-Bedrock"), x, y, w: 0.62, h: 0.62 });
```

`kit.icon()` returns a **pptx-safe PNG path**: the index records an SVG, and the helper
automatically swaps to the PNG sibling (PowerPoint renders PNG reliably; SVG is flaky).
If only an SVG exists it warns and returns the SVG — rasterize it with sharp in that case.
`kit.hasIcon(name)` tests existence without throwing.

### Finding the right name

Keys are the **full official service names** (not the curated short names). Search the
index — it maps `key → {set, path, label}`:

```bash
# list every key
grep -oE '"[A-Za-z0-9_-]+":' ../reactive-presentation/icons/index-lite.json | tr -d '":'
# fuzzy-find a service
python3 -c "import json,re; d=json.load(open('../reactive-presentation/icons/index-lite.json'))['icons']; print([k for k in d if re.search('lambda',k,re.I)])"
```

Common keys: `Amazon-EC2` · `Amazon-Elastic-Kubernetes-Service` · `AWS-Lambda` ·
`Amazon-Simple-Storage-Service` (S3) · `Amazon-Bedrock` · `Amazon-SageMaker` ·
`Amazon-API-Gateway` · `Amazon-CloudWatch` · `Amazon-DynamoDB` · `AWS-Fargate`.

### Sets in the library (`index-lite.json` → `set`)

| set | count | when to use |
|---|---|---|
| `services` | 307 | primary service icons (the colored square tiles) — default for diagrams |
| `resources` | 430 | resource-level sub-icons (e.g. `Amazon-EC2_Instance`) — finer-grained |
| `categories` | 25 | category tiles (Compute, Storage, …) — group/section headers |
| `groups` | 13 | architecture group marks (AWS Cloud, VPC, Region, Account) — boundaries |
| `agentcore` | 11 | AgentCore component icons (also bundled curated; prefer `kit.agentcoreIcon`) |
| `others` | 25 | third-party (Grafana, LangChain, vLLM, …); some are SVG-only — verify |

> The curated `kit.awsIcon` set still exists for the handful of pre-validated tiles and is
> what the demo uses. For anything broader, reach for `kit.icon(name)`.

## External tool icons — `assets/icons/tools/`

Logos for non-AWS tools that appear in diagrams (inference engines, frameworks,
model providers): e.g. `ray`, `vllm`. Use via `kit.toolIcon("ray")`.

Currently bundled: `ray` (Ray, from Simple Icons), `vllm` (vLLM wordmark).

### How to get an external tool/brand icon — 3-step strategy

When a slide needs a tool/brand logo that isn't already in `assets/icons/tools/`, get
it in this priority order:

**1. Simple Icons (preferred — local, no network, 3300+ brands).** `react-icons/si`
bundles the entire Simple Icons set. Most ML/infra brands are there: Ray, Hugging Face,
LangChain, PyTorch, TensorFlow, NVIDIA, OpenAI, Anthropic, Meta, Docker, Kubernetes,
Python, etc. Render to a PNG with the brand color:

```js
const si = require("react-icons/si");
const React = require("react"), RD = require("react-dom/server"), sharp = require("sharp");
const svg = RD.renderToStaticMarkup(React.createElement(si.SiRay, { color: "#028CF0", size: "256" }));
await sharp(Buffer.from(svg)).png().toFile("assets/icons/tools/ray.png");
```

Check existence first: `typeof require("react-icons/si").SiRay === "function"`.
Simple Icons gives the **symbol only** (no wordmark), which is clean for diagrams.
You supply the brand color (look it up; Simple Icons publishes official hex per brand).

**2. Extract from a reference deck the user provided.** If the user uploaded a deck
that already contains the logo (as in the EKS deck → Ray/vLLM), pull it from
`ppt/media/*.png|*.svg` and trim (python PIL):

```python
im = Image.open("media/imageNN.png").convert("RGBA")
im.crop(im.getbbox()).save("assets/icons/tools/vllm.png")
```

**3. Web search (last resort, when 1 & 2 fail).** The build container has no network,
but the assistant's `web_search` / `web_fetch` tools do. Workflow:
   - `web_search` for "<tool> logo svg" or the official brand/press page.
   - Prefer the **official source** (project site, GitHub, brand guidelines). Avoid
     random logo-aggregator sites.
   - `web_fetch` the SVG/PNG URL. If you can get the SVG markup as text, write it to a
     file and convert with sharp. If only a raster URL is available, pptxgenjs can take
     a remote URL directly (`s.addImage({ path: "https://.../logo.png" })`), but saving
     into `assets/` for reuse is better.
   - **Respect trademarks**: use official logos as-is, don't recolor/distort brand
     marks, and only for legitimate descriptive use (showing which tool is in the stack).

After obtaining any icon, **verify it visually** (render + view) before shipping —
source filenames are not semantic and brand colors must be correct.

## agenda tile icons

The agenda layout uses small line icons rendered from **react-icons** (`react-icons/fi`),
tinted with the accent blue, not the AWS/AgentCore PNGs:

```js
const { FiZap, FiSearch, FiGitBranch, FiShield } = require("react-icons/fi");
const data = await arch.renderIcon(FiZap, "#" + kit.C.blue);
// then: items:[{ num:"01", title, desc, iconData: data }]
```

Pick `fi` icons that match each chapter's topic. You may instead pass an AgentCore/AWS
PNG via `iconPath` if a chapter is about a specific service.
