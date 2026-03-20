# Workshop Infrastructure Guide

CloudFormation templates, contentspec.yaml configuration, and magic variables for Workshop Studio.

---

## Contentspec.yaml

Complete configuration file for Workshop Studio:

```yaml
version: 2.0

defaultLocaleCode: en-US
localeCodes:
  - en-US
  - ko-KR

params:
  workshop_title: "Workshop Title"
  workshop_duration: "2 hours"
  difficulty_level: "intermediate"
  target_audience: "engineers"
  prerequisites:
    - "Basic Kubernetes knowledge"
    - "AWS CLI configured"
  workshop_objectives:
    - "Objective 1"
    - "Objective 2"
  technologies:
    - "Amazon EKS"
    - "AWS Lambda"

awsAccountConfig:
  accountSources:
    - WorkshopStudio
  regionConfiguration:
    deployableRegions:
      optional:
        - us-east-1
        - us-west-2
        - ap-northeast-2
    minAccessibleRegions: 1
    maxAccessibleRegions: 3
  participantRole:
    managedPolicies: []
    iamPolicies:
      - static/iam-policy.json

infrastructure:
  cloudformationTemplates:
    - templateLocation: static/workshop.yaml
      label: Workshop
      participantVisibleStackOutputs:
        - URL
      parameters:
        - templateParameter: InstanceType
          defaultValue: "t3.large"
```

### Key Sections

| Section | Purpose |
|---------|---------|
| `version` | Always `2.0` for current Workshop Studio |
| `localeCodes` | Supported languages (en-US, ko-KR, etc.) |
| `params` | Workshop metadata displayed on landing page |
| `awsAccountConfig` | Account provisioning and IAM configuration |
| `infrastructure` | CloudFormation template references |

See `reference/contentspec-complete.md` for all available options.

---

## Magic Variables

Use these variables in CloudFormation templates and IAM policies:

| Variable | Description | Example Use |
|----------|-------------|-------------|
| `{{.ParticipantRoleArn}}` | Participant IAM role ARN | Trust policies |
| `{{.AssetsBucketName}}` | Assets S3 bucket name | S3 access policies |
| `{{.AssetsBucketPrefix}}` | Assets bucket prefix | S3 key construction |
| `{{.TeamID}}` | Unique team identifier | Resource naming |
| `{{.AccountId}}` | AWS account ID | ARN construction |
| `{{.AWSRegion}}` | Deployed AWS region | Regional resources |

### Usage in IAM Policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::{{.AssetsBucketName}}/{{.AssetsBucketPrefix}}/*"
    }
  ]
}
```

### Usage in CloudFormation

```yaml
Parameters:
  ParticipantRoleArn:
    Type: String
    Default: "{{.ParticipantRoleArn}}"

Resources:
  MyBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub "workshop-${AWS::AccountId}-${AWS::Region}"
```

---

## CloudFormation Infrastructure

### Directory Structure

```
static/
├── workshop.yaml       # Main CloudFormation template
└── iam-policy.json     # Participant IAM policy
```

### Common Resource Patterns

| Resource | Purpose | Notes |
|----------|---------|-------|
| EC2 + SSM | Code Editor instance | Ubuntu/AL2023 with VS Code Server |
| CloudFront | HTTPS access | Distribution for EC2 origin |
| Lambda | Custom resources | Use cfnresponse pattern |
| Step Functions | Long-running tasks | SSM Document execution |
| SSM Document | Instance bootstrap | Package install, env setup |

### Template Structure

```yaml
Description: Workshop infrastructure. Version 1.0.0

Parameters:
  InstanceType:
    Type: String
    Default: t4g.medium
    AllowedValues:
      - t4g.medium
      - t4g.large
      - t3.medium
      - t3.large

Conditions:
  IsGraviton: !Or
    - !Equals [!Ref InstanceType, "t4g.medium"]
    - !Equals [!Ref InstanceType, "t4g.large"]

Mappings:
  RegionAMI:
    us-east-1:
      ARM: "{{resolve:ssm:/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-arm64}}"
      X86: "{{resolve:ssm:/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64}}"

Resources:
  WorkshopInstance:
    Type: AWS::EC2::Instance
    Properties:
      InstanceType: !Ref InstanceType
      ImageId: !If [IsGraviton, !FindInMap [RegionAMI, !Ref "AWS::Region", ARM], !FindInMap [RegionAMI, !Ref "AWS::Region", X86]]

  WorkshopRole:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        Version: "2012-10-17"
        Statement:
          - Effect: Allow
            Principal:
              Service: ec2.amazonaws.com
            Action: sts:AssumeRole

Outputs:
  URL:
    Description: Workshop URL
    Value: !Sub "https://${CloudFrontDistribution.DomainName}"
```

### Validation Commands

```bash
# Install cfn-lint
pip install cfn-lint

# Validate template
cfn-lint static/workshop.yaml

# Install cfn_nag (security checks)
gem install cfn-nag

# Security scan
cfn_nag_scan --input-path static/workshop.yaml
```

### Best Practices

1. **Use SSM Parameter Store** for AMI IDs (auto-updated)
2. **Support both ARM and x86** with Conditions
3. **Output the workshop URL** for participant access
4. **Use Step Functions** for long-running bootstrap tasks (>15 min)
5. **Tag all resources** with workshop name for cost tracking

See `reference/cloudformation-reference.md` for detailed patterns.
