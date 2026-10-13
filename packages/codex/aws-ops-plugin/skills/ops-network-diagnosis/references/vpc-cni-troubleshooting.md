# VPC CNI Troubleshooting

IP address management, ENI allocation, and prefix delegation for EKS.

---

## Architecture

VPC CNI assigns real VPC IP addresses to each Pod via two components:
- **IPAMD (L-IPAM Daemon)**: Pre-allocates and manages ENIs and IPs on each node
- **CNI Binary**: Called by kubelet to assign IPs and configure pod network namespaces

## IP Allocation Modes

| Mode | Allocation Unit | Pod Density | Recommended For |
|------|----------------|-------------|-----------------|
| Secondary IP | Individual IPs | Limited by IPs per ENI | Small clusters |
| Prefix Delegation | /28 prefix (16 IPs) | Much higher | Large clusters |

## Instance Type Limits

| Instance Type | Max ENIs | IPv4 per ENI | Max Pods (secondary IP) |
|--------------|----------|-------------|------------------------|
| t3.medium | 3 | 6 | 17 |
| t3.large | 3 | 12 | 35 |
| m5.large | 3 | 10 | 29 |
| m5.xlarge | 4 | 15 | 58 |
| c5.4xlarge | 8 | 30 | 234 |

> Max Pods = (ENIs × IPs per ENI) - ENIs

## Key Environment Variables

| Variable | Description | Default |
|----------|------------|---------|
| `WARM_IP_TARGET` | Spare IPs to pre-allocate | Not set |
| `MINIMUM_IP_TARGET` | Minimum IPs on node | Not set |
| `WARM_ENI_TARGET` | Spare ENIs to pre-allocate | 1 |
| `ENABLE_PREFIX_DELEGATION` | Enable prefix delegation | false |
| `AWS_VPC_K8S_CNI_CUSTOM_NETWORK_CFG` | Enable custom networking | false |

## Diagnostic Commands

```bash
# IPAMD logs
kubectl logs -n kube-system -l k8s-app=aws-node -c aws-node | grep -i "insufficient\|error\|failed"

# Per-node IP usage
kubectl get nodes -o json | jq '.items[] | {name:.metadata.name, allocatable_pods:.status.allocatable.pods}'

# Subnet available IPs
aws ec2 describe-subnets --subnet-ids <subnet-id> --query 'Subnets[].{ID:SubnetId,CIDR:CidrBlock,Available:AvailableIpAddressCount}'

# ENI details per node
aws ec2 describe-network-interfaces --filters Name=attachment.instance-id,Values=<instance-id> --query 'NetworkInterfaces[].{ID:NetworkInterfaceId,PrivateIPs:PrivateIpAddresses|length(@)}'

# IPAMD metrics endpoint
kubectl exec -n kube-system ds/aws-node -c aws-node -- curl -s http://localhost:61678/v1/enis 2>/dev/null | jq .
```

## Common Issues

### IP Exhaustion
**Symptom**: Pods stuck in Pending with IP allocation failure

**Solutions**:
1. Enable Prefix Delegation: `kubectl set env daemonset aws-node -n kube-system ENABLE_PREFIX_DELEGATION=true`
2. Add Secondary CIDR: `aws ec2 associate-vpc-cidr-block --vpc-id <vpc-id> --cidr-block 100.64.0.0/16`
3. Use Custom Networking with dedicated Pod subnets
4. Tune WARM_IP_TARGET: `kubectl set env daemonset aws-node -n kube-system WARM_IP_TARGET=2 MINIMUM_IP_TARGET=4`

### ENI Limit Exceeded
**Symptom**: `ENI limit reached` error

**Solutions**:
1. Use larger instance type with more ENI slots
2. Enable Prefix Delegation (16 IPs per slot instead of 1)
3. Review and clean up branch ENIs from pod security groups

### Recommended Prefix Delegation Settings
```bash
kubectl set env daemonset aws-node -n kube-system \
  ENABLE_PREFIX_DELEGATION=true \
  WARM_PREFIX_TARGET=1 \
  WARM_IP_TARGET=5 \
  MINIMUM_IP_TARGET=2
```

## Subnet CIDR Planning Best Practice

```
VPC CIDR: 10.0.0.0/16
├── 10.0.0.0/19   - Node subnet (AZ-a)
├── 10.0.32.0/19  - Node subnet (AZ-b)
├── 10.0.64.0/19  - Node subnet (AZ-c)
└── Secondary CIDR: 100.64.0.0/16
    ├── 100.64.0.0/19  - Pod subnet (AZ-a)
    ├── 100.64.32.0/19 - Pod subnet (AZ-b)
    └── 100.64.64.0/19 - Pod subnet (AZ-c)
```

## Error → Solution Quick Reference

| Error | Solution |
|-------|---------|
| `InsufficientFreeAddressesInSubnet` | Add secondary CIDR or enable prefix delegation |
| `SecurityGroupLimitExceeded` | Clean up unused SGs or consolidate |
| `ENI limit reached` | Larger instance type or prefix delegation |
| `Failed to create ENI` | Add ENI creation permissions to node role |
| `Timeout waiting for pod IP` | Restart IPAMD: `kubectl rollout restart ds/aws-node -n kube-system` |
