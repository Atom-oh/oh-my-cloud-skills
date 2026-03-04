# oh-my-cloud-skills

[English](README.md)

[Claude Code](https://docs.anthropic.com/en/docs/claude-code)용 AWS 클라우드 플러그인 — 콘텐츠 제작과 인프라 운영.

**제공 기능:**

*콘텐츠 제작 (aws-content-plugin):*
- **인터랙티브 HTML/CSS/JS 프레젠테이션** — Canvas 애니메이션, 퀴즈, 발표자 뷰, GitHub Pages 배포
- **AWS 아키텍처 다이어그램** — Draw.io XML 자동 레이아웃, PNG/SVG 내보내기
- **애니메이션 트래픽 흐름 다이어그램** — SVG + SMIL 애니메이션, 인터랙티브 범례
- **기술 문서** — 전문적인 Markdown 보고서 및 비교 문서
- **GitBook 문서 사이트** — 내비게이션과 컴포넌트가 포함된 구조화된 문서
- **AWS Workshop Studio 콘텐츠** — 다국어 지원 실습 랩

*인프라 운영 (aws-ops-plugin):*
- **EKS 트러블슈팅** — 노드 문제, 업그레이드, 애드온, 5분 트리아지
- **네트워크 진단** — VPC CNI, ALB/NLB, DNS, IP 고갈
- **IAM 및 보안** — IRSA, Pod Identity, RBAC, 정책 검증
- **관측성** — CloudWatch, Container Insights, Prometheus, X-Ray
- **비용 최적화** — 가격 분석, 절감 계획, 라이트사이징

*플러그인 변환 (kiro-power-converter):*
- **Claude Code → Kiro Power** — 플러그인을 Kiro IDE에서 사용할 수 있도록 자동 변환
- **다양한 입력 소스** — GitHub URL, 로컬 경로, 마켓플레이스 검색, 개별 스킬
- **제로 의존성** — Python 3.8+ 표준 라이브러리만 사용

---

## 설치

```bash
# 마켓플레이스 추가
/plugin marketplace add https://github.com/Atom-oh/oh-my-cloud-skills

# 플러그인 설치
/plugin install aws-content-plugin@oh-my-cloud-skills
/plugin install aws-ops-plugin@oh-my-cloud-skills
/plugin install kiro-power-converter@oh-my-cloud-skills
```

로컬 개발용:
```bash
# 로컬 디렉토리에서 플러그인 로드
claude --plugin-dir ./plugins/aws-content-plugin
claude --plugin-dir ./plugins/aws-ops-plugin
claude --plugin-dir ./plugins/kiro-power-converter
```

제거:
```bash
# 플러그인 제거
/plugin uninstall aws-content-plugin@oh-my-cloud-skills
/plugin uninstall aws-ops-plugin@oh-my-cloud-skills
/plugin uninstall kiro-power-converter@oh-my-cloud-skills

# 마켓플레이스 제거
/plugin marketplace remove oh-my-cloud-skills
```

---

## 리액티브 프레젠테이션

핵심 기능입니다. 필요한 교육이나 프레젠테이션을 설명하면, Claude가 완전한 인터랙티브 HTML 슬라이드쇼를 만들어 줍니다. PowerPoint도, Reveal.js 설정도, npm install도 필요 없습니다.

### 생성되는 결과물

각 프레젠테이션은 공유 프레임워크를 사용하는 독립 HTML 파일 세트입니다:

```
your-repo/
├── index.html                      # 모든 프레젠테이션을 연결하는 허브 페이지
├── common/                         # 공유 프레임워크 (한 번만 복사)
│   ├── theme.css                   # 다크 테마, Pretendard 폰트, 16:9 레이아웃
│   ├── slide-framework.js          # 키보드/터치 내비게이션, 진행 바, 해시 라우팅
│   ├── presenter-view.js           # 드래그 가능한 스플리터가 있는 발표자 뷰
│   ├── animation-utils.js          # Canvas 프리미티브, AnimationLoop, easing
│   ├── quiz-component.js           # 퀴즈 자동 채점 및 피드백
│   ├── export-utils.js             # PDF 내보내기 및 ZIP 다운로드
│   └── aws-icons/                  # AWS Architecture Icons (선택사항)
└── eks-autoscaling/                # 프레젠테이션당 하나의 디렉토리
    ├── index.html                  # 목차
    ├── 01-fundamentals.html        # 블록 1 (20-35분)
    ├── 02-karpenter.html           # 블록 2
    └── 03-advanced.html            # 블록 3
```

### 슬라이드 유형

| 슬라이드 유형 | 기능 |
|---|---|
| Canvas Animation | Play/Pause 컨트롤이 있는 애니메이션 아키텍처 다이어그램 |
| Compare Toggle | 토글 버튼으로 A vs B 나란히 비교 |
| Tabs | 탭 콘텐츠 패널 (예: YAML 설정 변형) |
| Timeline | 수평 단계별 프로세스 시각화 |
| Checklist | 클릭하여 토글하는 베스트 프랙티스 (선택적 YAML 확장) |
| Quiz | 자동 채점 포함 객관식 문제 |
| Code Block | YAML/JSON/HCL 구문 강조 코드 블록 |
| Slider | 실시간 계산 출력이 있는 Range 입력 |
| Pain Quote | 고객 문제 설명 및 과제 목록 |

### 키보드 단축키

| 키 | 동작 |
|-----|--------|
| `<-` `->` | 이전 / 다음 슬라이드 |
| `Space` | 다음 슬라이드 |
| `F` | 전체 화면 전환 |
| `P` | 발표자 뷰 열기 (새 창) |
| `Esc` | 전체 화면 종료 |
| `Home` / `End` | 첫 / 마지막 슬라이드 |

### 작동 방식

1. **기획** — Claude가 주제, 대상, 시간, 언어, 선택적 PPTX 템플릿에 대해 질문
2. **작성** — Marp 마크다운으로 콘텐츠 원본 작성
3. **생성** — Canvas 애니메이션과 인터랙티브 요소가 포함된 HTML 파일 빌드
4. **검토** — 인터랙티브 피드백 루프: Marp 직접 편집, 프롬프트로 수정 요청, 또는 진행
5. **향상** — Canvas 애니메이션 추가, AWS 아이콘 추출, 발표자 뷰 테스트
6. **배포** — GitHub Pages로 `git push`. 빌드 단계 불필요

### 프레젠테이션 만들기

#### 시작하기

필요한 내용을 설명하는 것으로 시작합니다. 다음은 예시 프롬프트입니다:

```
"EKS 오토스케일링 교육 프레젠테이션 만들어줘"
```

```
"Create a presentation on AWS Lambda cold starts"
```

```
"Karpenter 마이그레이션 실습 슬라이드 만들어줘"
```

```
"S3 보안 베스트 프랙티스 교육 자료 만들어줘"
```

프레젠테이션 관련 키워드를 감지하면 에이전트가 자동으로 활성화됩니다.

#### Claude가 묻는 질문

콘텐츠를 생성하기 전에 Claude가 프레젠테이션을 맞춤 제작하기 위해 7가지 기획 질문을 합니다:

| # | 질문 | 설명 | 기본값 |
|---|------|------|--------|
| 1 | 주제 및 대상 | 기술적 깊이, 페인 포인트, 학습 목표 | — |
| 2 | 시간 | 전체 길이 — 블록 수와 슬라이드 수 결정 | — |
| 3 | 블록 | 블록당 20-35분, 블록 사이 5분 휴식 | 시간 기반 자동 분할 |
| 4 | 대상 저장소 | 배포용 GitHub 저장소 | `~/reactive_presentation/` |
| 5 | 언어 | 한국어 또는 영어 (기술 용어는 항상 영어) | 한국어 |
| 6 | PPTX 템플릿 | 테마 추출용 기업 브랜딩 `.pptx` 파일 | 없음 (다크 테마) |
| 7 | 발표자 정보 | 커버 슬라이드용 이름 및 소속 (재사용을 위해 저장) | — |

답변을 수집한 후 Claude가 Marp 마크다운 콘텐츠를 작성하고 인터랙티브 HTML 슬라이드를 생성합니다.

#### 검토 및 수정

Claude가 초기 콘텐츠를 생성한 후, 세 가지 옵션으로 검토 루프에 들어갑니다:

1. **Marp 직접 수정** — 에디터에서 `.md` 파일을 열고 변경한 후 "완료"라고 말합니다. Claude가 편집 내용을 읽고 HTML을 업데이트합니다.

2. **프롬프트로 수정 요청** — 변경할 내용을 설명합니다 (예: "슬라이드 5 뒤에 퀴즈 추가해줘", "타임라인을 3단계로 줄여줘"). Claude가 Marp 소스와 HTML 파일을 모두 업데이트합니다.

3. **진행** — 콘텐츠가 좋으면 승인하고 Canvas 애니메이션과 인터랙티브 요소가 추가되는 향상 단계로 넘어갑니다.

이 루프는 만족할 때까지 반복됩니다. Marp 마크다운은 항상 HTML과 동기화됩니다. Marp가 콘텐츠 원본이고, HTML이 그 위에 인터랙티비티를 추가합니다.

#### GitHub Pages 배포

프레젠테이션이 완성되면:

```bash
git add common/ {slug}/ index.html
git commit -m "feat: add {presentation-name} interactive training"
git push origin main
```

그 다음 GitHub Pages 활성화: Settings -> Pages -> main branch / root.

빌드 단계가 필요 없습니다. HTML 파일이 직접 서빙됩니다.

### PPTX 테마 추출

기업 PowerPoint 템플릿이 있으면 `.pptx` 파일을 제공하세요. 에이전트가 색상, 폰트, 로고를 추출하여 CSS 오버라이드로 변환합니다. 다크 테마 프레임워크에 기업 브랜딩이 자동으로 적용됩니다.

---

## 아키텍처 다이어그램

Draw.io XML 형식의 정적 AWS 아키텍처 다이어그램. 에이전트가 AWS 아이콘을 배치하고, VPC/서브넷 경계로 리소스를 그룹화하며, 연결을 자동 레이아웃합니다.

**출력**: `.drawio` 파일 — PNG 또는 SVG로 내보내기하여 프레젠테이션, 문서, GitBook 페이지에 삽입 가능.

**지원**: 자동 레이아웃, AWS 아이콘 배치, VPC/서브넷/리전 그룹화, 다중 티어 아키텍처.

```
"EKS와 ALB 아키텍처 다이어그램 그려줘"
```

```
"퍼블릭/프라이빗 서브넷이 있는 3티어 VPC 아키텍처 다이어그램 만들어줘"
```

---

## 애니메이션 다이어그램

SVG + SMIL 애니메이션을 사용한 동적 트래픽 흐름 다이어그램. 각 다이어그램은 재생/일시정지 컨트롤과 인터랙티브 범례가 포함된 독립 HTML 파일입니다.

**출력**: SVG 애니메이션이 포함된 `.html` 파일 — 의존성 없이 모든 브라우저에서 작동.

**지원**: 요청 라우팅 흐름, 데이터 파이프라인 시각화, 멀티 서비스 트래픽 패턴, 색상 구분 서비스 티어.

```
"API Gateway → Lambda → DynamoDB 흐름 애니메이션 만들어줘"
```

```
"EKS Pod 간 통신을 보여주는 트래픽 흐름 애니메이션 만들어줘"
```

---

## 문서

전문적인 Markdown 기술 문서 — 보고서, 솔루션 비교, 아키텍처 문서, 가이드. `architecture-diagram-agent`와 연동하여 인라인 다이어그램을 포함할 수 있습니다.

**출력**: 테이블, 코드 블록, 다이어그램 참조가 포함된 `.md` 파일.

```
"EKS vs ECS 비교 문서 작성해줘"
```

```
"S3 보안 베스트 프랙티스 기술 보고서 만들어줘"
```

---

## GitBook 사이트

내비게이션, 컴포넌트, 상호 참조가 포함된 구조화된 문서 사이트. `SUMMARY.md`, 코드 탭, 힌트, 확장 가능 섹션이 포함된 완전한 GitBook 프로젝트를 생성합니다.

**출력**: GitBook 프로젝트 디렉토리 — GitBook 연결 저장소에 푸시하면 자동 배포.

**지원**: 다중 페이지 내비게이션, 코드 탭 (다국어), 힌트/경고 블록, 임베드 다이어그램.

```
"API용 GitBook 문서 사이트 만들어줘"
```

```
"EKS 운영을 위한 GitBook 지식 베이스 만들어줘"
```

---

## 워크샵

실습 랩 모듈이 포함된 AWS Workshop Studio 콘텐츠. CloudFormation 템플릿, 단계별 지침, 다국어 지원(한국어 + 영어)을 포함한 완전한 워크샵 구조를 생성합니다.

**출력**: `contentspec.yaml`, 모듈 디렉토리, 이중 언어 `.ko.md` / `.en.md` 파일 쌍이 포함된 Workshop Studio 콘텐츠.

**지원**: 사전 조건이 있는 랩 모듈, CloudFormation 인프라 템플릿, Workshop Studio 지시문 (Hugo shortcode 아님).

```
"EKS 핸즈온 워크샵 만들어줘"
```

```
"Lambda와 DynamoDB 랩이 포함된 서버리스 워크샵 만들어줘"
```

---

## 콘텐츠 검토

모든 콘텐츠 유형의 품질 게이트. `content-review-agent`는 레이아웃, 용어, 할루시네이션, 언어, PII/민감 데이터, 가독성, 접근성, 구조적 완성도를 검사하여 100점 척도로 평가합니다.

콘텐츠 생성 워크플로우(프레젠테이션, 문서, GitBook, 워크샵) 완료 시 자동으로 사용됩니다. 직접 호출도 가능합니다:

```
"프레젠테이션 품질 검토해줘"
```

점수 세부 사항은 [품질 게이트](#품질-게이트) 섹션을 참조하세요.

---

## AWS 운영

AWS/EKS 인프라 운영 및 트러블슈팅. 문제를 설명하면 — 노드 장애, 네트워크 문제, IAM 오류, 비용 급증 — 적절한 에이전트가 자동으로 활성화됩니다.

### 에이전트

| 에이전트 | 도메인 | 예시 프롬프트 |
|----------|--------|---------------|
| `eks-agent` | EKS 클러스터 | "노드가 NotReady 상태, 트러블슈팅해줘" |
| `network-agent` | 네트워크 | "Pod가 외부 서비스에 연결 안 됨" |
| `iam-agent` | IAM/RBAC | "Pod에서 S3 접근 시 AccessDenied" |
| `observability-agent` | 관측성 | "EKS Container Insights 설정해줘" |
| `storage-agent` | 스토리지 | "PVC가 Pending 상태" |
| `database-agent` | 데이터베이스 | "EKS에서 Aurora 연결 타임아웃" |
| `cost-agent` | 비용 | "EKS 클러스터 비용 분석해줘" |
| `analytics-agent` | 데이터 분석 | "OpenSearch 클러스터 상태 확인해줘" |
| `ops-coordinator-agent` | 장애 조율 | "프로덕션 장애, 대응 조율해줘" |

### 스킬

| 스킬 | 트리거 | 기능 |
|------|--------|------|
| `ops-troubleshoot` | "troubleshoot", "장애" | 5분 트리아지 → 조사 → 해결 → 포스트모텀 |
| `ops-health-check` | "health check", "헬스체크" | 6개 도메인 인프라 상태 점검 |
| `ops-network-diagnosis` | "network issue", "네트워크 오류" | VPC CNI, 로드밸런서, DNS 심층 진단 |
| `ops-observability` | "monitoring", "모니터링" | CloudWatch, Prometheus, 로그 분석 |
| `ops-security-audit` | "security audit", "보안 점검" | IAM 감사, 네트워크 보안, 컴플라이언스 |

### MCP 연동

운영 플러그인은 AWS MCP 서버에 연결하여 실시간 인프라 데이터를 제공합니다:

| 서버 | 용도 |
|------|------|
| `awsknowledge` | 아키텍처 권장 사항 및 리전 가용성 |
| `awsdocs` | AWS 공식 문서 검색 |
| `awsapi` | AWS API 직접 호출 (describe, list 등) |
| `awspricing` | 서비스 요금 및 비용 분석 |
| `awsiac` | CloudFormation/CDK 검증 및 트러블슈팅 |

### 장애 대응 워크플로우

```
사용자 보고 → ops-coordinator (트리아지 + 심각도 평가)
               ├── 네트워크 → network-agent
               ├── 클러스터 → eks-agent
               ├── 인증     → iam-agent
               ├── 스토리지 → storage-agent
               ├── 로그     → observability-agent
               └── 검색/분석 → analytics-agent
             ← 종합 분석 → 근본 원인 → 해결 → 검증
```

모든 에이전트는 Claude가 일치하는 키워드를 감지하면 자동으로 활성화됩니다.

---

## Kiro Power 변환기

Claude Code 플러그인을 [Kiro IDE](https://kiro.dev) Power 형식으로 자동 변환합니다. 구조 변환, frontmatter 변환, MCP 설정 마이그레이션, 키워드 집계를 모두 처리합니다.

### 왜 필요한가

Claude Code 플러그인과 Kiro Power는 비슷한 개념(에이전트 + 스킬 + MCP 서버)을 공유하지만, 폴더 구조, 파일 형식, 설정 방식이 다릅니다. 이 플러그인은 수동 재작성 없이 Claude Code 플러그인을 Kiro에서 재사용할 수 있도록 합니다.

### 변환 매핑

| Claude Code | Kiro Power | 변환 내용 |
|-------------|------------|-----------|
| `.claude-plugin/plugin.json` | `POWER.md` | 매니페스트 → 집계된 키워드가 포함된 YAML frontmatter |
| `CLAUDE.md` | `steering/routing.md` | `inclusion: always`로 래핑 |
| `agents/*.md` | `steering/<agent>.md` | `tools`/`model` 제거, `inclusion: auto` 추가 |
| `skills/*/SKILL.md` | `steering/<skill>.md` | `triggers[]`를 description에 병합, `inclusion: auto` |
| `skills/*/references/*.md` | `steering/ref-*.md` | `inclusion: manual` frontmatter 추가 |
| `.mcp.json` | `mcp.json` | `type` 제거, `autoApprove`/`disabled` 추가 |

### 사용법

#### 에이전트 사용 (대화형)

자연어로 설명하면 됩니다. "키로 변환", "kiro power", "convert to kiro" 등의 키워드로 에이전트가 자동 활성화됩니다:

```
"aws-ops-plugin을 키로 파워로 변환해줘"
```

```
"Convert aws-ops-plugin to Kiro Power format"
```

#### 스크립트 사용 (CLI)

변환 스크립트는 4가지 입력 소스와 3가지 출력 대상을 지원합니다. 외부 의존성 없이 Python 3.8+ 표준 라이브러리만 사용합니다.

**로컬 플러그인에서 변환:**
```bash
python3 plugins/kiro-power-converter/skills/kiro-convert/scripts/convert_plugin_to_power.py \
  --source ./plugins/aws-ops-plugin \
  --output /tmp/aws-ops-power \
  --target export
```

**GitHub 저장소에서 변환:**
```bash
python3 plugins/kiro-power-converter/skills/kiro-convert/scripts/convert_plugin_to_power.py \
  --git-url https://github.com/Atom-oh/oh-my-cloud-skills \
  --plugin-path plugins/aws-ops-plugin \
  --output /tmp/aws-ops-power \
  --target global
```

**마켓플레이스 이름으로 변환:**
```bash
python3 plugins/kiro-power-converter/skills/kiro-convert/scripts/convert_plugin_to_power.py \
  --marketplace aws-ops-plugin \
  --output /tmp/aws-ops-power \
  --target global
```

**플러그인 검색:**
```bash
python3 plugins/kiro-power-converter/skills/kiro-convert/scripts/convert_plugin_to_power.py \
  --search "aws"
```

**개별 스킬 변환:**
```bash
# 단일 스킬 → 독립 steering 파일
python3 plugins/kiro-power-converter/skills/kiro-convert/scripts/convert_plugin_to_power.py \
  --skill ./plugins/aws-ops-plugin/skills/ops-troubleshoot \
  --output ~/.kiro/steering/ops-troubleshoot.md

# 여러 스킬 일괄 변환
python3 plugins/kiro-power-converter/skills/kiro-convert/scripts/convert_plugin_to_power.py \
  --skill ./skills/ops-troubleshoot \
  --skill ./skills/ops-health-check \
  --output ~/.kiro/steering/
```

### 출력 대상

| 대상 | 플래그 | 설치 경로 | 용도 |
|------|--------|----------|------|
| **export** | `--target export` (기본) | `--output` 경로 | 공유, 검토, 수동 설치 |
| **global** | `--target global` | `~/.kiro/powers/<name>/` | 모든 Kiro 프로젝트에서 사용 |
| **project** | `--target project` | `.kiro/powers/<name>/` | 현재 프로젝트에서만 사용 |

### 변환 결과 예시

`aws-ops-plugin` (에이전트 8개, 스킬 5개, MCP 서버 5개) 변환 결과:

```
aws-ops-power/
├── POWER.md                      # 약 96개 키워드가 집계된 매니페스트
├── mcp.json                      # 5개 AWS MCP 서버 (type 필드 제거됨)
└── steering/
    ├── routing.md                # 항상 로드되는 라우팅 컨텍스트
    ├── eks-agent.md              # 자동 활성화 에이전트 steering 파일
    ├── network-agent.md
    ├── iam-agent.md
    ├── observability-agent.md
    ├── storage-agent.md
    ├── database-agent.md
    ├── cost-agent.md
    ├── ops-coordinator-agent.md  # description에 "(Advanced reasoning)" 추가
    ├── ops-troubleshoot.md       # 트리거가 병합된 스킬
    ├── ops-health-check.md
    ├── ops-network-diagnosis.md
    ├── ops-observability.md
    ├── ops-security-audit.md
    └── ref-*.md                  # 15개 레퍼런스 파일 (manual inclusion)
```

### 엣지 케이스

| 상황 | 처리 방법 |
|------|----------|
| 대용량 에셋 (icons/, 4,224 파일) | 다운로드 스크립트 생성, 디렉토리 건너뜀 |
| Opus 모델 에이전트 | `model` 제거, description에 "(Advanced reasoning)" 추가 |
| 한/영 이중 키워드 | 양쪽 언어 모두 POWER.md keywords에 포함 |
| `.mcp.json` 없음 | `mcp.json` 생성 건너뜀 |
| 중첩 경로 참조 | Power 내 상대 경로로 변환 |

---

## 빠른 시작

### 콘텐츠 에이전트

| 에이전트 | 생성물 | 예시 프롬프트 | 출력 |
|---------|--------|-------------|------|
| `presentation-agent` | 인터랙티브 HTML 슬라이드 | "AWS 교육 프레젠테이션 만들어줘" | `.html` (GitHub Pages) |
| `architecture-diagram-agent` | AWS 아키텍처 다이어그램 | "VPC 아키텍처 다이어그램 그려줘" | `.drawio` -> `.png` |
| `animated-diagram-agent` | 애니메이션 트래픽 흐름 | "트래픽 흐름 애니메이션 만들어줘" | `.html` (SVG+SMIL) |
| `document-agent` | 기술 문서 | "EKS vs ECS 비교 문서 작성해줘" | `.md` |
| `gitbook-agent` | 문서 사이트 | "GitBook 문서 사이트 만들어줘" | GitBook project |
| `workshop-agent` | 워크샵 콘텐츠 | "EKS 워크샵 만들어줘" | Workshop Studio |
| `content-review-agent` | 품질 검토 | "프레젠테이션 검토해줘" | Review report |

### 운영 에이전트

| 에이전트 | 도메인 | 예시 프롬프트 | 출력 |
|---------|--------|-------------|------|
| `eks-agent` | EKS 클러스터 | "노드 NotReady 트러블슈팅" | 진단 + 수정 |
| `network-agent` | 네트워크 | "VPC CNI IP 부족" | 진단 + 수정 |
| `iam-agent` | IAM/RBAC | "Pod에서 S3 접근 불가" | 정책 수정 |
| `observability-agent` | 관측성 | "Container Insights 설정" | 설정 + 쿼리 |
| `storage-agent` | 스토리지 | "PVC Pending 상태" | 진단 + 수정 |
| `database-agent` | 데이터베이스 | "Aurora 타임아웃" | 진단 + 수정 |
| `cost-agent` | 비용 | "클러스터 비용 분석" | 비용 보고서 |
| `analytics-agent` | 데이터 분석 | "OpenSearch 상태 확인" | 진단 + 수정 |
| `ops-coordinator-agent` | 장애 조율 | "프로덕션 장애 대응" | 조율된 대응 |

모든 에이전트는 Claude가 프롬프트에서 일치하는 키워드를 감지하면 자동으로 활성화됩니다.

---

## 스킬

### 콘텐츠 스킬

| 스킬 | 제공 내용 |
|------|----------|
| `reactive-presentation` | 프레젠테이션 프레임워크 (CSS/JS), Marp 변환 스크립트, AWS 아이콘 추출, 슬라이드 패턴 참조 |
| `architecture-diagram` | Draw.io XML 템플릿, AWS 아이콘 참조, 레이아웃 패턴 |
| `animated-diagram` | SMIL 애니메이션 가이드, HTML 래퍼 템플릿, 트래픽 흐름 패턴 |
| `gitbook` | GitBook 구조 가이드, 컴포넌트 패턴, 내비게이션 템플릿 |
| `workshop-creator` | Workshop Studio 지시문, 모듈 템플릿, CloudFormation 참조 |

### 운영 스킬

| 스킬 | 제공 내용 |
|------|----------|
| `ops-troubleshoot` | 체계적 트러블슈팅 프레임워크, 장애 대응 절차 |
| `ops-health-check` | 6개 도메인 인프라 상태 점검 |
| `ops-network-diagnosis` | VPC CNI, 로드밸런서, DNS 심층 진단 참조 |
| `ops-observability` | CloudWatch, Prometheus, 로그 분석 설정 |
| `ops-security-audit` | IAM 감사, 네트워크 보안, 컴플라이언스 검사 절차 |

---

## 워크플로우

### 콘텐츠 워크플로우

```
프레젠테이션:       presentation-agent  -->  content-review-agent  -->  GitHub Pages
정적 다이어그램:    architecture-diagram-agent  -->  .drawio  -->  PNG export
애니메이션 다이어그램: animated-diagram-agent  -->  .html (SVG + SMIL)
문서:             document-agent  -->  content-review-agent  -->  .md
GitBook:          gitbook-agent  -->  content-review-agent  -->  git push
워크샵:           workshop-agent  -->  content-review-agent  -->  Workshop Studio
```

### 운영 워크플로우

```
장애 대응:     ops-coordinator  -->  전문 에이전트  -->  근본 원인  -->  해결  -->  검증
트러블슈팅:    매칭된 에이전트  -->  진단  -->  해결  -->  검증
헬스체크:      ops-health-check 스킬  -->  6개 도메인 평가
보안 감사:     ops-security-audit 스킬  -->  IAM + 네트워크 + 컴플라이언스
```

다이어그램은 프레젠테이션, 문서, GitBook 페이지에 더 큰 워크플로우의 일부로 임베드할 수 있습니다.

---

## 품질 게이트

모든 콘텐츠는 `content-review-agent`를 통해 레이아웃, 용어, 언어, 접근성, 구조적 완성도를 기준으로 100점 척도로 평가됩니다.

| 판정 | 점수 | 조건 | 결과 |
|------|------|------|------|
| **PASS** | >= 85 | Critical 0, Warning <= 3 | 배포 승인 |
| **REVIEW** | 70-84 | Critical 0, Warning 4-10 | 수정 후 재검토 |
| **FAIL** | < 70 | Critical >= 1 또는 Warning > 10 | 진행 불가 |

---

## 프로젝트 구조

```
plugins/
├── aws-content-plugin/                # 콘텐츠 제작 플러그인
│   ├── .claude-plugin/plugin.json     # 플러그인 매니페스트 (7 에이전트, 5 스킬)
│   ├── CLAUDE.md                      # 자동 호출 규칙 및 워크플로우
│   ├── agents/
│   │   ├── presentation-agent.md      # 인터랙티브 HTML 슬라이드쇼
│   │   ├── architecture-diagram-agent.md # Draw.io XML 다이어그램
│   │   ├── animated-diagram-agent.md  # SVG + SMIL 애니메이션
│   │   ├── document-agent.md          # Markdown 문서 및 보고서
│   │   ├── gitbook-agent.md           # GitBook 문서 사이트
│   │   ├── workshop-agent.md          # AWS Workshop Studio 콘텐츠
│   │   └── content-review-agent.md    # 통합 품질 검토
│   └── skills/
│       ├── reactive-presentation/     # 프레젠테이션 프레임워크 + AWS 아이콘
│       │   ├── SKILL.md               # 워크플로우 및 슬라이드 유형 참조
│       │   ├── assets/                # theme.css, slide-framework.js, export-utils.js, ...
│       │   ├── scripts/               # marp_to_slides.py, extract_pptx_theme.py
│       │   ├── references/            # framework-guide.md, slide-patterns.md
│       │   └── icons/                 # AWS Architecture Icons (4,224 파일)
│       ├── architecture-diagram/      # Draw.io 템플릿 및 패턴
│       ├── animated-diagram/          # SMIL 애니메이션 가이드 및 템플릿
│       ├── gitbook/                   # GitBook 구조 및 컴포넌트
│       └── workshop-creator/          # Workshop Studio 지시문 및 템플릿
│
├── aws-ops-plugin/                    # 인프라 운영 플러그인
│   ├── .claude-plugin/plugin.json     # 플러그인 매니페스트 (9 에이전트, 5 스킬)
│   ├── .mcp.json                      # AWS MCP 서버 설정
│   ├── CLAUDE.md                      # 자동 호출 규칙 및 워크플로우
│   ├── agents/
│   │   ├── eks-agent.md               # EKS 클러스터 운영
│   │   ├── network-agent.md           # VPC CNI, ALB/NLB, DNS
│   │   ├── iam-agent.md               # IRSA, Pod Identity, RBAC
│   │   ├── observability-agent.md      # CloudWatch, AMP, AMG, ADOT, Prometheus/Grafana
│   │   ├── storage-agent.md           # EBS/EFS/FSx CSI 드라이버
│   │   ├── database-agent.md          # RDS, Aurora, DynamoDB, ElastiCache
│   │   ├── cost-agent.md              # 비용 분석 및 최적화
│   │   ├── analytics-agent.md         # OpenSearch, ClickHouse, Athena, QuickSight, Kinesis
│   │   └── ops-coordinator-agent.md   # 다중 도메인 장애 조율
│   └── skills/
│       ├── ops-troubleshoot/          # 체계적 트러블슈팅
│       ├── ops-health-check/          # 인프라 상태 점검
│       ├── ops-network-diagnosis/     # VPC CNI, LB, DNS 심층 진단
│       ├── ops-observability/         # CloudWatch, Prometheus, 로그 분석
│       └── ops-security-audit/        # IAM 감사, 네트워크 보안, 컴플라이언스
│
└── kiro-power-converter/              # 플러그인 변환 도구
    ├── .claude-plugin/plugin.json     # 플러그인 매니페스트 (1 에이전트, 1 스킬)
    ├── CLAUDE.md                      # 자동 호출 규칙
    ├── agents/
    │   └── kiro-converter-agent.md    # 변환 에이전트 (4가지 입력 소스)
    └── skills/
        └── kiro-convert/              # 변환 스킬
            ├── SKILL.md               # 대화형 변환 워크플로우
            ├── scripts/
            │   └── convert_plugin_to_power.py  # CLI 변환기 (Python 3.8+, 의존성 없음)
            └── references/
                ├── kiro-power-format.md        # Kiro Power 형식 사양
                └── conversion-rules.md         # 필드별 변환 규칙
```
