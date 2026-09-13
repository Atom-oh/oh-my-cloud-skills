---
sidebar_position: 5
title: "Workshop creator skill"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="trigger-keywords" />
<span id="commands" />
<span id="provided-resources" />
<span id="references" />
<span id="directory-structure" />
<span id="workshop-studio-directives-detail" />
<span id="alert-directive" />
<span id="leaf-syntax-simple-messages" />
<span id="container-syntax-complex-content" />
<span id="code-directive" />
<span id="code-properties" />
<span id="supported-languages-40" />
<span id="tabs-directive" />
<span id="image-directive" />
<span id="expand-directive" />
<span id="mermaid-diagrams" />
<span id="contentspecyaml-guide" />
<span id="basic-configuration" />
<span id="full-configuration-options" />
<span id="magic-variables" />
<span id="cloudformation-infrastructure-patterns" />
<span id="vpc--eks-pattern" />
<span id="serverless-pattern" />
<span id="best-practices" />
<span id="event-params--central-account" />
<span id="workshop-templates" />
<span id="homepage-template" />
<span id="prerequisites" />
<span id="lab-content-template" />
<span id="front-matter" />
<span id="best-practices-1" />
<span id="do" />
<span id="dont" />
<span id="bilingual-content" />
<span id="usage-example" />
<span id="quality-review-required" />


# Workshop creator skill

Create AWS Workshop Studio content and project structure, including modules, labs, assets, and optional infrastructure.

## Project layout

The project contains contentspec.yaml, content pages grouped by module/lab, and static assets such as diagrams and infrastructure templates. Pages require a quoted `title`; optional `weight` controls navigation order. Follow the source [frontmatter reference](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-content-plugin/skills/workshop-creator/references/front-matter.md) for other fields. Do not use Hugo `chapter: true` or shortcode syntax.

## Authoring

Use Workshop Studio alert, code, tabs, image, expand, and Mermaid directives. Provide copyable commands, expected output, checkpoints, troubleshooting, and cleanup. Tabs can show real alternatives such as operating systems or deployment options. Keep infrastructure scoped to the exercise and document event parameters or central-account resources when the workshop uses them.

## Infrastructure and language

Validate CloudFormation and IAM before use, follow the repository's AWS security rules, and avoid embedding secrets. Localized page pairs are an output option when requested; otherwise use one consistent language. Explain every resource the lab creates and how learners verify or remove it.

## Review

Check contentspec paths, page order, directive syntax, files/assets, prerequisites, and lab completion criteria. Test the documented steps in the authorized environment and run content review before publication.


[Skill, resources, and quality requirements](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-content-plugin/skills/workshop-creator/SKILL.md)
