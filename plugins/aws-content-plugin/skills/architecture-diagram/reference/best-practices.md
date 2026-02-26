# AWS 아키텍처 다이어그램 모범사례

AWS 아키텍처 다이어그램 작성 시 따라야 할 가이드라인과 모범사례.

## 1. 레이아웃 원칙

### 계층 구조 (Outside-In)

외부에서 내부로 계층을 명확히 표현:

```
1. Users/Internet (최외곽)
   └── 2. AWS Cloud
       └── 3. Region
           └── 4. VPC
               └── 5. Availability Zone
                   └── 6. Subnet
                       └── 7. Services
```

### 데이터 흐름 방향

- **왼쪽 → 오른쪽**: 요청 흐름 (권장)
- **위 → 아래**: 계층별 분리
- **일관성 유지**: 한 다이어그램 내에서 방향 통일

### 3-Tier 아키텍처 배치

```
┌─────────────────────────────────────────────────────────────┐
│                     Presentation Tier                        │
│  CloudFront → ALB → Web Servers                              │
├─────────────────────────────────────────────────────────────┤
│                      Application Tier                        │
│  API Gateway → Lambda/ECS → Application Logic                │
├─────────────────────────────────────────────────────────────┤
│                         Data Tier                            │
│  RDS/Aurora → DynamoDB → ElastiCache → S3                   │
└─────────────────────────────────────────────────────────────┘
```

## 2. 색상 가이드 (AWS 공식)

### AWS 브랜드 색상

| 요소 | 색상 코드 | RGB | 용도 |
|------|-----------|-----|------|
| Squid Ink | #232F3E | 35, 47, 62 | AWS Cloud 배경 |
| Smile Orange | #FF9900 | 255, 153, 0 | 강조, CTA |
| Anchor | #147EBA | 20, 126, 186 | Region |
| Cosmos | #C7511F | 199, 81, 31 | Security 관련 |

### 컨테이너 색상

| 컨테이너 | 테두리 | 배경 | 텍스트 |
|----------|--------|------|--------|
| AWS Cloud | #232F3E | transparent | #232F3E |
| Region | #147EBA | #E6F2F8 | #147EBA |
| VPC | #248814 | #E7F4E8 | #248814 |
| Public Subnet | #248814 | #E7F4E8 | #248814 |
| Private Subnet | #147EBA | #E6F2F8 | #147EBA |
| Security Group | #DF3312 | transparent | #DF3312 |
| Availability Zone | #147EBA | transparent | #147EBA |

### 화살표 색상

| 유형 | 색상 | 용도 |
|------|------|------|
| 데이터 흐름 | #545B64 | 일반 연결 |
| 동기 호출 | #232F3E (실선) | API 호출 등 |
| 비동기 호출 | #232F3E (점선) | 이벤트, 메시지 |
| 보안 연결 | #DF3312 | Security Group 등 |

## 3. 폰트 가이드

### Amazon Ember (권장)

AWS 공식 브랜드 폰트:

```
fontFamily=Amazon Ember;
```

폰트 스택 (fallback):
```
Amazon Ember, Arial, Helvetica, sans-serif
```

### 폰트 크기 권장

| 요소 | 크기 | 굵기 |
|------|------|------|
| 다이어그램 제목 | 24px | Bold |
| 컨테이너 라벨 (Cloud, Region) | 16px | Bold |
| 서브넷/AZ 라벨 | 14px | Regular |
| 서비스 라벨 | 12px | Regular |
| 상세 설명 | 10px | Regular |

### 텍스트 배치

- 아이콘 라벨: 아이콘 아래 (verticalLabelPosition=bottom)
- 컨테이너 라벨: 상단 좌측 (verticalAlign=top)
- 화살표 라벨: 중앙 (align=center)

## 4. 아이콘 사용 가이드

### 아이콘 크기 일관성

```
표준 크기: 60x60px
소형 (밀집 레이아웃): 40x40px
대형 (강조): 80x80px
```

### 아이콘 간격

```
최소 간격: 20px
권장 간격: 40px
그룹 내 간격: 30px
```

### 아이콘 정렬

- 수평 정렬: 같은 계층의 서비스
- 수직 정렬: 데이터 흐름 방향
- 그리드 정렬 사용 권장 (gridSize=10)

## 5. 연결선 (Edge) 가이드

### 연결선 스타일

```xml
<!-- 직각 연결 (권장) -->
style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;"

<!-- 곡선 연결 -->
style="edgeStyle=elbowEdgeStyle;rounded=1;"

<!-- 직선 연결 -->
style="edgeStyle=none;"
```

### 화살표 유형

| 유형 | 스타일 | 용도 |
|------|--------|------|
| 단방향 | `endArrow=classic;startArrow=none;` | 요청 흐름 |
| 양방향 | `endArrow=classic;startArrow=classic;` | 동기 통신 |
| 없음 | `endArrow=none;startArrow=none;` | 연관 관계 |

### 점선 vs 실선

```xml
<!-- 실선 (동기 호출) -->
style="dashed=0;"

<!-- 점선 (비동기, 선택적) -->
style="dashed=1;dashPattern=8 8;"
```

## 6. 일반적인 아키텍처 패턴

### 패턴 1: 단순 웹 애플리케이션

```
Internet → CloudFront → ALB → EC2 (ASG) → RDS
                                    ↘ ElastiCache
```

### 패턴 2: 서버리스 아키텍처

```
Client → API Gateway → Lambda → DynamoDB
              ↓
         Cognito (인증)
```

### 패턴 3: 마이크로서비스

```
ALB → ECS/EKS Services → RDS/DynamoDB
  ↓
Service Mesh (App Mesh)
  ↓
X-Ray (추적)
```

### 패턴 4: 이벤트 기반 아키텍처

```
Producer → EventBridge/SNS → SQS → Lambda → Consumer
                  ↓
           Step Functions (오케스트레이션)
```

### 패턴 5: 데이터 레이크

```
Sources → Kinesis → S3 (Raw) → Glue ETL → S3 (Processed) → Athena/QuickSight
                                    ↓
                              Redshift (분석)
```

## 7. 고가용성 표현

### Multi-AZ 배치

```
┌─────────────────────────────────────────────────┐
│                      VPC                         │
│  ┌───────────────────┐  ┌───────────────────┐   │
│  │    AZ-a           │  │    AZ-c           │   │
│  │  ┌─────────────┐  │  │  ┌─────────────┐  │   │
│  │  │ Public      │  │  │  │ Public      │  │   │
│  │  │  ALB        │  │  │  │  ALB        │  │   │
│  │  └─────────────┘  │  │  └─────────────┘  │   │
│  │  ┌─────────────┐  │  │  ┌─────────────┐  │   │
│  │  │ Private     │  │  │  │ Private     │  │   │
│  │  │  EC2        │  │  │  │  EC2        │  │   │
│  │  └─────────────┘  │  │  └─────────────┘  │   │
│  └───────────────────┘  └───────────────────┘   │
│                    ↕ RDS Multi-AZ ↕              │
└─────────────────────────────────────────────────┘
```

### Active-Standby vs Active-Active

- **Active-Standby**: 한쪽 화살표만 활성화, 다른 쪽 점선
- **Active-Active**: 양쪽 모두 실선 화살표

## 8. 보안 표현

### Security Group 표현

```xml
<!-- 빨간색 점선 테두리 -->
style="rounded=1;dashed=1;strokeColor=#DF3312;fillColor=none;"
```

### 암호화 표현

- KMS 아이콘 추가
- 자물쇠 아이콘 또는 "Encrypted" 라벨

### 네트워크 경계

- Public/Private 서브넷 색상 구분
- NAT Gateway, Internet Gateway 명시
- VPC Endpoint 표시 (PrivateLink)

## 9. 주석 및 설명

### 범례 (Legend) 추가

다이어그램 우측 하단에 범례 배치:
- 색상 의미
- 화살표 유형 설명
- 약어 풀이

### 버전 정보

다이어그램에 포함할 정보:
- 다이어그램 제목
- 작성일/수정일
- 버전 번호
- 작성자

## 10. 체크리스트

### 레이아웃
- [ ] 계층 구조가 명확한가 (Cloud > Region > VPC > Subnet)
- [ ] 데이터 흐름 방향이 일관성 있는가
- [ ] 아이콘 크기가 균일한가
- [ ] 적절한 간격이 유지되는가

### 색상 및 스타일
- [ ] AWS 공식 색상을 사용하는가
- [ ] Amazon Ember 폰트가 적용되었는가
- [ ] 컨테이너 색상이 올바른가

### 연결선
- [ ] 화살표 방향이 올바른가
- [ ] 동기/비동기 구분이 되어 있는가 (실선/점선)
- [ ] 불필요한 연결선 교차가 없는가

### 완성도
- [ ] 모든 주요 구성요소가 포함되었는가
- [ ] 범례가 있는가
- [ ] 제목과 버전 정보가 있는가

## 11. 안티패턴 (피해야 할 것)

### 피해야 할 것

1. **과도한 상세**: 모든 리소스를 표시하지 말 것
2. **불일치한 아이콘 크기**: 같은 유형은 같은 크기로
3. **화살표 교차**: 가능한 최소화
4. **색상 남용**: 목적 없는 색상 사용 금지
5. **텍스트 과다**: 핵심 정보만 라벨에 표시
6. **계층 무시**: 컨테이너 없이 서비스만 나열하지 말 것

### 권장 사항

1. **단순화**: 청중에 맞는 수준으로 추상화
2. **일관성**: 한 다이어그램 내 스타일 통일
3. **명확성**: 한눈에 이해 가능하도록
4. **표준 준수**: AWS 아키텍처 아이콘 표준 사용
