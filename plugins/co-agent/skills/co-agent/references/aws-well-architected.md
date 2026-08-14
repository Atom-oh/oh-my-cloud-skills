# AWS Well-Architected Framework — Deep Review Checklist

Detailed checklist per pillar (6 pillars). Used for reviewing infrastructure code (Terraform, CDK, CloudFormation).

---

## Pillar 1: Operational Excellence

### OPS-01: IaC management
```bash
# Confirm all resources are managed as IaC
# Terraform
terraform state list | wc -l
# CDK
cdk diff 2>&1 | grep -c "Resources"
```
- [ ] All resources are defined as code
- [ ] No manual console changes (drift detection)
- [ ] Separated per environment (dev/staging/prod)

### OPS-02: Observability
- [ ] CloudWatch metrics dashboard
- [ ] Alarms configured (CPU, memory, error rate, latency)
- [ ] Structured logging (JSON format)
- [ ] Distributed tracing (X-Ray, ADOT)
- [ ] Log retention policy

### OPS-03: Change management
- [ ] CI/CD pipeline defined
- [ ] Automated test gates
- [ ] Blue/Green or Canary deployment
- [ ] Automated rollback

---

## Pillar 2: Security

### SEC-01: IAM
```bash
# Detect over-broad permissions
grep -rn "Action.*\"\*\"" --include="*.tf" --include="*.yaml" --include="*.json"
grep -rn "Resource.*\"\*\"" --include="*.tf" --include="*.yaml" --include="*.json"

# Check for AdministratorAccess usage
grep -rn "AdministratorAccess\|PowerUserAccess" --include="*.tf" --include="*.yaml"
```
- [ ] Principle of least privilege
- [ ] Dedicated IAM role per service
- [ ] IRSA / Pod Identity (EKS)
- [ ] Use of temporary credentials

### SEC-02: Data protection
- [ ] Encryption at rest (EBS, S3, RDS: KMS)
- [ ] Encryption in transit (TLS 1.2+)
- [ ] Secrets Manager / SSM Parameter Store
- [ ] S3 bucket public access blocked

### SEC-03: Network
```bash
# Detect security groups open to 0.0.0.0/0
grep -rn "0\.0\.0\.0/0\|::/0" --include="*.tf" --include="*.yaml" | grep -i "ingress\|cidr"
```
- [ ] VPC subnet separation (public/private)
- [ ] Security groups open the minimum ports
- [ ] VPC endpoints (S3, DynamoDB, ECR)
- [ ] WAF applied (public-facing)

---

## Pillar 3: Reliability

### REL-01: High availability
- [ ] Multi-AZ deployment
- [ ] Auto Scaling group configured
- [ ] Health checks (ALB + container)
- [ ] Circuit breaker pattern

### REL-02: Disaster recovery
```bash
# Check backup configuration
grep -rn "backup_retention\|point_in_time_recovery\|backup_window" --include="*.tf" --include="*.yaml"
```
- [ ] RDS automated backups + snapshots
- [ ] S3 versioning
- [ ] Cross-region replication (where required)
- [ ] RPO/RTO defined and tested

### REL-03: Limits management
- [ ] Service Quotas checked
- [ ] Rate limiting (API Gateway throttling)
- [ ] Queue-based load distribution (SQS)
- [ ] Graceful degradation

---

## Pillar 4: Performance Efficiency

### PERF-01: Compute
- [ ] Instance type suited to the workload
- [ ] Graviton processors considered
- [ ] Container resource requests/limits configured
- [ ] Lambda memory/timeout optimized

### PERF-02: Data
- [ ] Database index strategy
- [ ] Read replicas (distribute read load)
- [ ] Caching layer (ElastiCache, DAX)
- [ ] Query performance insights enabled

### PERF-03: Network
- [ ] CloudFront CDN (static content)
- [ ] Global Accelerator (global traffic)
- [ ] VPC endpoints (direct connection to AWS services)
- [ ] Appropriate region selection

---

## Pillar 5: Cost Optimization

### COST-01: Resource efficiency
```bash
# Detect oversized instances
grep -rn "instance_type\|instance_class" --include="*.tf" | grep -iE "xlarge|2xlarge|4xlarge|metal"
```
- [ ] Instance right-sizing
- [ ] Savings Plans / Reserved Instances analysis
- [ ] Spot instance usage (non-mission-critical workloads)
- [ ] Unused resources removed

### COST-02: Cost visibility
- [ ] Resource tagging strategy (team, environment, project)
- [ ] AWS budget alerts configured
- [ ] Cost Explorer dashboard
- [ ] Cost allocation tags

### COST-03: Architecture optimization
- [ ] Serverless migration feasibility (Lambda, Fargate)
- [ ] Storage tiering (S3 Lifecycle)
- [ ] Minimized data transfer cost
- [ ] NAT Gateway vs VPC endpoint

---

## Pillar 6: Sustainability

### SUS-01: Efficient resource use
- [ ] Graviton (ARM) processor adoption
- [ ] Serverless-first architecture
- [ ] Auto scaling to minimize idle resources
- [ ] Appropriate resource sizing

### SUS-02: Data management
- [ ] Data retention policy (TTL)
- [ ] Minimized unnecessary data movement
- [ ] Compression used (S3, logs)

---

## Scoring Guide

Each pillar is scored out of 5:

| Score | Criteria |
|------|------|
| ★★★★★ (5) | All checks pass, best practices followed |
| ★★★★☆ (4) | 1-2 unmet, minor improvement needed |
| ★★★☆☆ (3) | 3-4 unmet, improvement recommended |
| ★★☆☆☆ (2) | 5+ unmet, major improvement needed |
| ★☆☆☆☆ (1) | Basic requirements unmet, immediate action needed |

Per-pillar verdict:
- ★★★★☆ or better: **PASS**
- ★★★☆☆: **REVIEW**
- ★★☆☆☆ or worse: **FAIL**
</content>
</invoke>
