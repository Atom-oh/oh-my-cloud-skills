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
python3 <script_path>/remarp_to_slides.py issues <project_dir> --json

# Single file
python3 <script_path>/remarp_to_slides.py issues <file.md> --json
```

**Script location lookup order:**
1. `plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py` in the current workspace
2. `scripts/remarp_to_slides.py`
3. Search for `**/remarp_to_slides.py` with Glob

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

### Step 3: Rebuild

After all issues are fixed, regenerate the HTML.

```bash
python3 <script_path>/remarp_to_slides.py build <project_dir>
```

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
4. remarp_to_slides.py build doc-sites/static/demos/my-session/ → regenerated HTML
```
