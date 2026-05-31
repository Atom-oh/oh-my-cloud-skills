# docs/ — Documentation site (Docusaurus)

The project's documentation & demo site. Source content lives in `docs/docs/`
(Markdown/MDX), built into a static site under `docs/build/`.

## Layout
```
docs/
├── docs/            # Authored content (per-plugin overview/installation/agents/skills, intro, remarp-guide)
├── src/             # Docusaurus React components, CSS
├── static/          # Static assets (demos, images)
├── decisions/       # ADRs (ADR-NNN-*.md)
├── runbooks/        # Operational runbooks
├── architecture.md  # System architecture (bilingual KO/EN) — keep in sync with plugin inventory
├── i18n/            # Translations
└── build/, .docusaurus/, node_modules/   # generated / deps (not edited by hand)
```

## Conventions
- **Per-plugin pages** in `docs/docs/<plugin>/`: `overview.md`, `installation.md`, `agents/*.md`, `skills/*.md`. Mirror the plugin's actual agents/skills/commands.
- `intro.md` and `architecture.md` carry **plugin counts** (agents/skills/commands) — update them when a plugin's component count changes (the `/sync-docs` skill audits this).
- Bilingual (KO/EN) where user-facing; match the repo's no-emoji / clear-prose style.
- Do **not** hand-edit `build/`, `.docusaurus/`, or `node_modules/`.

## Commands
```bash
cd docs
npm install
npm run start     # local dev server
npm run build     # static build → build/
```

> Docusaurus content is documentation *about* the plugins; the plugins themselves live in `../plugins/`. Keep this site consistent with `../CLAUDE.md` and `marketplace.json`.
