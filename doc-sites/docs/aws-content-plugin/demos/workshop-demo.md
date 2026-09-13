---
sidebar_position: 8
title: "Workshop example"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="workshop-demo" />
<span id="생성-프롬프트" />
<span id="생성된-프로젝트-구조" />
<span id="contentspecyaml" />
<span id="homepage-indexenmd" />
<span id="module-overview" />
<span id="module-1-environment-setup-30-min" />
<span id="module-2-create-eks-cluster-45-min" />
<span id="module-3-deploy-application-45-min" />
<span id="module-4-monitoring-45-min" />
<span id="technologies-youll-master" />
<span id="prerequisites" />
<span id="time-required" />
<span id="prerequisites-check" />
<span id="check-eksctl-version" />
<span id="check-kubectl-version" />
<span id="verify-aws-credentials" />
<span id="key-takeaways" />
<span id="iam-policy-staticiam-policyjson" />
<span id="workshop-directive-사용-예시" />
<span id="alert-types" />
<span id="code-with-copy-button" />
<span id="tabs-for-multi-option-content" />
<span id="주요-포인트" />


# Workshop example

This example illustrates an EKS Workshop Studio project with a homepage, ordered modules, lab pages, infrastructure assets, and learner checkpoints.

## Project shape {#project-shape}

Keep `contentspec.yaml` at the project root, content pages under module/lab directories, and reusable images/templates in static assets. Homepage and module pages explain objectives and prerequisites; a lab page gives commands, expected results, verification, and cleanup.

## Content features {#content-features}

Use Workshop Studio alerts for cautions, code blocks with copy support, and tabs for real alternatives. Frontmatter controls title and ordering. Use only the requested language variants; localized input/output examples can be retained as frozen artifacts.

## Infrastructure review {#infrastructure-review}

Infrastructure and IAM are exercise-specific. Validate templates, scope permissions, keep public access controlled, and identify every resource the learner creates. An old example template is not a current production deployment recommendation.

The current [workshop skill](/docs/aws-content-plugin/skills/workshop-creator) links the directory, directive, contentspec, event-parameter, and infrastructure references used for new workshops.
