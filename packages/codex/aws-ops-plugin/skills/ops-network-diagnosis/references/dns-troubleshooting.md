# DNS Troubleshooting

CoreDNS, Route 53, and DNS resolution issues in EKS.

---

## CoreDNS Architecture in EKS

CoreDNS runs as a Deployment in kube-system namespace and provides:
- Service discovery (`.svc.cluster.local`)
- Pod DNS (`.pod.cluster.local`)
- External DNS forwarding (to VPC DNS resolver at 169.254.169.253)

## Diagnostic Commands

```bash
# CoreDNS status
kubectl get pods -n kube-system -l k8s-app=kube-dns -o wide
kubectl get svc -n kube-system kube-dns

# CoreDNS logs
kubectl logs -n kube-system -l k8s-app=kube-dns --tail=30

# CoreDNS config
kubectl get configmap coredns -n kube-system -o yaml

# DNS resolution test
kubectl run -it --rm dns-test --image=busybox:1.28 --restart=Never -- nslookup kubernetes.default.svc.cluster.local

# DNS latency test
kubectl run -it --rm dns-test --image=busybox:1.28 --restart=Never -- sh -c 'for i in $(seq 1 10); do time nslookup kubernetes.default 2>&1 | grep real; done'
```

## Common Issues

### DNS Resolution Timeout
**Symptoms**: `nslookup: can't resolve`, `dial tcp: lookup: no such host`

**Causes & Solutions**:
1. **CoreDNS not running**: `kubectl rollout restart deployment/coredns -n kube-system`
2. **CoreDNS overloaded**: Scale replicas or enable autoscaling
3. **ndots too high**: Default ndots=5 causes 5 DNS lookups for external names
   ```yaml
   # Pod spec optimization
   spec:
     dnsConfig:
       options:
         - name: ndots
           value: "2"
   ```
4. **VPC DNS throttling**: VPC resolver has 1024 packets/sec/ENI limit

### CoreDNS Scaling
```bash
# Check current replicas
kubectl get deployment coredns -n kube-system

# Manual scale
kubectl scale deployment coredns -n kube-system --replicas=3

# Enable autoscaling (proportional-autoscaler)
kubectl apply -f https://raw.githubusercontent.com/kubernetes-sigs/cluster-proportional-autoscaler/master/examples/dns-autoscaler.yaml
```

### CoreDNS ConfigMap Customization
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: coredns
  namespace: kube-system
data:
  Corefile: |
    .:53 {
        errors
        health
        kubernetes cluster.local in-addr.arpa ip6.arpa {
          pods insecure
          fallthrough in-addr.arpa ip6.arpa
        }
        prometheus :9153
        forward . /etc/resolv.conf
        cache 30
        loop
        reload
        loadbalance
    }
    # Custom zone forwarding
    example.com:53 {
        forward . 10.0.0.2
        cache 30
    }
```

### External DNS Not Resolving from Pods
```bash
# Check pod's resolv.conf
kubectl exec -it <pod> -- cat /etc/resolv.conf

# Expected:
# nameserver 172.20.0.10  (kube-dns service IP)
# search <namespace>.svc.cluster.local svc.cluster.local cluster.local
# options ndots:5

# If nameserver is wrong, check kubelet --cluster-dns setting
```

## Route 53 Integration

### external-dns Controller
```bash
# Check external-dns status
kubectl get pods -n kube-system -l app=external-dns
kubectl logs -n kube-system -l app=external-dns --tail=20

# Verify DNS record created
aws route53 list-resource-record-sets --hosted-zone-id <zone-id> --query "ResourceRecordSets[?Name=='<domain>.']"
```

## Error → Solution Quick Reference

| Symptom | Likely Cause | Solution |
|---------|-------------|---------|
| All DNS fails | CoreDNS down | Restart CoreDNS |
| External DNS slow | High ndots | Set ndots=2 in pod spec |
| Service discovery fails | Wrong namespace | Use FQDN: `svc.namespace.svc.cluster.local` |
| Route53 record not created | external-dns IAM | Fix IRSA for external-dns |
| Intermittent failures | DNS throttling | Scale CoreDNS, use NodeLocal DNSCache |
