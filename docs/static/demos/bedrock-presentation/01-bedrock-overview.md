---
remarp: true
block: bedrock-overview
title: "Amazon Bedrock Overview"
---

<!-- Slide 1: Cover -->
@type: cover

# Amazon Bedrock 핵심 이해

:::html
<div class="bedrock-cover">
  <div class="cover-mark fragment zoom-in" data-fragment-index="1">
    <img src="common/aws-icons/services/Arch_Amazon-Bedrock_48.svg" alt="Amazon Bedrock">
  </div>
  <p class="cover-subtitle fragment fade-up" data-fragment-index="2">Foundation model 선택에서 프로덕션 운영까지</p>
  <div class="cover-tags fragment fade-up" data-fragment-index="3">
    <span>30 min</span>
    <span>Level 200-300</span>
    <span>Developers / Architects</span>
  </div>
</div>
:::

:::css
.bedrock-cover {
  min-height: 22rem;
  max-height: 500px;
  display: grid;
  place-items: center;
  gap: 1.2rem;
  text-align: center;
  word-break: keep-all;
  overflow-wrap: break-word;
}
.cover-mark {
  width: 6rem;
  height: 6rem;
  border-radius: 1rem;
  display: grid;
  place-items: center;
  background: rgba(255, 153, 0, 0.12);
  border: 1px solid rgba(255, 153, 0, 0.45);
}
.cover-mark img { width: 4.2rem; height: 4.2rem; }
.cover-subtitle {
  margin: 0;
  font-size: 1.35rem;
  color: var(--text-secondary);
}
.cover-tags {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 0.75rem;
}
.cover-tags span {
  border: 1px solid var(--border);
  border-radius: 999px;
  padding: 0.45rem 0.8rem;
  background: var(--bg-card);
  color: var(--text-secondary);
}
:::

:::notes
{timing: 1min}
오늘은 Amazon Bedrock을 단순한 모델 호출 API가 아니라, 생성형 AI 애플리케이션을 실제 서비스까지 가져가기 위한 관리형 플랫폼으로 보겠습니다. 발표의 초점은 “어떤 모델이 가장 좋은가”보다 “모델, 데이터, 도구, 보안, 운영을 어떻게 한 덩어리로 설계할 것인가”에 있습니다. {cue: pause} 먼저 Bedrock을 도입하는 이유부터 정리하겠습니다.
:::

---
<!-- Slide 2: Why Bedrock -->
@type: content

## 왜 Amazon Bedrock인가

:::html
<div class="bedrock-three">
  <div class="bedrock-card fragment fade-up" data-fragment-index="1">
    <div class="card-kicker">Choice</div>
    <h3>여러 Foundation Model을 같은 방식으로 사용</h3>
    <p>Amazon, Anthropic, DeepSeek, Moonshot AI, MiniMax, OpenAI 등 다양한 모델을 관리형 API로 접근합니다.</p>
  </div>
  <div class="bedrock-card fragment fade-up" data-fragment-index="2">
    <div class="card-kicker">Enterprise</div>
    <h3>보안과 거버넌스를 기본 전제로 설계</h3>
    <p>IAM, 암호화, Guardrails, 로깅, 비용 추적을 앱 아키텍처 안에 포함합니다.</p>
  </div>
  <div class="bedrock-card fragment fade-up" data-fragment-index="3">
    <div class="card-kicker">Production</div>
    <h3>RAG, Agent, 평가, 운영까지 연결</h3>
    <p>모델 호출 이후에 필요한 Knowledge Bases, Agents, Guardrails, Observability를 함께 구성합니다.</p>
  </div>
</div>
:::

:::css
.bedrock-three {
  max-height: 500px;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1rem;
  word-break: keep-all;
  overflow-wrap: break-word;
}
.bedrock-card {
  min-height: 16rem;
  padding: 1.25rem;
  border: 1px solid var(--border);
  border-radius: 0.5rem;
  background: var(--bg-card);
}
.bedrock-card h3 {
  margin: 0.5rem 0 0.75rem;
  font-size: 1.35rem;
  line-height: 1.25;
}
.bedrock-card p {
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.55;
}
.card-kicker {
  color: var(--accent);
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0;
}
:::

:::notes
{timing: 3min}
Bedrock의 출발점은 모델 선택권입니다. 하지만 실무에서 더 중요한 포인트는 모델을 바꿔도 애플리케이션 구조와 운영 절차가 크게 흔들리지 않게 만드는 것입니다. 공식 문서도 Bedrock을 “secure, enterprise-grade access to high-performing foundation models”라고 설명합니다. 즉 모델 API 자체보다, 기업 환경에서 필요한 보안, 연결, 품질 관리, 배포 운영을 함께 생각하게 만드는 서비스입니다. {cue: question} 우리 조직에서 모델 호출보다 더 오래 걸리는 부분이 데이터 연결인지, 보안 검토인지, 운영 기준인지 떠올려보면 다음 구조가 더 잘 보입니다.
:::

---
<!-- Slide 3: Mental Model -->
@type: content

## Bedrock을 보는 6개 축

:::html
<div class="mental-grid">
  <div class="mental-item fragment fade-up" data-fragment-index="1">
    <strong>1. Model Access</strong>
    <span>Foundation model 선택, 호출 방식, 모델별 파라미터</span>
  </div>
  <div class="mental-item fragment fade-up" data-fragment-index="2">
    <strong>2. Prompt Runtime</strong>
    <span>Converse, InvokeModel, streaming, tool calling</span>
  </div>
  <div class="mental-item fragment fade-up" data-fragment-index="3">
    <strong>3. Knowledge</strong>
    <span>Knowledge Bases, RAG, vector store, citations</span>
  </div>
  <div class="mental-item fragment fade-up" data-fragment-index="4">
    <strong>4. Orchestration</strong>
    <span>Agents, action groups, API invocation, traces</span>
  </div>
  <div class="mental-item fragment fade-up" data-fragment-index="5">
    <strong>5. Safety</strong>
    <span>Guardrails, PII, topic policy, grounding checks</span>
  </div>
  <div class="mental-item fragment fade-up" data-fragment-index="6">
    <strong>6. Operations</strong>
    <span>evaluation, monitoring, cost allocation, change control</span>
  </div>
</div>
:::

:::css
.mental-grid {
  max-height: 500px;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.9rem;
  word-break: keep-all;
  overflow-wrap: break-word;
}
.mental-item {
  min-height: 8.5rem;
  padding: 1rem;
  border: 1px solid var(--border);
  border-radius: 0.5rem;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.04), rgba(255, 255, 255, 0.015));
}
.mental-item strong {
  display: block;
  color: var(--accent);
  margin-bottom: 0.65rem;
  font-size: 1.05rem;
}
.mental-item span {
  display: block;
  color: var(--text-secondary);
  line-height: 1.45;
}
:::

:::notes
{timing: 3min}
Bedrock을 설명할 때 기능 목록을 나열하면 금방 흩어집니다. 그래서 여섯 개 축으로 정리하는 편이 좋습니다. 첫째는 모델 접근, 둘째는 실제 호출 런타임, 셋째는 사내 데이터와 연결하는 지식 계층, 넷째는 도구를 호출하며 일을 끝내는 오케스트레이션, 다섯째는 안전장치, 여섯째는 운영입니다. 이 여섯 축을 기준으로 보면 PoC가 왜 프로덕션에서 막히는지도 선명해집니다. 대부분은 모델 품질 하나가 아니라, 지식, 안전, 운영 중 한 곳이 준비되지 않아서 멈춥니다. {cue: transition} 다음은 이 축들이 Bedrock 기능으로 어떻게 매핑되는지 보겠습니다.
:::

---
<!-- Slide 4: Core Capabilities -->
@type: content

## Core Capabilities

:::html
<div class="capability-grid">
  <div class="cap-card fragment fade-up" data-fragment-index="1">
    <img src="common/aws-icons/services/Arch_Amazon-Bedrock_48.svg" alt="Bedrock">
    <h3>Model Access</h3>
    <p>100개 이상의 Foundation Model을 관리형 API로 호출</p>
  </div>
  <div class="cap-card fragment fade-up" data-fragment-index="2">
    <img src="common/aws-icons/services/Arch_Amazon-OpenSearch-Service_48.svg" alt="OpenSearch">
    <h3>Knowledge Bases</h3>
    <p>RAG, citations, vector store, structured data retrieval</p>
  </div>
  <div class="cap-card fragment fade-up" data-fragment-index="3">
    <img src="common/aws-icons/services/Arch_AWS-Step-Functions_48.svg" alt="Step Functions">
    <h3>Agents</h3>
    <p>작업 분해, Knowledge Base 호출, action group API 실행</p>
  </div>
  <div class="cap-card fragment fade-up" data-fragment-index="4">
    <img src="common/aws-icons/services/Arch_AWS-Identity-and-Access-Management_48.svg" alt="IAM">
    <h3>Guardrails</h3>
    <p>유해 콘텐츠, denied topics, PII, grounding checks 제어</p>
  </div>
  <div class="cap-card fragment fade-up" data-fragment-index="5">
    <img src="common/aws-icons/services/Arch_AWS-Lambda_48.svg" alt="Lambda">
    <h3>Customization</h3>
    <p>prompt, evaluation, fine-tuning/import 기반 품질 개선</p>
  </div>
  <div class="cap-card fragment fade-up" data-fragment-index="6">
    <img src="common/aws-icons/services/Arch_Amazon-CloudWatch_48.svg" alt="CloudWatch">
    <h3>Operations</h3>
    <p>trace, logging, monitoring, 비용과 변경 관리</p>
  </div>
</div>
:::

:::css
.capability-grid {
  max-height: 500px;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.9rem;
  word-break: keep-all;
  overflow-wrap: break-word;
}
.cap-card {
  min-height: 9.4rem;
  padding: 1rem;
  border: 1px solid var(--border);
  border-radius: 0.5rem;
  background: var(--bg-card);
}
.cap-card img {
  width: 2.7rem;
  height: 2.7rem;
  margin-bottom: 0.5rem;
}
.cap-card h3 {
  margin: 0 0 0.45rem;
  font-size: 1.1rem;
}
.cap-card p {
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.4;
}
:::

:::notes
{timing: 3min}
핵심 기능을 여섯 개로 나누면 의사결정이 쉬워집니다. 모델 접근은 시작점이고, Knowledge Bases는 사내 문서와 데이터로 답변을 grounding하는 계층입니다. Agents는 사용자의 요청을 작은 단계로 쪼개고 필요한 API를 호출하게 해줍니다. Guardrails는 입력과 출력 모두에 일관된 안전 정책을 적용합니다. 운영 계층은 평가, 로깅, 추적, 비용 배분처럼 서비스화할 때 필요한 항목입니다. {cue: pause} 중요한 점은 이 기능들이 독립 메뉴가 아니라 한 애플리케이션 경로 안에서 같이 작동해야 한다는 것입니다.
:::

---
<!-- Slide 5: Reference Architecture -->
@type: content

## Reference Architecture

:::html
<div class="arch-flow">
  <div class="arch-group bg-blue fragment fade-right" data-fragment-index="1">
    <div class="flow-group-label">Experience</div>
    <div class="icon-item"><span class="text-icon">UI</span><span>Web / Mobile</span></div>
    <div class="icon-item"><span class="text-icon">API</span><span>Chat / Workflow</span></div>
  </div>
  <div class="flow-arrow fragment fade-right" data-fragment-index="2">→<span class="arrow-label">request</span></div>
  <div class="arch-group bg-orange fragment fade-right" data-fragment-index="2">
    <div class="flow-group-label">Application</div>
    <div class="icon-item"><img src="common/aws-icons/services/Arch_Amazon-API-Gateway_48.svg" alt="API Gateway"><span>API Gateway</span></div>
    <div class="icon-item"><img src="common/aws-icons/services/Arch_AWS-Lambda_48.svg" alt="Lambda"><span>Lambda</span></div>
  </div>
  <div class="flow-arrow fragment fade-right" data-fragment-index="3">→<span class="arrow-label">orchestrate</span></div>
  <div class="arch-group bg-purple fragment fade-right" data-fragment-index="3">
    <div class="flow-group-label">Bedrock</div>
    <div class="icon-item lg"><img src="common/aws-icons/services/Arch_Amazon-Bedrock_48.svg" alt="Bedrock"><span>Runtime</span></div>
    <div class="flow-box">Agents</div>
    <div class="flow-box">Guardrails</div>
  </div>
  <div class="flow-arrow fragment fade-right" data-fragment-index="4">→<span class="arrow-label">ground</span></div>
  <div class="arch-group bg-green fragment fade-right" data-fragment-index="4">
    <div class="flow-group-label">Data & Ops</div>
    <div class="icon-item"><img src="common/aws-icons/services/Arch_Amazon-Simple-Storage-Service_48.svg" alt="S3"><span>S3</span></div>
    <div class="icon-item"><img src="common/aws-icons/services/Arch_Amazon-OpenSearch-Service_48.svg" alt="OpenSearch"><span>Vector Store</span></div>
    <div class="icon-item"><img src="common/aws-icons/services/Arch_Amazon-CloudWatch_48.svg" alt="CloudWatch"><span>CloudWatch</span></div>
  </div>
</div>
:::

:::css
.arch-flow {
  max-height: 500px;
  display: grid;
  grid-template-columns: 1.05fr auto 1.05fr auto 1.2fr auto 1.15fr;
  align-items: stretch;
  gap: 0.55rem;
  word-break: keep-all;
  overflow-wrap: break-word;
}
.arch-group {
  border: 1px solid var(--border);
  border-radius: 0.5rem;
  padding: 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.55rem;
  min-height: 18rem;
}
.arch-flow .flow-arrow {
  align-self: center;
  text-align: center;
  min-width: 2.2rem;
}
.arch-flow .flow-box {
  text-align: center;
  min-width: auto;
  padding: 0.55rem 0.65rem;
}
.arch-flow .icon-item {
  min-height: 3.6rem;
}
:::

:::notes
{timing: 4min}
이 슬라이드는 실제 PPT에서 가장 중요한 구조도 역할을 합니다. 사용자는 Web, Mobile, Chat UI에서 요청을 보내고, 애플리케이션 계층은 API Gateway와 Lambda 같은 컴퓨트로 인증, 세션, 비즈니스 로직을 처리합니다. Bedrock Runtime은 모델 호출의 중심이고, Agents와 Guardrails가 오케스트레이션과 안전 정책을 담당합니다. 오른쪽의 데이터와 운영 계층은 S3, vector store, CloudWatch처럼 답변 품질과 서비스 운영을 지탱합니다. {cue: question} 여기서 놓치기 쉬운 점은 Bedrock만 그리면 아키텍처가 완성되지 않는다는 것입니다. 사용자 경험, 애플리케이션, 지식, 운영이 같이 그려져야 합니다.
:::

---
<!-- Slide 6: Knowledge Bases RAG -->
@type: content

## Knowledge Bases로 RAG 구성

:::html
<div class="rag-flow">
  <div class="rag-step fragment fade-right" data-fragment-index="1">
    <div class="step-no">01</div>
    <h3>Connect</h3>
    <p>S3, 문서, 구조화 데이터 소스를 연결합니다.</p>
  </div>
  <div class="rag-arrow fragment fade-right" data-fragment-index="2">→</div>
  <div class="rag-step fragment fade-right" data-fragment-index="2">
    <div class="step-no">02</div>
    <h3>Ingest</h3>
    <p>Chunking, embedding, sync로 검색 가능한 인덱스를 만듭니다.</p>
  </div>
  <div class="rag-arrow fragment fade-right" data-fragment-index="3">→</div>
  <div class="rag-step fragment fade-right" data-fragment-index="3">
    <div class="step-no">03</div>
    <h3>Retrieve</h3>
    <p>질문과 관련 높은 근거 문서를 찾아 reranking합니다.</p>
  </div>
  <div class="rag-arrow fragment fade-right" data-fragment-index="4">→</div>
  <div class="rag-step fragment fade-right" data-fragment-index="4">
    <div class="step-no">04</div>
    <h3>Generate</h3>
    <p>근거를 prompt에 넣고 답변과 citation을 반환합니다.</p>
  </div>
</div>
<div class="rag-bottom fragment fade-up" data-fragment-index="5">
  <strong>설계 기준:</strong> “모델이 아는 것”보다 “어떤 근거를 가져왔고, 그 근거를 답변에 어떻게 반영했는가”를 측정합니다.
</div>
:::

:::css
.rag-flow {
  max-height: 500px;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.55rem;
  align-items: stretch;
  word-break: keep-all;
  overflow-wrap: break-word;
}
.rag-step {
  min-height: 13.3rem;
  border: 1px solid var(--border);
  border-radius: 0.5rem;
  padding: 1rem;
  background: var(--bg-card);
}
.rag-arrow {
  display: none;
}
.step-no {
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: rgba(255, 153, 0, 0.14);
  color: var(--accent);
  font-weight: 700;
  margin-bottom: 0.8rem;
}
.rag-step h3 { margin: 0 0 0.65rem; }
.rag-step p {
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.5;
}
.rag-bottom {
  margin-top: 1rem;
  padding: 0.9rem 1rem;
  border-left: 0.3rem solid var(--accent);
  background: rgba(255, 153, 0, 0.08);
  color: var(--text-secondary);
  word-break: keep-all;
}
:::

:::notes
{timing: 3min}
Knowledge Bases는 Bedrock에서 RAG를 빠르게 구성하게 해주는 핵심 기능입니다. 공식 문서 기준으로는 데이터 소스에서 관련 정보를 검색하고, 그 정보를 사용해 더 정확하고 관련성 높은 답변을 생성하며, citation으로 원본을 확인할 수 있게 합니다. 실무에서는 “문서를 넣었더니 답한다”에서 멈추면 안 됩니다. 수집 주기, chunk 전략, embedding 모델, vector store 선택, reranking, citation 노출 방식이 품질을 좌우합니다. {cue: transition} RAG가 답변의 근거를 만든다면, Agents는 그 근거를 바탕으로 실제 행동까지 연결합니다.
:::

---
<!-- Slide 7: Agents -->
@type: content

## Agents: 질문에서 행동까지

:::html
<div class="agent-layout">
  <div class="agent-panel fragment fade-right" data-fragment-index="1">
    <h3>User Goal</h3>
    <p>“계약 갱신 리스크가 높은 고객을 찾아 담당자에게 후속 작업을 만들어줘.”</p>
  </div>
  <div class="agent-core fragment zoom-in" data-fragment-index="2">
    <img src="common/aws-icons/services/Arch_Amazon-Bedrock_48.svg" alt="Bedrock">
    <h3>Bedrock Agent</h3>
    <div class="agent-chip">task decomposition</div>
    <div class="agent-chip">orchestration</div>
    <div class="agent-chip">trace</div>
  </div>
  <div class="agent-tools fragment fade-left" data-fragment-index="3">
    <div class="tool-card">
      <img src="common/aws-icons/services/Arch_Amazon-OpenSearch-Service_48.svg" alt="OpenSearch">
      <span>Knowledge Base</span>
    </div>
    <div class="tool-card">
      <img src="common/aws-icons/services/Arch_AWS-Lambda_48.svg" alt="Lambda">
      <span>Action Group API</span>
    </div>
    <div class="tool-card">
      <img src="common/aws-icons/services/Arch_Amazon-DynamoDB_48.svg" alt="DynamoDB">
      <span>Business System</span>
    </div>
  </div>
</div>
:::

:::css
.agent-layout {
  max-height: 500px;
  display: grid;
  grid-template-columns: 1.05fr 1fr 1.15fr;
  gap: 1rem;
  align-items: stretch;
  word-break: keep-all;
  overflow-wrap: break-word;
}
.agent-panel,
.agent-core,
.agent-tools {
  border: 1px solid var(--border);
  border-radius: 0.5rem;
  background: var(--bg-card);
  padding: 1rem;
  min-height: 18rem;
}
.agent-panel {
  display: flex;
  flex-direction: column;
  justify-content: center;
}
.agent-panel p {
  color: var(--text-secondary);
  line-height: 1.6;
  font-size: 1.1rem;
}
.agent-core {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  text-align: center;
  border-color: rgba(255, 153, 0, 0.55);
}
.agent-core img { width: 4rem; height: 4rem; }
.agent-chip {
  width: 100%;
  border: 1px solid var(--border);
  border-radius: 999px;
  padding: 0.45rem 0.75rem;
  color: var(--text-secondary);
}
.agent-tools {
  display: grid;
  grid-template-rows: repeat(3, 1fr);
  gap: 0.65rem;
}
.tool-card {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  border: 1px solid var(--border);
  border-radius: 0.5rem;
  padding: 0.75rem;
}
.tool-card img { width: 2.4rem; height: 2.4rem; }
:::

:::notes
{timing: 3min}
Agents는 단순 챗봇과 다르게 사용자의 목표를 작은 단계로 나누고, 필요한 정보를 조회하고, 외부 API를 호출해 작업을 완성하도록 설계됩니다. Bedrock Agents 문서는 Foundation Model, data sources, software applications, user conversations 사이의 상호작용을 오케스트레이션한다고 설명합니다. 예를 들어 고객 리스크를 판단하려면 Knowledge Base에서 정책과 기준을 찾고, CRM API를 조회하고, 필요한 경우 후속 작업을 생성해야 합니다. 이때 action group은 실제 시스템을 호출하는 경계이므로 권한, 입력 검증, 실패 처리가 특히 중요합니다. {cue: transition} 행동을 허용할수록 안전장치와 거버넌스가 더 중요해집니다.
:::

---
<!-- Slide 8: Governance and Safety -->
@type: content

## Security & Governance

:::html
<div class="governance-grid">
  <div class="gov-card fragment fade-up" data-fragment-index="1">
    <img src="common/aws-icons/services/Arch_AWS-IAM-Identity-Center_48.svg" alt="IAM Identity Center">
    <h3>Identity Boundary</h3>
    <p>IAM principal, least privilege, tenant context, cost attribution 기준을 먼저 정합니다.</p>
  </div>
  <div class="gov-card fragment fade-up" data-fragment-index="2">
    <img src="common/aws-icons/services/Arch_AWS-Identity-and-Access-Management_48.svg" alt="IAM">
    <h3>Guardrail Policy</h3>
    <p>content filter, denied topics, word filter, sensitive information, grounding check를 use case별로 설정합니다.</p>
  </div>
  <div class="gov-card fragment fade-up" data-fragment-index="3">
    <img src="common/aws-icons/services/Arch_AWS-CloudTrail_48.svg" alt="CloudTrail">
    <h3>Audit Trail</h3>
    <p>누가 어떤 앱에서 어떤 모델과 데이터 경로를 사용했는지 추적 가능하게 만듭니다.</p>
  </div>
  <div class="gov-card fragment fade-up" data-fragment-index="4">
    <img src="common/aws-icons/services/Arch_Amazon-CloudWatch_48.svg" alt="CloudWatch">
    <h3>Runtime Observability</h3>
    <p>latency, error, token usage, blocked response, retrieval quality를 운영 지표로 봅니다.</p>
  </div>
</div>
:::

:::css
.governance-grid {
  max-height: 500px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
  word-break: keep-all;
  overflow-wrap: break-word;
}
.gov-card {
  min-height: 10.5rem;
  border: 1px solid var(--border);
  border-radius: 0.5rem;
  background: var(--bg-card);
  padding: 1rem;
}
.gov-card img {
  width: 2.8rem;
  height: 2.8rem;
  margin-bottom: 0.5rem;
}
.gov-card h3 {
  margin: 0 0 0.45rem;
}
.gov-card p {
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.45;
}
:::

:::notes
{timing: 3min}
생성형 AI 보안은 모델 앞단의 인증만으로 끝나지 않습니다. 누가 호출했는지, 어떤 데이터에 접근했는지, 어떤 답변이 차단되었는지, 비용이 어느 팀에 귀속되는지까지 연결해야 합니다. Guardrails는 유해 콘텐츠, 금지 주제, 민감 정보, contextual grounding, automated reasoning checks 같은 안전장치를 제공합니다. 특히 RAG 애플리케이션에서는 답변이 근거에서 벗어나는지를 보는 grounding check가 중요합니다. {cue: pause} 운영팀 관점에서는 차단율과 사용자 불만, latency, 비용, 품질 평가를 함께 봐야 정책이 과하거나 약한지 판단할 수 있습니다.
:::

---
<!-- Slide 9: Adoption Pattern -->
@type: content

## 도입 패턴: Pilot에서 Production까지

:::html
<div class="adoption-track">
  <div class="adopt-step fragment fade-up" data-fragment-index="1">
    <span>01</span>
    <h3>Pilot</h3>
    <p>업무 시나리오 하나와 성공 기준을 좁게 정의합니다.</p>
  </div>
  <div class="adopt-step fragment fade-up" data-fragment-index="2">
    <span>02</span>
    <h3>Baseline</h3>
    <p>모델, prompt, RAG, Guardrails, IAM 기준선을 만듭니다.</p>
  </div>
  <div class="adopt-step fragment fade-up" data-fragment-index="3">
    <span>03</span>
    <h3>Evaluate</h3>
    <p>정답성, 근거성, 안전성, 비용, latency를 데이터로 비교합니다.</p>
  </div>
  <div class="adopt-step fragment fade-up" data-fragment-index="4">
    <span>04</span>
    <h3>Launch</h3>
    <p>fallback, approval, rate limit, incident path를 포함해 배포합니다.</p>
  </div>
  <div class="adopt-step fragment fade-up" data-fragment-index="5">
    <span>05</span>
    <h3>Operate</h3>
    <p>모델 변경, 지식 갱신, 정책 변경을 정기 운영 절차로 관리합니다.</p>
  </div>
</div>
:::

:::css
.adoption-track {
  max-height: 500px;
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 0.75rem;
  word-break: keep-all;
  overflow-wrap: break-word;
}
.adopt-step {
  min-height: 16.5rem;
  border: 1px solid var(--border);
  border-radius: 0.5rem;
  background: var(--bg-card);
  padding: 0.9rem;
  position: relative;
}
.adopt-step span {
  display: inline-grid;
  place-items: center;
  width: 2.3rem;
  height: 2.3rem;
  border-radius: 50%;
  background: rgba(255, 153, 0, 0.14);
  color: var(--accent);
  font-weight: 700;
  margin-bottom: 0.8rem;
}
.adopt-step h3 {
  margin: 0 0 0.55rem;
  font-size: 1.05rem;
}
.adopt-step p {
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.45;
  font-size: 0.95rem;
}
:::

:::notes
{timing: 4min}
도입 순서는 기술 기능을 모두 써보는 방식보다, 실제 업무 한 가지를 잡고 운영 기준까지 통과시키는 방식이 좋습니다. Pilot에서는 성공 기준을 좁히고, Baseline에서는 모델과 prompt뿐 아니라 IAM, RAG, Guardrails 구성을 함께 고정합니다. Evaluate 단계에서는 정답성만 보지 말고 citation 품질, 비용, latency, 차단율도 봅니다. Launch에서는 fallback과 사람 승인 경로, 장애 대응을 포함해야 합니다. Operate 단계에서는 모델 버전 변경과 지식 동기화가 품질에 영향을 주기 때문에 정기적인 회귀 평가가 필요합니다. {cue: transition} 마지막으로 오늘의 판단 기준을 요약하겠습니다.
:::

---
<!-- Slide 10: Summary -->
@type: content

## Key Takeaways

:::html
<div class="takeaway-grid">
  <div class="takeaway-card fragment fade-up" data-fragment-index="1">
    <strong>1</strong>
    <h3>Bedrock은 모델 호출 API보다 넓다</h3>
    <p>모델, 데이터, 도구, 안전, 운영을 묶는 관리형 생성형 AI 플랫폼으로 봐야 합니다.</p>
  </div>
  <div class="takeaway-card fragment fade-up" data-fragment-index="2">
    <strong>2</strong>
    <h3>좋은 PPT의 핵심은 구조도다</h3>
    <p>Experience, Application, Bedrock, Data/Ops 계층을 분리하면 설명력이 올라갑니다.</p>
  </div>
  <div class="takeaway-card fragment fade-up" data-fragment-index="3">
    <strong>3</strong>
    <h3>프로덕션 기준은 평가와 운영이다</h3>
    <p>RAG 품질, Guardrails 정책, trace, cost, latency를 출시 전부터 측정합니다.</p>
  </div>
</div>
<div class="closing-line fragment zoom-in" data-fragment-index="4">Thank you</div>
:::

:::css
.takeaway-grid {
  max-height: 500px;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1rem;
  word-break: keep-all;
  overflow-wrap: break-word;
}
.takeaway-card {
  min-height: 14rem;
  border: 1px solid var(--border);
  border-radius: 0.5rem;
  background: var(--bg-card);
  padding: 1.1rem;
}
.takeaway-card strong {
  display: inline-grid;
  place-items: center;
  width: 2.4rem;
  height: 2.4rem;
  border-radius: 50%;
  background: rgba(255, 153, 0, 0.14);
  color: var(--accent);
  margin-bottom: 0.75rem;
}
.takeaway-card h3 {
  margin: 0 0 0.65rem;
  font-size: 1.2rem;
}
.takeaway-card p {
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.45;
}
.closing-line {
  margin-top: 1rem;
  text-align: center;
  color: var(--accent);
  font-size: 1.4rem;
  font-weight: 700;
}
:::

:::notes
{timing: 3min}
정리하면 Bedrock은 Foundation Model을 호출하는 API만이 아니라, 생성형 AI 애플리케이션을 안전하게 만들고 운영하기 위한 플랫폼입니다. 좋은 발표 자료를 만들 때도 이 관점이 중요합니다. 모델 로고만 나열하는 대신, 사용자 경험에서 애플리케이션 계층, Bedrock Runtime, Knowledge Bases, Agents, Guardrails, 운영 지표까지 이어지는 구조도를 보여주면 훨씬 설득력이 있습니다. {cue: question} 이후 논의에서는 우리 조직의 첫 use case를 기준으로 RAG가 먼저인지, Agent가 먼저인지, Guardrails 기준선이 먼저인지 결정하면 됩니다.
:::
