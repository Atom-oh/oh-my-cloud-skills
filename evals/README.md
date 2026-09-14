# Behavioral Eval Pipeline

E2E runtime testing for plugin skills. Complements `scripts/eval-skills.py` (structural/static analysis) by actually executing skills via `claude --print` and scoring the generated output.

## When to Use

| Tool | Purpose |
|------|---------|
| `scripts/eval-skills.py` | Static quality check: SKILL.md structure, references, token efficiency |
| `scripts/eval-skill-behavior.py` | Runtime behavior check: does the skill produce correct output? |

## Quick Start

```bash
# Dry-run (parse cases, no execution)
python3 scripts/eval-skill-behavior.py --skill reactive-presentation --dry-run

# Run a single case
python3 scripts/eval-skill-behavior.py --case evals/reactive-presentation/flow-layout.yaml

# Run all cases for a skill
python3 scripts/eval-skill-behavior.py --skill reactive-presentation

# CI mode (exit 1 for a failed build or any case below threshold)
python3 scripts/eval-skill-behavior.py --skill reactive-presentation --ci --threshold 70

# Enable LLM judge scorer (costs API tokens)
python3 scripts/eval-skill-behavior.py --skill reactive-presentation --llm-judge

# JSON output for programmatic consumption
python3 scripts/eval-skill-behavior.py --skill reactive-presentation --json

# Verbose mode (preserves temp dirs for debugging)
python3 scripts/eval-skill-behavior.py --case evals/reactive-presentation/basic-slides.yaml -v
```

## Directory Structure

```
evals/
├── README.md
└── <skill-name>/          # One directory per skill
    ├── basic-slides.yaml   # Eval case files
    ├── flow-layout.yaml
    └── anti-patterns.yaml
```

## YAML Case Format

```yaml
name: flow-layout                              # Case identifier
description: "What this case verifies"         # Human-readable description
skill: reactive-presentation                   # Skill name (matches evals/ subdir)
plugin: aws-content-plugin                     # Plugin directory name
timeout: 120                                   # Max seconds for claude --print

prompt: |                                      # Prompt sent to claude --print
  Create a 3-slide presentation about X.
  Use flow-h class. Output to ./output/

scorers:                                       # List of scoring checks
  - type: file_exists
    files: ["output/*.html"]

  - type: html_check
    target: "output/*.html"
    contains: ["flow-h", "SlideFramework"]
    not_contains: [":::css", "custom-flow"]

  - type: build_check
    project_dir: "output/"

  - type: llm_judge
    enabled: false                             # Opt-in only (--llm-judge flag)
    criteria:
      - "Uses flow-h for horizontal layout"
    max_score: 30
```

## Scorer Types

| Scorer | What It Checks | Score Range | Config Keys |
|--------|---------------|-------------|-------------|
| `file_exists` | Expected files exist (glob patterns) | 0-100 | `files` (list of glob patterns) |
| `html_check` | HTML contains/excludes patterns | 0-100 | `target`, `contains`, `not_contains` |
| `build_check` | Recognized Remarp source compiles into fresh HTML containing actual slide elements | 0-100 | `project_dir` |
| `llm_judge` | Claude grades output quality | 0-N | `enabled`, `criteria`, `max_score` |

**Final score** = sum(scorer scores) / sum(scorer max_scores) * 100, unless a build check fails. A failed build sets `total_score` to 0 and `build_failed` to `true`; the case fails regardless of other scores or the threshold. Individual scorer results and the summed `max_score` remain available for diagnosis.

Build checks compile into a new temporary output directory. Existing HTML, comments containing slide markup, or empty CSS cannot substitute for source and actual compiled slides. Compiler warnings retain the existing score penalty.

## Adding New Eval Cases

1. Create a YAML file in `evals/<skill-name>/`:
   ```bash
   evals/reactive-presentation/my-new-case.yaml
   ```

2. Define the prompt that exercises the behavior you want to verify.

3. Add scorers that check for expected output patterns.

4. Test with dry-run first:
   ```bash
   python3 scripts/eval-skill-behavior.py --case evals/reactive-presentation/my-new-case.yaml --dry-run
   ```

5. Run the actual eval:
   ```bash
   python3 scripts/eval-skill-behavior.py --case evals/reactive-presentation/my-new-case.yaml -v
   ```

## Adding Eval Cases for Other Skills

Create a new subdirectory matching the skill name:

```
evals/
├── reactive-presentation/   # Existing
├── architecture-diagram/    # New skill evals
│   └── basic-diagram.yaml
└── workshop-creator/        # New skill evals
    └── basic-module.yaml
```

The `plugin` field in YAML must match the plugin directory name (e.g., `aws-content-plugin`, `aws-ops-plugin`).

## Output Format

```
=== Skill Behavior Eval ===
Case                     | file_exists | html_check | build  | TOTAL | Status
-------------------------+-------------+------------+--------+-------+-------
basic-slides             |     100/100 |      85/100| 100/100|    95 | PASS
flow-layout              |     100/100 |      90/100| 100/100|    97 | PASS
anti-patterns            |      80/100 |      70/100|  80/100|    77 | REVIEW

Summary: 2 PASS, 1 REVIEW, 0 FAIL (threshold=85)
```

**Status thresholds**: PASS >= threshold (default 85), REVIEW >= 70, FAIL < 70. A failed build always reports FAIL.

**Exit codes**: 0 = all pass, 1 = a failed build or a case below threshold, 2 = input/discovery error

## Isolation

Each case runs in a disposable temporary directory. Setup commands and `claude --print` use that directory as their working directory; relative setup paths do not target the repository checkout. The workspace is removed unless `--verbose` preserves it for debugging, so fixtures do not need source-tree cleanup commands. This working-directory isolation is not a shell sandbox.

`--dry-run` parses cases and skips setup, Claude execution and scoring.
