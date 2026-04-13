# Security & Reliability Pillars — Assessment Reference

---

## Part A: Security Pillar

### Security Score (100-point)

| Category | Deduction | Max Deduction |
|----------|-----------|--------------|
| Public Exposure issues | -15 each | -30 |
| Encryption gaps | -10 each | -30 |
| IAM Hygiene issues | -5 each | -20 |
| Compliance gaps | -5 each | -20 |

### Public Exposure Checklist

| Finding | Severity | Command |
|---------|----------|---------|
| Public S3 buckets (block public access disabled) | Critical | `aws s3api get-public-access-block --bucket <name>` |
| SG allowing 0.0.0.0/0 on ports 22,3389,3306,5432,6379,9200 | Critical | `aws ec2 describe-security-groups --filters Name=ip-permission.cidr,Values=0.0.0.0/0 --query 'SecurityGroups[].[GroupId,GroupName]'` |
| Public RDS/ElastiCache/OpenSearch | Critical | `aws rds describe-db-instances --query 'DBInstances[?PubliclyAccessible==\`true\`].[DBInstanceIdentifier,Engine]'` |
| Public ELBs without WAF | Warning | `aws elbv2 describe-load-balancers --query 'LoadBalancers[?Scheme==\`internet-facing\`].[LoadBalancerArn,LoadBalancerName]'` |
| EC2 with public IP in private subnet | Warning | Check route table for IGW presence |

### Encryption Coverage Matrix

Check encryption for each resource type:

```bash
# EBS encryption
aws ec2 describe-volumes --query 'Volumes[].[VolumeId,Encrypted]' --output table

# RDS encryption
aws rds describe-db-instances --query 'DBInstances[].[DBInstanceIdentifier,StorageEncrypted]' --output table

# S3 default encryption
aws s3api get-bucket-encryption --bucket <name> 2>/dev/null

# ElastiCache encryption
aws elasticache describe-cache-clusters --query 'CacheClusters[].[CacheClusterId,AtRestEncryptionEnabled,TransitEncryptionEnabled]' --output table
```

Output table: Resource Type / Total / Encrypted / Unencrypted / Coverage %

### IAM Security Assessment

```bash
# Root account MFA
aws iam get-account-summary --query 'SummaryMap.AccountMFAEnabled'

# IAM users without MFA
aws iam generate-credential-report && sleep 5
aws iam get-credential-report --query 'Content' --output text | base64 -d | awk -F, 'NR>1 && $4=="true" && $8=="false" {print $1}'

# Access keys older than 90 days
aws iam generate-credential-report && sleep 3
aws iam get-credential-report --query 'Content' --output text | base64 -d | awk -F, 'NR>1 && $9=="true" {print $1, $10}'

# Overly permissive policies (AdministratorAccess)
aws iam list-entities-for-policy --policy-arn arn:aws:iam::aws:policy/AdministratorAccess --query '{Users:PolicyUsers[].UserName,Roles:PolicyRoles[].RoleName}'
```

---

## Part B: Reliability Pillar

### Network Architecture Assessment

```bash
# VPC inventory with subnets and AZ distribution
aws ec2 describe-vpcs --query 'Vpcs[].[VpcId,CidrBlock,Tags[?Key==`Name`].Value|[0]]' --output table

# Subnets per AZ
aws ec2 describe-subnets --query 'Subnets[].[SubnetId,VpcId,AvailabilityZone,CidrBlock,MapPublicIpOnLaunch]' --output table

# NAT Gateway redundancy per VPC
aws ec2 describe-nat-gateways --filter Name=state,Values=available --query 'NatGateways[].[NatGatewayId,VpcId,SubnetId,Tags[?Key==`Name`].Value|[0]]' --output table
```

### NAT Gateway Redundancy Rules
| Condition | Severity |
|-----------|----------|
| Production VPC with 1 NAT Gateway | Critical |
| Private subnets routing to NAT in different AZ | Warning |
| Best practice: 1 NAT Gateway per AZ | — |

### AZ Coverage Analysis
- Flag VPCs with resources in only 1 AZ → Single Point of Failure
- Check: workloads distributed across >= 2 AZs?
- RDS/ElastiCache in single AZ (production) → Critical

### SPOF Detection Framework

Check each category for single points of failure:
1. **Network**: Single NAT GW, single VPN tunnel, no redundant Direct Connect
2. **Compute**: ASG min=max=1, standalone EC2 (no ASG)
3. **Data**: Single-AZ RDS (production), no read replicas for read-heavy workloads
4. **DNS**: No health check on Route 53 records

### Database Reliability

```bash
# RDS Multi-AZ check
aws rds describe-db-instances --query 'DBInstances[].[DBInstanceIdentifier,Engine,EngineVersion,MultiAZ,StorageEncrypted,BackupRetentionPeriod]' --output table

# Engine version currency
aws rds describe-db-engine-versions --engine mysql --query 'DBEngineVersions[?Status==`deprecated`].EngineVersion'
```

| Finding | Severity |
|---------|----------|
| Production DB without Multi-AZ | Critical |
| Backup retention < 7 days | Warning |
| Deprecated engine version | Warning |
| No automated backups | Critical |

### Compute Reliability

```bash
# ASG coverage (instances in ASG vs standalone)
aws autoscaling describe-auto-scaling-instances --query 'AutoScalingInstances[].InstanceId' --output text
aws ec2 describe-instances --filters Name=instance-state-name,Values=running --query 'Reservations[].Instances[].InstanceId' --output text
# Compare: ASG instances / total running instances = ASG coverage %

# ASG scaling policy audit
aws autoscaling describe-policies --query 'ScalingPolicies[].[AutoScalingGroupName,PolicyName,PolicyType]' --output table
```

| Finding | Severity |
|---------|----------|
| Production EC2 without ASG | Warning |
| ASG with min=max=desired (no scaling) | Warning |
| Old-gen instances (m4, c4, r4) | Info |
