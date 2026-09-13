---
sidebar_position: 3
title: "Use co-agent"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="사용법-가이드" />
<span id="빠른-시작" />
<span id="패널-확인" />
<span id="모드별-사용-예시" />
<span id="1-review--멀티-ai-코드아키텍처-리뷰" />
<span id="2-decide--의사결정-보조" />
<span id="3-adr--의사결정-기록-협업" />
<span id="4-sync-context--ai-컨텍스트-동기화" />
<span id="5-consensus--자율-docplan구현-파이프라인" />
<span id="6-harness--host-설계--peer-구현--패널-리뷰" />
<span id="7-setup--패널-준비도-preflight" />
<span id="패널-튜닝-co-agentconfigure" />
<span id="자동-동기화-autosync" />
<span id="동작-원리" />
<span id="의장-원칙" />
<span id="다음-단계" />


# Use co-agent

## Start with readiness

```text
/co-agent:setup
/co-agent review the current diff
/co-agent decide between a queue and an event bus
/co-agent adr record the selected deployment model
```

Setup discovers each peer's plugin/CLI access path, performs a real probe, and records READY or the failure reason. A CLI binary existing on PATH is not proof that authentication or a model call works. Ordinary review, decide, and ADR work can continue solo with notice. Consensus and harness stop for setup when no peer is READY.

## Choose an implementation workflow

```text
/co-agent:consensus docs/spec.md
/co-agent:harness docs/spec.md
```

Consensus takes the document through planning, a plan gate, host implementation,
final review, and reporting. Harness keeps design, tests, verification, and commits
with the host. An eligible peer implements in isolated worktrees when READY;
otherwise the host implements. A READY raw-CLI reviewer is still mandatory. Kiro can
review but cannot be the harness implementer because it lacks the required write
sandbox. See the [harness contract](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/co-agent/commands/harness.md).

## Tune and inspect

```text
/co-agent:configure
/co-agent:configure set autosync on
/co-agent:configure set pr_autofix max_iterations 5
/co-agent:sync-context
```

Inspect effective settings before changing models or reasoning effort. Committed defaults merge with user and repository-local overrides; the current host determines the applicable paths and peer roster. Use the configuration output and canonical defaults rather than copying model IDs from an example.

## Read the result

The host sends comparable prompts, checks peer findings against source, separates confirmed problems from unsupported claims, and records peer failures. Large inputs can exceed a peer's configured context limit; missing coverage must be disclosed. Review verdicts are advisory and do not override repository CI or merge requirements.

Use [commands](/docs/co-agent/commands/) for settings and workflow entry points, and [PR autofix](/docs/co-agent/skills/pr-autofix) for the feedback loop.

## Related links

- [overview](/docs/co-agent/overview)
- [co agent](/docs/co-agent/skills/co-agent)
