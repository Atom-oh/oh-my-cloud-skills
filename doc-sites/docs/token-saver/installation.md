---
sidebar_position: 1
title: "Install token-saver"
---
# Install token-saver

## Claude Code {#claude-code}

```text
/plugin marketplace add Atom-oh/oh-my-cloud-skills
/plugin install token-saver@oh-my-cloud-skills
```

For local development from a repository checkout:

```bash
claude --plugin-dir ./plugins/token-saver
```

Use the host's hook controls to inspect and trust the plugin, then start a new
session. Manual activation is available with `/token-saver:concise-responses`.

## Codex {#codex}

Install `token-saver` from this repository's marketplace through `/plugins`.
Enable hook support if required by your Codex version, inspect the plugin's hook
in `/hooks`, grant trust, and start a new thread. Installation alone does not prove
the hook ran.

For manual activation, select `token-saver:concise-responses` from `/skills` or the
skill picker. The generated package resolves the shared policy from the installed
plugin location.

## Verify {#verify}

Automatic use requires Python 3; the generated Codex hook bridge also uses Bash.
Confirm that the host reports the plugin's `SessionStart` hook as enabled and
trusted. Compare an ordinary explanation with an explicitly detailed or
schema-constrained request: prose should stay short while required content and
format remain complete.

Offline checks from the repository root:

```bash
python3 tests/structure/test-token-saver.py
python3 scripts/test-plugins.py -p token-saver
python3 scripts/test-codex-plugins.py -p token-saver
python3 scripts/sync-codex-plugins.py --check --plugin token-saver
```

These checks validate packaging and hook behavior, not a universal savings rate.

## Existing global rules {#existing-global-rules}

If you already placed the same style rule in `~/.codex/AGENTS.md` or
`~/.claude/CLAUDE.md`, confirm plugin loading before removing only that matching
section. Keep unrelated instructions. Otherwise, both copies may enter context.
The plugin never edits or removes these files.

## Disable or remove {#disable-or-remove}

Disable the plugin in the host's plugin manager and start a new session. To remove
it, use `/plugin uninstall token-saver@oh-my-cloud-skills` in Claude Code or
uninstall it through Codex `/plugins`. Existing global rules are independent and
continue to apply until you change them.
