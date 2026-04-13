# Cost Optimization Pillar — Assessment Reference

## 1. Cost Overview

### Data Commands
```bash
# Monthly cost by service (last 30 days)
aws ce get-cost-and-usage \
  --time-period Start=$(date -d '30 days ago' +%Y-%m-%d),End=$(date +%Y-%m-%d) \
  --granularity MONTHLY --metrics BlendedCost \
  --group-by Type=DIMENSION,Key=SERVICE

# Daily cost trend (7 days)
aws ce get-cost-and-usage \
  --time-period Start=$(date -d '7 days ago' +%Y-%m-%d),End=$(date +%Y-%m-%d) \
  --granularity DAILY --metrics BlendedCost

# Cost by tag (EKS cluster)
aws ce get-cost-and-usage \
  --time-period Start=$(date -d '30 days ago' +%Y-%m-%d),End=$(date +%Y-%m-%d) \
  --granularity MONTHLY --metrics BlendedCost \
  --group-by Type=TAG,Key=eks:cluster-name
```

### Scoring Thresholds
| Condition | Severity |
|-----------|----------|
| Any top-5 service MoM > 20% | Warning |
| Total spend MoM > 15% | Critical |
| Any service > 40% of total | Concentration Risk |

## 2. Compute Cost

### AWS Pricing Benchmarks
| Optimization | Discount |
|-------------|----------|
| Graviton instances | ~20% cheaper than x86 |
| Savings Plans | Up to 72% vs On-Demand |
| Spot instances | Up to 90% (with interruption risk) |
| Lambda ARM (Graviton2) | 20% cheaper than x86 |

### Analysis Commands
```bash
# EC2 instance types and purchasing
aws ec2 describe-instances --query 'Reservations[].Instances[].[InstanceId,InstanceType,Placement.AvailabilityZone,Architecture,State.Name]' --output table

# Savings Plans coverage
aws ce get-savings-plans-coverage \
  --time-period Start=$(date -d '30 days ago' +%Y-%m-%d),End=$(date +%Y-%m-%d) \
  --granularity MONTHLY

# Right-sizing recommendations
aws ce get-rightsizing-recommendation --service AmazonEC2 --configuration RecommendationTarget=SAME_INSTANCE_FAMILY,BenefitsConsidered=true
```

### Analysis Points
- Instance type distribution: Family / Count / Cost / % Total
- Architecture: x86 vs Graviton (arm64) ratio
- Purchasing: On-Demand vs RI vs SP vs Spot breakdown
- Graviton migration candidates table: Current Type / Count / Graviton Equiv / Est. Savings

## 3. Network Cost

### Pricing Reference (ap-northeast-2)
| Service | Rate |
|---------|------|
| NAT Gateway | $0.045/hr + $0.045/GB processed |
| Data Transfer Out (first 10TB) | $0.126/GB |
| Inter-AZ traffic | $0.01/GB each direction ($0.02 round-trip) |
| VPC Gateway Endpoint (S3/DynamoDB) | Free data processing |
| VPC Interface Endpoint | $0.013/hr + $0.01/GB |

### Analysis Commands
```bash
# NAT Gateway list
aws ec2 describe-nat-gateways --query 'NatGateways[].[NatGatewayId,SubnetId,State,Tags[?Key==`Name`].Value|[0]]' --output table

# VPC Endpoints
aws ec2 describe-vpc-endpoints --query 'VpcEndpoints[].[VpcEndpointId,ServiceName,VpcEndpointType,State]' --output table
```

### Key Optimizations
- Deploy Gateway endpoints for S3/DynamoDB (free, eliminates NAT traversal)
- Interface endpoints for ECR/STS/CloudWatch (reduce NAT costs)
- Minimize cross-AZ traffic via topology-aware routing

## 4. Storage Cost

### Pricing Reference
| Storage Class | $/GB/month |
|---------------|-----------|
| S3 Standard | $0.025 |
| S3 Infrequent Access | $0.0138 |
| S3 Glacier Instant Retrieval | $0.005 |
| S3 Glacier Deep Archive | $0.002 |
| EBS gp2 | $0.114 |
| EBS gp3 | $0.0912 (~20% cheaper) |
| EBS Snapshots | $0.05 |

### Analysis Commands
```bash
# S3 bucket list with size (approximate)
aws s3api list-buckets --query 'Buckets[].Name' --output text

# EBS volumes by type
aws ec2 describe-volumes --query 'Volumes[].[VolumeId,VolumeType,Size,State,Attachments[0].InstanceId]' --output table

# Lifecycle policy coverage
aws s3api get-bucket-lifecycle-configuration --bucket <bucket-name> 2>/dev/null
```

### Analysis Points
- S3: class audit, lifecycle policy coverage (With/Without/Coverage %)
- EBS: gp2→gp3 candidates (20% savings), over-sized volumes
- Snapshots: >90 day old snapshots cost, orphaned snapshots

## 5. Idle Resource Detection

### Resource Categories and Commands
```bash
# Unattached EBS volumes
aws ec2 describe-volumes --filters Name=status,Values=available --query 'Volumes[].[VolumeId,VolumeType,Size,CreateTime]' --output table

# Stopped EC2 instances
aws ec2 describe-instances --filters Name=instance-state-name,Values=stopped --query 'Reservations[].Instances[].[InstanceId,InstanceType,Tags[?Key==`Name`].Value|[0],StateTransitionReason]' --output table

# Unassociated Elastic IPs (~$3.60/month each)
aws ec2 describe-addresses --query 'Addresses[?AssociationId==null].[AllocationId,PublicIp]' --output table

# Old snapshots (>90 days)
aws ec2 describe-snapshots --owner-ids self --query "Snapshots[?StartTime<='$(date -d '90 days ago' +%Y-%m-%d)'].[SnapshotId,VolumeSize,StartTime]" --output table

# Unused security groups
aws ec2 describe-security-groups --query 'SecurityGroups[].GroupId' --output text
aws ec2 describe-network-interfaces --query 'NetworkInterfaces[].Groups[].GroupId' --output text
# Diff the two lists to find unused SGs
```

### Scoring
| Condition | Severity |
|-----------|----------|
| Total waste > $500/month | Critical |
| Total waste > $100/month | Optimization recommended |
| > 10 idle resources | Housekeeping overdue |
