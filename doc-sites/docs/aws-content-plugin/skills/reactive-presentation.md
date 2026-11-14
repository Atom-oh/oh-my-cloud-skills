---
sidebar_position: 1
title: "Reactive presentation skill"
---

# Reactive presentation skill

**Presenting a deck someone else created?** Start with the [presenter's guide](../presenter-guide.md). It covers opening the slides, sharing the right window, reading notes, operating interactive slides, and recovering during a talk. This page explains how to create and maintain the deck.

{/* Legacy section links retained after the English rewrite. */}
<span id="trigger-keywords" />
<span id="provided-resources" />
<span id="assets" />
<span id="scripts" />
<span id="references" />
<span id="icons" />
<span id="key-features" />
<span id="remarp-format-recommended" />
<span id="pptx-theme-extraction" />
<span id="data-visualization-patterns" />
<span id="typography-hierarchy" />
<span id="css-only-charts" />
<span id="kpi-card-layout" />
<span id="chartjs-integration" />
<span id="canvas-vs-html-decision-guide" />
<span id="the-4-box-rule" />
<span id="decision-matrix" />
<span id="html-architecture-pattern" />
<span id="remarp-workflow-detail" />
<span id="step-1-theme-setup-optional" />
<span id="step-2-content-planning" />
<span id="step-3-create-project-structure" />
<span id="step-4-write-remarp-content" />
<span id="step-5-build-html" />
<span id="step-6-review--iterate" />
<span id="step-7-enhancement" />
<span id="step-8-quality-review" />
<span id="step-9-deploy" />
<span id="interactive-pattern-guide" />
<span id="simulator-pattern" />
<span id="calculator-pattern" />
<span id="dashboard-pattern" />
<span id="speaker-notes-writing-guide" />
<span id="requirements" />
<span id="structure-template" />
<span id="good-example" />
<span id="bad-example-what-not-to-do" />
<span id="slide-types" />
<span id="keyboard-shortcuts" />
<span id="usage-example" />
<span id="quality-review-required" />

Build an interactive HTML presentation from Remarp Markdown, then present it in a browser or export static slide images. This guide walks through a complete small project and the choices that make a technical training useful, especially at L200.

**Remarp is the source of truth.** Keep content, notes and interaction code in the source files. The compiler owns generated HTML and the shared framework.

| Desired result | Use |
| --- | --- |
| Browser slides with tabs, quizzes, controlled steps and live inputs | reactive-presentation |
| A PowerPoint copy of the web deck's appearance | reactive-presentation screenshot export; the result is not editable slide objects |
| Native PowerPoint with editable text, shapes and layouts | [aws-light-fcd](./aws-light-fcd.md) |

For a first run, follow **Prepare the tools → Build your first deck → Validate and preview**. The later sections explain richer interactions and publication.

## Workflow {#workflow}

1. **Brief:** agree on audience, level, language, duration, output location, quiz inclusion and reference material.
2. **Plan:** decide the message and interaction for each slide; divide longer training into independently viewable blocks.
3. **Author:** write shared metadata, block files, structured notes and any local assets.
4. **Validate and build:** fix CRITICAL source findings before generating HTML.
5. **Rehearse and review:** exercise the built deck, measure layout and obtain a content-review PASS.
6. **Export or publish:** export a static copy or deploy the complete output only after authorization.

A successful compiler run proves that the source can build, not that the teaching, data or browser interactions are correct.

## Prepare the tools {#prepare-the-tools}

Install [aws-content-plugin](../installation.md) for your host. In Claude Code, request an interactive/web presentation so the presentation dispatcher selects this workflow. In Codex, select the installed reactive-presentation skill or name it in your request; specialist procedures do not require a native Claude subagent.

For manual commands, use Python 3 and the script directory belonging to the skill version you installed. The examples below use a **repository checkout**, not a hardcoded plugin-cache version:

```bash
# From the oh-my-cloud-skills repository root:
export SKILL_DIR="$(pwd)/plugins/aws-content-plugin/skills/reactive-presentation"
python3 "$SKILL_DIR/scripts/remarp_to_slides.py" --help
mkdir -p my-talk/assets
cat > my-talk/assets/logo.svg <<'SVG'
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 48">
  <rect width="160" height="48" rx="8" fill="#232f3e"/>
  <text x="80" y="31" text-anchor="middle" fill="white" font-size="20">Example team</text>
</svg>
SVG
```

For an installed package, set SKILL_DIR to its actual reactive-presentation procedure directory containing scripts and assets. Do not guess a deleted cache version or assume CLAUDE_PLUGIN_ROOT is exported in Codex. Run the help command to confirm the path.

The sample logo is a self-contained placeholder for a third-party training deck. Replace it and the footer with branding you are authorized to use. Real AWS-branded deliverables use the applicable AWS branding and copyright.

Use PyYAML for the complete YAML metadata examples. Browser measurement requires the Python Playwright package **and** a launchable Chromium; PowerPoint export additionally requires python-pptx. Install dependencies in an approved project environment only when needed. A configured Playwright MCP and local Python Playwright can use different browser installations.

## Request examples {#request-examples}

Give the assistant concrete constraints instead of asking only for “nice slides.” The prompts are shared English examples; change the requested language and project details rather than expecting metadata to translate the prose.

**L200 introduction:**

```text
Use reactive-presentation to create a 30-minute L200 introduction to
event-driven applications for developers new to cloud architecture.
Language: Korean. Output: ./event-driven-intro/.
Include speaker notes, a knowledge check and a Key Takeaways slide.
Explain unfamiliar terms at first use with plain meanings and examples.
Use stepwise request flows, a before/after comparison and one input-driven
simulation. Prefer an explorable Archify diagram for grouped architecture.
Use official AWS icons for AWS services. Keep essential meaning visible
in static exports. Validate and review before publication.
Do not deploy or overwrite an existing deck without my confirmation.
```

**Multi-block technical training:**

```text
Create a 90-minute reactive-presentation training in ./platform-training/.
Audience: platform engineers. Level: L300. Language: English.
Plan three 30-minute blocks: fundamentals, architecture and operations.
Include a session cover and Thank You slide in each block, shared branding,
structured speaker notes and one knowledge check per block.
Use the supplied reference documents as evidence; do not invent benchmarks.
Show the outline and interaction plan before authoring the Remarp sources.
```

**A bounded revision to an existing deck:**

```text
Update ./event-driven-intro/02-architecture.md only:
turn the request-flow slide into three controllable steps and add a
plain-language detail panel for the first use of "event".
Preserve the existing theme, notes, quiz answers and unrelated slides.
Edit Remarp source, not generated HTML. Validate, sync the complete project,
then check the changed slide in both themes. Do not deploy.
```

## Project layout {#project-layout}

```text
my-talk/
  _presentation.md       # Shared metadata, branding and block list
  01-basics.md           # Remarp slides and speaker notes
  assets/
    logo.svg             # Project-local image, kept with the output
  index.html             # Generated merged deck
  toc.html               # Generated block agenda and export controls
  01-basics.html         # Generated block deck
  common/                # Generated framework and referenced AWS icons
```

Only metadata belongs in the shared presentation file. Each numbered block needs its own Remarp frontmatter and slides. Keep each block name consistent with the shared list and its filename stem. Block durations must add up to the total; agree separately whether breaks are part of that time.

The project build writes HTML beside the sources by default. Custom images are not bundled automatically. Keeping the default output beside assets makes the sample logo resolve; when using a separate output directory, copy project-local assets and check every relative path.

## Build your first deck {#first-deck}

The complete example is a **12-minute, five-slide** teaching skeleton: cover, ordered reveal, tabs, quiz and closing. It intentionally stays small; expand its content and interactions before using it as a full training.

Save the shared configuration as **my-talk/_presentation.md**:

```yaml
---
remarp: true
version: 1
title: "Requests in motion"
ratio: "16:9"
speaker:
  name: "Alex Morgan"
  title: "Engineer"
  company: "Example team"
audience: "Developers new to request processing"
level: "200"
quiz: true
duration: 12
lang: en
blocks:
  - name: 01-basics
    title: "Request basics"
    duration: 12
theme:
  footer: "© 2026 Example team. All rights reserved."
  logo: "./assets/logo.svg"
transition:
  default: fade
  duration: 400
---
```

The aspect ratio, audience level, language, quiz choice, branding and timing are explicit. The example is English; for Korean, change the language metadata to ko and write the slide text and notes in Korean. Metadata alone does not translate content.

Save the block as **my-talk/01-basics.md**. The required summary marker stays literally [요약], even in English notes:

```markdown
---
remarp: true
block: 01-basics
title: "Request basics"
---

<!-- Slide 1: Session cover -->
@type: cover

# Requests in motion

Follow a request from an action to a result.

:::notes
{timing: 1min}
[요약]
- Introduce the request journey.
- Ask for a familiar application.
- Preview the knowledge check.

Ask the audience to imagine pressing Save in an application.
Explain that the session follows the work triggered by that action.
The aim is to identify where work starts, where it is processed and
how the result reaches the user, without needing a cloud background.
:::

---
<!-- Slide 2: Reveal a sequence -->
@type: content

## Every request has a path

- The client sends a request. {.click order=1}
- A worker processes the request. {.click order=2}
- The client receives the result. {.click order=3}

:::notes
{timing: 3min}
[요약]
- Reveal one action at a time.
- Connect each action to Save.
- Separate a request from its result.

Define the client as the part of an application asking for work.
Reveal the worker only after asking who performs that work.
Use saving a document as the running example: the client asks to save,
the worker stores the change and the client shows confirmation.
{cue: question}
Ask what the user might see while waiting for the result.
:::

---
<!-- Slide 3: Compare explanations -->
@type: tabs

## Choose when to wait

### Wait
The client waits for the worker's result before continuing.

### Continue
The client continues while work finishes separately.
It needs a way to discover whether the work succeeded.

:::notes
{timing: 3min}
[요약]
- Show both interaction choices.
- Compare what the user sees.
- Avoid promising that all work becomes faster.

Select each tab and describe the user experience, not just the labels.
Waiting can be appropriate when the result is needed for the next action.
Continuing can help when work takes longer, but the application still
needs to communicate progress and report failures to the user.
:::

---
<!-- Slide 4: Knowledge check -->
@type: quiz

## Check the request path

**What starts the work in this example?**
- [x] The client sends a request.
- [ ] The result appears before any request.
- [ ] The worker never receives an input.

:::notes
{timing: 3min}
[요약]
- Let the audience choose first.
- Explain why the request starts work.
- Revisit the sequence if needed.

Pause before selecting an answer. Ask someone to describe the Save
example in their own words. Choose the correct answer and explain
why a visible result follows processing rather than preceding it.
Use an incorrect answer to revisit the sequence without judging the learner.
:::

---
<!-- Slide 5: Closing -->
@type: thankyou
@toc: toc.html

# Thank You

Trace one request in your own application.

:::notes
{timing: 2min}
[요약]
- Recap the request journey.
- Invite one practical next step.
- Leave time for questions.

Ask the audience to choose one action in their own application and name
the client, the work performed and the visible result.
Use the agenda link to return to the block list, then invite questions
about where waiting or progress reporting would help that example.
:::
```

## Validate and preview {#validate-and-preview}

```bash
python3 "$SKILL_DIR/scripts/remarp_to_slides.py" validate ./my-talk/
python3 "$SKILL_DIR/scripts/remarp_to_slides.py" build ./my-talk/
python3 -m http.server 8080 --bind 127.0.0.1 --directory ./my-talk/
```

Open the [merged deck](http://127.0.0.1:8080/index.html) or the [block agenda and exports](http://127.0.0.1:8080/toc.html). Stop the server with Ctrl+C when finished. Use another port if 8080 is already taken.

Validation exits nonzero on invalid input or CRITICAL findings. Build and sync enforce that same gate. Resolve style warnings during authoring too, but do not confuse an advisory warning with a compiler rejection.

Check these observable results:
- Five slides appear in order, with no extra blank slide.
- Right/Space reveals the three request actions before changing slides; Left reverses.
- The tabs switch by click and the registered Up/Down controls.
- The quiz shows appropriate feedback for both a distractor and the correct choice.
- The closing button reaches the agenda; the logo and footer load.

Put directives after a separator, without wrapping them in another frontmatter block. A single-file build has a different default output: slides/default.html with slides/common/.

## Choose content and interaction {#content-and-interaction}

| Need | Pattern | What to test |
| --- | --- | --- |
| Explain one idea | content with ordered fragments | Reveal and reverse in the intended reading order |
| Compare alternatives | compare or tabs | Each button and Up/Down cycling |
| Check understanding | quiz with one marked answer | Correct and incorrect feedback |
| Track completion | explicit checklist | Checkbox state, not quiz scoring |
| Show a short linear process | Canvas DSL, at most four boxes/icons | Every forward and reverse step |
| Explore groups or branches | HTML/CSS or Archify | Labels, focus, navigation and both themes |
| Show the effect of a parameter | HTML controls plus script | Initial value, limits, changed value and reset |

Use ordered fragments for information that accumulates. Use tabs when alternatives should occupy the same space. Keep the important conclusion on the visible slide instead of hiding it entirely behind controls. Raw block HTML belongs in an HTML source block; scripts belong in a script source block. A quiz uses a checked item for a correct answer; more than one checked item does not establish a multi-select scoring contract.

## Make L200 explanations dynamic {#l200-teaching}

At L200, use interaction to expose **cause and effect**, not to add decoration. A practical teaching sequence is:
1. Show a familiar situation and define unfamiliar terms.
2. Ask the audience to predict what happens next.
3. Reveal one step or change one input.
4. Show the visible result and explain why it changed.
5. Reset or reverse the sequence, then check understanding.

For a 30-minute introduction, a useful authoring plan is a short scenario, one controllable request flow, a comparison, one input-driven example, a knowledge check and a recap. This is a planning suggestion, not an automatic compiler rule: setting the level to 200 does not create animations or simulations.

Prefer a paused, presenter-controlled sequence over an endless autoplay loop. Provide a readable final state and text explanation for static exports. For custom motion, support reduced-motion preferences and a pause/reset path; verify those behaviors rather than assuming the framework supplies them.

## Add a controllable Canvas flow {#canvas-steps}

Insert this slide before the quiz and update the planned duration. Its three generic boxes use the 960 × 400 design coordinates: with a 160-pixel box width, the horizontal gap is (880 − 3 × 160) / 2 = 200. The left positions are 40, 400 and 760. The equal colors indicate peers, not a severity ranking.

```markdown
---
<!-- Slide: Stepwise request flow -->
@type: canvas
@canvas-id: request-steps

## Follow one request

:::canvas
box client "Client" at 40,180 size 160,55 color blue step 1
box worker "Worker" at 400,180 size 160,55 color blue step 2
box result "Result" at 760,180 size 160,55 color blue step 3
arrow client -> worker "request" step 2
arrow worker -> result "complete" step 3
:::

:::notes
{timing: 3min}
[요약]
- Identify the client.
- Advance to the worker.
- End with the visible result.

Start with the client alone and ask what happens after the Save action.
Advance to the worker, then to the result. Reverse the steps once so the
audience can explain the sequence rather than memorize a finished picture.
The arrows show an illustrative order, not a measured latency.
:::
```

Walk forward and backward through every step with Down/Up. Check arrow labels, margins and text at FHD and 4K. Keep Canvas to at most four boxes/icons in a linear flow; use HTML/CSS or Archify for groups, branches and larger diagrams. When the diagram represents AWS services, use verified official icon aliases from the shared bundle instead of generic substitute boxes.

## Add an input-driven explanation {#input-driven-example}

This example changes an illustrative request rate while holding average processing time fixed. Add it as a new slide, then update notes and total/block duration. It is a teaching widget, not an AWS sizing calculator.

```markdown
---
<!-- Slide: Input-driven explanation -->
@type: content

## Waiting keeps work active

:::html
<section id="load-lab" class="card">
  <label for="request-rate">Requests per second</label>
  <input id="request-rate" type="range" min="10" max="100" step="10" value="50">
  <p>Rate: <output id="rate-value">50</output> requests/s</p>
  <p>Assumed average time: 200 ms</p>
  <p>Average in-flight requests: <output id="inflight-value" aria-live="polite">10</output></p>
  <button id="reset-load" type="button">Reset</button>
  <p>Illustrative steady-state estimate: rate × time in seconds.
     This is not a capacity benchmark or a scaling recommendation.</p>
</section>
:::

:::script
const root = document.getElementById('load-lab');
const input = root.querySelector('#request-rate');
const update = () => {
  const rate = Number(input.value);
  root.querySelector('#rate-value').textContent = String(rate);
  root.querySelector('#inflight-value').textContent = (rate * 0.2).toFixed(0);
};
input.addEventListener('input', update);
root.querySelector('#reset-load').addEventListener('click', () => {
  input.value = '50';
  update();
});
update();
:::

:::notes
{timing: 3min}
[요약]
- Change only the request rate.
- Keep average time fixed.
- Explain the estimate's limitation.

Ask the audience to predict what doubling the rate does to work in flight.
Move the slider from 50 to 100 requests per second, then reset it.
The estimate assumes a steady flow and a 200 ms average time per request.
It does not prove that a real application has enough resources or that
an AWS service should scale at a particular threshold.
:::
```

Verify 10, 50 and 100 requests/s produce 2, 10 and 20 average in-flight requests. Test keyboard adjustment and Reset. Use unique DOM IDs when creating another widget, label every input and keep the assumptions visible. Scripts execute in the deck's page, so treat source HTML/JavaScript as executable code and never paste untrusted scripts.

## Architecture diagrams and line-art motion {#architecture-and-line-art}

Choose the diagram by the question being taught:
- **“What happens next?”** Use controlled Canvas steps or an animated-diagram SVG for a request/traffic sequence.
- **“What connects to what?”** Use Archify for explorable groups, zoom and path highlighting, or an official-icon HTML/CSS layout.
- **“What must be shared as a static artifact?”** Use [architecture-diagram](./architecture-diagram.md) for Draw.io and PNG/SVG.

For Archify, first prepare a valid architecture JSON spec at the referenced path. The following is an **embedding excerpt**, not a complete slide or JSON spec; add the file, notes and surrounding project metadata before building:

```markdown
---
@type: content

## Explore the request route

:::archify id=request-map height=680px
./assets/request-map.json
:::
```

The builder needs Node.js and a pinned Archify clone. The pin is owned by the installed skill's icon helper. On the first setup, with authorized network access and a fresh dependency directory:

```bash
# Read the pin from the same skill version used to build the deck.
PIN="$(python3 - "$SKILL_DIR/scripts/archify_icons.py" <<'PY'
import runpy
import sys
print(runpy.run_path(sys.argv[1])["ARCHIFY_PIN"])
PY
)"
git clone https://github.com/tt-a1i/archify ./archify-dependency
git -C ./archify-dependency checkout "$PIN"
export ARCHIFY_DIR="$(pwd)/archify-dependency"
python3 "$SKILL_DIR/scripts/remarp_to_slides.py" build ./my-talk/
```

For an existing clone, verify its commit and set ARCHIFY_DIR to it instead of cloning over it. Do not bypass the pin check to “fix” a build. Give every diagram a unique ID. AWS vocabulary IDs such as alb, eks and s3 can receive official icons automatically; inspect unmapped-node messages and the final diagram.

The generated diagram files live under archify/ and must travel with the deck. Serve the deck over HTTP: clicking the diagram gives its iframe focus, and Esc returns focus to the deck on the same origin. Under file URLs, click outside instead. A browser export flattens the diagram; use the PowerPoint export's hosted URL option for the interactive link in notes.

For a [line-art-animation-style](https://github.com/JDhruv14/line-art-animation) effect, ask for an SVG path reveal or highlighted connection in an HTML source block with source-owned styles/scripts. **There is no built-in line-art directive or automatic installation of that repository.** The [animated-diagram skill](./animated-diagram.md) is another supported route for SVG traffic motion. Review any third-party license before copying code or assets. Keep the final drawing meaningful without motion, provide pause/reset for custom playback and respect reduced-motion preferences.

## Navigation and detail layers {#navigation-and-detail-layers}

Hover the top-right corner to open the agenda. Cmd+K, Ctrl+K or / searches slide titles, visible content and detail text, but not speaker notes. Agenda and search are excluded from overview, presenter previews, measurement and export captures.

For a one-sentence definition, use a tooltip:

```markdown
[Worker]{tip="The part of the application that performs the requested work."}
```

For a longer explanation, keep the trigger and detail block on the same slide:

```markdown
[API]{detail=api}

:::detail api "How an API connects applications"
tip: API (Application Programming Interface): an agreed way for programs to request data or actions.

An API defines which requests a program accepts and what it returns.
For example, a weather app requests a forecast instead of collecting sensor data itself.
:::
```

Detail blocks must be top-level, with unique slide-local IDs and matching references. Duplicate IDs or missing references are CRITICAL DETAIL_REF findings. Hover/focus reveals the summary; click, Enter or Space opens the detail panel. Tip-only terms also support touch. Move onto the tooltip to read it; Esc dismisses it. A detail panel closes on Esc, an outside click or a slide change. Test focus return and ensure an activation does not advance the slide.

## Audience-aware explanations {#audience-aware-explanations}

Explain unfamiliar terminology, acronyms and industry jargon at their first meaningful use in each independently viewable block. Common names such as API, JSON, EKS and S3 are not automatically familiar to a beginner. Repeat a definition after a long gap only when readers need it.

For **L100/L200**, give the full name, a plain-language meaning and a practical example or reason it matters. L300/L400 can be shorter but still needs unfamiliar domain concepts explained. Presenter notes supplement these explanations; they do not replace audience-facing text.

- **Charts:** provide a focusable text caption explaining axes, units, population/timeframe, baseline, conclusion and relevant limitations/source. Mark illustrative data; do not invent benchmark results.
- **Quotations:** keep attribution visible and provide context. Label illustrative or unverified quotes explicitly.
- **Static copies:** essential meaning, chart labels/units, conclusions and attribution remain visible without hovering or opening a panel.

The compiler checks annotation structure. Content review judges whether the audience can actually understand the explanation.

## Copy gates {#copy-gates}

Resolve EM_DASH, AI_TONE and AUDIENCE_TONE warnings during source authoring. SENTENCE_RUNON is a rendered measurement warning. Keep card text to one claim line and an optional reason line; move longer explanation into a detail panel. In authored presentation text and notes, avoid em dashes and middle dots; use natural sentences, commas, parentheses or separate lines.

## Design, branding and notes {#design-and-notes}

Use semantic color tokens and class-based light/dark themes. Do not assign a different severity color to every peer card unless that color has an explained category meaning. The first slide of each block is a session cover; the last is a Thank You slide returning to the agenda.

For an authorized PowerPoint template, replace the sample theme configuration:

```yaml
theme:
  source: "./company-template.pptx"
  footer: auto
  logo: auto
```

Keep the template path accessible to the project. For explicit extraction and inspection:

```bash
python3 "$SKILL_DIR/scripts/extract_pptx_theme.py" ./company-template.pptx \
  -o ./my-talk/common/pptx-theme/
```

Inspect the manifest, extracted logos and theme-override.css, then verify that the final deck links the override and contains its images. Brand input uses --pptx-* variables. Extraction does not install fonts; verify font availability and both themes. PDF theme extraction is currently unimplemented, so use PDF/image inputs as visual references rather than promising equivalent branding extraction.

Every slide needs useful structured notes: timing, the literal summary marker, a few summary bullets, a spoken explanation and delivery cues where helpful. The complete example demonstrates this. Do not merely repeat the slide bullets. Use **N**, not P, to open presenter view; P belongs to the pen/laser controls.

## Edit and rebuild safely {#edit-and-rebuild}

Edit only the affected Remarp source and preserve notes, quiz answers, Canvas and script blocks. Never patch generated HTML independently. After a source, theme, shared metadata or asset change:

```bash
python3 "$SKILL_DIR/scripts/remarp_to_slides.py" validate ./my-talk/ --json
python3 "$SKILL_DIR/scripts/remarp_to_slides.py" sync ./my-talk/
# Only the named block; this does not refresh the merged deck or agenda.
python3 "$SKILL_DIR/scripts/remarp_to_slides.py" build ./my-talk/ --block 01-basics
python3 "$SKILL_DIR/scripts/remarp_to_slides.py" issues ./my-talk/ --json
```

Sync regenerates the complete project, agenda and framework assets; it is not a timestamp-based incremental rebuild. Use a partial block build during iteration, then full sync before rehearsal or export.

Leave an issue annotation on the affected source slide when asking for a correction:

```markdown
<!-- issue: Explain this term at first use and reveal the flow in three steps. -->
```

The issues command lists annotations; it does not fix them. Request [slide-fix](./slide-fix.md) to apply the feedback. The compiler removes issue comments from generated slides.

In VS Code, distinguish approximate text preview from compiled HTML preview. Design Studio in extension 0.2.0+ supports compiler-backed snapshots and bounded source edits; complex interactions remain source-editable. Its AI request is a clipboard handoff, not an automatic provider call. Preview or Studio never replaces the validation and content-review gates.

## Presenter controls {#presenter-controls}

| Key | Current default |
| --- | --- |
| Right / Space, Left | Reveal/advance, reverse/go back |
| Down / Up | Registered Canvas steps, tab cycling or slide-specific action |
| N | Presenter window and notes |
| F / G / S | Fullscreen / overview / sidebar |
| T / H | Toggle deck theme / hide current slide locally |
| P / O / I / U / Y | Laser / pen / highlighter / eraser / magnifier |
| C / Esc | Clear current-slide ink / leave pen mode first |

Custom key mappings can override some defaults. With pen mode enabled, the overlay takes pointer input; turn it off before using tabs, quizzes and detail links. Presenter-note edits are browser-local and do not rewrite Remarp. For lasting edits, change the source and sync. See the [current keyboard reference](/docs/remarp-guide/keyboard-shortcuts) for the complete behavior and fullscreen caveats.

## Quality checklist before sharing {#quality-checklist}

Run the source gate, then the two output gates on the **built project with common assets**:

```bash
python3 "$SKILL_DIR/scripts/check_deck.py" ./my-talk/
python3 "$SKILL_DIR/scripts/measure_deck.py" ./my-talk/ \
  --viewports 1920x1080,1280x720,3840x2160 --themes light,dark
```

Measurement must have no FAIL findings and no unresolved UNDERFILL findings. Fix warnings in their actual context; a clean static check does not prove interaction or factual quality.

Before sharing:
- Verify browser startup and that every CSS, script, image and iframe loads.
- Check all interactive/Canvas slides at 1920 × 1080 and 3840 × 2160; walk through every Canvas step in both directions.
- Exercise tabs, quiz answers, sliders, reset buttons and keyboard/focus/touch explanations.
- Test both themes, fullscreen, presenter synchronization and the closing agenda link.
- Verify technical claims against official sources; label illustrative numbers and scan for secrets or sensitive account data.
- Inspect a real export for final-state legibility, notes, chart labels and attribution.
- Obtain a **content-review PASS**, not just a numerical score: on the normal 100-point scale, score ≥85, Critical 0 and Warning ≤3. Applicable Visual Testing exemptions use the documented 90-point scale and must be disclosed; do not treat unavailable tools as a passed test.

Ask “Review content at ./my-talk/ and report the scale, findings and verdict.” Fix findings and re-review before publishing.

## Exports and existing decks {#tools-and-exports}

The generated agenda has PDF, ZIP and PPTX export controls, but their preservation guarantees differ:

- **Browser PDF:** the print path hides Canvas drawings and substitutes an interactive-animation placeholder. It does not preserve the final Canvas step. Use an inspected screenshot-based route when the finished drawing must appear in a static copy.
- **Browser ZIP:** the helper assumes a legacy parent-level common directory and does not collect Archify iframe documents. Do not rely on it as a portable archive of the project layout in this guide. Archive the complete generated tree with its assets, check the extracted relative paths and test it again.
- **Browser PPTX:** uses html2canvas and PptxGenJS from a CDN; test dependency access before presenting offline.

To archive the complete sample project, including its Remarp sources and notes, use the standard Python ZIP tool. Inspect those sources and notes for sensitive material before sharing:

```bash
python3 -m zipfile -c ./my-talk.zip ./my-talk/
```

For a more reliable screenshot-based PowerPoint export:

```bash
# Use your project's approved Python environment.
python3 -m pip install 'playwright>=1.40' 'python-pptx>=1.0'
python3 -m playwright install chromium
python3 "$SKILL_DIR/scripts/export_pptx.py" ./my-talk/ -o ./my-talk.pptx
```

Export only a deck you built and trust, because capture executes its HTML/JavaScript. Fragments are revealed and Canvas is captured at its final step; speaker notes are retained. Quiz choices, tabs, simulations and detail layers are not live in the resulting PowerPoint. Inspect the selected state and keep essential explanations visible. For editable objects, choose the native PowerPoint skill instead.

For Archify links in the exported notes, replace the placeholders with the actual published deck location:

```bash
python3 "$SKILL_DIR/scripts/export_pptx.py" ./my-talk/ -o ./my-talk.pptx \
  --base-url "https://YOUR_USER.github.io/YOUR_REPO/my-talk/"
```

To start from an existing PowerPoint:

```bash
python3 "$SKILL_DIR/scripts/convert_to_remarp.py" ./existing-deck.pptx \
  -o ./converted-talk/ --lang ko
```

Conversion is a starting point, not a guarantee of preserved animations or layout. PDF input additionally needs PyMuPDF and uses image backgrounds with extracted text. Review and rewrite the Remarp, add audience explanations and interactions, then validate/build. The converter's force option overwrites with a backup; do not use it without approval.

## Publish the complete deck {#publish-the-complete-deck}

When someone else will present, send the [presenter's guide and handoff template](../presenter-guide.md#author-handoff) with the deck link. Include the intended audience, timing, slide-by-slide speaking notes, exact interaction sequence, quiz explanations, tested reset behavior, and a checked static backup. A deck that works for its creator still needs a running order for its next presenter.

Publish generated HTML, common/, project-local assets and archify/ together. Keep relative paths valid under the repository's Pages subpath. Check the deployed deck without authentication and verify the agenda, all block links and exports.

A generation request is not deployment permission. Confirm the target repository/site, public visibility and overwrite scope before committing or pushing. Use its existing GitHub Pages workflow or configure Pages for the intended output. Do not assume the plugin marketplace's own documentation deployment publishes your separate deck. Keep sensitive source material and notes out of a public site unless authorized.

## Troubleshooting {#troubleshooting}

| Symptom | Check and fix |
| --- | --- |
| No slides or unexpected empty slides | Mark block frontmatter as Remarp; keep slide separators separate from metadata and directives |
| Wrong merged deck after a partial build | Run full sync; a block-only build does not refresh index or agenda |
| A script path disappeared after upgrade | Resolve the current installed procedure path, not an old cache version |
| Logo/image missing with separate output | Copy custom assets and verify paths relative to each output page |
| CRITICAL DETAIL_REF | Keep matching trigger/detail IDs on the same slide; remove duplicates |
| CRITICAL Canvas complexity or overlap | Recalculate coordinates; move grouped/large diagrams to HTML/CSS or Archify |
| Archify build cannot find or accept its clone | Verify ARCHIFY_DIR, Node.js and the skill-owned pin; do not bypass validation |
| Chromium cannot launch | Check local Playwright package and matching browser executable; MCP readiness is separate |
| Clicks or hover stop working | Exit pen/magnifier mode and check iframe focus |
| Presentation controls use an unexpected key | Check custom key mappings against the current N/P defaults |
| Text clips or density is wrong | Fix content/layout from measured findings instead of editing generated HTML |
| Export loses interactions or details | This is a static copy; show essential information on the slide and link the web deck |

The compiler does not expose a watch or output-format option. Use its help and the [CLI reference](/docs/remarp-guide/build-cli) instead of guessing flags.

## Further reading and demos {#further-reading}

- [Remarp quick start](/docs/remarp-guide/quick-start), [frontmatter](/docs/remarp-guide/syntax/frontmatter), [directives](/docs/remarp-guide/syntax/directives) and [CLI](/docs/remarp-guide/build-cli).
- [Fragments](/docs/remarp-guide/syntax/fragments), [Canvas DSL](/docs/remarp-guide/syntax/canvas-dsl), [speaker notes](/docs/remarp-guide/syntax/speaker-notes) and [keyboard reference](/docs/remarp-guide/keyboard-shortcuts).
- [VS Code extension and Design Studio](/docs/remarp-guide/vscode-extension), [theme extraction](/docs/remarp-guide/themes/pptx-extraction) and [design tokens](/docs/remarp-guide/themes/css-variables).
- [Basic presentation demo](../demos/basic-presentation.mdx) and [full feature tour](../demos/full-presentation-demo.mdx). These frozen demos illustrate features; they are not current validation certificates.
- [Maintained skill and authoring resources](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-content-plugin/skills/reactive-presentation/SKILL.md), [Archify block contract](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-content-plugin/skills/reactive-presentation/references/remarp-format-guide.md#archify--explorable-archify-diagram-adr-020) and [content-review rubric](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-content-plugin/agents/content-review-agent.md).
