# ADR-023: Bilingual Public Guides

## Status

Accepted (2026-09-13). Partially supersedes ADR-021 for the public guide site only.

## Context

After the v2.0.0 guide update, the owner clarified that Korean and English are
standard requirements for the public guide. ADR-021's English-only site scope
therefore needs an explicit exception without duplicating internal agent context.

## Options Considered

- Keep the site English-only: smallest maintenance surface, but misses the request.
- Put both languages on each page: available together, but doubles reading length.
- Use matching localized pages and a language switcher: preserves concise pages
  while requiring translation and routing checks.

## Decision

- Use native Docusaurus locales for Korean and English, with Korean as the default.
- Keep English guide source in `doc-sites/docs/` and matching Korean locale files
  in `doc-sites/i18n/ko/`. Internal instructions, ADRs, README/CHANGELOG and review
  reports remain English.
- Preserve page routes, explicit heading IDs, legacy fragments, code/API literals
  and frozen example assets. Translate maintained prose and visible UI.
- Stage translation content before activation. Enable the Korean default and
  English route only after complete page/UI coverage, builds, link checks,
  language-switching checks and content review pass.
- Locale compatibility redirects must preserve query/fragment information and
  must not replace a real localized page.

## Consequences

Readers can use either language without duplicate prose on one page. Translation
maintenance and two-locale validation are additional release work; missing locale
content must not silently qualify as a completed guide. PR review, security,
upstream ownership and generated-artifact requirements remain unchanged.

## References

- [ADR-021](ADR-021-english-docs-current-review-authority.md)
- [Site maintenance contract](../../doc-sites/CLAUDE.md)
- [Locale configuration](../../doc-sites/docusaurus.config.ts)
