# Load Balancer Troubleshooting

ALB and NLB troubleshooting for EKS with AWS Load Balancer Controller.

---

## Prerequisites Checklist

1. **LB Controller installed**: `kubectl get deployment -n kube-system aws-load-balancer-controller`
2. **IRSA configured**: Service account has correct IAM role annotation
3. **Subnet tags**: Public subnets tagged `kubernetes.io/role/elb=1`, private subnets tagged `kubernetes.io/role/internal-elb=1`
4. **IngressClass**: `kubectl get ingressclass` shows `alb` class

## Key Annotations Reference

### ALB (Ingress)
| Annotation | Description | Default |
|------------|-------------|---------|
| `alb.ingress.kubernetes.io/scheme` | internet-facing or internal | internal |
| `alb.ingress.kubernetes.io/target-type` | ip or instance | instance |
| `alb.ingress.kubernetes.io/subnets` | Subnet IDs | Auto-detect |
| `alb.ingress.kubernetes.io/certificate-arn` | ACM cert ARN | - |
| `alb.ingress.kubernetes.io/healthcheck-path` | Health check path | / |
| `alb.ingress.kubernetes.io/group.name` | Share ALB across Ingresses | - |

### NLB (Service)
| Annotation | Description | Default |
|------------|-------------|---------|
| `service.beta.kubernetes.io/aws-load-balancer-type` | external (NLB) | - |
| `service.beta.kubernetes.io/aws-load-balancer-nlb-target-type` | ip or instance | instance |
| `service.beta.kubernetes.io/aws-load-balancer-scheme` | internet-facing or internal | internal |
| `service.beta.kubernetes.io/aws-load-balancer-ssl-cert` | ACM cert ARN | - |

## Common Issues

### ALB Not Created
```bash
# Check controller logs
kubectl logs -n kube-system -l app.kubernetes.io/name=aws-load-balancer-controller --tail=50

# Check Ingress events
kubectl describe ingress <name> -n <namespace>

# Common causes:
# 1. Missing IngressClass: add spec.ingressClassName: alb
# 2. Missing subnet tags
# 3. IAM permission insufficient
# 4. Invalid annotation values
```

### Targets Unhealthy
```bash
# Check target health
aws elbv2 describe-target-health --target-group-arn <arn>

# Test health check from pod
kubectl exec -it <pod> -- curl -s localhost:<port><health-path>

# Common causes:
# 1. Health check path returns non-200
# 2. Security group blocks ALB→Pod traffic
# 3. Pod not ready/running
# 4. Wrong targetPort
```

### 502 Bad Gateway
Root causes:
1. **Pod not ready** — Check pod status and readiness probe
2. **Target deregistering** — Target group draining in progress
3. **Health check failing** — Verify health check path and timeout
4. **Security group** — ALB SG must allow traffic to pod CIDR

```bash
# Debugging steps
kubectl get pods -l app=<app>
aws elbv2 describe-target-health --target-group-arn <arn>
kubectl describe ingress <name>
```

### SSL Certificate Issues
```bash
# Certificate must be:
# 1. In ISSUED status
# 2. In same region as ALB
# 3. Domain validation completed
aws acm describe-certificate --certificate-arn <arn> --query 'Certificate.{Status:Status,DomainName:DomainName}'
```

## Subnet Tagging

```bash
# Public subnets (internet-facing LB)
aws ec2 create-tags --resources <subnet-id> --tags Key=kubernetes.io/role/elb,Value=1

# Private subnets (internal LB)
aws ec2 create-tags --resources <subnet-id> --tags Key=kubernetes.io/role/internal-elb,Value=1

# Cluster tag (optional)
aws ec2 create-tags --resources <subnet-id> --tags Key=kubernetes.io/cluster/$CLUSTER_NAME,Value=shared
```

## Cost Optimization

Share a single ALB across multiple services using Ingress groups:
```yaml
# In each Ingress:
alb.ingress.kubernetes.io/group.name: shared-alb
alb.ingress.kubernetes.io/group.order: "1"  # Priority within group
```
