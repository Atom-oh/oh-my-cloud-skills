# ADR-003: Comprehensive Architecture Deep-Review Skill via Kiro CLI

## Status

Accepted

## Context

Coding with Claude Code, code review and architecture review were limited by depending on a single agent's perspective. In particular, security vulnerability detection, spec-driven development, and AWS infrastructure review (CDK/CloudFormation) all benefit from dedicated, specialized verification. Kiro provides capabilities such as code review, EARS-requirement-based design, and adversarial security review; integrating these into the Claude Code workflow enables multi-perspective deep review.

## Options Considered

### Option 1: Use only Claude Code's built-in review

- **Pros**: No additional tool installation required; everything processed in a single context
- **Cons**: Limited to a single perspective, no adversarial security review possible, no spec-driven development workflow

### Option 2: Integrate external review via the Kiro CLI plugin

- **Pros**: Multi-perspective review (general + adversarial security), automated EARS requirements → design → implementation pipeline, specialized AWS infrastructure review support, ability to delegate background tasks
- **Cons**: Adds an external tool dependency, requires Kiro CLI installation, may introduce network latency

### Option 3: Implement review functionality directly as an MCP server

- **Pros**: No external dependency, full customizability
- **Cons**: High development/maintenance cost, difficult to reach the quality of Kiro's existing review engine

## Decision

Adopt Option 2. Integrate kiro-cli-plugin (https://github.com/whchoi98/kiro-cli-plugin) as a Claude Code plugin to build a comprehensive architecture deep-review skill.

### Core Capabilities

| Skill | Role |
|------|------|
| `/kiro-cli:review` | Delegates code review of changes (including security-focused adversarial review) |
| `/kiro-cli:task` | Delegates debugging/implementation tasks (supports background execution) |
| `/kiro-cli:spec` | Auto-generates EARS requirements + architecture design + implementation tasks |

### AWS Infrastructure Support Scope

- CDK/CloudFormation template review
- Cost optimization analysis
- Multi-region DR design verification

### Installation

```bash
/plugin marketplace add https://github.com/whchoi98/kiro-cli-plugin
/plugin install kiro-cli@kiro-cli-plugin
/reload-plugins
```

## Consequences

### Positive

- Multi-perspective review improves code quality and security posture
- Spec-driven development establishes traceability from requirements → design → implementation
- Complements the existing content-review-agent Quality Gate in oh-my-cloud-skills

### Negative

- Requires Kiro CLI installation and authentication as a prerequisite
- Dependency on an external service makes it unusable in offline environments
- Review response wait time can introduce workflow delays

## References

- kiro-cli-plugin: https://github.com/whchoi98/kiro-cli-plugin
- Existing Quality Gate: `aws-content-plugin/agents/content-review-agent.md`
- ADR-001: Stack-based parser (internal tool quality basis)
- ADR-002: Image-based PPTX export (client-side architecture decision)
