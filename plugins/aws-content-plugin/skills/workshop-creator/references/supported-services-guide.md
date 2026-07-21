# Supported Services & Limitations Guide (지원 서비스 / 제약 가이드)

콘텐츠를 설계하기 전에 "이 워크숍이 Workshop Studio 계정에서 실제로 동작할 수 있는가"를 판단하기 위한 가이드. 표준 계정의 근본 제약은 **계정 재활용(recycling)** 때문이다 — 이벤트 종료 후 계정을 깨끗한 상태로 되돌려 다음 이벤트에 다시 쓸 수 있어야 하므로, **Delete/Unregister API가 없는 서비스나 되돌릴 수 없는 리소스는 원천적으로 지원되지 않는다.**

---

## 근본적으로 지원되지 않는 것들

| 범주 | 이유 |
|------|------|
| **AWS Organizations 의존 서비스** (Control Tower, Landing Zone, Firewall Manager 등) | Workshop Studio 자체가 계정 관리에 Organizations를 쓰므로 참가자 계정에서 중첩 사용 불가 |
| **계정 자체의 설정 변경** (얼로우리스트, 서비스 한도 상향 등) | 계정 재활용 전제가 깨짐 — 절대 내부 도구로 직접 수정 시도하지 않는다 |
| **불변(immutable) 스토리지** (S3 Object Lock, AWS Backup Legal Hold) | Workshop Studio가 이후 삭제할 수 없는 리소스가 생성됨 |
| **장기 구매/커밋먼트** (EC2/RDS Reserved Instance, DynamoDB Reserved Capacity, Route53 도메인 구매) | 임시 핸즈온 성격의 이벤트 범위를 벗어남 |
| **Business/Enterprise Support, Trusted Advisor 전체 기능** | 계정에 활성화되어 있지 않음 |
| **Opt-in 리전, 특수 리전**(중국/GovCloud) | 표준 상용 리전만 지원 |
| 서드파티 데이터셋 | `references/workshop-assets-guide.md`의 자산 스캔/정책 제약을 따름 |

새 서비스/액션이 필요하면 Workshop Studio 팀에 직접 요청해야 하며(Delete API가 없는 서비스는 원천적으로 불가), 콘텐츠 저자가 임의로 우회할 방법은 없다.

---

## 대형 인스턴스 / GPU 제약

표준 계정은 신규-검증 계정 수준의 내부 위험 평가 점수를 가진다 — 대형 인스턴스(예: `x1.32xlarge`, 수백 vCPU급)나 EC2 프리픽스(`ml.` 아님) GPU 인스턴스는 기본적으로 **거의 전부 quota 0**이다. SageMaker(`ml.*`) GPU는 허용되지만 보통 단일 인스턴스 + `ml.p3.2xlarge` 이하 수준으로 제한된다.

표준 한도를 넘는 특정 인스턴스/작업 타입이 필요하면 `contentspec.yaml`의 `requiredResources`로 명시적으로 요청해야 한다 — 상세: `references/event-quotas-guide.md`. **콘텐츠당 1개의 required resource 선언만 가능**하므로, sagemaker와 다른 서비스를 동시에 요청할 수 없다.

실제 표준 EC2 vCPU 한도(대표 예시, 리전 공통):

| 인스턴스 계열 | On-Demand vCPU 한도 |
|--------------|---------------------|
| 표준(A/C/D/H/I/M/R/T/Z) | 256 vCPU |
| G/VT (GPU) | 0 vCPU |
| P (GPU) | 0 vCPU |
| High Memory / X | 0 vCPU |
| HPC | 192 vCPU |

→ **테스트 이벤트로 반드시 실제 한도를 검증**한다. 목록에 없는 한도는 테스트 이벤트에서 Service Quotas 콘솔로 직접 확인한다.

---

## AWS Marketplace 지원 범위

현재는 **무상(no-cost) 1st/2nd party AMI, Container, Data Exchange 상품만** 지원한다 (Private Marketplace 기능으로 구현). 유상 상품이나 3rd party 상품, SaaS 상품은 아직 지원되지 않으며 단계적으로 확대될 예정이다. Marketplace 상품에 의존하는 워크숍은 사전에 반드시 테스트 이벤트로 계정에서 실제로 구독/실행되는지 확인한다.

## Amazon Bedrock 지원 범위

- **리전 제한**: `us-west-2`, `us-east-1`에서만 사용 가능
- 대부분의 Foundation Model은 Marketplace 액세스를 통해 활성화되며, 공개 후 약 2주 내 활성화를 목표로 하지만 Bedrock 팀과 조율되는 사안이라 확정된 일정은 아니다. Titan/Nova/OpenAI gpt-oss/Mistral 등 일부 모델은 기본적으로 바로 사용 가능
- **Legacy/EOL 모델은 콘텐츠에 사용하지 않는다** — Bedrock이 주기적으로 구모델을 폐기(deprecate)하므로, 콘텐츠가 시간이 지나 깨질 수 있다
- 대규모 이벤트(대략 팀 50개 이상)에서 특정 서비스를 대량으로 쓰는 경우, 용량 문제로 사전에 해당 서비스팀의 승인이 필요할 수 있다 — Bedrock을 포함해 몇몇 서비스가 이런 용량 제약 대상이다. 대규모 이벤트를 계획한다면 Workshop Studio 팀과 사전에 조율한다.

---

## 크로스 리전 읽기 접근

이벤트의 배포/접근 가능 리전(`deployableRegions`/`accessibleRegions`) **바깥**에서도, 참가자 역할은 대부분의 AWS 서비스에 대해 **읽기 전용(Describe/Get/List) API는 리전 제약 없이** 호출할 수 있다 (예: `ec2:Describe*`, `s3:Get*`, `sagemaker:List*` 등). 콘솔에서 다른 리전의 리소스를 조회하는 화면이 깨지지 않도록 설계된 것으로, **쓰기/생성 작업은 여전히 배포/접근 가능 리전에만 한정**된다. 참가자 정책을 짤 때 "왜 다른 리전에서도 조회가 되는지" 헷갈리지 않도록 이 동작을 알고 있으면 된다.

---

## 체크리스트

- [ ] Delete API가 없는 서비스에 의존하는 콘텐츠는 처음부터 배제
- [ ] GPU/대형 인스턴스가 필요하면 `requiredResources`로 명시하고 테스트 이벤트로 실제 한도 검증
- [ ] Bedrock을 쓴다면 리전을 `us-west-2`/`us-east-1`로 제한하고 Legacy 모델 사용 금지
- [ ] Marketplace 상품은 무상 1st/2nd party AMI/Container/Data Exchange인지 먼저 확인
- [ ] 대규모(수십~수백 팀) 이벤트를 계획한다면 Workshop Studio 팀과 사전 조율
