# CI workflow setup

One-time project setup for AI review mode — not part of the poll/fix/push loop, so it
does not need to load on every tick. Read this only when the AI Code Review CI
workflow itself needs to be installed or updated in a project.

AI review mode needs the AI Code Review GitHub Actions workflow: copy
`references/pr-review-workflow.yml` to the project's `.github/workflows/pr-review.yml`,
`scripts/review_gate.py` to `.github/scripts/pr-review-gate.py`, and
`scripts/review_format.py` to `.github/scripts/review_format.py` in the same trusted-base
change. Copy all three when updating; missing validators fail closed.
The runner must provide `python3` (standard library only) and Claude CLI.
Set the provider-specific `ANTHROPIC_MODEL` in repository variables,
ensure Bedrock access on the runner (or `ANTHROPIC_API_KEY` for direct API), and grant
`pull-requests: write` + `contents: read`.
