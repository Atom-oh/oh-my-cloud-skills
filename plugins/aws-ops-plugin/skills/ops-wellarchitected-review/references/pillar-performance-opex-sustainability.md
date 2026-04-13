# Performance Efficiency, Operational Excellence & Sustainability Pillars

---

## Part A: Performance Efficiency Pillar

### Compute Right-sizing

```bash
# EC2 instances with architecture and generation
aws ec2 describe-instances --filters Name=instance-state-name,Values=running \
  --query 'Reservations[].Instances[].[InstanceId,InstanceType,Architecture,Placement.AvailabilityZone]' --output table

# Lambda functions with memory and runtime
aws lambda list-functions --query 'Functions[].[FunctionName,Runtime,MemorySize,Timeout,Architectures[0]]' --output table

# ECS services
aws ecs list-clusters --query 'clusterArns[]' --output text
```

### Scoring Criteria
| Condition | Finding |
|-----------|---------|
| EC2 CPU avg < 10% | Over-provisioned (flag for right-sizing) |
| Lambda avg duration > 80% of timeout | Timeout risk |
| Deprecated runtime (Python 3.8, Node 14) | Runtime update needed |
| Old-gen instance (m4, c4, r4, t2) | Modernization candidate |

### EKS Resource Efficiency

```bash
# Node utilization
kubectl top nodes

# Pod resource usage vs requests
kubectl top pods -A

# Pods without resource limits
kubectl get pods -A -o json | jq '.items[] | select(.spec.containers[].resources.limits == null) | .metadata.namespace + "/" + .metadata.name'

# HPA coverage
kubectl get hpa -A

# PDB coverage
kubectl get pdb -A
```

| Condition | Finding |
|-----------|---------|
| Namespace waste > 50% (requested >> used) | Over-provisioned |
| Pods without resource limits/requests | Warning |
| No HPA on production deployments | Warning |
| No PDB on production workloads | Warning |

### Database Tuning

```bash
# RDS instance utilization (check CloudWatch for CPUUtilization)
aws cloudwatch get-metric-statistics --namespace AWS/RDS \
  --metric-name CPUUtilization --dimensions Name=DBInstanceIdentifier,Value=<id> \
  --start-time $(date -d '7 days ago' -u +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 86400 --statistics Average

# ElastiCache metrics
aws cloudwatch get-metric-statistics --namespace AWS/ElastiCache \
  --metric-name CacheHitRate --dimensions Name=CacheClusterId,Value=<id> \
  --start-time $(date -d '7 days ago' -u +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 86400 --statistics Average
```

| Condition | Finding |
|-----------|---------|
| RDS CPU avg < 15% | Over-provisioned |
| ElastiCache eviction rate high + low hit ratio | Under-sized or inefficient usage |
| OpenSearch JVM pressure > 80% | Under-sized |

---

## Part B: Operational Excellence Pillar

### Monitoring Coverage

```bash
# CloudWatch alarm inventory
aws cloudwatch describe-alarms --query 'MetricAlarms | length(@)'

# Alarms by state
aws cloudwatch describe-alarms --query 'MetricAlarms[].StateValue' | sort | uniq -c

# Log groups and retention
aws logs describe-log-groups --query 'logGroups[].[logGroupName,retentionInDays,storedBytes]' --output table

# CloudTrail status
aws cloudtrail get-trail-status --name default 2>/dev/null || aws cloudtrail describe-trails --query 'trailList[].[Name,IsMultiRegionTrail,IsLogging]'

# Container Insights (EKS)
aws eks describe-cluster --name <cluster> --query 'cluster.logging.clusterLogging[?enabled==`true`].types[]'
```

### Scoring Criteria
| Condition | Finding |
|-----------|---------|
| No CloudWatch alarms for production services | Critical gap |
| Log groups without retention policy (indefinite) | Cost risk |
| CloudTrail disabled | Critical |
| No Container Insights on EKS | Monitoring gap |

### Automation Maturity

```bash
# IaC detection — CloudFormation stacks
aws cloudformation list-stacks --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE \
  --query 'StackSummaries[].[StackName,CreationTime]' --output table

# Terraform state files (if S3 backend)
aws s3api list-objects-v2 --bucket <state-bucket> --prefix <prefix> --query 'Contents[].Key' 2>/dev/null

# Systems Manager patching
aws ssm describe-instance-information --query 'InstanceInformationList[].[InstanceId,PingStatus,IsLatestVersion]' --output table
```

| Condition | Finding |
|-----------|---------|
| No IaC detected (no CFn stacks, no Terraform) | Manual provisioning risk |
| ASG without scaling policies | No auto-healing |
| No automated patching | Compliance risk |

---

## Part C: Sustainability Pillar

### Graviton Adoption

```bash
# Instance architecture breakdown
aws ec2 describe-instances --filters Name=instance-state-name,Values=running \
  --query 'Reservations[].Instances[].Architecture' --output text | tr '\t' '\n' | sort | uniq -c

# Graviton-eligible instance types (check if arm64 equivalent exists)
# m5 → m7g, c5 → c7g, r5 → r7g, t3 → t4g
```

### Graviton Migration Mapping
| Current | Graviton Equivalent | Savings |
|---------|-------------------|---------|
| m5/m6i | m7g | ~20% |
| c5/c6i | c7g | ~20% |
| r5/r6i | r7g | ~20% |
| t3 | t4g | ~20% |

### Efficiency Metrics

```bash
# gp2 vs gp3 volume ratio
aws ec2 describe-volumes --query 'Volumes[].VolumeType' --output text | tr '\t' '\n' | sort | uniq -c

# Lambda architecture (arm64 vs x86_64)
aws lambda list-functions --query 'Functions[].Architectures[0]' --output text | tr '\t' '\n' | sort | uniq -c

# Serverless adoption (Lambda function count)
aws lambda list-functions --query 'Functions | length(@)'
```

| Metric | Good | Fair | Needs Attention |
|--------|------|------|-----------------|
| Graviton ratio | >50% | 10-50% | <10% |
| gp3 ratio | >80% | 40-80% | <40% |
| Serverless adoption | Active Lambda use | Minimal | None |
