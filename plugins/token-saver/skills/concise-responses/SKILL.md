---
name: concise-responses
description: Use when the user explicitly requests concise replies or reduced response verbosity.
disable-model-invocation: true
---

# Concise responses

## Scope

Use this manual entry when the user requests a brief response or wants the
token-saver policy in the current conversation. The automatic session hook normally
provides it after installation and host trust. This skill does not configure that
hook or change persistent preferences.

## Workflow

Apply the [shared response policy](references/policy.md) to this conversation.
Reuse it if already present; otherwise read it once. Complete the requested work,
check the relevant evidence and edge cases, then compress only the delivered prose.
Preserve user-selected models and reasoning effort.

## Output

| Request type | Response pattern | Preserve |
|---|---|---|
| Ordinary explanation, analysis, comparison or review | Short plain paragraphs | Material facts, findings and limitations |
| Explicitly detailed answer or procedure | Requested depth and structure | Every required step |
| Code, files or documents | Complete artifact | Usable implementation and validation |
| JSON, CI review or another required format | Exact requested schema | All required fields and severity sections |

## Examples

An ordinary explanation can answer directly:

```text
The default list is created once and reused. Use None as the default, then create
a new list inside each call.
```

A required machine-readable report keeps its structure:

```json
{"verdict":"BLOCKED","critical":[],"major":["Missing review for the current HEAD"]}
```

## Boundaries

Do not rewrite completed output through another model, hide blockers, skip tests,
or drop artifact content to make the answer shorter. Do not edit global instructions
or configuration to activate this skill. If automatic loading is unavailable, this
manual entry still applies the policy; it does not prove that the host trusted or
executed a hook. Follow explicit output requirements over the default prose style.
