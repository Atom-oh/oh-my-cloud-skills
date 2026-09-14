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

# CI mode (exit 1 if any case < threshold)
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
| `build_check` | `remarp_to_slides.py build` succeeds | 0-100 | `project_dir` |
| `llm_judge` | Claude grades output quality | 0-N | `enabled`, `criteria`, `max_score` |

**Final score** = sum(scorer scores) / sum(scorer max_scores) * 100

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

**Status thresholds**: PASS >= threshold (default 85), REVIEW >= 70, FAIL < 70

**Exit codes**: 0 = all pass, 1 = some below threshold, 2 = execution error

## Isolation

Each case runs in an isolated temp directory (`/tmp/eval-{skill}-{case}-{ts}/`). The directory is automatically cleaned up unless `--verbose` is set, which preserves it for debugging.
