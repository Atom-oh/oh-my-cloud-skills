# Changelog

All notable changes to oh-my-cloud-skills are documented in this file.

## [v1.2.3] - 2026-03-20

### Added
- Canvas complexity gate in content-review-agent
- HTML Architecture pattern and STOP gate in reactive-presentation SKILL.md
- Interactive slide patterns guide (interactive-patterns-guide.md)

### Changed
- Strengthened canvas vs HTML selection guidance in agent and SKILL.md decision guides
- Fixed monitoring/dashboard mapping from canvas to html+script
- Enhanced plugin documentation with detailed agent and skill reviews
- Enhanced Remarp guide documentation

### Fixed
- Canvas overuse — agent no longer defaults all diagrams to :::canvas

## [v1.2.2] - 2026-03-15

### Added
- Orthogonal arrow routing to Canvas DSL
- Data visualization design guide for reactive-presentation
- Visual editor, canvas editor, and CSS editor to Remarp VSCode extension
- `:::prompt` block support and per-block export buttons
- AIOps 90-minute presentation demo

### Changed
- Enhanced plugin skills with hooks, references, and improved patterns
- Migrated plugins to latest Claude Code format with hooks, validation, and token optimization

### Fixed
- Blocks config bug in multi-block presentations

## [v1.2.1] - 2026-03-05

### Added
- Remarp VSCode extension completions and preview improvements
- Remarp-first workflow documentation

### Changed
- Enhanced canvas animation prompts, PPTX theme extractor, and kiro conversion rules
- Updated plugin CLAUDE.md keyword routing and team workflow docs
- Removed hardcoded model field from agent frontmatter

### Fixed
- Strip 'Block N:' prefix from slide titles in converter
- Correct `../common/` to `./common/` asset paths in remarp_to_slides.py
- 3 rendering bugs in remarp_to_slides.py converter

## [v1.1.0] - 2026-03-03

### Added
- kiro-power-converter plugin for Claude Code to Kiro Power conversion
- Docusaurus documentation site with GitHub Pages deployment
- i18n support (ko default, en placeholder)
- Remarp VSCode extension for syntax highlighting and preview
- Audience frontmatter field and strengthened agent planning questions

### Changed
- Replaced cloudwatch-agent with observability-agent, added analytics-agent
- Made Remarp the default content authoring format for presentations

### Fixed
- PPTX theme extraction with Slide Master layout details

## [v1.0.0] - 2026-02-26

### Added
- Initial release
- aws-content-plugin: presentation, architecture diagram, animated diagram, document, gitbook, workshop agents
- aws-ops-plugin: EKS, network, IAM, observability, storage, database, cost, analytics, ops-coordinator agents
- reactive-presentation skill with Canvas animations, quizzes, and keyboard navigation
- Content review quality gate (100-point scale)
- PPTX/PDF theme extraction
- AWS Architecture Icons integration (4,224 files)
- Presenter view with speaker notes

[v1.2.3]: https://github.com/Atom-oh/oh-my-cloud-skills/compare/v1.2.2...v1.2.3
[v1.2.2]: https://github.com/Atom-oh/oh-my-cloud-skills/compare/v1.2.1...v1.2.2
[v1.2.1]: https://github.com/Atom-oh/oh-my-cloud-skills/compare/v1.1.0...v1.2.1
[v1.1.0]: https://github.com/Atom-oh/oh-my-cloud-skills/compare/v1.0.0...v1.1.0
[v1.0.0]: https://github.com/Atom-oh/oh-my-cloud-skills/releases/tag/v1.0.0
