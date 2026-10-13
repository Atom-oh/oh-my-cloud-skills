# Incident Response

5-minute triage checklist and incident management framework.

---

## First 5-Minute Checklist

The first 5 minutes are most critical when an incident occurs. Follow this checklist in order.

### Step 1: Cluster Status (30 seconds)
```bash
kubectl cluster-info
kubectl get nodes -o wide
kubectl get pods -A --field-selector=status.phase!=Running
```

### Step 2: Recent Events (30 seconds)
```bash
kubectl get events -A --sort-by='.lastTimestamp' | tail -50
```

### Step 3: Core System Pods (30 seconds)
```bash
kubectl get pods -n kube-system
kubectl get pods -n amazon-vpc-cni-system
```

### Step 4: Resource Usage (30 seconds)
```bash
kubectl top nodes
kubectl top pods -A --sort-by=memory | head -20
```

### Step 5: Recent Changes (1 minute)
```bash
kubectl get deployments -A -o json | jq '.items[] | select(.status.unavailableReplicas > 0) | {name:.metadata.name,ns:.metadata.namespace,unavailable:.status.unavailableReplicas}'
kubectl rollout history deployment/<name> -n <namespace>
```

### Step 6: AWS Service Status (1 minute)
```bash
aws eks describe-cluster --name $CLUSTER_NAME --query 'cluster.status'
aws ec2 describe-instance-status --filters Name=instance-state-name,Values=running --query 'InstanceStatuses[?InstanceStatus.Status!=`ok`]'
```

---

## Severity Matrix

| Severity | Response Time | Escalation | Criteria |
|----------|--------------|------------|----------|
| **P1 Critical** | < 5 min | Immediate team + management | Complete service outage, data loss, 50%+ nodes down |
| **P2 High** | < 30 min | Team lead | Major degradation, high error rate > 10%, critical pod failures |
| **P3 Medium** | < 4 hours | On-call engineer | Single node issue, non-critical pod failures, performance degradation |
| **P4 Low** | Next business day | Ticket | Warning alerts, optimization opportunities, non-urgent maintenance |

---

## Incident Lifecycle

```
Detection → Triage → Investigation → Mitigation → Resolution → Postmortem
   │           │          │              │            │            │
   └─ Alert    └─ P1-P4   └─ Root cause  └─ Stop      └─ Fix      └─ Prevent
     Monitor     Severity    analysis      bleeding     root cause   recurrence
```

---

## Postmortem Template

```markdown
## Incident Postmortem: [Title]

**Date**: YYYY-MM-DD
**Duration**: HH:MM
**Severity**: P1/P2/P3/P4
**Author**: [Name]

### Summary
[1-2 sentence summary]

### Timeline
| Time (UTC) | Event |
|-----------|-------|
| HH:MM | [First alert/report] |
| HH:MM | [Triage started] |
| HH:MM | [Root cause identified] |
| HH:MM | [Mitigation applied] |
| HH:MM | [Fully resolved] |

### Root Cause
[Detailed analysis]

### Impact
- [Affected users/services]
- [Duration]
- [Data loss if any]

### Resolution
[What was done to fix]

### Action Items
| Action | Owner | Due Date | Status |
|--------|-------|----------|--------|
| [Preventive action] | [Name] | [Date] | [Open/Done] |
```
