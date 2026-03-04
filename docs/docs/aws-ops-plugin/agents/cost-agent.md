---
sidebar_position: 7
title: Cost Agent
---

# Cost Agent

AWS 비용 분석 및 최적화 전문 에이전트입니다. awspricing MCP를 활용합니다.

## 기본 정보

| 항목 | 값 |
|------|-----|
| Model | sonnet |
| Tools | Read, Write, Glob, Grep, Bash, AskUserQuestion |

## 트리거 키워드

| 영어 | 한국어 |
|------|--------|
| "cost analysis", "cost optimization", "billing", "savings plan", "reserved instance" | "비용 분석", "비용 절감", "요금" |

## 핵심 기능

1. **비용 분석** - 서비스별 비용 분석, 트렌드 분석, 이상 탐지
2. **EKS 비용 최적화** - Right-sizing, Spot 인스턴스, Karpenter, Graviton
3. **Savings Plans & RIs** - 커버리지 분석, 권장사항 생성
4. **리소스 최적화** - 유휴 리소스 탐지, Right-sizing, 정리
5. **CloudWatch 비용** - 메트릭/로그 비용 최적화, 보존 기간 튜닝

## 분석 명령어

### 비용 개요

```bash
# 서비스별 월별 비용
aws ce get-cost-and-usage \
  --time-period Start=$(date -d '30 days ago' +%Y-%m-%d),End=$(date +%Y-%m-%d) \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --group-by Type=DIMENSION,Key=SERVICE

# 일별 비용 트렌드
aws ce get-cost-and-usage \
  --time-period Start=$(date -d '7 days ago' +%Y-%m-%d),End=$(date +%Y-%m-%d) \
  --granularity DAILY \
  --metrics BlendedCost

# 태그별 비용 (EKS 클러스터)
aws ce get-cost-and-usage \
  --time-period Start=$(date -d '30 days ago' +%Y-%m-%d),End=$(date +%Y-%m-%d) \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --group-by Type=TAG,Key=eks:cluster-name
```

### EKS 리소스 사용량

```bash
# 노드 사용률
kubectl top nodes
kubectl get nodes -o json | jq '.items[] | {name:.metadata.name, instance_type:.metadata.labels["node.kubernetes.io/instance-type"], capacity_cpu:.status.capacity.cpu, capacity_memory:.status.capacity.memory}'

# 파드 리소스 요청 vs 실제 사용
kubectl top pods -A --sort-by=cpu
kubectl get pods -A -o json | jq '[.items[] | {ns:.metadata.namespace, name:.metadata.name, cpu_req:.spec.containers[].resources.requests.cpu, mem_req:.spec.containers[].resources.requests.memory}]'

# 미사용 PVC
kubectl get pvc -A -o json | jq '.items[] | select(.status.phase=="Bound") | {ns:.metadata.namespace, name:.metadata.name, size:.spec.resources.requests.storage}'
```

### 절감 기회

```bash
# RI 권장사항
aws ce get-reservation-purchase-recommendation --service "Amazon Elastic Compute Cloud - Compute" --term-in-years ONE_YEAR --payment-option NO_UPFRONT

# Savings Plan 권장사항
aws ce get-savings-plans-purchase-recommendation --savings-plans-type COMPUTE_SP --term-in-years ONE_YEAR --payment-option NO_UPFRONT

# Right-sizing 권장사항
aws ce get-rightsizing-recommendation --service "AmazonEC2"
```

## 최적화 전략

| 전략 | 절감율 | 노력 | 위험 |
|------|--------|------|------|
| 과다 프로비저닝 Right-size | 20-40% | Low | Low |
| Spot 인스턴스 (stateless) | 60-90% | Medium | Medium |
| Graviton 마이그레이션 | 20-40% | Medium | Low |
| Savings Plans (1년) | 20-30% | Low | Low (약정) |
| Reserved Instances (1년) | 30-40% | Low | Medium (약정) |
| Karpenter 통합 | 15-30% | Medium | Low |
| CloudWatch 로그 최적화 | 30-50% | Low | Low |
| 유휴 리소스 삭제 | 100% | Low | None |

## 의사결정 트리

```mermaid
flowchart TD
    START[비용 최적화] --> ANALYZE[현재 지출 분석]
    ANALYZE --> TOP{주요 비용 요인?}

    TOP -->|EC2/EKS| COMPUTE[컴퓨팅 최적화]
    TOP -->|Data Transfer| NETWORK[네트워크 비용]
    TOP -->|Storage| STORAGE[스토리지 최적화]
    TOP -->|CloudWatch| CW[관측성 비용]

    COMPUTE --> C_UTIL{사용률?}
    C_UTIL -->|Low <40%| C_RIGHT[인스턴스 Right-size]
    C_UTIL -->|Medium 40-70%| C_SPOT[Spot 인스턴스 추가]
    C_UTIL -->|High >70%| C_SP[Savings Plans / RIs]

    NETWORK --> N_AZ{Cross-AZ?}
    N_AZ -->|High| N_TOPO[Topology-aware 라우팅 사용]
    N_AZ -->|Low| N_NAT[NAT Gateway 최적화]

    STORAGE --> S_TYPE{미사용?}
    S_TYPE -->|Yes| S_DELETE[미사용 볼륨/스냅샷 삭제]
    S_TYPE -->|No| S_TIER[스토리지 티어 최적화 (gp3, Glacier)]

    CW --> CW_LOG{로그 볼륨?}
    CW_LOG -->|High| CW_FILTER[로그 필터링, 보존기간 조정]
    CW_LOG -->|Normal| CW_METRIC[커스텀 메트릭 축소]
```

## MCP 서버 연동

| MCP 서버 | 용도 |
|----------|------|
| `awspricing` | 서비스 가격 조회, 비용 추정, 가격 비교 |
| `awsdocs` | 비용 최적화 모범 사례, Savings Plans 문서 |
| `awsknowledge` | 비용 아키텍처 권장사항 |

## 사용 예시

### 월간 비용 분석

```
이번 달 AWS 비용을 서비스별로 분석해줘.
```

Cost Agent가 자동으로 호출되어 다음을 수행합니다:
1. Cost Explorer API로 비용 데이터 조회
2. 서비스별 비용 분류
3. 이전 달 대비 변화 분석
4. 주요 비용 증가 요인 식별

### EKS 비용 최적화

```
EKS 클러스터 비용을 최적화하고 싶어.
```

Cost Agent가 다음을 수행합니다:
1. 노드 사용률 분석
2. 과다 프로비저닝 리소스 식별
3. Spot 인스턴스 전환 가능 워크로드 분석
4. Savings Plans 권장사항 제공

## 출력 형식

```
## Cost Analysis Report
- **Period**: [분석 기간]
- **Total Spend**: [$X,XXX]
- **Top Services**: [순위 목록]

## Optimization Recommendations

### Quick Wins (< 1주)
| Action | Estimated Savings | Effort |
|--------|-------------------|--------|
| [작업] | $XXX/month | Low |

### Medium-Term (1-4주)
| Action | Estimated Savings | Effort |
|--------|-------------------|--------|
| [작업] | $XXX/month | Medium |

### Strategic (1-3개월)
| Action | Estimated Savings | Effort |
|--------|-------------------|--------|
| [작업] | $XXX/month | High |

## Total Estimated Savings: $X,XXX/month
```
