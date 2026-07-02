# doc-sites/ — Documentation site (Docusaurus)

The project's public documentation & demo site, published to GitHub Pages. Source content
lives in `doc-sites/docs/` (Markdown/MDX), built into a static site under `doc-sites/build/`.

This is **only** the Docusaurus project. Internal, Claude-facing repo docs (ADRs, runbooks,
reference docs, superpowers specs/plans, architecture notes) live in `../docs/` instead —
see `../docs/CLAUDE.md`. Don't mix the two: this directory is public-site content only.

## Layout
```
doc-sites/
├── docs/            # Authored content (per-plugin overview/installation/agents/skills, intro, remarp-guide)
├── src/             # Docusaurus React components, CSS
├── static/          # Static assets (demos, images)
├── i18n/            # Translations
└── build/, .docusaurus/, node_modules/   # generated / deps (not edited by hand)
```

## Conventions
- **Per-plugin pages** in `doc-sites/docs/<plugin>/`: `overview.md`, `installation.md`, `agents/*.md`, `skills/*.md`. Mirror the plugin's actual agents/skills/commands.
- `intro.md` carries **plugin counts** (agents/skills/commands) — update it when a plugin's component count changes (the `/sync-docs` skill audits this; the counts also live in `../docs/architecture.md`, keep both in sync).
- Bilingual (KO/EN) where user-facing; match the repo's no-emoji / clear-prose style.
- Do **not** hand-edit `build/`, `.docusaurus/`, or `node_modules/`.

## Commands
```bash
cd doc-sites
npm install
npm run start     # local dev server
npm run build     # static build → build/
```

> This site documents the plugins; the plugins themselves live in `../plugins/`. Keep it
> consistent with `../CLAUDE.md` and `marketplace.json`. CI: `.github/workflows/deploy-docs.yml`
> (triggers on `doc-sites/**`, builds and deploys to GitHub Pages on push to `main`).
