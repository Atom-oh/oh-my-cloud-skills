---
sidebar_position: 0
title: "token-saver overview"
---
# token-saver

Keep conversational answers brief while preserving the full task. `token-saver`
supplies the same English response policy to Claude Code and Codex.

## What changes {#what-changes}

Answers lead with the useful result and omit introductions, repeated questions,
unnecessary recaps, and invitations for more detail. Ordinary analysis, review,
comparison, and summary requests also get a short answer.

Complete code, files, documents, requested procedures, detailed answers, and
required review or CI formats retain the length and structure they need. Material
findings, risks, limitations, reasoning, and verification remain part of the work.

## How it runs {#how-it-runs}

A single `SessionStart` command adds the packaged policy when the host invokes
that event. It makes no additional model calls, reads no transcript, and changes
no user or project settings. The manual `concise-responses` skill applies the same
policy when automatic hooks are unavailable.

## Limits {#limits}

The policy adds a small amount of input context. It does not impose a hard token
budget, change the selected model or effort, or guarantee a billing reduction.
Actual behavior depends on the model, task, explicit requests, and other applicable
instructions. Hook support and trust are controlled by the host.

## Get started {#get-started}

See [installation and verification](installation.md). The maintained policy and
hook live under `plugins/token-saver/`; both host packages ship in this marketplace.
