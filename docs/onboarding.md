# Contributor onboarding

This marketplace supports Claude Code and Codex. Read the root and scoped
`CLAUDE.md`/`AGENTS.md` instructions before editing. The [architecture inventory](architecture.md)
lists eight plugins: 70 shared procedures, 68 generated Codex entries and 24 plugin
hook commands. Source, entry and CI-cell counts describe different things.

## Setup

Use Git, Python 3, and the host CLI you intend to test. The Docusaurus site requires
Node.js 20 or newer (`doc-sites/package.json`); other tools may have their own
dependencies. Provider credentials are needed only for workflows that call providers.

```bash
git clone https://github.com/Atom-oh/oh-my-cloud-skills.git
cd oh-my-cloud-skills
./scripts/setup.sh

# Claude Code: load a source plugin for local testing.
claude --plugin-dir ./plugins/aws-content-plugin
```

Setup installs site dependencies and local Git hooks, and may create `.env` from
`.env.example`. Run the checks below explicitly; setup is not validation evidence.
For Codex installation, discovery and hook trust, follow
[Codex runtime verification](reference/codex-runtime-verification.md).

Build the public site from its own directory:

```bash
cd doc-sites
npm ci
npm run build
```

## Verify from the repository root

```bash
bash tests/run-all.sh
python3 scripts/test-plugins.py
python3 scripts/test-codex-plugins.py
python3 scripts/sync-codex-plugins.py --check
python3 scripts/eval-skills.py
```

Record failures and distinguish new regressions from an independently established
baseline. A known local limitation does not waive a required CI check.
For host adaptation, installation or hook changes, also run the applicable runtime
checks described in the runtime guide; static inventory checks do not prove discovery
or hook execution.

## Change workflow

1. Edit shared source procedures or their owning helpers. Source skills use
   `description` for trigger keywords; a separate `triggers:` field is inert.
2. If generated Codex files are affected, update the owning `scripts/codex/` adapter
   as needed and run `python3 scripts/sync-codex-plugins.py`. Do not hand-edit overlays.
   Preserve the [project-init upstream boundary](reference/project-init-upstream-sync.md).
3. Update affected maintained docs in concise English. Preserve dated ADR rationale,
   and record changed authority or scope in a new ADR. Functional literals and the
   language of artifacts requested by users remain independent of doc language.
4. Run relevant tests and every applicable [review gate](reference/review-routing.md).
   Before merge, require latest-HEAD AI review, no unresolved Critical/Major findings,
   complete configured coverage, separate Codex package validation, and branch
   protection checks. Failed or missing reviews need repair/retry, not a PASS.
5. For a release, update every plugin's manifests and both marketplaces to one
   version, regenerate adapters, validate, then tag the approved release commit
   `v{version}`. Feature edits do not by themselves require a release tag.

## Concepts and troubleshooting

| Surface | Meaning / check |
|---|---|
| `agents/*.md` | Claude specialist definitions; Codex exposes procedural entry skills |
| `skills/*/SKILL.md`, `commands/*.md` | Shared procedures; generated inventories map them to Codex names |
| Plugin hooks | Host event handlers; confirm support and trust before claiming execution |
| Project-init hook templates | Separately installed project configuration, excluded from plugin-hook totals |
| Missing co-agent peers | Review/decide/ADR may report solo mode; consensus/harness require READY raw-CLI peers |
