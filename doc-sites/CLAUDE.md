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
├── i18n/ko/         # Korean guide and UI translations
├── src/             # Docusaurus React components, CSS
├── scripts/, tests/ # Locale coverage, source parity and redirect regression checks
├── static/          # Static assets (demos, images)
├── plugins/         # Build-time compatibility redirects
└── build/, .docusaurus/, node_modules/   # generated / deps (not edited by hand)
```

## Conventions
- **Per-plugin pages** in `doc-sites/docs/<plugin>/`: `overview.md`, `installation.md`, `agents/*.md`, `skills/*.md`. Mirror the plugin's actual agents/skills/commands.
- `intro.md` and the home page list the eight plugins. Derive component inventories from manifests/source directories and link canonical settings instead of duplicating model catalogs. Codex command wrappers are generated skills, so their counts differ from Claude source skills.
- Public guide prose and UI follow the Korean/English contract in ADR-023. Keep
  `docs/` as the English source and matching Korean content under
  `i18n/ko/docusaurus-plugin-content-docs/current/`; internal project docs stay English.
- The active/default locales are defined in `docusaurus.config.ts`. Translation
  files may be prepared while inactive. Enable a locale only after page, UI and
  anchor coverage checks pass; do not present fallback English as a completed translation.
- Preserve source page IDs, routing metadata, explicit heading IDs, required syntax
  literals and legacy fragment IDs. Locale redirects must not overwrite real locale pages.
- Slash-command fragments such as `kiro`, `kiro-1`, `co-agent` and `co-agent-1`
  preserve IDs observed in the Docusaurus 3.9.2 build; full command labels still render.
  Do not replace them with guessed github-slugger output or infer them from older
  translated spans. Keep pinned IDs when adding sections and choose a fresh ID for each new one.
- `static/demos/` and associated visual assets are frozen examples; localized input/output artifacts can remain unchanged. Explain their historical scope in the maintained wrapper pages.
- Do **not** hand-edit `build/`, `.docusaurus/`, or `node_modules/`.

## Locale ownership and routing

Korean is the default at `/oh-my-cloud-skills/`; English lives at `/oh-my-cloud-skills/en/`.
The explicit `/ko/` prefix is a compatibility alias for the Korean root. Redirects
preserve path, query and fragment; they never overwrite English pages.

`ko.translate: true` loads the Korean overrides even though Korean is the default
locale. `en.translate: false` uses the canonical English files directly. Keep the
two guide trees paired rather than moving Korean prose into the English source.
UI messages live in `i18n/ko/code.json`, theme catalogs and the docs sidebar catalog.
Use canonical `Translate`/`{translate}` imports and static translation IDs in React;
the release notice uses a localized Link. Use explicit IDs on H2–H6 ATX headings
and inline Markdown links. The locale checker rejects live MDX logic and
unsupported heading/link forms; keep syntax examples in fenced code blocks.

After changing English guides, review/update the matching Korean pages and run
`npm run record:locales` to record the source fingerprints. This explicit command
does not replace translation review. Default checks reject missing pages, changed
code/routing/anchors, literal English copies, missing UI messages and stale hashes.
Do not update hashes merely to silence an unreviewed translation difference.

## Commands
```bash
cd doc-sites
npm install
npm run start     # local dev server
npm run start -- --locale en  # preview English; a dev server serves one locale
npm run test:i18n
npm run check:locales
npm run build     # static build → build/
```

`prebuild` runs the locale tests and coverage check. A production build contains both
locales; use it for link and language-switching checks. The isolated GitHub-hosted
`docs-validation.yml` validates the PR HEAD with read-only repository permissions and
no persisted checkout credential. The existing Pages workflow builds the merged site.

> This site documents the plugins; the plugins themselves live in `../plugins/`. Keep it
> consistent with `../CLAUDE.md` and `marketplace.json`. CI: `.github/workflows/deploy-docs.yml`
> (triggers on `doc-sites/**`, builds and deploys to GitHub Pages on push to `main`).
