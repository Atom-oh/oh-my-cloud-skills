# AWS 아이콘 레퍼런스

Draw.io에서 사용 가능한 AWS 아이콘 shape 이름과 스타일 가이드.

## Shape 이름 규칙

AWS 아이콘의 shape 이름 형식:
```
shape=mxgraph.aws4.[service_name]
```

## ⚠️ 필수 규칙: 아이콘 라벨 표시

**AWS 아이콘 추가 시 반드시 아이콘 이름을 라벨로 표시해야 합니다.**

```
┌─────────────┐
│   [아이콘]   │
│             │
│ SecretManager│  ← 아이콘 아래에 서비스 이름 필수
└─────────────┘
```

### 라벨 스타일 설정

```
labelPosition=center;      # 라벨 가로 위치
verticalLabelPosition=bottom;  # 라벨을 아이콘 아래에
align=center;              # 텍스트 가운데 정렬
verticalAlign=top;         # 텍스트 상단 정렬
fontFamily=Amazon Ember;   # AWS 폰트
fontSize=12;               # 폰트 크기
fontColor=#FFFFFF;         # Dark 테마용 흰색
```

### 라벨 예시

| 아이콘 | 라벨 텍스트 |
|--------|------------|
| Secrets Manager | `Secrets Manager` |
| Lambda | `Lambda` |
| API Gateway | `API Gateway` |
| DynamoDB | `DynamoDB` |
| CloudWatch | `CloudWatch` |

---

## 카테고리별 아이콘

### Compute

| 서비스 | Shape 이름 | 설명 |
|--------|-----------|------|
| EC2 | `mxgraph.aws4.ec2` | Elastic Compute Cloud |
| Lambda | `mxgraph.aws4.lambda_function` | 서버리스 함수 |
| ECS | `mxgraph.aws4.ecs` | Elastic Container Service |
| EKS | `mxgraph.aws4.eks` | Elastic Kubernetes Service |
| Fargate | `mxgraph.aws4.fargate` | 서버리스 컨테이너 |
| Batch | `mxgraph.aws4.batch` | 배치 컴퓨팅 |
| Elastic Beanstalk | `mxgraph.aws4.elastic_beanstalk` | 앱 배포 |
| Lightsail | `mxgraph.aws4.lightsail` | 간편 VPS |
| App Runner | `mxgraph.aws4.app_runner` | 컨테이너 앱 |

### Storage

| 서비스 | Shape 이름 | 설명 |
|--------|-----------|------|
| S3 | `mxgraph.aws4.s3` | Simple Storage Service |
| S3 Bucket | `mxgraph.aws4.bucket` | S3 버킷 |
| EBS | `mxgraph.aws4.elastic_block_store` | 블록 스토리지 |
| EFS | `mxgraph.aws4.elastic_file_system` | 파일 시스템 |
| FSx | `mxgraph.aws4.fsx` | 고성능 파일 시스템 |
| Glacier | `mxgraph.aws4.glacier` | 아카이브 스토리지 |
| Storage Gateway | `mxgraph.aws4.storage_gateway` | 하이브리드 스토리지 |

### Database

| 서비스 | Shape 이름 | 설명 |
|--------|-----------|------|
| RDS | `mxgraph.aws4.rds` | Relational Database Service |
| Aurora | `mxgraph.aws4.aurora` | 고성능 관계형 DB |
| DynamoDB | `mxgraph.aws4.dynamodb` | NoSQL 데이터베이스 |
| ElastiCache | `mxgraph.aws4.elasticache` | 인메모리 캐시 |
| Redshift | `mxgraph.aws4.redshift` | 데이터 웨어하우스 |
| DocumentDB | `mxgraph.aws4.documentdb` | MongoDB 호환 DB |
| Neptune | `mxgraph.aws4.neptune` | 그래프 데이터베이스 |
| Timestream | `mxgraph.aws4.timestream` | 시계열 데이터베이스 |
| QLDB | `mxgraph.aws4.qldb` | 원장 데이터베이스 |
| MemoryDB | `mxgraph.aws4.memorydb` | Redis 호환 |

### Networking & Content Delivery

| 서비스 | Shape 이름 | 설명 |
|--------|-----------|------|
| VPC | `mxgraph.aws4.vpc` | Virtual Private Cloud |
| CloudFront | `mxgraph.aws4.cloudfront` | CDN |
| Route 53 | `mxgraph.aws4.route_53` | DNS 서비스 |
| API Gateway | `mxgraph.aws4.api_gateway` | API 관리 |
| ELB/ALB | `mxgraph.aws4.application_load_balancer` | 로드밸런서 |
| NLB | `mxgraph.aws4.network_load_balancer` | 네트워크 LB |
| NAT Gateway | `mxgraph.aws4.nat_gateway` | NAT 게이트웨이 |
| Internet Gateway | `mxgraph.aws4.internet_gateway` | IGW |
| VPN Gateway | `mxgraph.aws4.vpn_gateway` | VPN |
| Direct Connect | `mxgraph.aws4.direct_connect` | 전용선 |
| Transit Gateway | `mxgraph.aws4.transit_gateway` | 네트워크 허브 |
| PrivateLink | `mxgraph.aws4.privatelink` | 프라이빗 연결 |
| Global Accelerator | `mxgraph.aws4.global_accelerator` | 글로벌 가속 |

### Security, Identity & Compliance

| 서비스 | Shape 이름 | 설명 |
|--------|-----------|------|
| IAM | `mxgraph.aws4.identity_and_access_management` | 접근 관리 |
| Cognito | `mxgraph.aws4.cognito` | 사용자 인증 |
| WAF | `mxgraph.aws4.waf` | 웹 방화벽 |
| Shield | `mxgraph.aws4.shield` | DDoS 보호 |
| KMS | `mxgraph.aws4.key_management_service` | 키 관리 |
| Secrets Manager | `mxgraph.aws4.secrets_manager` | 시크릿 관리 |
| Certificate Manager | `mxgraph.aws4.certificate_manager` | SSL/TLS 인증서 |
| GuardDuty | `mxgraph.aws4.guardduty` | 위협 탐지 |
| Inspector | `mxgraph.aws4.inspector` | 취약점 스캔 |
| Macie | `mxgraph.aws4.macie` | 데이터 보안 |
| Security Hub | `mxgraph.aws4.security_hub` | 보안 허브 |

### Application Integration

| 서비스 | Shape 이름 | 설명 |
|--------|-----------|------|
| SQS | `mxgraph.aws4.sqs` | 메시지 큐 |
| SNS | `mxgraph.aws4.sns` | 알림 서비스 |
| EventBridge | `mxgraph.aws4.eventbridge` | 이벤트 버스 |
| Step Functions | `mxgraph.aws4.step_functions` | 워크플로우 |
| AppSync | `mxgraph.aws4.appsync` | GraphQL API |
| MQ | `mxgraph.aws4.mq` | 메시지 브로커 |

### Analytics

| 서비스 | Shape 이름 | 설명 |
|--------|-----------|------|
| Kinesis | `mxgraph.aws4.kinesis` | 스트리밍 데이터 |
| Athena | `mxgraph.aws4.athena` | S3 쿼리 |
| EMR | `mxgraph.aws4.emr` | 빅데이터 처리 |
| Glue | `mxgraph.aws4.glue` | ETL 서비스 |
| QuickSight | `mxgraph.aws4.quicksight` | BI 시각화 |
| OpenSearch | `mxgraph.aws4.elasticsearch_service` | 검색/분석 (ES 아이콘 사용) |
| Data Pipeline | `mxgraph.aws4.data_pipeline` | 데이터 이동 |
| Lake Formation | `mxgraph.aws4.lake_formation` | 데이터 레이크 |
| MSK | `mxgraph.aws4.managed_streaming_for_kafka` | Kafka |

### Machine Learning

| 서비스 | Shape 이름 | 설명 |
|--------|-----------|------|
| SageMaker | `mxgraph.aws4.sagemaker` | ML 플랫폼 |
| Bedrock | `mxgraph.aws4.bedrock` | 생성형 AI |
| Rekognition | `mxgraph.aws4.rekognition` | 이미지/비디오 분석 |
| Comprehend | `mxgraph.aws4.comprehend` | NLP |
| Lex | `mxgraph.aws4.lex` | 챗봇 |
| Polly | `mxgraph.aws4.polly` | TTS |
| Transcribe | `mxgraph.aws4.transcribe` | STT |
| Translate | `mxgraph.aws4.translate` | 번역 |
| Textract | `mxgraph.aws4.textract` | 문서 분석 |

### Management & Governance

| 서비스 | Shape 이름 | 설명 |
|--------|-----------|------|
| CloudWatch | `mxgraph.aws4.cloudwatch` | 모니터링 |
| CloudTrail | `mxgraph.aws4.cloudtrail` | 감사 로그 |
| CloudFormation | `mxgraph.aws4.cloudformation` | IaC |
| Systems Manager | `mxgraph.aws4.systems_manager` | 운영 관리 |
| Config | `mxgraph.aws4.config` | 리소스 구성 |
| Organizations | `mxgraph.aws4.organizations` | 계정 관리 |
| Control Tower | `mxgraph.aws4.control_tower` | 랜딩존 |
| Service Catalog | `mxgraph.aws4.service_catalog` | 서비스 카탈로그 |

### Developer Tools

| 서비스 | Shape 이름 | 설명 |
|--------|-----------|------|
| CodeCommit | `mxgraph.aws4.codecommit` | Git 저장소 |
| CodeBuild | `mxgraph.aws4.codebuild` | 빌드 서비스 |
| CodeDeploy | `mxgraph.aws4.codedeploy` | 배포 자동화 |
| CodePipeline | `mxgraph.aws4.codepipeline` | CI/CD |
| Cloud9 | `mxgraph.aws4.cloud9` | 클라우드 IDE |
| X-Ray | `mxgraph.aws4.xray` | 분산 추적 |

## AWS Groups (컨테이너/그룹 Shape)

아키텍처 다이어그램에서 리소스를 논리적으로 그룹화하는 컨테이너입니다.

### 기본 인프라 그룹

| 요소 | Shape 이름 | 색상 | 설명 |
|------|-----------|------|------|
| AWS Cloud | `mxgraph.aws4.group_aws_cloud` | #242F3E | AWS 클라우드 전체 경계 |
| AWS Cloud (Alt) | `mxgraph.aws4.group_aws_cloud_alt` | #242F3E | AWS 클라우드 (대체 스타일) |
| Region | `mxgraph.aws4.group_region` | #147EBA | 리전 경계 |
| Availability Zone | `mxgraph.aws4.group_availability_zone` | #147EBA | 가용영역 (AZ) |

### 네트워크 그룹

| 요소 | Shape 이름 | 색상 | 설명 |
|------|-----------|------|------|
| VPC | `mxgraph.aws4.group_vpc` | #248814 | Virtual Private Cloud |
| VPC (alt) | `mxgraph.aws4.group_vpc2` | #248814 | VPC 대체 스타일 |
| Public Subnet | `mxgraph.aws4.group_public_subnet` | #248814 | 퍼블릭 서브넷 (실선) |
| Private Subnet | `mxgraph.aws4.group_private_subnet` | #147EBA | 프라이빗 서브넷 (점선) |
| Security Group | `mxgraph.aws4.group_security_group` | #DF3312 | 보안 그룹 |
| Network ACL | `mxgraph.aws4.group_nacl` | #248814 | 네트워크 ACL |

### 컴퓨팅 그룹

| 요소 | Shape 이름 | 색상 | 설명 |
|------|-----------|------|------|
| Auto Scaling Group | `mxgraph.aws4.group_auto_scaling` | #ED7100 | Auto Scaling 그룹 |
| EC2 Instance Contents | `mxgraph.aws4.group_ec2_instance_contents` | #ED7100 | EC2 인스턴스 내부 |
| Spot Fleet | `mxgraph.aws4.group_spot_fleet` | #ED7100 | 스팟 플릿 |
| ECS Cluster | `mxgraph.aws4.group_ecs_cluster` | #ED7100 | ECS 클러스터 |
| EKS Cluster | `mxgraph.aws4.group_eks_cluster` | #ED7100 | EKS 클러스터 |

### 서비스/기능 그룹

| 요소 | Shape 이름 | 색상 | 설명 |
|------|-----------|------|------|
| AWS Account | `mxgraph.aws4.group_aws_account` | #242F3E | AWS 계정 경계 |
| Corporate Data Center | `mxgraph.aws4.group_corporate_data_center` | #7D8998 | 온프레미스 데이터센터 |
| Elastic Beanstalk Container | `mxgraph.aws4.group_elastic_beanstalk` | #248814 | EB 환경 |
| Step Functions | `mxgraph.aws4.group_step_functions` | #CD2264 | Step Functions 워크플로우 |
| Generic Group | `mxgraph.aws4.group_generic` | #7D8998 | 일반 그룹 |
| Generic Group (alt) | `mxgraph.aws4.group_generic_alt` | #7D8998 | 일반 그룹 (대체) |

### 그룹 스타일 가이드

```
# 기본 그룹 스타일
shape=mxgraph.aws4.group_[type];
strokeWidth=2;
dashed=0;               # 실선 (퍼블릭 서브넷)
dashed=1;               # 점선 (프라이빗 서브넷)
rounded=1;
arcSize=10;
fillColor=none;         # 투명 배경 권장
fontFamily=Amazon Ember;
fontStyle=1;            # Bold
fontSize=14;
verticalAlign=top;
spacingTop=10;
spacingLeft=10;
```

### 그룹 중첩 순서 (바깥 → 안쪽)

```
1. AWS Cloud
   └── 2. Region
       └── 3. Availability Zone
           └── 4. VPC
               └── 5. Subnet (Public/Private)
                   └── 6. Security Group
                       └── 7. EC2 Instance / Auto Scaling Group
```

### 그룹 색상 팔레트

| 그룹 유형 | Border Color | Fill Color | 용도 |
|----------|--------------|------------|------|
| AWS Cloud | #242F3E | none | 전체 클라우드 |
| Region/AZ | #147EBA | none | 지역/가용영역 |
| VPC/Public Subnet | #248814 | none | 네트워크 (실선) |
| Private Subnet | #147EBA | none | 프라이빗 (점선) |
| Security Group | #DF3312 | none | 보안 |
| Compute (ASG/EC2) | #ED7100 | none | 컴퓨팅 |
| Generic | #7D8998 | none | 일반 |

## 일반 아이콘

| 요소 | Shape 이름 | 설명 |
|------|-----------|------|
| User | `mxgraph.aws4.user` | 사용자 |
| Users | `mxgraph.aws4.users` | 사용자 그룹 |
| Client | `mxgraph.aws4.client` | 클라이언트 |
| Mobile Client | `mxgraph.aws4.mobile_client` | 모바일 |
| Traditional Server | `mxgraph.aws4.traditional_server` | 온프레미스 서버 |
| Corporate Data Center | `mxgraph.aws4.corporate_data_center` | 데이터센터 |
| Internet | `mxgraph.aws4.internet` | 인터넷 |
| Cloud | `mxgraph.aws4.cloud` | 일반 클라우드 |

## 서비스 아이콘 색상 코드 (fillColor / gradientColor)

AWS 아이콘은 **서비스 카테고리별로 색상이 구분**됩니다. 아래 색상을 사용하면 AWS 공식 스타일과 일치합니다.

### 카테고리별 색상 매핑

| 카테고리 | fillColor | gradientColor | 대표 서비스 |
|----------|-----------|---------------|-------------|
| **Compute** (Orange) | `#D05C17` | `#F78E04` | EC2, Lambda, ECS, EKS |
| **Storage** (Green) | `#277116` | `#60A337` | S3, EBS, EFS, Glacier |
| **Database** (Blue) | `#3334B9` | `#4D72F3` | RDS, DynamoDB, Aurora |
| **Security** (Red) | `#C7131F` | `#F54749` | IAM, WAF, GuardDuty |
| **Networking** (Purple) | `#5A30B5` | `#945DF2` | VPC, CloudFront, Route53 |
| **Management** (Pink) | `#BC1356` | `#F34482` | CloudWatch, CloudTrail |
| **AI/ML** (Teal) | `#116D5B` | `#4AB29A` | SageMaker, Bedrock |
| **Integration** (Magenta) | `#BC1356` | `#F34482` | SQS, SNS, EventBridge |
| **Analytics** (Purple) | `#5A30B5` | `#945DF2` | Kinesis, Athena, Glue |
| **Developer** (Blue) | `#3334B9` | `#4D72F3` | CodePipeline, CodeBuild |

### 색상 적용 XML 예시

```xml
<!-- Compute (EC2) -->
<mxCell id="ec2" value="EC2"
  style="sketch=0;outlineConnect=0;fontColor=#232F3E;
         gradientColor=#F78E04;gradientDirection=north;
         fillColor=#D05C17;strokeColor=#ffffff;
         dashed=0;verticalLabelPosition=bottom;verticalAlign=top;
         align=center;html=1;fontSize=9;fontStyle=0;aspect=fixed;
         shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.ec2;
         fontFamily=Amazon Ember;"
  vertex="1" parent="1">
  <mxGeometry x="100" y="100" width="48" height="48" as="geometry" />
</mxCell>

<!-- Database (RDS) -->
<mxCell id="rds" value="RDS"
  style="sketch=0;outlineConnect=0;fontColor=#232F3E;
         gradientColor=#4D72F3;gradientDirection=north;
         fillColor=#3334B9;strokeColor=#ffffff;
         dashed=0;verticalLabelPosition=bottom;verticalAlign=top;
         align=center;html=1;fontSize=9;fontStyle=0;aspect=fixed;
         shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.rds;
         fontFamily=Amazon Ember;"
  vertex="1" parent="1">
  <mxGeometry x="200" y="100" width="48" height="48" as="geometry" />
</mxCell>

<!-- Security (WAF) -->
<mxCell id="waf" value="WAF"
  style="sketch=0;outlineConnect=0;fontColor=#232F3E;
         gradientColor=#F54749;gradientDirection=north;
         fillColor=#C7131F;strokeColor=#ffffff;
         dashed=0;verticalLabelPosition=bottom;verticalAlign=top;
         align=center;html=1;fontSize=9;fontStyle=0;aspect=fixed;
         shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.waf;
         fontFamily=Amazon Ember;"
  vertex="1" parent="1">
  <mxGeometry x="300" y="100" width="48" height="48" as="geometry" />
</mxCell>
```

### 연결선 색상 가이드

| 연결 유형 | strokeColor | strokeWidth | 설명 |
|----------|-------------|-------------|------|
| Direct Connect | `#FF9800` | 4 | 전용선 연결 |
| PrivateLink | `#5A30B5` | 2 | VPC 간 프라이빗 연결 |
| VPN | `#7D8998` | 2 | VPN 터널 |
| 일반 연결 | `#545B64` | 2 | 기본 화살표 |
| 데이터 흐름 | `#3334B9` | 2 | 데이터 이동 |

---

## 스타일 템플릿

### AWS 아이콘 기본 스타일

```
shape=mxgraph.aws4.[service];
fontFamily=Amazon Ember;
fontSize=12;
labelPosition=center;
verticalLabelPosition=bottom;
align=center;
verticalAlign=top;
```

### 그룹/컨테이너 스타일

```
shape=mxgraph.aws4.group_[type];
fontFamily=Amazon Ember;
fontSize=14;
fontStyle=1;
verticalAlign=top;
spacingTop=10;
strokeColor=#[color];
fillColor=#[background];
dashed=0;
```

## 아이콘 크기 가이드

| 유형 | 권장 크기 | 용도 |
|------|----------|------|
| 서비스 아이콘 | 60x60 | 표준 아이콘 |
| 소형 아이콘 | 40x40 | 밀집 레이아웃 |
| 대형 아이콘 | 80x80 | 강조할 때 |
| 리소스 아이콘 | 48x48 | 세부 리소스 |

## MCP로 아이콘 검색

```
# AWS 카테고리 확인
mcp__drawio__get-shape-categories

# AWS 카테고리의 모든 shape 조회
mcp__drawio__get-shapes-in-category
→ category: "AWS"

# 특정 서비스 검색
mcp__drawio__get-shape-by-name
→ name: "ec2"
```
