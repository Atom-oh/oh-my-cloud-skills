---
name: gitbook
description: "Create GitBook documentation sites with proper structure, navigation, and rich components. Use when creating documentation sites, technical guides, or knowledge bases with GitBook."
---

# GitBook Skill

Create structured GitBook documentation sites with proper navigation, components, and content organization.

## When to Use

- Documentation sites for AWS architectures or services
- Technical knowledge bases
- Project documentation with rich formatting
- Multi-chapter guides with navigation

## Quick Start

1. Create SUMMARY.md (navigation structure)
2. Create .gitbook.yaml (configuration)
3. Create chapter directories with README.md index pages
4. Add content pages with GitBook components
5. Push to git repository connected to GitBook

## Quality Review (필수 — 생략 불가)

콘텐츠 완성 후 배포/완료 선언 전에 반드시:
1. content-review-agent 호출 → `review content at [프로젝트경로]`
2. FAIL/REVIEW 판정 시 수정 후 재리뷰 (최대 3회)
3. PASS (≥85점) 획득 후에만 완료 선언

> ⚠️ 이 단계를 건너뛰고 완료를 선언하는 것은 금지됩니다.

## References

- `reference/structure-guide.md` — Project structure patterns and conventions
- `reference/component-patterns.md` — GitBook component syntax and usage
