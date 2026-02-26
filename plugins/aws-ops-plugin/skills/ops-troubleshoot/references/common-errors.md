# Common Errors and Solutions

Error message → root cause → solution mapping for EKS operations.

---

## Cluster Errors

| Error Message | Root Cause | Solution |
|--------------|------------|---------|
| `Unable to connect to the server` | API server unreachable | Check VPC endpoint, SG, kubeconfig |
| `error: the server doesn't have a resource type` | API version mismatch | Update kubectl version |
| `Unauthorized` | Invalid/expired token | `aws eks update-kubeconfig --name <cluster>` |
| `certificate signed by unknown authority` | Wrong CA | Update kubeconfig with correct cluster |

## Node Errors

| Error Message | Root Cause | Solution |
|--------------|------------|---------|
| `NodeNotReady` | kubelet stopped, network issue | Check kubelet: `journalctl -u kubelet -n 100` |
| `MemoryPressure` | Node memory exhaustion | Evict pods, increase node size |
| `DiskPressure` | Disk full | Clean images: `crictl rmi --prune`, expand disk |
| `PIDPressure` | Too many processes | Increase PID limit, check for fork bombs |
| `NetworkUnavailable` | CNI plugin failure | Restart aws-node DaemonSet |
| `Taint node.kubernetes.io/not-ready` | Node not ready | Fix underlying condition |
| `node has insufficient CPU/memory` | Resource exhaustion | Scale out node group |

## Pod Errors

| Error Message | Root Cause | Solution |
|--------------|------------|---------|
| `CrashLoopBackOff` | App crash, OOM, config error | `kubectl logs <pod> --previous` |
| `ImagePullBackOff` | Wrong image/tag, auth failure | Check image name, imagePullSecrets |
| `ErrImagePull` | ECR login expired, network | Refresh ECR token, check SG |
| `OOMKilled` | Container exceeded memory limit | Increase memory limit |
| `Evicted` | Node resource pressure | Set resource limits, increase node capacity |
| `CreateContainerConfigError` | Missing ConfigMap/Secret | Verify ConfigMap/Secret exists |
| `FailedScheduling: Insufficient cpu` | No node has enough CPU | Scale out or reduce resource requests |
| `FailedScheduling: pod has unbound PVCs` | PVC not bound | Check StorageClass, CSI driver |

## Network Errors

| Error Message | Root Cause | Solution |
|--------------|------------|---------|
| `InsufficientFreeAddressesInSubnet` | IP exhaustion | Add secondary CIDR, enable prefix delegation |
| `ENI limit reached` | Instance type ENI limit | Use larger instance or prefix delegation |
| `dial tcp: lookup <service>: no such host` | DNS failure | Check CoreDNS, ndots setting |
| `connection refused` | Service not listening | Check pod port, targetPort, service selector |
| `context deadline exceeded` | Timeout | Check SG rules, network policy, routing |
| `502 Bad Gateway` (ALB) | Target unhealthy | Check pod readiness, health check path |
| `503 Service Temporarily Unavailable` | No healthy targets | Check target group registration |

## Storage Errors

| Error Message | Root Cause | Solution |
|--------------|------------|---------|
| `FailedAttachVolume` | AZ mismatch, volume busy | Match PV AZ, force detach old |
| `FailedMount` | Mount point error, SG | Check mount target SG (EFS), device path |
| `MountVolume.SetUp failed for volume` | Filesystem error | Check fsType, securityContext |
| `volume already attached to another node` | Stale attachment | Delete VolumeAttachment, force detach |

## IAM/Auth Errors

| Error Message | Root Cause | Solution |
|--------------|------------|---------|
| `AccessDenied` | Missing IAM permission | Add policy to role |
| `Forbidden: User "system:anonymous"` | Authentication failed | Fix aws-auth ConfigMap or access entries |
| `could not get token` (IRSA) | OIDC provider issue | Verify OIDC provider, trust policy |
| `WebIdentityErr` | Trust policy mismatch | Fix condition in IAM trust policy |
| `An error occurred (AccessDenied) when calling the AssumeRoleWithWebIdentity` | IRSA misconfigured | Check SA annotation, OIDC, trust policy |
