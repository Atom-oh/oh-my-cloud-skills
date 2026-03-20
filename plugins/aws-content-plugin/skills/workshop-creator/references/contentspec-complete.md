# Workshop Studio Contentspec Complete Reference

`contentspec.yaml` 파일의 전체 레퍼런스입니다.

---

## 기본 구조

```yaml
version: 2.0

defaultLocaleCode: ko-KR

localeCodes:
  - ko-KR
  - en-US

awsAccountConfig:
  # ... AWS 계정 설정

infrastructure:
  # ... 인프라 설정
```

---

## 기본 설정

### version (필수)

```yaml
version: 2.0  # 항상 2.0 사용
```

### defaultLocaleCode (필수)

기본 로케일 코드 (languageCode-countryCode 형식)

```yaml
defaultLocaleCode: ko-KR
```

### localeCodes (필수)

지원하는 모든 로케일 코드 목록

```yaml
localeCodes:
  - ko-KR
  - en-US
  - ja-JP
```

### params (선택)

워크샵 내에서 참조할 수 있는 파라미터

```yaml
params:
  clusterName: my-eks-cluster
  region: ap-northeast-2
  nodeCount: 3
```

마크다운에서 사용:
```markdown
클러스터 이름: :param{key="clusterName"}
```

### additionalLinks (선택)

네비게이션에 표시할 추가 링크

```yaml
additionalLinks:
  - title: AWS Documentation
    link: https://docs.aws.amazon.com/
  - title: EKS User Guide
    link: https://docs.aws.amazon.com/eks/
```

---

## awsAccountConfig

AWS 계정 관련 설정입니다.

### accountSources (필수)

```yaml
awsAccountConfig:
  accountSources:
    - workshop_studio    # Workshop Studio가 계정 제공
    - customer_provided  # 참가자가 자체 계정 사용
```

### serviceLinkedRoles (선택)

자동 생성할 서비스 연결 역할

```yaml
  serviceLinkedRoles:
    - appsync.amazonaws.com
    - ecs.amazonaws.com
    - eks.amazonaws.com
```

### participantRole

참가자 역할 설정

```yaml
  participantRole:
    # IAM 정책 파일 경로 (static/ 하위)
    iamPolicies:
      - static/iam/workshop-policy.json

    # AWS 관리형 정책
    managedPolicies:
      - "arn:aws:iam::aws:policy/IAMReadOnlyAccess"
      - "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"

    # 신뢰 주체
    trustedPrincipals:
      service:
        - ec2.amazonaws.com
        - lambda.amazonaws.com
        - eks.amazonaws.com
```

### ec2KeyPair (선택)

EC2 키 페어 자동 생성

```yaml
  ec2KeyPair: true  # ws-default-keypair 생성
```

### regionConfiguration

리전 설정

```yaml
  regionConfiguration:
    minAccessibleRegions: 1
    maxAccessibleRegions: 3

    # 배포 리전
    deployableRegions:
      required:
        - ap-northeast-2
      recommended:
        - ap-northeast-2
        - us-east-1
      optional:
        - us-west-2
        - eu-west-1

    # 접근 가능 리전 (배포 없이 접근만)
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

CloudFormation 템플릿 배포 설정

```yaml
infrastructure:
  cloudformationTemplates:
    - templateLocation: static/cfn/base-stack.yaml
      label: Base Infrastructure
      tags:
        - key: Environment
          value: Workshop
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
```

### requiredResources (선택)

특별 리소스 요청 (예: GPU 인스턴스)

```yaml
  requiredResources:
    sagemaker:
      - type: endpoint/ml.g5.12xlarge
        quantity: 1
    ec2:
      - type: p3.2xlarge
        quantity: 1
```

---

## centralAccountInfrastructure (선택)

중앙 계정 인프라 설정

```yaml
centralAccountInfrastructure:
  cloudformationTemplates:
    - templateLocation: static/cfn/central-stack.yaml
      label: Central Account Stack
      parameters:
        - templateParameter: NotificationBusArn
          defaultValue: "{{.NotificationBusArn}}"
        - templateParameter: WSEventsAPIEndpoint
          defaultValue: "{{.WSEventsAPIEndpoint}}"
```

---

## Magic Variables

### Team CloudFormation 파라미터용

| 변수 | 설명 | 예시 |
|------|------|------|
| `{{.TeamID}}` | 팀 고유 ID | `d30035ed-7bef-405a-8741-6144faa15e17` |
| `{{.TeamIndex}}` | 팀 인덱스 (0부터) | `0`, `1`, `2` |
| `{{.ParticipantRoleName}}` | IAM 역할 이름 | `WSParticipantRole` |
| `{{.ParticipantRoleArn}}` | IAM 역할 ARN | `arn:aws:iam::123456789012:role/WSParticipantRole` |
| `{{.ParticipantAssumedRoleSessionName}}` | 세션 이름 | `Participant` |
| `{{.ParticipantAssumedRoleArn}}` | Assumed Role ARN | `arn:aws:sts::123456789012:assumed-role/WSParticipantRole/Participant` |
| `{{.AssetsBucketName}}` | 자산 버킷 이름 | `ws-event-2009c59b-6c7-us-east-1` |
| `{{.AssetsBucketPrefix}}` | 자산 버킷 접두사 | `371c6734-2735-4958-8749-4f4db058a75f/assets/` |
| `{{.EC2KeyPairName}}` | EC2 키페어 이름 | `ws-default-keypair` |

### Central CloudFormation 파라미터용

| 변수 | 설명 | 예시 |
|------|------|------|
| `{{.NotificationBusArn}}` | EventBridge 버스 ARN | `arn:aws:events:us-east-1:123456789012:event-bus/lifecycle-notification-bus` |
| `{{.AssetsBucketName}}` | 자산 버킷 이름 | `ws-event-2009c59b-6c7-us-east-1` |
| `{{.AssetsBucketPrefix}}` | 자산 버킷 접두사 | `371c6734-2735-4958-8749-4f4db058a75f/assets/` |
| `{{.TeamSize}}` | 팀당 최대 참가자 수 | `5` |
| `{{.WSEventsAPIEndpoint}}` | Workshop Studio API 엔드포인트 | `events-api.us-east-1.prod.workshops.aws` |
| `{{.WSEventsAPIRegion}}` | Workshop Studio API 리전 | `us-east-1` |

### IAM Policy JSON용

| 변수 | 설명 | 예시 |
|------|------|------|
| `{{.ParticipantRoleName}}` | IAM 역할 이름 | `WSParticipantRole` |
| `{{.ParticipantRoleArn}}` | IAM 역할 ARN | `arn:aws:iam::123456789012:role/WSParticipantRole` |
| `{{.ParticipantAssumedRoleSessionName}}` | 세션 이름 | `Participant` |
| `{{.ParticipantAssumedRoleArn}}` | Assumed Role ARN | `arn:aws:sts::123456789012:assumed-role/WSParticipantRole/Participant` |
| `{{.AccountId}}` | AWS 계정 ID | `123456789012` |

---

## 전체 예제

### 기본 워크샵 (계정 제공)

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

### EKS 워크샵 (인프라 프로비저닝)

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

## IAM Policy 예제

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
