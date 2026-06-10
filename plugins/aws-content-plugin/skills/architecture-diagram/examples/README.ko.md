# 골든 Exemplar — 스펙 기반 AWS 다이어그램

`scripts/layout_aws.py`의 레퍼런스 출력물입니다. 각 항목은 **스펙(`.yaml`) + 생성된
다이어그램(`.drawio`)** 쌍으로, 두 게이트를 모두 **100/100 [geometry · design]** 으로
통과합니다. 새 다이어그램을 만들 때 스펙을 출발점으로 복사하세요 — 구조/라벨/흐름만 수정하고
좌표는 절대 쓰지 않습니다.

| 스펙 | 패턴 | 시연 내용 |
|------|------|-----------|
| `multi-az-3tier.yaml` | Multi-AZ 웹 3-Tier (CloudFront → ALB → ECS → RDS) | `vpc` 엔진: 미러된 2-AZ 컬럼, 퍼블릭/프라이빗 서브넷, cross-AZ 흐름 |
| `eks-multi-az.yaml` | EKS Multi-AZ 클러스터 | `vpc` 엔진: 서브넷당 다중 서비스 행(EKS Node + Worker), Aurora 데이터 티어 |
| `serverless-api.yaml` | 서버리스 REST API (API GW → Lambda → DynamoDB/S3 + EventBridge) | `stages` 엔진: 좌→우 스테이지 컬럼, VPC 없음, 동기 + 비동기 흐름 |

## 재생성 / 검증

```bash
cd ..                          # 스킬 루트
python3 scripts/layout_aws.py examples/multi-az-3tier.yaml -o /tmp/out.drawio
python3 scripts/validate_drawio.py /tmp/out.drawio
python3 scripts/lint_layout.py /tmp/out.drawio          # 100/100 기대
xvfb-run -a drawio -x -f png -s 2 -o /tmp/out.png /tmp/out.drawio
```

## 스펙 형식 (좌표 없음)

Region의 형태가 레이아웃 엔진을 선택합니다: **`vpc`**(Multi-AZ / 티어) 또는 **`stages`**
(서버리스 / 파이프라인). `external`, `edge`, `title`, `flows`는 공통입니다.

### `vpc` 엔진 — Multi-AZ / 티어형

```yaml
title: "..."
external: [{id, icon, label}]          # 좌측 컬럼, AWS 외부 (사용자, 온프렘)
edge:     [{id, icon, label}]          # external과 Region 사이 (CloudFront/Route53/WAF/ALB)
region:
  label: "AWS Region (...)"
  vpc:
    label: "VPC ..."
    azs: ["AZ-a", "AZ-c"]              # >=1; 동일 크기 미러 컬럼으로 렌더
    tiers:                             # 위→아래 행; (티어 × az)마다 서브넷 1개
      - {name, kind: public|private, services: [{id, icon, label}, ...]}
flows: [{from, to, label, kind: sync|async|highlight}]
```

서비스 id는 AZ별로 인스턴스화됩니다: `alb` → `alb_0`(AZ-0), `alb_1`(AZ-1). bare id를 쓴
flow는 AZ-0 인스턴스에 연결됩니다.

### `stages` 엔진 — 서버리스 / 파이프라인

```yaml
region:
  label: "AWS Region (...)"
  stages:                              # 좌→우 컬럼, VPC/서브넷 없음
    - {name: "Compute", services: [{id: fn, icon: lambda, label: "OrderFn"}, ...]}
    - {name: "Data",    services: [{id: ddb, icon: dynamodb, label: "DynamoDB"}, ...]}
flows: [{from: client, to: fn}, {from: fn, to: ddb}]   # id를 직접 사용 (AZ 접미사 없음)
```

아이콘 short-name은 `layout_aws.py`(`ICONS`)에 있습니다.

> 손으로 좌표를 찍는 XML이나 범용 자동배치 엔진보다 나은 이유: `../SKILL.md` 상단과
> bake-off 보고서 참조 (drawio가 충실도 1위; ELK/Graphviz는 AWS Multi-AZ 대칭을 깨뜨림;
> 격차의 원인은 LLM의 좌표 추측이었고, 이 생성기가 그것을 제거합니다).
