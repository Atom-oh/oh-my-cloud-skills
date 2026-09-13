---
sidebar_position: 2
title: "Architecture diagram skill"
---

# Architecture diagram skill

{/* Legacy section links retained after the English rewrite. */}
<span id="trigger-keywords" />
<span id="supported-modes" />
<span id="provided-resources" />
<span id="references" />
<span id="templates" />
<span id="scripts" />
<span id="canvas-size-for-ppt" />
<span id="drawio-xml-code-examples" />
<span id="empty-canvas-ppt-1600x900" />
<span id="aws-cloud-container" />
<span id="vpc-container" />
<span id="public-subnet-green" />
<span id="private-subnet-blue" />
<span id="ec2-instance-icon" />
<span id="lambda-function-icon" />
<span id="aurora-database-icon" />
<span id="connection-arrow" />
<span id="layout-patterns-detail" />
<span id="3-tier-architecture-pattern" />
<span id="hybrid-cloud-pattern" />
<span id="serverless-architecture-pattern" />
<span id="aws-icon-label-rules" />
<span id="aws-color-guide" />
<span id="service-category-colors" />
<span id="best-practices-checklist" />
<span id="layout" />
<span id="colors--style" />
<span id="connections" />
<span id="completeness" />
<span id="png-export" />
<span id="usage-example" />
<span id="drawio-mcp-setup-optional" />
<span id="quality-review-required" />
<span id="validation-checklist" />

Create editable AWS Draw.io diagrams and exported images. Standard VPC/Multi-AZ/tiered, serverless/pipeline, multi-region, and hybrid patterns use a YAML spec with `layout_aws.py`; unsupported shapes can use hand-authored XML.

## Generate and validate

```bash
python3 plugins/aws-content-plugin/skills/architecture-diagram/scripts/layout_aws.py my-spec.yaml -o output.drawio
python3 plugins/aws-content-plugin/skills/architecture-diagram/scripts/validate_drawio.py output.drawio
python3 plugins/aws-content-plugin/skills/architecture-diagram/scripts/lint_layout.py output.drawio
drawio -x -f png -s 2 -t -o output.png output.drawio
```

Require layout score at least 80 before export. Headless Linux export can use `xvfb-run -a`. Reopen the image and compare service/cell coverage to the intended architecture; successful export status alone does not catch truncation.

## Structure and tokens

Use vertex nesting that matches Cloud/Region/VPC/Subnet containment. Edges use parent="1" and explicit orthogonal anchors. Distinguish public and private subnet groups using their correct AWS group styles. Copy sizing, colors, fonts, pitch, and label rules from the canonical token file rather than maintaining a second table.

Avoid decorative XML comments and malformed entities. Keep boundaries readable, align same-kind resources, label services, and minimize crossings. The optional Draw.io MCP can help interactive editing; it is not needed for script generation.

[Canonical tokens](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-content-plugin/skills/architecture-diagram/references/design-tokens.md) · [Example specs and diagrams](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-content-plugin/skills/architecture-diagram/examples/)

[Skill, resources, and quality requirements](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-content-plugin/skills/architecture-diagram/SKILL.md)
