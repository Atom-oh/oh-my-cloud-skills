# Alert Directive Reference

A brief message that provides information or instructs users to take a specific action.

## Declaration Types

| Type | Supported | Syntax | Use Case |
|------|-----------|--------|----------|
| Text | No | - | Not supported |
| Leaf | Yes | `::alert[content]{props}` | Simple single-line messages |
| Container | Yes | `:::alert{props}\ncontent\n:::` | Complex content with markdown |

## Properties

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `header` | `string` | No | - | Header text displayed above the message |
| `type` | `string` | No | `"info"` | Message type: `success`, `error`, `warning`, `info` |

## Alert Types

| Type | Purpose | Use When |
|------|---------|----------|
| `info` | General information | Providing helpful tips or additional context |
| `success` | Positive confirmation | Indicating successful completion or correct setup |
| `warning` | Caution notice | Highlighting potential issues or important considerations |
| `error` | Critical alert | Showing errors, blockers, or dangerous actions |

## Examples

### Basic Alert (Leaf)

```markdown
::alert[This is an informational message]
```

### Alert with Header

```markdown
::alert[Please complete this step before proceeding]{header="Important"}
```

### Different Alert Types

```markdown
::alert[Operation completed successfully]{type="success"}

::alert[This action cannot be undone]{type="warning"}

::alert[Invalid configuration detected]{type="error"}

::alert[Additional resources are available]{type="info"}
```

### Alert with Header and Type

```markdown
::alert[Your AWS account is now ready]{header="Setup Complete" type="success"}
```

### Container Alert with Complex Content

```markdown
:::alert{header="Prerequisites" type="warning"}
Before starting this lab, ensure you have:

1. An AWS account with administrator access
2. AWS CLI installed and configured
3. Node.js 18+ installed

```bash
# Verify your setup
aws sts get-caller-identity
node --version
```
:::
```

### Container Alert with Code Blocks

```markdown
:::alert{header="Important" type="warning"}
Make sure to update your local mainline branch before creating a new feature branch:

1. Checkout your local `mainline` branch
    ```bash
    git checkout mainline
    ```
1. Fetch changes from remote
    ```bash
    git fetch
    ```
1. Rebase your local `mainline` branch
    ```bash
    git pull --rebase
    ```
:::
```

## Best Practices

### Do

```markdown
::alert[Ensure your IAM role has the required permissions before proceeding]{header="Permissions Required" type="warning"}
```

```markdown
:::alert{header="Cleanup" type="info"}
Remember to delete these resources after completing the workshop:
- EC2 instances
- S3 buckets
- Lambda functions
:::
```

### Don't

```markdown
::alert[Warning!!! IMPORTANT!!! READ THIS!!!]{type="error"}
```

```markdown
:::alert{type="info"}
This is just some regular text that doesn't need to be in an alert box.
:::
```

## Usage Guidelines

| Scenario | Recommended Type |
|----------|------------------|
| Step completion confirmation | `success` |
| Cost or billing warnings | `warning` |
| Prerequisite requirements | `warning` |
| Helpful tips | `info` |
| Configuration errors | `error` |
| Security considerations | `warning` or `error` |
| Time estimates | `info` |

## Common Patterns

### Prerequisite Alert

```markdown
:::alert{header="Prerequisites" type="warning"}
This module requires:
- Completion of Module 1
- An active AWS account
- Basic knowledge of Amazon S3
:::
```

### Cost Warning

```markdown
::alert[This lab may incur AWS charges. Remember to clean up resources after completion.]{header="Cost Warning" type="warning"}
```

### Success Confirmation

```markdown
::alert[Your CloudFormation stack has been successfully deployed!]{header="Deployment Complete" type="success"}
```
