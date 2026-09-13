---
sidebar_position: 7
title: "Content review agent"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="기본-정보" />
<span id="트리거-키워드" />
<span id="지원-콘텐츠-타입" />
<span id="16개-검사-카테고리" />
<span id="1-layout-inspection-레이아웃-검사" />
<span id="2-terminology-appropriateness-용어-적절성" />
<span id="3-hallucination-detection-환각-탐지" />
<span id="4-language-check-언어-검사" />
<span id="5-piisensitive-data-inspection-민감-데이터-검사" />
<span id="6-content-type-specific-quality-타입별-품질" />
<span id="7-16-추가-검사" />
<span id="visual-testing-html-콘텐츠" />
<span id="점수-체계-100점-만점" />
<span id="판정" />
<span id="자동-fail" />
<span id="리뷰-리포트-형식" />
<span id="리뷰-프로세스" />
<span id="step-1-file-collection" />
<span id="step-2-type-specific-inspection" />
<span id="step-3-visual-testing-html만" />
<span id="step-4-report-generation" />
<span id="리비전-루프" />
<span id="출력물" />


# Content review agent

Reviews presentations, diagrams, documents, GitBook pages, workshops, brochures, and profile pages. A report must name actual files, evidence, severity, corrections, and the applicable score.

## Review coverage

Check layout and hierarchy; precise terminology; unsupported factual claims; the requested language; secrets and personal data; content-type rules; icon references; readability; accessibility; structural completeness; data consistency; legal attribution; message clarity; duplication/gaps; and external references.

HTML output also requires browser checks: load without application errors, inspect representative viewports, exercise navigation and controls, and check images, diagrams, overflow, and text contrast. A screenshot does not prove a quiz, tab, calculator, or animation works; exercise it.

## Content-specific checks

Remarp needs valid source, framework initialization, notes, slide types, and interactions. Prefer HTML/CSS when a diagram exceeds the simple Canvas policy. Draw.io needs valid XML, correct nesting, canonical tokens, layout validation, and a complete export. GitBook navigation must match files. Workshops use Workshop Studio directives and the source rubric's language-file checks.

## Quality gate

The source rubric defines category weights and format-specific handling. PASS requires a score of at least 85, zero Critical findings, and no more than three Warnings. A sensitive-data leak, serious fabricated claim, or other automatic-fail condition cannot be offset by points in unrelated categories. Non-HTML output follows the rubric's visual-testing exemption.

Return the score, verdict, evidence, and repair checklist. Fix REVIEW/FAIL issues and re-review within the workflow's iteration bound; report unresolved blockers instead of claiming publication readiness.

[Canonical rubric and report contract](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-content-plugin/agents/content-review-agent.md)
