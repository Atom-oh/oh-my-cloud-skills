# ADR-018: English-Only for Every Markdown File Claude Code Reads Operationally

## Status

Accepted (2026-08-14)

## Context

Every CLAUDE.md, SKILL.md, agent/command/reference file, and ADR in this repo mixed
Korean explanatory prose with English technical terms — the repo's own stated
convention, documented in several places (`docs/decisions/CLAUDE.md`: "Korean body with
English technical terms"; root `CLAUDE.md`'s auto-invocation tables). The user asked
for these files to be converted to English-only, to reduce the context size Claude Code
loads per session.

## Decision

Translate the Korean prose in every markdown file Claude Code reads operationally —
CLAUDE.md files (root + per-plugin), SKILL.md, `agents/*.md`, `commands/*.md`,
`references/*.md`, `docs/decisions/*.md` (ADRs), `docs/superpowers/{specs,plans}/*.md` —
to English, executed as a repo-wide sweep (PR #154).

**Excluded**, because translating them would work against their own documented purpose
rather than reduce context Claude Code reads:
- `README.ko.md` and its two skill-example pairs, `tools/remarp-vscode/README.ko.md` —
  deliberate Korean translations of their English counterparts (an existing documented
  auto-sync pair).
- `CHANGELOG.md`'s Korean half — the same bilingual-pair pattern, single-file instead of
  split-file.
- `doc-sites/docs/**` — the public Docusaurus site's Korean-default locale, backed by
  real `doc-sites/i18n/en`+`ko` infrastructure. Converting the default-locale source
  needs a locale-config change (which locale is default), not a translation pass — left
  for a separate decision if wanted.
- `plugins/project-init/**` — a documented byte-identical upstream mirror; edits are
  wiped on the next sync.

**Preserved wherever Korean remains** in the in-scope files:
- YAML frontmatter `description` trigger keywords. These are the literal phrases
  Korean-speaking users type to invoke a skill/agent (root `CLAUDE.md`: "Korean/English
  bilingual keywords in all auto-invocation rules"). Translating them would silently
  break Korean-language auto-invocation — a functional regression, not a context-size
  win.
- Code/bash/YAML/XML blocks, file paths, command names, model IDs.
- Embedded example content that demonstrates actual Korean-language tool output (e.g.
  sample Korean slide decks in `reactive-presentation`'s authoring guides) — Korean is a
  first-class *target output* language for that tool, so Korean-language examples of its
  output are real content, not incidental prose.
- **Prose that quotes a runtime literal a script actually emits** (a status banner, a
  comment-body header) when that script itself wasn't in scope of the sweep (only `.md`
  files were). Translating the quoted literal makes the doc describe output that doesn't
  exist — the runbook then tells an operator to grep for a string CI never prints. Two
  instances of exactly this were caught by the chair review during this sweep
  (`docs/ci-pr-review-runbook.md`'s coverage-degraded/collapsed banners and its L1-failure
  header) and fixed by quoting the actual Korean literal with an English gloss instead of
  translating it outright — the pattern to follow for any such literal found later.

**Convention updates**: `docs/decisions/CLAUDE.md`'s ADR language rule changed from
"Korean body with English technical terms" to "English throughout." `docs/CLAUDE.md`'s
entry for `architecture.md` dropped "(bilingual KO/EN)" — see Consequences below.

## Consequences

- Two files had a duplicate-bilingual-toggle structure (a `# 한국어`/`# Korean` section
  followed by a full parallel `# English` section, badge-linked) rather than inline
  mixed prose: `docs/architecture.md` and `docs/decisions/ADR-004-agentcore-creator-skill.md`.
  Translating the Korean half in place would have produced two identical English
  sections — doubling content instead of reducing it. Both were collapsed to a single
  English section instead.
- `docs/pr-review/review-memory.md`'s section headings changed language, and
  `scripts/pr-review/lib.sh::memory_excerpt`'s awk filter does an exact match on the old
  Korean heading text to exclude the panel-cell-judgment-quality table from the lens/chair
  excerpt. Fixed in the same PR (#154) — the awk pattern now matches either heading, so
  the exclusion contract (ADR-015) survives the rename regardless of which heading text a
  given `review-memory.md` revision uses.
- The scripts themselves (`scripts/pr-review/*.sh`, `.github/workflows/pr-review.yml`)
  were **not** in scope — only markdown files were. Their Korean literal strings
  (status banners, the L1-failure header) are unchanged, so `docs/ci-pr-review-runbook.md`
  now quotes those banners as the Korean literals they actually are (with an English
  gloss), rather than claiming they already read in English.
- No functional change to skill/agent triggering: `python3 scripts/test-plugins.py`
  passes on all 7 plugins after the sweep, and Korean-language auto-invocation keywords
  in frontmatter are untouched.

## References

- PR #154 (the translation sweep and this ADR)
- `docs/decisions/CLAUDE.md`, `docs/CLAUDE.md` (updated conventions)
- `scripts/pr-review/lib.sh` (`memory_excerpt` heading-match fix)
- ADR-015 (review-memory loop — heading-match contract this ADR keeps intact)
