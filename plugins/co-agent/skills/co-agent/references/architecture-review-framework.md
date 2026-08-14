# Architecture Review Framework

A framework for comprehensive architecture review. Verifies from code changes through infrastructure across multiple perspectives.

## Review Dimensions

### 1. Code Quality

| Item | Verification method | Tool |
|------|-----------|------|
| Cyclomatic complexity | ≤10 conditional branches per function | Kiro review, radon |
| Duplicate code | Same logic repeated 3+ times | Kiro review, jscpd |
| Error handling | No catch-all; specific exception handling | Kiro adversarial |
| Test coverage | Tests exist for the changed code | coverage report |
| Dependency health | No CVEs, license-compatible packages | npm audit, pip-audit |

### 2. Security

OWASP Top 10 + AWS-specific security checks:

```
A01:2021 - Broken Access Control
  → IAM least privilege, RBAC verification, API Gateway authentication
A02:2021 - Cryptographic Failures
  → TLS 1.2+, KMS encryption, secrets management
A03:2021 - Injection
  → SQL/Command/LDAP injection, ORM usage, parameter binding
A04:2021 - Insecure Design
  → threat modeling, secure design patterns
A05:2021 - Security Misconfiguration
  → debug mode, default credentials, unnecessary open ports
A06:2021 - Vulnerable Components
  → known CVEs, EOL libraries
A07:2021 - Authentication Failures
  → MFA, session management, password policy
A08:2021 - Data Integrity Failures
  → signature verification, CI/CD pipeline security
A09:2021 - Logging Failures
  → audit logs, sensitive-data masking
A10:2021 - SSRF
  → external URL validation, metadata service blocking
```

### 3. Infrastructure

Based on the AWS Well-Architected Framework (see the dedicated doc):
- `references/aws-well-architected.md`

### 4. Operational Readiness

| Item | Criteria |
|------|------|
| Monitoring | CloudWatch metrics/alarms or Prometheus configuration included |
| Logging | Structured logs (JSON), appropriate log levels |
| Deployment | Blue/Green or Canary deployment strategy |
| Rollback | 1-click rollback available |
| Runbook | Incident-response procedures documented |

---

## Severity Classification

### Verdict matrix

```
           Impact
         Low    High
    ┌────────┬────────┐
Low │  LOW   │ MEDIUM │  Likelihood
    ├────────┼────────┤
High│ MEDIUM │  HIGH  │
    ├────────┼────────┤
Cert│  HIGH  │CRITICAL│
    └────────┴────────┘
```

### Severity definitions

| Severity | Criteria | SLA | Example |
|--------|------|-----|------|
| CRITICAL | Fix immediately, blocks merge | Immediate | SQL injection, hardcoded AWS keys, IAM `*:*` |
| HIGH | Fix before release | 24h | Improper error handling, public S3 bucket, auth bypass |
| MEDIUM | Next sprint | 1 week | Code duplication, insufficient tests, inefficient queries |
| LOW | Backlog | Optional | Naming conventions, missing comments, style issues |

### Overall verdict logic

```python
def verdict(findings):
    critical = count(f for f in findings if f.severity == "CRITICAL")
    high = count(f for f in findings if f.severity == "HIGH")
    
    if critical > 0:
        return "FAIL"      # blocks merge
    elif high >= 3:
        return "REVIEW"    # requires manual approval
    else:
        return "PASS"      # passes
```

---

## Review Process Flow

### Solo run (Kiro not installed)

1. Analyze the change based on `git diff`
2. Static pattern scan (secrets, injection, unsafe patterns)
3. AWS Well-Architected checklist (for infrastructure code)
4. Generate a combined report

### Panel-integrated run (Kiro/Codex/Antigravity)

Fans out **the same review prompt, headlessly**, to the installed panel CLIs — using the
adapters in `references/ai-cli-adapters.md` directly rather than a slash command
(`co_agent_config.py pairs`/`panel` already emit the real binary name in the first column:
`kiro-cli`/`codex`/`agy` — there is no separate resolver subcommand;
**never invoke bare `kiro`**, always `kiro-cli`).

1. Analyze the change based on `git diff` → write the context (diff) to a temp file
2. Fan out to the panel (e.g. `kiro-cli chat "<review prompt>\n\nRead the review context with fs_read from: <CTX_FILE>" --no-interactive --trust-tools=fs_read --wrap never`,
   `cat ctx | codex exec -s read-only`, `cat ctx | agy -p … --sandbox`) — same prompt, in parallel.
   ⚠️ **Kiro ignores stdin in `chat`**, so never pass the diff via stdin — write the
   context to a file and instruct via a short prompt to use `fs_read` (the only valid
   read-only tool name). Codex/Agy use the stdin channel. Details:
   `references/ai-cli-adapters.md`.
3. Apply the AWS Well-Architected checklist
4. Validate findings with `check_citations.py` → synthesize consensus/dissent
5. Merge results → combined PASS/REVIEW/FAIL report
</content>
</invoke>
