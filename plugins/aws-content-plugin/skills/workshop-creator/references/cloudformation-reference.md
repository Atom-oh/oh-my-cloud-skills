# CloudFormation Reference for Workshop Studio

Workshop Studio uses CloudFormation to provision workshop infrastructure including Code Editor instances, EKS clusters, and other AWS resources.

## Infrastructure Overview

```
workshop-name/
├── contentspec.yaml                  # References CloudFormation template
└── static/
    ├── workshop.yaml                 # Main CloudFormation template
    └── iam-policy.json              # IAM policy for participants
```

## contentspec.yaml Infrastructure Section

```yaml
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
      label: Workshop Infrastructure
      participantVisibleStackOutputs:
        - URL
      parameters:
        - templateParameter: InstanceType
          defaultValue: "t4g.medium"
        - templateParameter: InstanceVolumeSize
          defaultValue: "40"
```

## Magic Variables

Use these variables in CloudFormation templates and IAM policies:

| Variable | Description | Example Usage |
|----------|-------------|---------------|
| `{{.ParticipantRoleArn}}` | Participant's IAM role ARN | IAM trust policies |
| `{{.AssetsBucketName}}` | Assets S3 bucket name | S3 resource access |
| `{{.AssetsBucketPrefix}}` | Assets bucket prefix | S3 path construction |
| `{{.TeamID}}` | Unique team identifier | Resource naming |
| `{{.AccountId}}` | AWS account ID | ARN construction |
| `{{.AWSRegion}}` | Deployed AWS region | Region-specific resources |

## CloudFormation Template Structure

### Basic Template Layout

```yaml
Description: Workshop infrastructure template. Version 1.0.0

Parameters:
  InstanceType:
    Type: String
    Default: t4g.medium
    AllowedValues: ["t4g.medium", "t4g.large", "m6g.large"]
  InstanceVolumeSize:
    Type: Number
    Default: 40
    MinValue: 20
    MaxValue: 100

Conditions:
  IsGraviton: !Not [!Equals [!Select [0, !Split ["g", ...]], ...]]

Metadata:
  AWS::CloudFormation::Interface:
    ParameterGroups:
      - Label:
          default: Instance Configuration
        Parameters:
          - InstanceType
          - InstanceVolumeSize

Mappings:
  ArmImage:
    AmazonLinux-2023:
      ImageId: "{{resolve:ssm:/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-arm64}}"
    Ubuntu-24:
      ImageId: "{{resolve:ssm:/aws/service/canonical/ubuntu/server/noble/stable/current/arm64/hvm/ebs-gp3/ami-id}}"

Resources:
  # Resources go here

Outputs:
  URL:
    Description: Workshop URL
    Value: !Sub https://${CloudFrontDistribution.DomainName}
```

## Common Resource Patterns

### EC2 Instance with SSM

```yaml
WorkshopInstance:
  Type: AWS::EC2::Instance
  Properties:
    ImageId: !FindInMap [ArmImage, !Ref OperatingSystem, ImageId]
    InstanceType: !Ref InstanceType
    BlockDeviceMappings:
      - DeviceName: /dev/xvda
        Ebs:
          VolumeSize: !Ref InstanceVolumeSize
          VolumeType: gp3
          DeleteOnTermination: true
          Encrypted: true
    IamInstanceProfile: !Ref InstanceProfile
    SecurityGroupIds:
      - !Ref SecurityGroup
    Tags:
      - Key: Name
        Value: !Sub ${AWS::StackName}-workshop
```

### IAM Role with Trust Policy

```yaml
InstanceRole:
  Type: AWS::IAM::Role
  Properties:
    AssumeRolePolicyDocument:
      Version: 2012-10-17
      Statement:
        - Effect: Allow
          Principal:
            Service:
              - !Sub ec2.${AWS::URLSuffix}
              - !Sub ssm.${AWS::URLSuffix}
          Action: sts:AssumeRole
    ManagedPolicyArns:
      - !Sub arn:${AWS::Partition}:iam::aws:policy/AmazonSSMManagedInstanceCore
      - !Sub arn:${AWS::Partition}:iam::aws:policy/CloudWatchAgentServerPolicy
    Policies:
      - PolicyName: WorkshopPolicy
        PolicyDocument:
          Version: 2012-10-17
          Statement:
            - Effect: Allow
              Action:
                - s3:GetObject
                - s3:ListBucket
              Resource:
                - !Sub arn:${AWS::Partition}:s3:::${AssetsBucket}
                - !Sub arn:${AWS::Partition}:s3:::${AssetsBucket}/*
```

### Lambda Function with Custom Resource

```yaml
CustomResourceLambdaRole:
  Type: AWS::IAM::Role
  Properties:
    AssumeRolePolicyDocument:
      Version: 2012-10-17
      Statement:
        - Effect: Allow
          Principal:
            Service: !Sub lambda.${AWS::URLSuffix}
          Action: sts:AssumeRole
    ManagedPolicyArns:
      - !Sub arn:${AWS::Partition}:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

CustomResourceLambda:
  Type: AWS::Lambda::Function
  Properties:
    Description: Custom resource handler
    Handler: index.lambda_handler
    Runtime: python3.13
    MemorySize: 128
    Timeout: 60
    Architectures:
      - arm64
    Role: !GetAtt CustomResourceLambdaRole.Arn
    Code:
      ZipFile: |
        import cfnresponse
        import logging

        logger = logging.getLogger()
        logger.setLevel(logging.INFO)

        def lambda_handler(event, context):
            try:
                if event['RequestType'] == 'Delete':
                    cfnresponse.send(event, context, cfnresponse.SUCCESS, {})
                    return

                # Your logic here
                response_data = {'Result': 'Success'}
                cfnresponse.send(event, context, cfnresponse.SUCCESS, response_data)
            except Exception as e:
                logger.error(e)
                cfnresponse.send(event, context, cfnresponse.FAILED, {}, reason=str(e))

CustomResource:
  Type: Custom::MyResource
  Properties:
    ServiceToken: !GetAtt CustomResourceLambda.Arn
    ServiceTimeout: 120
    # Custom parameters
    Param1: !Ref SomeParameter
```

### SSM Document for Instance Bootstrap

```yaml
BootstrapSSMDoc:
  Type: AWS::SSM::Document
  Properties:
    DocumentType: Command
    Content:
      schemaVersion: "2.2"
      description: Bootstrap workshop instance
      parameters:
        WorkshopFolder:
          type: String
          default: /workshop
      mainSteps:
        - name: InstallPackages
          action: aws:runShellScript
          inputs:
            timeoutSeconds: 600
            runCommand:
              - "#!/bin/bash"
              - set -euo pipefail
              - |
                # Install required packages
                apt-get update
                apt-get install -y git curl jq

        - name: SetupEnvironment
          action: aws:runShellScript
          inputs:
            timeoutSeconds: 300
            runCommand:
              - "#!/bin/bash"
              - !Sub |
                mkdir -p {{ WorkshopFolder }}
                echo "export AWS_REGION=${AWS::Region}" >> /etc/environment
```

### CloudFront Distribution

```yaml
CloudFrontDistribution:
  Type: AWS::CloudFront::Distribution
  Properties:
    DistributionConfig:
      Enabled: True
      HttpVersion: http2and3
      DefaultCacheBehavior:
        AllowedMethods:
          - GET
          - HEAD
          - OPTIONS
          - PUT
          - POST
          - PATCH
          - DELETE
        CachePolicyId: 4135ea2d-6df8-44a3-9df3-4b5a84be39ad  # CachingDisabled
        OriginRequestPolicyId: 216adef6-5c7f-47e4-b989-5492eafa07d3  # AllViewer
        TargetOriginId: !Sub Origin-${AWS::StackName}
        ViewerProtocolPolicy: allow-all
      Origins:
        - DomainName: !GetAtt Instance.PublicDnsName
          Id: !Sub Origin-${AWS::StackName}
          CustomOriginConfig:
            OriginProtocolPolicy: http-only
```

### Security Group for CloudFront Only

```yaml
SecurityGroup:
  Type: AWS::EC2::SecurityGroup
  Properties:
    GroupDescription: Allow CloudFront ingress only
    SecurityGroupIngress:
      - Description: Allow HTTP from CloudFront
        IpProtocol: tcp
        FromPort: 80
        ToPort: 80
        SourcePrefixListId: !FindInMap [CloudFrontPrefixLists, !Ref "AWS::Region", PrefixList]
```

## Step Functions for Long-Running Operations

For operations that exceed Lambda's 15-minute timeout:

```yaml
StateMachine:
  Type: AWS::StepFunctions::StateMachine
  Properties:
    RoleArn: !GetAtt StateMachineRole.Arn
    DefinitionString: !Sub |
      {
        "StartAt": "RunBootstrap",
        "States": {
          "RunBootstrap": {
            "Type": "Task",
            "Resource": "${BootstrapLambda.Arn}",
            "ResultPath": "$.bootstrapResult",
            "Retry": [{"ErrorEquals": ["States.TaskFailed"], "IntervalSeconds": 30, "MaxAttempts": 3}],
            "Next": "WaitForCompletion"
          },
          "WaitForCompletion": {
            "Type": "Task",
            "Resource": "${CheckCompletionLambda.Arn}",
            "Retry": [{"ErrorEquals": ["States.TaskFailed"], "IntervalSeconds": 180, "MaxAttempts": 60}],
            "End": true
          }
        }
      }
```

## IAM Policy File (iam-policy.json)

Participant IAM policy for workshop access:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudformation:ListStacks",
        "cloudformation:DescribeStacks",
        "cloudformation:DescribeStackEvents",
        "cloudformation:DescribeStackResources",
        "cloudformation:GetTemplate"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::{{.AssetsBucketName}}",
        "arn:aws:s3:::{{.AssetsBucketName}}/{{.AssetsBucketPrefix}}/*"
      ]
    }
  ]
}
```

## Best Practices

### Do

1. **Use SSM Parameter Store for AMI IDs**
```yaml
ImageId: "{{resolve:ssm:/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-arm64}}"
```

2. **Use Partition-aware ARNs**
```yaml
!Sub arn:${AWS::Partition}:iam::aws:policy/AmazonSSMManagedInstanceCore
```

3. **Use URL Suffix for service endpoints**
```yaml
!Sub ec2.${AWS::URLSuffix}
```

4. **Add Metadata for cfn_nag suppressions**
```yaml
Metadata:
  cfn_nag:
    rules_to_suppress:
      - id: W58
        reason: Role has AWSLambdaBasicExecutionRole attached
```

5. **Enable encryption for EBS volumes**
```yaml
Ebs:
  Encrypted: true
```

### Don't

1. **Don't hardcode account IDs**
```yaml
# Bad
Resource: arn:aws:s3:::bucket-123456789012

# Good
Resource: !Sub arn:${AWS::Partition}:s3:::bucket-${AWS::AccountId}
```

2. **Don't hardcode regions**
```yaml
# Bad
ImageId: ami-0abcdef1234567890

# Good
ImageId: !FindInMap [RegionMap, !Ref "AWS::Region", AMI]
```

3. **Don't use overly permissive policies**
```yaml
# Bad
Action: "*"
Resource: "*"

# Good - Least privilege
Action:
  - s3:GetObject
  - s3:ListBucket
Resource:
  - !Sub arn:${AWS::Partition}:s3:::${BucketName}
```

## Validation

### cfn-lint

```bash
# Install
pip install cfn-lint

# Validate
cfn-lint static/workshop.yaml
```

### cfn_nag

```bash
# Install
gem install cfn-nag

# Validate
cfn_nag_scan --input-path static/workshop.yaml
```

### AWS CloudFormation Linter (IDE Extension)

VS Code extension for real-time CloudFormation validation.

## Debugging Tips

### Check Stack Events

```bash
aws cloudformation describe-stack-events \
  --stack-name workshop-stack \
  --query 'StackEvents[?ResourceStatus==`CREATE_FAILED`]'
```

### View SSM Command Output

```bash
# List command invocations
aws ssm list-command-invocations \
  --instance-id i-1234567890abcdef0

# Get specific command output
aws ssm get-command-invocation \
  --command-id "command-id" \
  --instance-id "i-1234567890abcdef0"
```

### CloudWatch Logs for Lambda

```bash
aws logs tail /aws/lambda/FunctionName --follow
```

## Common Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| EC2 instance not responding | SSM agent not running | Check IAM role has SSMManagedInstanceCore |
| CloudFront 502 error | Origin not reachable | Check security group allows CloudFront prefix list |
| Lambda timeout | Operation too long | Use Step Functions for long operations |
| cfnresponse not working | Lambda timeout before send | Ensure cfnresponse.send() is called in all paths |
| AMI not found | Region mismatch | Use SSM Parameter Store for latest AMI IDs |
