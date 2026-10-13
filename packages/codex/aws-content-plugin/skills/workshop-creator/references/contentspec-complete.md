# Workshop Studio Contentspec Complete Reference

The complete reference for the `contentspec.yaml` file.

---

## Basic structure

```yaml
version: 2.0

defaultLocaleCode: ko-KR

localeCodes:
  - ko-KR
  - en-US

awsAccountConfig:
  # ... AWS account settings

infrastructure:
  # ... infrastructure settings
```

---

## Basic settings

### version (required)

```yaml
version: 2.0  # always use 2.0
```

### defaultLocaleCode (required)

The default locale code (languageCode-countryCode format)

```yaml
defaultLocaleCode: ko-KR
```

### localeCodes (required)

The list of all supported locale codes

```yaml
localeCodes:
  - ko-KR
  - en-US
  - ja-JP
```

### params (optional)

Parameters referenceable within the workshop. A **free-form YAML dictionary** that allows scalars, nested
objects, and arrays with no fixed schema. It is unrelated to CloudFormation and is for content text only.

```yaml
params:
  clusterName: my-eks-cluster
  region: ap-northeast-2
  nodeCount: 3
  contact:
    name: John Doe
  levels:
    - 100
    - 200
```

Used in markdown (dot notation for nested keys, bracket/dot notation for array index access):
```markdown
Cluster name: :param{key="clusterName"}
Contact: :param{key=contact.name}
Difficulty: :param{key=levels[0]}
Fallback for a missing value: :param{key=missingKey defaultValue="N/A"}
```

Details (distinction from operator overrides / CFN parameters): `references/event-params-guide.md`

### additionalLinks (optional)

Additional links shown in the navigation

```yaml
additionalLinks:
  - title: AWS Documentation
    link: https://docs.aws.amazon.com/
  - title: EKS User Guide
    link: https://docs.aws.amazon.com/eks/
```

---

## awsAccountConfig

AWS account-related settings.

### accountSources (required)

```yaml
awsAccountConfig:
  accountSources:
    - workshop_studio    # Workshop Studio provides the account
    - customer_provided  # participants use their own account
```

### serviceLinkedRoles (optional)

Service-linked roles to auto-create

```yaml
  serviceLinkedRoles:
    - appsync.amazonaws.com
    - ecs.amazonaws.com
    - eks.amazonaws.com
```

### participantRole

Participant role settings

```yaml
  participantRole:
    # IAM policy file path (under static/)
    iamPolicies:
      - static/iam/workshop-policy.json

    # AWS managed policies
    managedPolicies:
      - "arn:aws:iam::aws:policy/IAMReadOnlyAccess"
      - "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"

    # Trusted principals
    trustedPrincipals:
      service:
        - ec2.amazonaws.com
        - lambda.amazonaws.com
        - eks.amazonaws.com
```

### ec2KeyPair (optional)

Auto-generate an EC2 key pair

```yaml
  ec2KeyPair: true  # creates ws-default-keypair
```

### regionConfiguration

Region settings

```yaml
  regionConfiguration:
    minAccessibleRegions: 1
    maxAccessibleRegions: 3

    # Regions for deployment
    deployableRegions:
      required:
        - ap-northeast-2
      recommended:
        - ap-northeast-2
        - us-east-1
      optional:
        - us-west-2
        - eu-west-1

    # Accessible regions (access only, no deployment)
    accessibleRegions:
      required:
        - ap-northeast-2
      recommended:
        - us-east-1
      optional:
        - us-west-2
```

---

## infrastructure

CloudFormation template deployment settings

```yaml
infrastructure:
  cloudformationTemplates:
    - templateLocation: static/cfn/base-stack.yaml
      label: Base Infrastructure
      tags:
        - key: Environment
          value: Workshop
      # [optional] Outputs to expose to participants (default: not exposed)
      participantVisibleStackOutputs:
        - VpcId
      parameters:
        - templateParameter: VPCCidr
          defaultValue: "10.0.0.0/16"
        - templateParameter: ParticipantRoleArn
          defaultValue: "{{.ParticipantRoleArn}}"

    - templateLocation: static/cfn/eks-stack.yaml
      label: EKS Cluster
      parameters:
        - templateParameter: ClusterName
          defaultValue: workshop-cluster
          # [optional] if true, the event operator can override this value per event
          userOverridable: true
```

For details on the `userOverridable` parameter flag and the Output exposure rules
(`participantVisibleStackOutputs` / `participantAllStackOutputsVisible`), including operator-facing usage,
see: `references/event-params-guide.md`

### requiredResources (optional)

Requesting special resources that exceed standard account limits (e.g. GPU instances). **Only one service
can be declared per piece of content** — the only currently allowed services are `sagemaker` and
`guardduty`, and the type/quantity must exactly match the allow-list. Details: `references/event-quotas-guide.md`

```yaml
  requiredResources:
    sagemaker:
      - type: endpoint/ml.g5.12xlarge
        quantity: 1
```

---

## centralAccountInfrastructure (optional)

Infrastructure settings for a shared account (the "central account") separate from team accounts — at most
one per event. Shares the same field structure as `infrastructure`, differing only in that the target is
the central account rather than teams. Up to 5 templates can be defined. Define this only when the workshop
needs shared resources or gamification.

```yaml
centralAccountInfrastructure:
  cloudformationTemplates:
    - templateLocation: static/cfn/central-stack.yaml
      label: Central Account Stack
      tags:
        - key: Environment
          value: Workshop
      # [optional] specify only the Outputs to expose to participants
      participantVisibleStackOutputs:
        - LeaderboardUrl
      # [optional] expose all Outputs/Exports (default false)
      participantAllStackOutputsVisible: false
      parameters:
        - templateParameter: NotificationBusArn
          defaultValue: "{{.NotificationBusArn}}"
        - templateParameter: WSEventsAPIEndpoint
          defaultValue: "{{.WSEventsAPIEndpoint}}"
        - templateParameter: WksEventsRegion
          defaultValue: "{{.WSEventsAPIRegion}}"
```

For the concept (when to use it), the Central Account Client API, NotificationBus lifecycle notifications,
and deployment order, see: `references/central-account-guide.md`

---

## Magic Variables

### For Team CloudFormation parameters

| Variable | Description | Example |
|------|------|------|
| `{{.TeamID}}` | unique team ID | `d30035ed-7bef-405a-8741-6144faa15e17` |
| `{{.TeamIndex}}` | team index (starting at 0) | `0`, `1`, `2` |
| `{{.ParticipantRoleName}}` | IAM role name | `WSParticipantRole` |
| `{{.ParticipantRoleArn}}` | IAM role ARN | `arn:aws:iam::123456789012:role/WSParticipantRole` |
| `{{.ParticipantAssumedRoleSessionName}}` | session name | `Participant` |
| `{{.ParticipantAssumedRoleArn}}` | assumed role ARN | `arn:aws:sts::123456789012:assumed-role/WSParticipantRole/Participant` |
| `{{.AssetsBucketName}}` | assets bucket name | `ws-event-2009c59b-6c7-us-east-1` |
| `{{.AssetsBucketPrefix}}` | assets bucket prefix | `371c6734-2735-4958-8749-4f4db058a75f/assets/` |
| `{{.EC2KeyPairName}}` | EC2 key pair name | `ws-default-keypair` |

### For Central CloudFormation parameters

| Variable | Description | Example |
|------|------|------|
| `{{.NotificationBusArn}}` | EventBridge bus ARN | `arn:aws:events:us-east-1:123456789012:event-bus/lifecycle-notification-bus` |
| `{{.AssetsBucketName}}` | assets bucket name | `ws-event-2009c59b-6c7-us-east-1` |
| `{{.AssetsBucketPrefix}}` | assets bucket prefix | `371c6734-2735-4958-8749-4f4db058a75f/assets/` |
| `{{.TeamSize}}` | maximum participants per team | `5` |
| `{{.WSEventsAPIEndpoint}}` | Workshop Studio API endpoint | `events-api.us-east-1.prod.workshops.aws` |
| `{{.WSEventsAPIRegion}}` | Workshop Studio API region | `us-east-1` |

### For IAM Policy JSON

| Variable | Description | Example |
|------|------|------|
| `{{.ParticipantRoleName}}` | IAM role name | `WSParticipantRole` |
| `{{.ParticipantRoleArn}}` | IAM role ARN | `arn:aws:iam::123456789012:role/WSParticipantRole` |
| `{{.ParticipantAssumedRoleSessionName}}` | session name | `Participant` |
| `{{.ParticipantAssumedRoleArn}}` | assumed role ARN | `arn:aws:sts::123456789012:assumed-role/WSParticipantRole/Participant` |
| `{{.AccountId}}` | AWS account ID | `123456789012` |

---

## Full examples

### Basic workshop (account provided)

```yaml
version: 2.0
defaultLocaleCode: ko-KR
localeCodes:
  - ko-KR
  - en-US

awsAccountConfig:
  accountSources:
    - workshop_studio
  participantRole:
    iamPolicies:
      - static/iam/workshop-policy.json
  regionConfiguration:
    minAccessibleRegions: 1
    maxAccessibleRegions: 1
    deployableRegions:
      recommended:
        - ap-northeast-2
        - us-east-1
```

### EKS workshop (infrastructure provisioning)

```yaml
version: 2.0
defaultLocaleCode: ko-KR
localeCodes:
  - ko-KR
  - en-US

awsAccountConfig:
  accountSources:
    - workshop_studio
  serviceLinkedRoles:
    - eks.amazonaws.com
  participantRole:
    iamPolicies:
      - static/iam/eks-workshop-policy.json
    trustedPrincipals:
      service:
        - eks.amazonaws.com
  ec2KeyPair: true
  regionConfiguration:
    minAccessibleRegions: 1
    maxAccessibleRegions: 1
    deployableRegions:
      recommended:
        - ap-northeast-2
        - us-east-1

infrastructure:
  cloudformationTemplates:
    - templateLocation: static/cfn/vpc-stack.yaml
      label: VPC Infrastructure
      parameters:
        - templateParameter: VPCCidr
          defaultValue: "10.0.0.0/16"
    - templateLocation: static/cfn/eks-stack.yaml
      label: EKS Cluster
      parameters:
        - templateParameter: ClusterName
          defaultValue: workshop-cluster
        - templateParameter: ParticipantRoleArn
          defaultValue: "{{.ParticipantRoleArn}}"
```

### BYOA (Bring Your Own Account)

```yaml
version: 2.0
defaultLocaleCode: ko-KR
localeCodes:
  - ko-KR
  - en-US

awsAccountConfig:
  accountSources:
    - customer_provided
```

---

## IAM Policy example

`static/iam/workshop-policy.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "EC2FullAccess",
      "Effect": "Allow",
      "Action": [
        "ec2:*"
      ],
      "Resource": "*"
    },
    {
      "Sid": "EKSFullAccess",
      "Effect": "Allow",
      "Action": [
        "eks:*"
      ],
      "Resource": "*"
    },
    {
      "Sid": "S3ReadAccess",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": "*"
    },
    {
      "Sid": "IAMPassRole",
      "Effect": "Allow",
      "Action": [
        "iam:PassRole"
      ],
      "Resource": "{{.ParticipantRoleArn}}"
    }
  ]
}
```
