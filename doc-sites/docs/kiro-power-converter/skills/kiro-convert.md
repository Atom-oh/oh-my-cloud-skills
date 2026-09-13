---
sidebar_position: 1
title: "Kiro convert skill"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="kiro-convert-스킬" />
<span id="기본-정보" />
<span id="트리거-키워드" />
<span id="대화형-워크플로우" />
<span id="phase-1-소스-선택" />
<span id="phase-2-플러그인-탐색" />
<span id="phase-3-대상-선택" />
<span id="phase-4-변환" />
<span id="phase-5-검증" />
<span id="phase-6-다음-단계" />
<span id="사용-예시" />
<span id="기본-사용" />
<span id="키워드로-트리거" />
<span id="전체-명령어-예시" />
<span id="참조-문서" />


# Kiro convert skill

Convert a plugin into a Kiro Power with a manifest, steering, supported hooks, MCP
configuration, and assets. Standalone `--skill` conversion instead emits steering
Markdown; it does not create a Power manifest, MCP configuration or hooks.

## Local conversion {#local-conversion}

Run from a checkout of this marketplace:

```bash
python3 plugins/kiro-power-converter/skills/kiro-convert/scripts/convert_plugin_to_power.py --source ./plugins/aws-ops-plugin --output /var/tmp/aws-ops-power --target export
```

For plugin conversion, add `--preserve-skills` to retain skill directories and their
references/scripts. GitHub sources use `--git-url`, with `--plugin-path` and
`--branch` when needed. `--skill` accepts individual skill directories and returns
through the separate steering-only path; `--preserve-skills` does not apply there.

## Marketplace selection {#marketplace-selection}

List candidates with `--marketplace --search "ops"`, then convert the intended path using `--source`. Exact-name conversion must not guess between multiple installations or cached versions.

## Validate and deliver {#validate-and-deliver}

For plugin packages, POWER.md needs supported metadata; steering needs valid `inclusion` and `globs` when file-matched; MCP secrets become environment references; hooks must be valid Kiro JSON. For standalone skill output, validate the steering Markdown. Report source/target paths, produced artifact counts, required variables, skipped features, and manual installation checks.

[Full workflow](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/kiro-power-converter/skills/kiro-convert/SKILL.md)
