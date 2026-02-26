# Health Check Procedures

Detailed step-by-step procedures for each health check domain.

---

## Cluster Health Check

### EKS Control Plane
```bash
# API server responsiveness
time kubectl get --raw /healthz
time kubectl get --raw /readyz

# Cluster version and status
aws eks describe-cluster --name $CLUSTER_NAME --query 'cluster.{status:status,version:version,platformVersion:platformVersion,endpoint:endpoint}'

# Control plane logging status
aws eks describe-cluster --name $CLUSTER_NAME --query 'cluster.logging.clusterLogging'

# Add-on status
aws eks list-addons --cluster-name $CLUSTER_NAME --output table
for addon in $(aws eks list-addons --cluster-name $CLUSTER_NAME --output text); do
  echo "--- $addon ---"
  aws eks describe-addon --cluster-name $CLUSTER_NAME --addon-name $addon --query 'addon.{version:addonVersion,status:status,health:health.issues}'
done
```

### Node Health
```bash
# Node conditions check
kubectl get nodes -o json | jq '.items[] | {
  name: .metadata.name,
  ready: [.status.conditions[] | select(.type=="Ready") | .status][0],
  memory_pressure: [.status.conditions[] | select(.type=="MemoryPressure") | .status][0],
  disk_pressure: [.status.conditions[] | select(.type=="DiskPressure") | .status][0],
  pid_pressure: [.status.conditions[] | select(.type=="PIDPressure") | .status][0]
}'

# Node resource utilization
kubectl top nodes --sort-by=cpu
kubectl top nodes --sort-by=memory

# Node ages (find stale nodes)
kubectl get nodes -o json | jq '.items[] | {name:.metadata.name, age:.metadata.creationTimestamp, instance_type:.metadata.labels["node.kubernetes.io/instance-type"]}'
```

### Workload Health
```bash
# Deployment health
kubectl get deployments -A -o json | jq '.items[] | select(.status.replicas != .status.readyReplicas) | {name:.metadata.name, ns:.metadata.namespace, replicas:.status.replicas, ready:.status.readyReplicas}'

# StatefulSet health
kubectl get statefulsets -A -o json | jq '.items[] | select(.status.replicas != .status.readyReplicas) | {name:.metadata.name, ns:.metadata.namespace, replicas:.status.replicas, ready:.status.readyReplicas}'

# DaemonSet health
kubectl get daemonsets -A -o json | jq '.items[] | select(.status.desiredNumberScheduled != .status.numberReady) | {name:.metadata.name, ns:.metadata.namespace, desired:.status.desiredNumberScheduled, ready:.status.numberReady}'

# Jobs stuck
kubectl get jobs -A -o json | jq '.items[] | select(.status.active > 0) | select(now - (.status.startTime | fromdateiso8601) > 3600) | {name:.metadata.name, ns:.metadata.namespace, active:.status.active}'
```

### Network Health
```bash
# CoreDNS health
kubectl get pods -n kube-system -l k8s-app=kube-dns -o wide
kubectl logs -n kube-system -l k8s-app=kube-dns --tail=10

# VPC CNI health
kubectl get pods -n kube-system -l k8s-app=aws-node -o wide
kubectl logs -n kube-system -l k8s-app=aws-node -c aws-node --tail=10

# Subnet IP availability
for subnet in $(aws ec2 describe-subnets --filters Name=tag:kubernetes.io/cluster/$CLUSTER_NAME,Values=owned Name=tag:kubernetes.io/cluster/$CLUSTER_NAME,Values=shared --query 'Subnets[].SubnetId' --output text 2>/dev/null); do
  aws ec2 describe-subnets --subnet-ids $subnet --query 'Subnets[].{ID:SubnetId,AZ:AvailabilityZone,Available:AvailableIpAddressCount,CIDR:CidrBlock}'
done
```

### Storage Health
```bash
# PVC status
kubectl get pvc -A -o json | jq '.items[] | {ns:.metadata.namespace, name:.metadata.name, status:.status.phase, size:.spec.resources.requests.storage, storageClass:.spec.storageClassName}'

# CSI driver health
kubectl get pods -n kube-system -l app=ebs-csi-controller -o wide
kubectl get pods -n kube-system -l app=efs-csi-controller -o wide

# Unused PVs
kubectl get pv --field-selector status.phase=Released
```

### Security Health
```bash
# Privileged containers
kubectl get pods -A -o json | jq '[.items[] | select(.spec.containers[].securityContext.privileged==true) | {name:.metadata.name, ns:.metadata.namespace}]'

# Pods running as root
kubectl get pods -A -o json | jq '[.items[] | select(.spec.securityContext.runAsUser==0 or .spec.containers[].securityContext.runAsUser==0) | {name:.metadata.name, ns:.metadata.namespace}]'

# Network policies
kubectl get networkpolicies -A

# Secrets without encryption
kubectl get secrets -A -o json | jq '.items | length'
```
