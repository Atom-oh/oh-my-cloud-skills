# evals/

Behavioral evaluation fixtures and test cases for skills.

## Structure

```
evals/
├── reactive-presentation/   # Remarp slide generation test cases
│   └── *.yaml              # Individual test case definitions
└── README.md               # Eval framework documentation
```

## Running

```bash
python3 scripts/eval-skill-behavior.py --skill reactive-presentation --dry-run
python3 scripts/eval-skill-behavior.py --case evals/reactive-presentation/flow-layout.yaml
```
