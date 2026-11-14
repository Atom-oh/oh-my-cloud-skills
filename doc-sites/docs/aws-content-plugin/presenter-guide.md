---
sidebar_position: 3
title: "Presenting a deck someone else created"
---

# Presenting a deck someone else created

Use this guide when someone sends you a reactive-presentation slide deck to present. A **deck** is the complete set of slides. You can present a published deck in a browser; you do not need Claude Code, Codex, the plugin, or knowledge of Markdown.

**First time? Follow [Start your presentation](#start-your-presentation), rehearse [the interactions](#operate-interactive-slides), and keep [the recovery table](#recover-during-a-talk) nearby.** The author should send you the presentation link and a slide-by-slide running order using the [handoff template](#author-handoff).

These instructions describe the current default controls. A deck can customize its keys and interactions, and an older deck keeps the version with which it was built. Use the author's tested instructions when they differ.

## What to ask the author for {#what-you-need}

| Ask for | Why you need it |
| --- | --- |
| Presentation link and starting slide or session | Opens the correct material at the intended starting point |
| Audience, duration, and learning objectives | Tells you how much background to explain and where to spend time |
| Speaker notes and a slide-by-slide running order | Gives you the explanation, interaction sequence, quiz answer, and transition for each slide |
| Tested desktop browser and any changed keys | Lets you rehearse in the same environment |
| Internet-dependent demos and their alternatives | Gives you something to show if the network or a live demo fails |
| A checked PDF or PowerPoint backup | Lets you finish with a static explanation if the interactive deck becomes unavailable |

Prefer the ready-to-open presentation link. If you receive a ZIP, extract the complete folder and follow the author's tested opening instructions. Keep **common/**, **assets/**, and **archify/** beside the HTML when supplied. Moving only an HTML file can lose styles, images, or diagrams. Ask for a working link if no opening instructions were included.

The main slides are usually **index.html**. **toc.html** is the session menu, where you choose a block of the presentation. Neither filename is a universal requirement; use the link supplied for your talk.

## Start your presentation {#start-your-presentation}

### 1. Open the slides and try one move {#open-the-slides}

1. Open the supplied link in the desktop browser the author tested.
2. If a session menu appears, select the session you are presenting.
3. Click an empty part of the slide so the keyboard controls reach the presentation.
4. Press **Right** once, then **Left** once. A bullet may appear or disappear without the slide number changing. This is normal: some slides reveal their explanation in steps.
5. Check that the text, images, and diagrams load before connecting to the audience display.

If you are rehearsing on a phone or tablet, verify touch controls separately. The two-window setup below is intended for a desktop browser.

### 2. Open the private presenter window {#open-presenter-window}

Press **N** in the slide window. A second window, **Presenter View**, opens with the current slide, next slide, speaker notes, and an elapsed timer. If nothing opens, allow pop-ups for the presentation site and press N again.

Keep the original slide window open. The presenter window is connected to it. Opening a second copy of the presentation link is not a replacement for the presenter window opened with N.

![Audience slide window showing a sample request-flow slide](/img/reactive-presentation/audience-window.png)

[Open the audience screenshot at full size](/img/reactive-presentation/audience-window.png).

*The original window is the audience view. Screenshots in this guide use the tutorial's sample deck; your titles and content will differ.*

![Presenter View with Current Slide, Next Slide, Speaker Notes, and timer](/img/reactive-presentation/presenter-window.png)

[Open the presenter screenshot at full size](/img/reactive-presentation/presenter-window.png).

*The second window is your presenter view. Keep it on your own display.*

### 3. Choose the correct window to show {#choose-the-shared-window}

| Presentation setup | Put in front of the audience | Keep for yourself |
| --- | --- | --- |
| Projector or second monitor | Original slide window on the audience display | Presenter View on your laptop |
| Video meeting | Share the original slide window or its browser tab | Presenter View as a separate, unshared window |
| One display with no private window space | Original slide window | Use a separate copy of your speaking notes if needed |

For two physical displays, use **extended displays** so they can show different windows. Mirroring shows the same desktop on both screens. Move the original slide window to the audience display, click inside that window, and press **F** for full screen.

In a video meeting, check the meeting application's share preview, or ask a colleague to confirm that only the slides are visible. Sharing the entire desktop can also show your presenter notes when you bring that window forward.

### 4. Check synchronization and return to the start {#check-sync}

In Presenter View, click its title area outside the notes editor and press **Right**. Confirm that the audience window advances the same slide or reveal step. Press **Left** to reverse it. Then return to the intended first slide using **Home** in the slide window, or find it through the session menu, search, or sidebar.

Close unrelated copies of the deck before the talk. Rehearse with the exact windows you will use. Merely returning to the first slide does not reset every quiz, input widget, or annotation; use the reset behavior the author documented.

## The controls you need first {#essential-controls}

Use these keys in the **original slide window**, after clicking an empty area. Plain letter keys do not need Ctrl, Command, or Alt. If a letter key does not respond while you are typing with an input method, switch to English input and try again.

| Key | What you will see | When to use it |
| --- | --- | --- |
| Right / Space / PageDown | Reveals the next item; moves to the next slide when no reveal remains | Normal forward presentation |
| Left / PageUp | Reverses a reveal where supported, then moves to the previous slide | Repeat an explanation |
| Down / Up | Operates the slide's registered interaction, such as Canvas steps or tabs; behavior depends on the slide | Follow the author's interaction instructions |
| N | Opens or focuses Presenter View | Read notes while presenting |
| F | Enters or leaves full screen | Show the audience only the slides |
| G | Opens or closes the slide overview grid | Look over the slides; use search or the sidebar to jump |
| S | Shows or hides the thumbnail sidebar outside full screen | Select a thumbnail to move to that slide |
| Home / End | Moves to the first / last slide | Return to the beginning or closing |
| T | Switches the overall light/dark theme | Match the room or projector; a slide with a fixed theme stays unchanged |
| Escape | Exits a drawing mode or an open view, depending on the current state | Recover the normal slide view |

**A clicker can send different keys.** Test its forward and back buttons on both a plain slide and an animated slide. If it advances slides but cannot operate a Canvas sequence, use the keyboard's Down/Up keys for that sequence.

The presenter window supports navigation and reveal keys too. Its bottom **Previous / Next** buttons move by whole slides; they do not substitute for the keyboard's step-by-step reveal. Use the keyboard when the explanation depends on revealing one item at a time. Full screen, overview, and search should be operated from the original slide window.

## Read and adapt your speaker notes {#use-speaker-notes}

| Presenter View area | How to use it |
| --- | --- |
| Current Slide | Check what the audience is seeing, including revealed items |
| Next Slide | Prepare your transition; this preview is not an interactive control |
| Speaker Notes | Read the explanation, examples, questions, and cues prepared by the author |
| Target | The authored timing for this slide, when supplied |
| Top timer | Elapsed time since Presenter View was first opened for the current page session; it is not a per-slide countdown |
| Dividers between panels | Drag to give the notes or current slide more space |

Read the notes before rehearsing. A good sequence is **say the point → ask the question → operate the slide → explain the result → move on**. Do not reveal a quiz answer while you are still asking the audience to choose.

On slides with steps, an orange ↓ badge in the notes marks where to press Down, and the status line under the arrow buttons tells you whether the slide still has steps, for example ↓ more steps (now 1/3), or whether the next press moves to the next slide. See [Step cue and Down marks](../remarp-guide/keyboard-shortcuts.md#step-cue).

If only the summary is visible, scroll inside the notes area to read the explanation below it. You can also drag the horizontal divider upward to give the notes more space.

To adapt wording for yourself:

1. Select **Edit notes**, or double-click the notes.
2. Change the text.
3. Select **Save notes**, or press **Ctrl+Enter / Command+Enter**. Escape cancels an edit still in progress; leaving the editor also saves it.
4. Click outside the editor before using presentation keys. While editing, arrow keys belong to the text field.

**Edited** marks a local change. **Reset to original** restores the author's notes for that slide. Your edits are stored in that browser and do not update the author's source, another computer, or the exported PowerPoint. Send wording that should become part of the shared deck back to the author. Authored cues and timing remain unchanged when you edit the note text.

The elapsed timer starts during rehearsal if you open Presenter View then. Do not treat it as the official session start; use a separate clock if necessary. There is no timer-reset button in the current presenter toolbar.

## Operate interactive slides {#operate-interactive-slides}

First, exit the pen or magnifier mode so clicks can reach the slide. The controls below apply when the author included that type of interaction.

### Text that appears in steps {#stepwise-text}

Press **Right** or **Space** once, explain the new item, then press again. Keep an eye on the slide number: it stays the same while items appear. Use **Left** to reverse supported reveal steps. After the last reveal, the next forward key moves to the next slide.

### Flow animation or Canvas diagram {#canvas-flows}

For a standard step-controlled Canvas slide, use **Down** to advance and **Up** to go back. Explain what moved, appeared, or changed before advancing again. A slide may also have its own play, pause, or reset control; use the author's running order for those controls.

Do not hold down a navigation key: it can run through the teaching steps or move beyond the slide. Confirm in rehearsal how the last step behaves. A moving picture does not always mean it is playing automatically.

### Tabs and comparisons {#tabs-and-comparisons}

Click a tab or the slide's comparison control, describe the selected alternative, and switch to the next one. Standard tabs also use **Down / Up** to cycle. A changed tab is not necessarily a changed slide.

When comparing two designs, first tell the audience what to look for, such as which component is waiting. Switching rapidly without explaining the difference makes the interaction harder to follow.

### Quizzes {#quizzes}

1. Read the question and give the audience time to choose.
2. Ask for an answer verbally or through the meeting tool you are using.
3. Click the chosen answer in the slide window.
4. Read the displayed feedback and use the author's explanation to discuss it.

The slide's click is a local demonstration; it is not a shared audience-voting system. The author's quiz implementation determines retry and reset behavior. Check the correct answer and how to repeat the quiz before presenting. Do not assume that moving away and back clears an earlier selection.

### Sliders, simulations, and calculators {#input-widgets}

Say which input you will change and what you expect. Move one slider or change one field, point out the resulting value, and explain why it changed. Use the visible **Reset** control if provided to return to the prepared example.

After using an input, click an empty slide area before pressing navigation keys. Some slides have no reset control; the author should supply their initial values and recovery procedure. Reloading the whole page is not a universal reset and can lose unsaved drawing marks.

### Explanations and explorable architecture diagrams {#details-and-diagrams}

An emphasized term may show a short explanation on hover or keyboard focus, and clicking it may open a detail panel. Close the panel with its close button when finished. Only terms authored as controls behave this way.

An Archify diagram is an interactive page embedded inside the slide. Use its visible controls to explore the route or zoom. After clicking inside it, click the slide area outside the diagram to return keyboard control to the presentation. The diagram's keyboard focus can otherwise keep arrow keys from reaching the slide.

For sliders, quizzes, embedded diagrams, or controls that do not respond in the presenter preview, operate them in the original slide window. The preview forwards supported clicks; it is not a second fully independent copy of every interactive widget.

## Point, draw, and magnify {#point-and-draw}

These controls are optional aids during explanation. Try them before relying on them in a talk.

| Key | Action |
| --- | --- |
| P | Turns on the laser; pressing it again while already in laser mode turns drawing mode off |
| O | Turns on the pen for persistent marks during this page session |
| I | Turns on the highlighter |
| U | Turns on the stroke eraser |
| Y | Turns on the magnifier; move the pointer over what you want to enlarge |
| C | Clears all drawing marks on the current slide |
| 1 / 2 / 3 | Selects thin / medium / thick strokes; in magnifier mode selects 2× / 3× / 4× |
| Escape | Turns drawing mode off when the key reaches the page |

With a drawing tool active, drag to draw. Laser marks normally disappear after three seconds; pen and highlighter marks remain for this page session. The presenter preview and audience window share those marks. They are not saved into the deck, and reloading the page loses them.

**Before clicking a quiz, tab, or diagram, turn drawing mode off.** From pen, highlighter, eraser, or magnifier mode, press P twice: the first press switches to the laser and the second turns the mode off. If you are already in laser mode, press P once. Merely changing from a pen to a laser does not restore slide clicks.

In full screen, Escape behavior varies by browser and focus. If it does not leave the presentation, click an empty slide area and try again, hold Escape, or use the browser's exit-full-screen control. You can find colors and browser-specific details in the [keyboard reference](/docs/remarp-guide/keyboard-shortcuts).

## Find or skip a slide {#find-or-skip}

- **Search:** close the overview if it is open. With the search feature present, press **Ctrl+K / Command+K**, or **/** outside a text field. Enter a title or phrase, use Up/Down to choose a result, and press Enter. Escape closes search.
- **Sidebar:** if the overview is open, close it with **G** first. Leave full screen in the original slide window with **F**, then press **S** if the thumbnail sidebar is hidden. Click the thumbnail of the slide you need.
- **Overview:** **G** opens or closes the slide grid. In the current version, selecting a grid thumbnail does not reliably jump to that slide. Use search or the sidebar for the actual move.
- **H**, or **Hide slide** in Presenter View, toggles whether normal forward/back navigation skips the current slide. A hidden slide remains visible in overview and reachable through search or the sidebar. It is not deleted.

Hidden-slide choices are remembered in this browser. If a slide unexpectedly disappears from the running order, find it through search or the sidebar and toggle H again, or use the sidebar's eye control. Agree on optional slides with the author before the talk instead of hiding unfamiliar material during the presentation.

## Rehearse once before the audience joins {#rehearsal}

Allow about five minutes for this operational check, in addition to rehearsing the content itself. Use the actual computer, browser, and display-sharing arrangement for the talk.

1. Open the supplied link and confirm the intended session and starting slide.
2. Open Presenter View with N. Confirm that notes are readable and are not in the audience share.
3. Advance one text reveal and one Canvas step, if present, then reverse them.
4. Try one tab, one quiz answer, and one input widget from the running order. Restore their intended starting states using the author's instructions.
5. Try P, make a laser mark, turn it off, and confirm that a normal slide control works again.
6. Find a slide through search or the sidebar, return to the start, and check which slides are hidden.
7. Open the static backup and confirm how you will reach it during a failure.

Ask the author to fill in any missing interaction instructions before presenting. Knowing the keys does not replace knowing what to say at each step.

## Recover during a talk {#recover-during-a-talk}

| What happened | What to do now |
| --- | --- |
| N does not open notes | Click the slide background, switch to English input if needed, and allow pop-ups for this site. Check whether Presenter View is already open behind another window |
| The audience sees notes | Stop sharing, select the original slide window or tab, and check the meeting preview before continuing |
| Right changes content but not the slide number | Finish the current reveal sequence; use one keypress per explanation |
| Arrow keys seem stuck | Finish editing notes or an input, close search, or click outside the embedded diagram; then click the slide background |
| Quiz or tab clicks do nothing | Turn pen/magnifier mode off. Try the control in the original slide window |
| A slide is skipped | Find it through search or the sidebar and check its hidden state with H or the eye control |
| Presenter View and the slides disagree | Close extra copies. Keep the intended original slide window open and reopen its presenter window with N |
| F does nothing in Presenter View | Click the original slide window and press F there |
| An image or architecture diagram is missing | Check the connection and the author's opening instructions. Use the static backup if it cannot be restored quickly |
| Full screen will not exit | Click outside inputs/iframes, then try Escape or the browser's full-screen exit control |
| A quiz or slider is still in the rehearsal state | Use its documented reset or initial values; ask the author if none were supplied |

If you switch to PDF or PowerPoint, continue with a verbal explanation of the interaction. Tabs, quizzes, and sliders in a screenshot-based export do not remain interactive. Check the backup in advance: browser PDF export can replace Canvas content with a placeholder.

## Author: send a complete handoff {#author-handoff}

Send this guide **with** the deck link. A presenter should be able to find it without searching the plugin's authoring documentation. Copy and fill in the message below; replace every bracketed item before sending it.

> Here are the slides for your session.
>
> Presentation: [presentation URL]\
> Presenter instructions: [URL of this presenter guide]\
> Audience and assumed background: [audience]\
> Duration, session, and starting slide: [duration / session / slide title]\
> Main points to leave with the audience: [two or three points]\
> Tested browser and changed controls: [browser / changes, or defaults]\
> Optional or hidden slides: [slide titles, or none]\
> Interactive-slide running order and quiz explanations: [document or notes location]\
> Internet-dependent parts and alternatives: [demo / alternative, or none]\
> Checked static backup: [PDF or PowerPoint URL]\
> Content questions or problems: [contact]

Provide a running order like this, replacing the example titles and actions with those in the actual deck:

| Slide title / number | Say or ask | Operate | Expected result / reset | Time |
| --- | --- | --- | --- | --- |
| Request path / [number] | Ask what happens after Save | Right once for each of three text reveals | Client → worker → result; Left reverses the reveals | 3 min |
| Architecture / [number] | Trace one request from entry to completion | [Exact diagram control and click order] | [Highlighted route and how to restore the initial view] | 4 min |
| Knowledge check / [number] | Ask who starts the request | Wait for answers, then click [correct choice] | [Feedback, explanation, and tested retry/reset procedure] | 2 min |

Keep each slide's speaker notes useful to someone who did not create it: **main message, spoken explanation, action cue, expected visible change, timing, and transition to the next slide**. Identify illustrative figures and give the source or limits of factual claims. The presenter should not have to infer an animation sequence from a finished picture.

The presenter window keeps notes off the audience display; it is not access control. Published HTML may contain the source notes. Remove confidential material before sharing, and include any local rehearsal edits in the maintained source if the next presenter needs them.

For creation, rebuilding, and export procedures, return to the [authoring guide](./skills/reactive-presentation.md).
