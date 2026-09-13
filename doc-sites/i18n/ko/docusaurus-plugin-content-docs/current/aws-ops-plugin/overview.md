---
sidebar_position: 1
title: "AWS 운영 플러그인"
---

{/* 영문 개편 이전의 섹션 링크를 유지합니다. */}
<span id="aws-ops-plugin-개요" />
<span id="구성-요소" />
<span id="에이전트-목록" />
<span id="스킬-목록" />
<span id="인시던트-대응-워크플로우" />
<span id="단일-도메인-트러블슈팅-플로우" />
<span id="팀-워크플로우-트리거" />
<span id="자동-호출-키워드" />


# AWS 운영 플러그인

컴퓨팅, 네트워크, 자격 증명, 관측성, 스토리지, 데이터베이스, 분석, 비용 영역의 AWS 및 EKS 인시던트를 진단합니다.

## 전문가 {#specialists}

- [EKS 에이전트](/docs/aws-ops-plugin/agents/eks-agent): 클러스터와 노드 상태, 추가 기능 수명 주기, 업그레이드, 파드 스케줄링, CrashLoopBackOff, ImagePullBackOff, 축출, 리소스 부족을 다룹니다.
- [네트워크 에이전트](/docs/aws-ops-plugin/agents/network-agent): VPC CNI, ENI/IP 용량, 파드 연결, 로드 밸런서, DNS, 경로, 네트워크 정책, 보안 그룹, VPC 엔드포인트를 다룹니다.
- [IAM 에이전트](/docs/aws-ops-plugin/agents/iam-agent): IRSA, EKS Pod Identity, IAM 신뢰와 권한, Kubernetes RBAC, EKS 액세스 항목, 기존 aws-auth 매핑을 다룹니다.
- [관측성 에이전트](/docs/aws-ops-plugin/agents/observability-agent): CloudWatch/Container Insights, Logs Insights, 알람, AMP, AMG, ADOT, 자체 관리형 Prometheus/Grafana를 다룹니다.
- [스토리지 에이전트](/docs/aws-ops-plugin/agents/storage-agent): EBS/EFS, CSI 드라이버, 영구 볼륨과 클레임, StorageClasses, 액세스 모드, 토폴로지, 연결 실패, 처리량, 수명 주기를 다룹니다.
- [데이터베이스 에이전트](/docs/aws-ops-plugin/agents/database-agent): RDS/Aurora의 연결과 성능, DynamoDB의 요청 제한과 용량, ElastiCache의 연결·메모리·지연 시간을 다룹니다.
- [분석 에이전트](/docs/aws-ops-plugin/agents/analytics-agent): OpenSearch 및 OpenSearch Serverless, ClickHouse, Athena, QuickSight, Kinesis의 수집·쿼리 파이프라인을 다룹니다.
- [비용 에이전트](/docs/aws-ops-plugin/agents/cost-agent): 서비스별 지출, EKS 비용 배분, 유휴 리소스, 사용률, 스토리지 수명 주기, 약정 및 적정 규모 조정 기회를 다룹니다.
- [운영 조정 에이전트](/docs/aws-ops-plugin/agents/ops-coordinator-agent): 인시던트 심각도, 5분 초기 분류, 영역별 작업 배정, 영역 간 근거 분석, 완화, 검증, 사후 분석을 다룹니다.
- [Well-Architected 에이전트](/docs/aws-ops-plugin/agents/wellarchitected-agent): 운영 우수성, 보안, 안정성, 성능 효율성, 비용 최적화, 지속 가능성을 검토합니다.

## 워크플로 {#workflows}

구체적인 장애에는 ops-troubleshoot, 전반적인 평가에는 ops-health-check, 연결 문제에는 ops-network-diagnosis, 텔레메트리에는 ops-observability, 보안 근거에는 ops-security-audit, 6개 핵심 요소의 점수 평가에는 ops-wellarchitected-review를 사용합니다.

범위 설정과 읽기 전용 근거 수집부터 시작합니다. 리소스를 변경하기 전에 진단하고, 승인된 시정 조치만 적용한 뒤 원래 증상을 기준으로 검증합니다. 단일 영역의 작업은 전문가에게 맡깁니다. 심각하거나 여러 영역에 걸친 인시던트는 호스트가 지원하는 경우 조정자와 병렬 전문가를 활용할 수 있습니다.

Claude 매니페스트는 에이전트 10개와 스킬 6개를 선언합니다. Codex는 생성된 스킬 오버레이와 호스트별 도구를 사용합니다. 번들 MCP 설정은 패키지에 실제 선언된 서버로 한정됩니다.
