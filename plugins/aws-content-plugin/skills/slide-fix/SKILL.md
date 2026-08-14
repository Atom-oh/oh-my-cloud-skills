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

Reads `<!-- issue: content -->` annotations inserted into Remarp `.md` files, applies each issue to the corresponding source slide, and then removes the annotation.

---

## Workflow

### Step 1: Collect Issues

Find the project directory or file path, and collect the issue list with the `remarp_to_slides.py issues` command.

```bash
# Project directory (scans multiple .md files)
python3 <script_path>/remarp_to_slides.py issues <project_dir> --json

# Single file
python3 <script_path>/remarp_to_slides.py issues <file.md> --json
```

**Script location search order:**
1. `plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py` in the current workspace
2. `scripts/remarp_to_slides.py`
3. Search with Glob for `**/remarp_to_slides.py`

**JSON output format:**
```json
[
  {
    "file": "doc-sites/static/demos/my-session/01-intro.md",
    "block": "01-intro",
    "slide": 3,
    "title": "Architecture Overview",
    "issue": "Please add a diagram"
  }
]
```

### Step 2: Fix Each Issue

For each issue:

1. **Read the source file**: Read the `.md` file at the `file` path
2. **Locate the slide**: slides are separated by `---`; find the one matching the `slide` number (1-based)
3. **Apply the issue content**: apply the improvement described in the `issue` text to the slide
   - text edits, layout changes, content additions/removals, etc.
   - follow Remarp syntax rules (see the reactive-presentation SKILL.md)
4. **Remove the annotation**: after the fix is complete, remove the corresponding `<!-- issue: ... -->` comment

### Step 3: Rebuild

After all issues are fixed, regenerate the HTML.

```bash
python3 <script_path>/remarp_to_slides.py build <project_dir>
```

---

## Notes

- Process one issue at a time, and remove the annotation immediately after each fix
- Do not modify slides unrelated to the issue
- When editing `:::html` + `:::css` blocks, preserve the existing style patterns
- Convert `:::canvas` DSL to `:::html` when there are 5 or more boxes (per the reactive-presentation SKILL.md rule)
- If there are 0 issues, print "No issue annotations found." and exit

---

## Example

When the user runs `/slide-fix`:

```
1. remarp_to_slides.py issues doc-sites/static/demos/my-session/ --json
   → 3 issues found

2. Issue 1: slide 3 "Architecture Overview" → "Please add a diagram"
   → Add an architecture diagram to slide 3 of 01-intro.md
   → Remove <!-- issue: Please add a diagram -->

3. Issue 2: slide 5 "Performance" → "Change the numbers into a graph"
   → Convert slide 5's text figures in 01-intro.md into a :::html graph
   → Remove <!-- issue: Change the numbers into a graph -->

4. Issue 3: slide 2 "Overview" → "Split into tabs"
   → Restructure slide 2 of 02-deep-dive.md into a tab UI
   → Remove <!-- issue: Split into tabs -->

5. remarp_to_slides.py build doc-sites/static/demos/my-session/
   → HTML regeneration complete
```
