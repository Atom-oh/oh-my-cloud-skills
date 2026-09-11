---
name: slide-fix
description: "Remarp 슬라이드 이슈 어노테이션(<!-- issue: -->)을 읽고 수정 반영. Triggers: /slide-fix, issue 반영, slide fix, 이슈 수정, 슬라이드 이슈, fix slide issues, apply issue annotations"
allowed-tools:
  - Read
  - Edit
  - Glob
  - Grep
  - Bash
---

# Slide Fix Skill

Reads `<!-- issue: content -->` annotations inserted into Remarp `.md` files, applies each issue to the source slide, then removes the annotation.

---

## Workflow

### Step 1: Collect Issues

Locate the project directory or file path, and collect the issue list with the `remarp_to_slides.py issues` command.

```bash
# Project directory (scans multiple .md files)
python3 "${CLAUDE_PLUGIN_ROOT}/skills/reactive-presentation/scripts/remarp_to_slides.py" issues <project_dir> --json

# Single file
python3 "${CLAUDE_PLUGIN_ROOT}/skills/reactive-presentation/scripts/remarp_to_slides.py" issues <file.md> --json
```

**Script location:** use the bundled sibling `reactive-presentation` skill in this
plugin installation. Resolve the plugin root from the loaded skill's location; the
consumer workspace does not need a marketplace checkout or its own copy of the script.

**JSON output format:**
```json
[
  {
    "file": "doc-sites/static/demos/my-session/01-intro.md",
    "block": "01-intro",
    "slide": 3,
    "title": "Architecture Overview",
    "issue": "다이어그램을 추가해주세요"
  }
]
```

### Step 2: Fix Each Issue

For each issue:

1. **Read the source file**: Read the `.md` file at the `file` path
2. **Locate the slide**: separate slides by the `---` delimiter and find the slide corresponding to the `slide` number (1-based)
3. **Apply the issue content**: apply the improvement described in the `issue` text to the slide
   - Text edits, layout changes, content additions/removals, etc.
   - Comply with Remarp syntax rules (see reactive-presentation SKILL.md)
4. **Remove the annotation**: after the fix is applied, remove the corresponding `<!-- issue: ... -->` comment

### Step 3: Validate

After all issues are fixed, run the Remarp rejection loop:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/reactive-presentation/scripts/remarp_to_slides.py" validate <project_dir> --json
```

Read the findings and fix every CRITICAL issue before building. The validator can
return exit code 0 with findings, so shell success alone does not pass this gate.

### Step 4: Rebuild

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/reactive-presentation/scripts/remarp_to_slides.py" build <project_dir>
```

### Step 5: Quality Review

Submit the rebuilt artifacts to `content-review-agent` (`review content at [path]`)
before declaring completion. Apply the reviewer's rubric from
`${CLAUDE_PLUGIN_ROOT}/agents/content-review-agent.md`, fix REVIEW/FAIL findings,
and obtain PASS for the final artifacts. Substantive source changes invalidate the
previous artifact review; rebuilding alone is not a quality review.

---

## Caveats

- The goal is to "apply only the requested issues precisely": do not modify slides unrelated to an issue, and do not leave the annotation behind once an issue has been applied
- When editing `:::html` + `:::css` blocks, preserve existing style patterns; canvas complexity rules follow reactive-presentation's `references/authoring-rules.md` (validated by `remarp_to_slides.py validate`)
- If there are 0 issues, report that there is nothing to fix and exit

---

## Example

```
1. remarp_to_slides.py issues doc-sites/static/demos/my-session/ --json → found 3 issues
2. slide 3 "Please add a diagram" → added a diagram to slide 3, removed the annotation
3. slide 5 "Change the numbers to a graph" → converted to a :::html graph, removed the annotation
4. remarp_to_slides.py validate doc-sites/static/demos/my-session/ --json → zero CRITICAL findings
5. remarp_to_slides.py build doc-sites/static/demos/my-session/ → regenerated HTML
6. content-review-agent → final artifacts PASS
```
