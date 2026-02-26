# Network Security Audit

Security group, network policy, and VPC endpoint audit procedures.

---

## Security Group Audit

### EKS Cluster Security Groups
```bash
# Get cluster security group
CLUSTER_SG=$(aws eks describe-cluster --name $CLUSTER_NAME --query 'cluster.resourcesVpcConfig.clusterSecurityGroupId' --output text)

# Check rules
aws ec2 describe-security-group-rules --filter Name=group-id,Values=$CLUSTER_SG --query 'SecurityGroupRules[].{Direction:IsEgress,Protocol:IpProtocol,FromPort:FromPort,ToPort:ToPort,Source:CidrIpv4,SourceSG:ReferencedGroupInfo.GroupId}'
```

### Node Security Groups
```bash
# Find node security groups
aws ec2 describe-instances \
  --filters Name=tag:eks:cluster-name,Values=$CLUSTER_NAME \
  --query 'Reservations[].Instances[].SecurityGroups[].GroupId' --output text | sort -u | while read sg; do
  echo "=== $sg ==="
  aws ec2 describe-security-group-rules --filter Name=group-id,Values=$sg --query 'SecurityGroupRules[?!IsEgress].{Protocol:IpProtocol,FromPort:FromPort,ToPort:ToPort,Source:CidrIpv4,SourceSG:ReferencedGroupInfo.GroupId}'
done
```

### Security Group Red Flags
| Finding | Risk | Remediation |
|---------|------|-------------|
| Inbound 0.0.0.0/0 on non-443/80 | HIGH | Restrict to specific CIDRs |
| Outbound 0.0.0.0/0 all ports | MEDIUM | Restrict to necessary services |
| SSH (22) open to 0.0.0.0/0 | CRITICAL | Use SSM Session Manager instead |
| Unused security groups | LOW | Clean up stale SGs |

## Network Policy Audit

### Coverage Assessment
```bash
# Namespaces without network policies
for ns in $(kubectl get ns -o jsonpath='{.items[*].metadata.name}'); do
  policies=$(kubectl get networkpolicies -n $ns 2>/dev/null | tail -n +2 | wc -l)
  if [ "$policies" -eq "0" ]; then
    echo "WARNING: $ns has no network policies"
  fi
done
```

### Default Deny Policy Template
```yaml
# Apply to every namespace for zero-trust
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
spec:
  podSelector: {}
  policyTypes:
    - Ingress
    - Egress
```

## VPC Endpoint Audit

```bash
# List existing VPC endpoints
aws ec2 describe-vpc-endpoints --filters Name=vpc-id,Values=<vpc-id> --query 'VpcEndpoints[].{Service:ServiceName,Type:VpcEndpointType,State:State}'

# Recommended endpoints for EKS
# - com.amazonaws.REGION.ec2
# - com.amazonaws.REGION.ecr.api
# - com.amazonaws.REGION.ecr.dkr
# - com.amazonaws.REGION.s3
# - com.amazonaws.REGION.sts
# - com.amazonaws.REGION.logs
# - com.amazonaws.REGION.elasticloadbalancing
```

## Cluster Endpoint Access

```bash
# Check endpoint access configuration
aws eks describe-cluster --name $CLUSTER_NAME --query 'cluster.resourcesVpcConfig.{publicAccess:endpointPublicAccess,privateAccess:endpointPrivateAccess,publicCIDRs:publicAccessCidrs}'

# Best practice: Private access + restricted public CIDRs
# Never: Public access from 0.0.0.0/0 in production
```
