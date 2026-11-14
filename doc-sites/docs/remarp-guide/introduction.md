---
sidebar_position: 1
title: "Remarp"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="remarp-소개" />
<span id="왜-remarp인가" />
<span id="비교표" />
<span id="핵심-장점" />
<span id="1-사람이-읽을-수-있는-마크다운" />
<span id="2-프래그먼트-애니메이션" />
<span id="3-canvas-dsl" />
<span id="4-스피커-노트--타이밍" />
<span id="5-pptx-테마-통합" />
<span id="6-멀티파일-프로젝트" />
<span id="7-인터랙티브-패턴" />
<span id="8-vscode-visual-edit" />
<span id="하위-호환성" />
<span id="다음-단계" />


# Remarp

Remarp turns Markdown into a browser-based presentation. You write the content and speaking notes in text files, then build a slide deck with step-by-step explanations, tabs, quizzes, and diagrams. A **deck** is the complete set of slides for a talk.

You can use AI to draft a deck, edit it in VS Code or code-server, and send a presentation link to another speaker. The person presenting a published deck needs a browser, not the authoring tools.

## Start with your task {#choose-your-path}

| What you want to do | Start here | What you will learn |
| --- | --- | --- |
| Present slides someone sent you | [Presenter's guide](/docs/aws-content-plugin/presenter-guide) | Open the deck, share the correct window, use notes, and operate the interactions |
| Create your first deck with AI | [Detailed authoring guide](/docs/aws-content-plugin/skills/reactive-presentation) | Request a deck, prepare the source, build, rehearse, and export |
| Write Markdown yourself | [Quick start](./quick-start.md) | Create source files and run the compiler |
| Edit a deck in VS Code or code-server | [Editor guide](./vscode-extension.md) | Install the appropriate extension, choose a preview, and edit supported elements in Studio |
| Change one existing slide | [Source editing workflow](./workflow.md) | Locate the owning source, make a bounded change, rebuild, and verify |

You do not have to learn every directive before trying a presentation. Choose one path above and return to the syntax references when you need a specific interaction.

## What you can make {#what-you-can-make}

| Teaching need | What the audience does or sees |
| --- | --- |
| Understand a sequence | The presenter reveals one item or one diagram step at a time |
| Compare alternatives | Tabs or comparison controls switch between explanations |
| Check understanding | A quiz displays feedback after an answer is selected |
| Explore cause and effect | A slider or input changes an authored simulation or calculator |
| Read background without crowding the slide | A term can expose a short explanation or a detail panel |
| Explore an architecture | An authored diagram can highlight routes or provide its own exploration controls |

These are authoring options, not automatic effects added to every slide. An L200 introductory deck benefits from a small number of understandable interactions: explain the situation, ask what will happen, change one thing, then discuss the result.

The primary result is **HTML for a browser**. A screenshot-based PowerPoint preserves a captured appearance but not live tabs, quizzes, or simulations. For editable PowerPoint text and shapes, use [aws-light-fcd](/docs/aws-content-plugin/skills/aws-light-fcd). Check the [export instructions](/docs/aws-content-plugin/skills/reactive-presentation#tools-and-exports) before choosing a static backup.

## Authoring model {#authoring-model}

Use `.md` files with `remarp: true` frontmatter. A single file can hold a short deck; a longer session can use `_presentation.md` plus numbered block files. `.remarp.md` remains supported for existing sources and editor integration.

**Frontmatter** is the settings block at the top of a source file, enclosed by separator lines. It identifies the document as Remarp and can specify its title, language, theme, and presentation blocks. A **block** is a group of slides, useful for a separate session or part of a longer talk.

Slides are separated by `---`. Directives such as `@type: tabs` precede content. `{.click}` reveals fragments. `:::notes` contains speaking guidance. HTML/CSS/script blocks support layouts and interactive tools beyond the small Canvas DSL.

A multi-file project typically contains these files:

```text
my-talk/
  _presentation.md   # Shared presentation settings and block list
  01-basics.md       # Slide content, interaction instructions and notes
  assets/           # Local logos, images and diagram specifications
  index.html        # Generated complete deck
  toc.html          # Generated session menu
  common/           # Generated runtime and styles
```

Edit the Markdown source to change the message or speaking notes. Keep the generated HTML and its resource folders together when sharing a working deck. If you are only presenting, ask the author for the ready-to-open link instead of rebuilding the project.

## Try a first presentation {#try-a-first-presentation}

### 1. Describe a small, concrete talk {#describe-your-talk}

After setting up the [content plugin](/docs/aws-content-plugin/installation) in your AI tool, send a request like this. Replace the topic, audience, time, and destination with your own choices.

> Use reactive-presentation to make a 15-minute L200 introduction to request processing for developers who are new to the topic. Write in the language we are using in this conversation and place the project in ./my-talk/. First show the slide titles and the interaction planned for each slide.
>
> Include a controllable three-step explanation, a comparison, and one quiz. Define unfamiliar terms when they first appear. Add notes that another person can use to present: what to say, when to press a key or click a control, what should change, and how to transition to the next slide.
>
> Validate and build the sources, check the actual browser behavior, and review the content. Give me the preview link and presentation instructions. Do not publish it yet.

You can also [follow the complete sample manually](/docs/aws-content-plugin/skills/reactive-presentation#first-deck). It supplies the source text, file locations, and build commands.

### 2. Check the result you receive {#check-the-result}

Ask for the source folder, the generated presentation or local preview link, and a short description of the interactions. A list of slide titles alone is not a finished deck.

Open the supplied link. Try one forward and backward reveal, one tab or quiz, and **N** for speaker notes in the standalone slide window. The [presenter's guide](/docs/aws-content-plugin/presenter-guide#start-your-presentation) explains which window the audience should see and how to rehearse.

### 3. Make one specific revision {#make-one-revision}

Give the author or AI the slide title, the problem, and the desired audience experience. For example:

> On the request-flow slide, explain what the client is before showing the worker. Reveal the three actions one at a time, and add a note telling the presenter when to pause for a question. Keep the theme, the other slides, and the quiz answer unchanged. Update the source and rebuild the complete deck.

Reopen or refresh the generated presentation after rebuilding. Check the changed behavior rather than assuming that a saved source file automatically updated every preview.

## Workflow {#workflow}

| Stage | What happens | What to check before moving on |
| --- | --- | --- |
| Plan | Choose audience, time, messages, and interactions | Each interaction helps explain something |
| Author | Write sources, notes, and local assets | Another speaker can follow the notes |
| Validate | Check the source structure and required authoring rules | Resolve errors that block compilation |
| Build | Produce the HTML and runtime resources | The intended complete deck and session menu exist |
| Rehearse | Open the real browser output | Keys, inputs, diagrams, notes, and themes behave as intended |
| Review and hand off | Check quality and prepare the recipient's instructions | The speaker has a running order and a checked backup |

Edit source and rebuild; generated HTML is not the durable editing source. Studio can write supported visual content edits back to Markdown, while ordinary previews do not provide that visual editing. Approximate Text Preview can still add or remove issue annotations. [Marp migration](./migration-from-marp.md) can provide a starting point, but its generated output still needs validation and review.

## Use VS Code or code-server {#editor-and-code-server}

The Remarp Slides extension offers three distinct views:

| View | Use it for |
| --- | --- |
| Approximate Text Preview | Check source order and wording quickly while typing |
| Build and Preview Compiled HTML | Check saved sources through the actual compiler |
| Open Design Studio | Select and edit supported source-backed elements while looking at a compiler-rendered snapshot |

Open the actual Remarp source file before choosing a command. In Studio, Design is for selecting/editing, and Play is for trying the slide's interactions. Preview and Studio are separate commands; opening a preview does not enable visual editing.

With **code-server**, the extension and Python compiler run on the server even though you use the editor in a browser. Compiler paths must exist on that server. A package installed only in desktop VS Code is not automatically installed in code-server. Check the installed extension version, workspace trust, and compiler configuration using the [step-by-step editor guide](./vscode-extension.md).

Use the standalone browser deck for the actual presentation and final interaction checks. Editor previews can have different restrictions on pop-ups, embedded documents, and resources.

## Hand the talk to another speaker {#present-and-share}

Give the recipient more than a deck URL. Include the audience and duration, the intended starting slide, useful speaker notes, the exact actions for interactive slides, quiz explanations, and a verified static backup.

Use the [ready-to-fill handoff message and running order](/docs/aws-content-plugin/presenter-guide#author-handoff). For each interactive slide, spell out **what to say → what to operate → what should change → how to reset → how much time to spend**. A new presenter should not need to reconstruct the explanation from the finished image.

## Next steps {#next-steps}

1. Presenting today: follow the [presenter's guide](/docs/aws-content-plugin/presenter-guide).
2. Creating your first deck: use the [complete authoring walkthrough](/docs/aws-content-plugin/skills/reactive-presentation).
3. Editing in a browser-based development environment: follow the [VS Code/code-server guide](/docs/remarp-guide/vscode-extension).
4. Writing and building by hand: start with [Quick start](/docs/remarp-guide/quick-start), then the [Build CLI](/docs/remarp-guide/build-cli).

## Related links {#related-links}

- [Quick start](./quick-start.md)
- [Frontmatter](./syntax/frontmatter.md)
- [VS Code and code-server](./vscode-extension.md)
- [Canvas DSL](./syntax/canvas-dsl.md)
