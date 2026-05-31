# AWS Well-Architected Framework — Deep Review Checklist

6개 필러별 상세 체크리스트. 인프라 코드(Terraform, CDK, CloudFormation) 리뷰에 사용합니다.

---

## Pillar 1: Operational Excellence (운영 우수성)

### OPS-01: IaC 관리
```bash
# 모든 리소스가 IaC로 관리되는지 확인
# Terraform
terraform state list | wc -l
# CDK
cdk diff 2>&1 | grep -c "Resources"
```
- [ ] 모든 리소스가 코드로 정의됨
- [ ] 수동 콘솔 변경 없음 (drift detection)
- [ ] 환경별 분리 (dev/staging/prod)

### OPS-02: 관찰 가능성
- [ ] CloudWatch 메트릭 대시보드
- [ ] 알람 설정 (CPU, 메모리, 에러율, 지연)
- [ ] 구조화된 로깅 (JSON 형식)
- [ ] 분산 추적 (X-Ray, ADOT)
- [ ] 로그 보존 정책

### OPS-03: 변경 관리
- [ ] CI/CD 파이프라인 정의
- [ ] 자동 테스트 게이트
- [ ] Blue/Green or Canary 배포
- [ ] 롤백 자동화

---

## Pillar 2: Security (보안)

### SEC-01: IAM
```bash
# 과도한 권한 탐지
grep -rn "Action.*\"\*\"" --include="*.tf" --include="*.yaml" --include="*.json"
grep -rn "Resource.*\"\*\"" --include="*.tf" --include="*.yaml" --include="*.json"

# AdministratorAccess 사용 여부
grep -rn "AdministratorAccess\|PowerUserAccess" --include="*.tf" --include="*.yaml"
```
- [ ] 최소 권한 원칙
- [ ] 서비스별 전용 IAM 역할
- [ ] IRSA / Pod Identity (EKS)
- [ ] 임시 자격증명 사용

### SEC-02: 데이터 보호
- [ ] 저장 시 암호화 (EBS, S3, RDS: KMS)
- [ ] 전송 중 암호화 (TLS 1.2+)
- [ ] Secrets Manager / SSM Parameter Store
- [ ] S3 버킷 퍼블릭 액세스 차단

### SEC-03: 네트워크
```bash
# 보안 그룹 0.0.0.0/0 오픈 탐지
grep -rn "0\.0\.0\.0/0\|::/0" --include="*.tf" --include="*.yaml" | grep -i "ingress\|cidr"
```
- [ ] VPC 서브넷 분리 (public/private)
- [ ] 보안 그룹 최소 포트 오픈
- [ ] VPC 엔드포인트 (S3, DynamoDB, ECR)
- [ ] WAF 적용 (public-facing)

---

## Pillar 3: Reliability (안정성)

### REL-01: 고가용성
- [ ] 멀티 AZ 배포
- [ ] Auto Scaling 그룹 설정
- [ ] 헬스체크 (ALB + 컨테이너)
- [ ] 서킷 브레이커 패턴

### REL-02: 장애 복구
```bash
# 백업 설정 확인
grep -rn "backup_retention\|point_in_time_recovery\|backup_window" --include="*.tf" --include="*.yaml"
```
- [ ] RDS 자동 백업 + 스냅샷
- [ ] S3 버전 관리
- [ ] 크로스 리전 복제 (필요 시)
- [ ] RPO/RTO 정의 및 테스트

### REL-03: 한계 관리
- [ ] Service Quotas 확인
- [ ] 속도 제한 (API Gateway throttling)
- [ ] 큐 기반 부하 분산 (SQS)
- [ ] 그레이스풀 디그레이데이션

---

## Pillar 4: Performance Efficiency (성능 효율성)

### PERF-01: 컴퓨팅
- [ ] 워크로드에 적합한 인스턴스 타입
- [ ] Graviton 프로세서 고려
- [ ] 컨테이너 리소스 요청/제한 설정
- [ ] Lambda 메모리/타임아웃 최적화

### PERF-02: 데이터
- [ ] 데이터베이스 인덱스 전략
- [ ] 읽기 복제본 (읽기 부하 분산)
- [ ] 캐싱 레이어 (ElastiCache, DAX)
- [ ] 쿼리 성능 인사이트 활성화

### PERF-03: 네트워크
- [ ] CloudFront CDN (정적 콘텐츠)
- [ ] Global Accelerator (글로벌 트래픽)
- [ ] VPC 엔드포인트 (AWS 서비스 직접 연결)
- [ ] 적절한 리전 선택

---

## Pillar 5: Cost Optimization (비용 최적화)

### COST-01: 리소스 효율성
```bash
# 과도한 인스턴스 사이징 탐지
grep -rn "instance_type\|instance_class" --include="*.tf" | grep -iE "xlarge|2xlarge|4xlarge|metal"
```
- [ ] 인스턴스 Right-sizing
- [ ] Savings Plans / Reserved Instances 분석
- [ ] 스팟 인스턴스 활용 (비 미션 크리티컬)
- [ ] 미사용 리소스 제거

### COST-02: 비용 가시성
- [ ] 리소스 태깅 전략 (팀, 환경, 프로젝트)
- [ ] AWS 예산 알림 설정
- [ ] Cost Explorer 대시보드
- [ ] 비용 할당 태그

### COST-03: 아키텍처 최적화
- [ ] 서버리스 전환 가능 여부 (Lambda, Fargate)
- [ ] 스토리지 계층화 (S3 Lifecycle)
- [ ] 데이터 전송 비용 최소화
- [ ] NAT Gateway vs VPC 엔드포인트

---

## Pillar 6: Sustainability (지속 가능성)

### SUS-01: 효율적 리소스 사용
- [ ] Graviton (ARM) 프로세서 채택
- [ ] 서버리스 우선 아키텍처
- [ ] 자동 스케일링으로 유휴 리소스 최소화
- [ ] 적절한 리소스 사이징

### SUS-02: 데이터 관리
- [ ] 데이터 보존 정책 (TTL)
- [ ] 불필요한 데이터 이동 최소화
- [ ] 압축 사용 (S3, 로그)

---

## Scoring Guide

각 필러는 5점 만점으로 채점:

| 점수 | 기준 |
|------|------|
| ★★★★★ (5) | 모든 체크 통과, Best Practice 준수 |
| ★★★★☆ (4) | 1-2개 미충족, 경미한 개선 필요 |
| ★★★☆☆ (3) | 3-4개 미충족, 개선 권고 |
| ★★☆☆☆ (2) | 5개 이상 미충족, 주요 개선 필요 |
| ★☆☆☆☆ (1) | 기본 사항 미충족, 즉각 대응 필요 |

필러별 판정:
- ★★★★☆ 이상: **PASS**
- ★★★☆☆: **REVIEW**
- ★★☆☆☆ 이하: **FAIL**
