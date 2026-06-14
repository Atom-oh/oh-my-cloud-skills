# Review Routing — `superpowers:requesting-code-review` → the right gate

`superpowers:requesting-code-review` targets **code**. This repo's deliverables also include
non-code artifacts and infrastructure, each with its own quality gate. This file maps an
artifact type to its gate and — critically — defines **precedence for mixed changesets** so no
required review is silently skipped.

> The root `CLAUDE.md` "superpowers Integration Routing" table force-reads this file at the
> review phase. (superpowers is read-only; routing is ours.)

## Artifact → gate

| Artifact type in the diff | Review gate | Pass bar |
|---------------------------|-------------|----------|
| Code (source, scripts, tests) | `co-agent` Review (multi-AI) and/or `superpowers:requesting-code-review` | reviewer judgment |
| Presentation / slides (Remarp, HTML) | `aws-content`: `content-review-agent` | ≥ 85 / 100 |
| Diagram (`.drawio`, animated SVG/HTML) | `aws-content`: `content-review-agent` | ≥ 85 / 100 |
| Document / GitBook / workshop / brochure | `aws-content`: `content-review-agent` | ≥ 85 / 100 |
| IaC / architecture (CDK, Terraform, CFN) | `aws-ops`: `wellarchitected-agent` | 6-pillar score |
| Security-sensitive IaC/AWS (SG, IAM, Lambda, S3, Route53) | `aws-ops`: `ops-security-audit` **(mandatory)** | no banned pattern |

## Mixed changeset — precedence rule

**A single diff that spans multiple artifact types triggers ALL matching gates — not just one.**
Selecting one gate and skipping the others is the failure mode this rule prevents.

Procedure:
1. Classify every changed path by artifact type (a path may match more than one).
2. Run **each** matching gate from the table above.
3. **Security is non-negotiable**: if any changed path touches AWS security surface
   (Security Group, IAM policy/role, Lambda permission/URL, S3 bucket policy, Route53, secrets),
   `ops-security-audit`'s banned-pattern check (no `0.0.0.0/0` ingress, no `Principal:"*"`,
   no `Resource:"*"` without a Condition, no `AuthType:NONE`, no secrets in env, no ALB bypassing
   CloudFront) is a **required, blocking** leg — even if the change is "mostly docs".
4. Aggregate: the review passes only when **every** fired gate passes. One failing gate blocks.

## Notes

- These gates stay **distinct** — this file cross-references them, it does not merge them.
- For pure-code diffs, `co-agent` Review (multi-AI) already covers it; this routing adds the
  non-code and infra arms that `superpowers:requesting-code-review` alone doesn't reach.
- Catch security violations earlier when possible: see `superpowers:writing-plans` shift-left
  pre-check (integration ④) so a banned pattern never reaches review in the first place.
