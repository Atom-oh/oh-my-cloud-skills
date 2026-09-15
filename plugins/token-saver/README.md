# token-saver

Concise responses with complete work. The plugin supplies a small shared policy
when the host starts or resumes a session, without reducing reasoning effort,
verification, required reports, or artifact completeness.

## Use

Install `token-saver` from the `oh-my-cloud-skills` marketplace in Claude Code or
Codex, enable its hook through the host's trust controls, and start a new session.
Claude Code supports `/plugin install token-saver@oh-my-cloud-skills`; Codex users
can select it in `/plugins`.

For manual activation, use `/token-saver:concise-responses` in Claude Code, or
select `token-saver:concise-responses` from Codex's skill picker. This also works
when automatic hooks are unavailable.

The only hook is a synchronous `SessionStart` command. It emits at most 2 KiB of
packaged policy as `additionalContext`. Python 3 is required; the generated Codex
bridge also uses Bash. Supported events and hook trust depend on the host version.
See the [public installation guide](../../doc-sites/docs/token-saver/installation.md).

## Boundaries

- No extra model calls, output-rewriting loop, transcript reads, telemetry, or
  changes to global/project configuration.
- Explicit output formats, review/CI schemas, complete code/files/documents, and
  requests for detailed answers take priority over short prose.
- The policy adds some input context. It is guidance, not a hard output-token cap
  or a guarantee of lower billing or unchanged accuracy on every task.
- Disable the plugin through the host and start a new session to stop its hook.
  Independently installed global instructions remain in effect.

If the same rule is already in `~/.codex/AGENTS.md` or `~/.claude/CLAUDE.md`, confirm
the plugin is loaded before removing that matching style section to avoid duplicate
context. Preserve unrelated instructions. The plugin does not migrate those files.

## Maintained source

`skills/concise-responses/references/policy.md` is shared by
`hooks/session-start.py` and the manual skill.
Regenerate the Codex overlay through `scripts/sync-codex-plugins.py`; do not edit
generated files alone.

Inspired by the [concise-response reference](https://d32q3lzpy95cdh.cloudfront.net/).
Its reported percentages are not measurements or guarantees for this plugin.
