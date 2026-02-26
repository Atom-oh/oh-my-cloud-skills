# IAM Security Audit

IAM, IRSA, Pod Identity, and RBAC security audit procedures.

---

## IRSA Audit

### Check All Service Account Annotations
```bash
# List all IRSA-annotated service accounts
kubectl get sa -A -o json | jq '.items[] | select(.metadata.annotations["eks.amazonaws.com/role-arn"] != null) | {namespace:.metadata.namespace, name:.metadata.name, role:.metadata.annotations["eks.amazonaws.com/role-arn"]}'
```

### Verify Trust Policies
```bash
# For each IRSA role, verify trust policy is scoped correctly
ROLE_NAME=<role-name>
aws iam get-role --role-name $ROLE_NAME --query 'Role.AssumeRolePolicyDocument'

# Trust policy should:
# 1. Limit to specific OIDC provider
# 2. Limit to specific namespace:serviceaccount
# 3. Use StringEquals (not StringLike) where possible
```

### Check IRSA Permissions
```bash
# List all policies attached to an IRSA role
aws iam list-attached-role-policies --role-name $ROLE_NAME
aws iam list-role-policies --role-name $ROLE_NAME

# Check for overly permissive policies
aws iam get-role-policy --role-name $ROLE_NAME --policy-name <policy> | jq '.PolicyDocument.Statement[] | select(.Action=="*" or .Resource=="*")'
```

## Pod Identity Audit

```bash
# List all Pod Identity associations
aws eks list-pod-identity-associations --cluster-name $CLUSTER_NAME

# Check each association
for assoc_id in $(aws eks list-pod-identity-associations --cluster-name $CLUSTER_NAME --query 'associations[].associationId' --output text); do
  aws eks describe-pod-identity-association --cluster-name $CLUSTER_NAME --association-id $assoc_id
done
```

## RBAC Audit

### Overly Permissive Roles
```bash
# Find cluster-admin bindings
kubectl get clusterrolebindings -o json | jq '.items[] | select(.roleRef.name=="cluster-admin") | {name:.metadata.name, subjects:.subjects}'

# Find roles with wildcard permissions
kubectl get clusterroles -o json | jq '.items[] | select(.rules[].verbs[] == "*" or .rules[].resources[] == "*") | .metadata.name'

# Check specific user/SA permissions
kubectl auth can-i --list --as=system:serviceaccount:<ns>:<sa>
```

### aws-auth ConfigMap Audit
```bash
# View current mappings
kubectl get configmap aws-auth -n kube-system -o yaml

# Check for:
# 1. Unnecessary admin mappings
# 2. Stale role ARNs
# 3. Overly broad group mappings (system:masters)
```

### Access Entry Audit (EKS API)
```bash
# List all access entries
aws eks list-access-entries --cluster-name $CLUSTER_NAME

# Check each entry
for principal in $(aws eks list-access-entries --cluster-name $CLUSTER_NAME --query 'accessEntries[]' --output text); do
  echo "=== $principal ==="
  aws eks list-associated-access-policies --cluster-name $CLUSTER_NAME --principal-arn $principal
done
```

## Security Best Practices Checklist

| Check | Command | Expected |
|-------|---------|----------|
| No wildcard IAM policies | Check IRSA role policies | No `*` in Action/Resource |
| Trust policy scoped | Check AssumeRolePolicyDocument | Specific namespace:SA |
| No stale IRSA roles | Cross-reference SA and roles | All roles have active SAs |
| Minimal cluster-admin | Check ClusterRoleBindings | Only essential bindings |
| Pod Identity preferred | Check associations vs IRSA | Migrated where possible |
| Audit logging enabled | Check cluster config | authenticator + audit enabled |
