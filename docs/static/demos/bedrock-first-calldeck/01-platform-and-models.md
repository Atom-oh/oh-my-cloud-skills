---
remarp: true
block: 1
title: "플랫폼과 파운데이션 모델"
---

# Amazon Bedrock
## 생성형 AI를 프로덕션으로 — First Call

@type: cover
@speaker: AWS Solutions Architect
@date: 2026-06-11

:::notes
{timing: 1min}
안녕하세요. 오늘은 Amazon Bedrock을 처음 검토하시는 관점에서, 플랫폼 전체 그림을 함께 그려보는 자리입니다.
이미 생성형 AI PoC는 많이들 해보셨을 겁니다. 핵심 질문은 "이걸 어떻게 안전하게, 비용 효율적으로, 프로덕션까지 가져가느냐"입니다.
오늘 세션은 200 레벨로, 서비스 나열이 아니라 "왜 Bedrock인가"와 "무엇을 먼저 시작하면 되는가"에 초점을 둡니다.
{cue: transition} 먼저 오늘의 큰 흐름을 보겠습니다.
:::

---

## 오늘 함께 볼 것

@type: agenda

- 플랫폼과 파운데이션 모델 {18min}
- AgentCore와 레퍼런스 아키텍처 {17min}

:::notes
{timing: 1min}
[요약]
- 1부: Bedrock 플랫폼·모델 선택·추론 옵션·Mantle 추론 엔진
- 2부: AgentCore로 에이전트를 프로덕션화 + 끝에서 끝 아키텍처
- 총 35분, 중간에 질문 환영

오늘은 크게 두 부분입니다. 1부에서는 Bedrock이 무엇이고, 어떤 모델을 어떻게 고르며, 새로워진 추론 엔진 Mantle이 무엇을 바꾸는지 봅니다.
2부에서는 모델을 넘어 "에이전트"를 프로덕션으로 올리는 AgentCore와, 이 모든 걸 합친 레퍼런스 아키텍처, 그리고 다음 단계를 다룹니다.
{cue: question} 혹시 지금 가장 관심 있는 워크로드가 챗봇인지, 검색/RAG인지, 아니면 에이전트인지 먼저 여쭤봐도 될까요?
{cue: transition} 그럼 왜 지금 이 논의가 필요한지부터 시작하겠습니다.
:::

---

## PoC는 쉽고, 프로덕션은 어렵다

@type: content
@theme: dark

:::html
<div class="col-2">
  <div class="callout callout-warning fragment fade-up" data-fragment-index="1">
    <strong>모델 고착</strong><div class="metric-label">한 모델에 코드가 묶여 교체·비교가 어렵다</div>
  </div>
  <div class="callout callout-warning fragment fade-up" data-fragment-index="2">
    <strong>운영·확장</strong><div class="metric-label">쿼터·지연·가용성을 직접 떠안게 된다</div>
  </div>
  <div class="callout callout-danger fragment fade-up" data-fragment-index="3">
    <strong>보안·거버넌스</strong><div class="metric-label">데이터 경계·감사·비용 가시성 부재</div>
  </div>
  <div class="callout callout-danger fragment fade-up" data-fragment-index="4">
    <strong>에이전트의 벽</strong><div class="metric-label">세션·메모리·도구 연동이 프로토타입에서 멈춘다</div>
  </div>
</div>
:::

:::notes
{timing: 2min}
[요약]
- PoC→프로덕션 전환에서 막히는 4가지: 모델 고착, 운영·확장, 보안·거버넌스, 에이전트화
- Bedrock은 이 네 가지를 "관리형 플랫폼"으로 흡수

대부분의 조직이 데모까지는 빠르게 갑니다. 문제는 그다음입니다.
첫째, 특정 모델 SDK에 코드가 묶여서 더 좋은 모델이 나와도 갈아타기 어렵습니다. 둘째, 트래픽이 늘면 쿼터와 지연, 가용성을 직접 관리해야 합니다.
셋째, 고객 데이터가 외부로 나가지 않는지, 누가 무엇을 호출했는지 감사할 수 있는지가 발목을 잡습니다. 넷째, 에이전트로 가면 세션·메모리·도구 연동·인증이라는 새로운 난관이 생깁니다.
{cue: pause} 이 네 가지가 오늘 이야기의 뼈대입니다.
{cue: transition} Bedrock은 이걸 어떻게 흡수하는지 보겠습니다.
:::

---

## Bedrock은 무엇인가

@type: content

:::html
<div class="col-3">
  <div class="metric-card fragment fade-up" data-fragment-index="1">
    <strong>단일 API · 멀티 모델</strong>
    <div class="metric-label">15+ 프로바이더를 하나의 인터페이스로</div>
  </div>
  <div class="metric-card fragment fade-up" data-fragment-index="2">
    <strong>서버리스</strong>
    <div class="metric-label">인프라 0 · 호출당 과금 · 자동 확장</div>
  </div>
  <div class="metric-card fragment fade-up" data-fragment-index="3">
    <strong>커스터마이즈</strong>
    <div class="metric-label">RAG · 파인튜닝 · 모델 증류</div>
  </div>
  <div class="metric-card fragment fade-up" data-fragment-index="4">
    <strong>책임형 AI</strong>
    <div class="metric-label">Guardrails로 안전·정책 일괄 적용</div>
  </div>
  <div class="metric-card fragment fade-up" data-fragment-index="5">
    <strong>엔터프라이즈</strong>
    <div class="metric-label">VPC · PrivateLink · IAM · CloudTrail</div>
  </div>
  <div class="metric-card fragment fade-up" data-fragment-index="6">
    <strong>에이전트</strong>
    <div class="metric-label">AgentCore로 프로덕션 에이전트까지</div>
  </div>
</div>
:::

:::notes
{timing: 2min}
[요약]
- Bedrock = 파운데이션 모델을 위한 완전관리형 서버리스 플랫폼
- 6개 기둥: 단일 API·서버리스·커스터마이즈·Guardrails·엔터프라이즈·에이전트

한 문장으로 정의하면, Bedrock은 "여러 회사의 파운데이션 모델을 하나의 API로, 서버리스로 쓰게 해 주는 완전관리형 플랫폼"입니다.
인프라를 띄울 필요가 없고 호출한 만큼만 냅니다. 모델을 그대로 쓰는 것을 넘어 RAG, 파인튜닝, 모델 증류로 우리 데이터에 맞출 수 있습니다.
Guardrails로 유해 콘텐츠·민감정보·주제 이탈을 모델과 무관하게 일괄 통제하고, VPC·PrivateLink·IAM·CloudTrail로 엔터프라이즈 보안 요건을 충족합니다.
{cue: transition} 그럼 가장 먼저 마주치는 질문, "어떤 모델을 고르지?"로 가겠습니다.
:::

---

## 모델은 골라 쓰는 시대

@type: tabs

### Anthropic Claude

:::html
<div class="col-3">
  <div class="metric-card"><strong>Opus</strong><div class="metric-label">최고 난도 추론·코딩 · $5/$25 per 1M</div></div>
  <div class="metric-card"><strong>Sonnet</strong><div class="metric-label">균형형 주력 · $3/$15 per 1M</div></div>
  <div class="metric-card"><strong>Haiku</strong><div class="metric-label">저지연·대량 처리 · $1/$5 per 1M</div></div>
</div>
<p class="metric-label">고난도는 Opus, 일상 워크로드는 Sonnet, 대량·실시간은 Haiku로 계층화</p>
:::

### Amazon Nova

:::html
<div class="col-3">
  <div class="metric-card"><strong>Nova Pro</strong><div class="metric-label">멀티모달 주력 · $0.80/$3.20 per 1M</div></div>
  <div class="metric-card"><strong>Nova Lite</strong><div class="metric-label">빠르고 저렴 · $0.06/$0.24 per 1M</div></div>
  <div class="metric-card"><strong>Nova Micro</strong><div class="metric-label">텍스트 초경량 · $0.035/$0.14 per 1M</div></div>
</div>
<p class="metric-label">AWS 자체 모델 — 가격 대비 성능이 강점, 비용 민감 워크로드의 기본값. 가격은 On-Demand·us-east-1·2026-06 기준 입력/출력 1M 토큰 (변동 가능)</p>
:::

### Open-weight · 15+

:::html
<div class="col-2">
  <div class="callout callout-info"><strong>오픈웨이트</strong><div class="metric-label">DeepSeek · GLM · Kimi · Qwen · MiniMax 등 풀리매니지드</div></div>
  <div class="callout callout-info"><strong>프론티어 외부 모델</strong><div class="metric-label">Meta Llama · Mistral · Cohere · Stability · GPT 계열</div></div>
</div>
<p class="metric-label">같은 Bedrock API로 15+ 프로바이더를 호출 — 벤더 락인 없이 비교·교체</p>
:::

:::notes
{timing: 2min}
[요약]
- Claude(Opus/Sonnet/Haiku): 추론·코딩 강자, 난도별 계층화
- Nova(Pro/Lite/Micro): AWS 자체 모델, 가성비
- Open-weight·15+: 단일 API로 멀티 벤더, 락인 없음

모델 선택의 핵심은 "하나로 통일"이 아니라 "작업별로 맞춰 쓰는 것"입니다.
Claude는 복잡한 추론과 코딩에서 강하고, Opus·Sonnet·Haiku로 난도와 비용을 계층화합니다. Amazon Nova는 AWS 자체 모델로 가성비가 뛰어나 비용 민감한 대량 워크로드의 기본값으로 좋습니다.
여기에 DeepSeek, Llama, Mistral 등 오픈웨이트와 외부 프론티어 모델까지 같은 API로 부릅니다. 즉, 더 좋은 모델이 나오면 코드를 거의 안 바꾸고 갈아탈 수 있습니다.
{cue: pause} 가격은 입력/출력 100만 토큰 기준이며, 캐싱·배치로 더 낮출 수 있습니다.
{cue: transition} 그 "더 낮추는 방법", 추론 옵션을 보겠습니다.
:::

---

## 추론은 워크로드에 맞춰

@type: content

:::html
<div class="col-3">
  <div class="metric-card fragment fade-up" data-fragment-index="1"><strong>On-Demand</strong><div class="metric-label">약정 없이 호출당 과금 · 기본값</div></div>
  <div class="metric-card fragment fade-up" data-fragment-index="2"><strong>Provisioned</strong><div class="metric-label">처리량 예약 · 안정적 지연 · 할인</div></div>
  <div class="metric-card fragment fade-up" data-fragment-index="3"><strong>Batch</strong><div class="metric-label">대량 비동기 · 약 50% 절감</div></div>
  <div class="metric-card fragment fade-up" data-fragment-index="4"><strong>Prompt Caching</strong><div class="metric-label">반복 컨텍스트 캐시 · 최대 90% 절감</div></div>
  <div class="metric-card fragment fade-up" data-fragment-index="5"><strong>Global Endpoints</strong><div class="metric-label">최적 리전 자동 라우팅</div></div>
  <div class="metric-card fragment fade-up" data-fragment-index="6"><strong>Cross-Region</strong><div class="metric-label">용량 분산으로 스로틀 완화</div></div>
</div>
:::

:::notes
{timing: 2min}
[요약]
- 4가지 과금: On-Demand(기본)·Provisioned(예약)·Batch(50%↓)·Caching(90%↓)
- 라우팅: Global/Cross-Region 엔드포인트로 가용성·지연 개선

같은 모델이라도 어떻게 호출하느냐로 비용과 안정성이 크게 달라집니다.
기본은 약정 없는 On-Demand입니다. 트래픽이 꾸준하면 Provisioned로 처리량을 예약해 지연을 안정화하고 단가를 낮춥니다. 야간 일괄 처리 같은 비동기 작업은 Batch로 약 절반 비용에 돌립니다.
특히 RAG처럼 같은 시스템 프롬프트가 반복되면 Prompt Caching으로 캐시된 입력에 최대 90%까지 할인을 받습니다. 가용성은 Global·Cross-Region 엔드포인트가 최적 리전으로 분산해 스로틀과 지연을 줄여줍니다.
{cue: transition} 이 추론을 실제로 떠받치는 엔진이 새로워졌습니다. Mantle입니다.
:::

---

## 추론 비용, 직접 계산

@type: content

:::html
<div class="col-2">
  <div>
    <div class="slider-row"><label>월 입력 토큰</label><input type="range" id="bc-in" min="1" max="500" value="50"><span class="value" id="bc-inv">50M</span></div>
    <div class="slider-row"><label>월 출력 토큰</label><input type="range" id="bc-out" min="1" max="200" value="20"><span class="value" id="bc-outv">20M</span></div>
    <div class="btn-group" id="bc-models">
      <button class="btn btn-sm active" data-in="3" data-out="15">Claude Sonnet</button>
      <button class="btn btn-sm" data-in="1" data-out="5">Claude Haiku</button>
      <button class="btn btn-sm" data-in="0.06" data-out="0.24">Nova Lite</button>
    </div>
  </div>
  <div class="card-grid">
    <div class="metric-card"><div class="metric-value" id="bc-od">$0</div><div class="metric-label">On-Demand / 월</div></div>
    <div class="metric-card"><div class="metric-value text-success" id="bc-batch">$0</div><div class="metric-label">Batch (50%↓)</div></div>
    <div class="metric-card"><div class="metric-value text-accent" id="bc-cache">$0</div><div class="metric-label">Prompt Caching (입력 90%↓)</div></div>
  </div>
</div>
:::

:::css
.text-success { color: var(--success); }
.text-accent  { color: var(--accent); }
:::

:::script
(function(){
  const $ = id => document.getElementById(id);
  const inEl=$('bc-in'), outEl=$('bc-out'), inV=$('bc-inv'), outV=$('bc-outv');
  const od=$('bc-od'), bt=$('bc-batch'), ca=$('bc-cache'), models=$('bc-models');
  if(!inEl||!models) return;
  let pin=3, pout=15;
  const fmt = n => '$' + (n>=1000 ? (n/1000).toFixed(1)+'k' : n.toFixed(0));
  function calc(){
    const i=+inEl.value, o=+outEl.value;
    inV.textContent=i+'M'; outV.textContent=o+'M';
    const cost=i*pin + o*pout;            // per 1M token pricing × M tokens
    od.textContent=fmt(cost);
    bt.textContent=fmt(cost*0.5);          // batch ~50% off
    ca.textContent=fmt(i*pin*0.1 + o*pout); // ~90% off cached input
  }
  inEl.addEventListener('input', calc);
  outEl.addEventListener('input', calc);
  models.addEventListener('click', e=>{
    const b=e.target.closest('button'); if(!b) return;
    models.querySelectorAll('button').forEach(x=>x.classList.remove('active'));
    b.classList.add('active'); pin=+b.dataset.in; pout=+b.dataset.out; calc();
  });
  calc();
})();
:::

:::notes
{timing: 2min}
[요약]
- 슬라이더로 월 토큰량·모델을 바꾸면 On-Demand / Batch / Caching 비용이 실시간 계산
- 추론 옵션만으로 비용이 크게 달라짐을 체감

직접 만져보겠습니다. 월 입력·출력 토큰을 슬라이더로 조절하고 모델을 바꾸면 비용이 실시간으로 갱신됩니다.
같은 워크로드라도 Batch는 약 절반, Prompt Caching은 반복 입력에서 최대 90%까지 줄여줍니다 — 모델 단가만큼이나 "어떻게 호출하느냐"가 비용을 좌우합니다.
{cue: question} 우리 워크로드의 월 토큰량이 대략 어느 정도일지 같이 넣어볼까요?
{cue: transition} 이 추론을 떠받치는 엔진이 새로워졌습니다 — Mantle입니다.
:::

---

## Mantle: 추론 엔진의 진화

@type: content

:::html
<div class="flow-h">
  <div class="flow-group bg-blue" data-fragment-index="1">
    <div class="flow-group-label">호출</div>
    <div class="flow-box">OpenAI 호환 API</div>
    <div class="flow-box">Anthropic Messages</div>
  </div>
  <div class="flow-arrow">→</div>
  <div class="flow-group bg-orange" data-fragment-index="2">
    <div class="flow-group-label">bedrock-mantle 엔진</div>
    <div class="flow-box">자동 용량관리</div>
    <div class="flow-box">통합 쿼터 풀</div>
    <div class="flow-box">QoS 제어</div>
  </div>
  <div class="flow-arrow">→</div>
  <div class="flow-group bg-green" data-fragment-index="3">
    <div class="flow-group-label">결과</div>
    <div class="flow-box">서버리스 추론</div>
    <div class="flow-box">빠른 신규 모델 온보딩</div>
  </div>
</div>
:::

:::notes
{timing: 2min}
[요약]
- Mantle = Bedrock의 대규모 분산 추론 엔진(bedrock-mantle 엔드포인트)
- 자동 용량관리·통합 쿼터 풀·QoS로 높은 기본 쿼터와 안정성
- 신규 모델을 더 빠르게 서비스에 올림

Mantle은 Bedrock의 새로운 분산 추론 엔진입니다. 기존에 모델마다 따로 관리하던 용량과 쿼터를 통합 풀로 묶고, 자동 용량관리와 QoS 제어로 더 높은 기본 쿼터와 안정적인 성능을 제공합니다.
운영 관점에서 중요한 변화는 두 가지입니다. 하나는 신규 모델이 나왔을 때 서비스에 올라오는 속도가 빨라진다는 것, 다른 하나는 엔드포인트 하나로 일관된 서버리스 추론을 받는다는 것입니다.
{cue: pause} bedrock-mantle 엔드포인트는 PrivateLink로 사설 접근도 됩니다.
{cue: transition} 개발자 입장에서 가장 체감되는 건 "API 호환성"입니다. 다음 슬라이드에서 보죠.
:::

---

## Mantle: OpenAI처럼, Bedrock답게

@type: tabs

### OpenAI 호환

:::html
<div class="col-2">
  <div class="callout callout-success"><strong>Chat Completions · Responses API</strong><div class="metric-label">기존 OpenAI SDK 코드를 엔드포인트만 바꿔 재사용</div></div>
  <div class="callout callout-info"><strong>마이그레이션 비용 ↓</strong><div class="metric-label">앱 재작성 없이 Bedrock의 보안·거버넌스로 이전</div></div>
</div>
:::

### Anthropic Messages

:::html
<div class="col-2">
  <div class="callout callout-success"><strong>Messages API 네이티브</strong><div class="metric-label">Claude를 표준 Anthropic 포맷으로 직접 호출</div></div>
  <div class="callout callout-info"><strong>도구 호출·비전</strong><div class="metric-label">tool use·멀티모달을 그대로 활용</div></div>
</div>
:::

### Projects & 모델

:::html
<div class="col-3">
  <div class="metric-card"><strong>Projects API</strong><div class="metric-label">앱·팀·환경별 격리 + IAM + 태그 비용 가시성</div></div>
  <div class="metric-card"><strong>오픈웨이트 6종</strong><div class="metric-label">DeepSeek·MiniMax·GLM·Kimi·Qwen 등</div></div>
  <div class="metric-card"><strong>CloudWatch</strong><div class="metric-label">mantle 엔드포인트 트래픽 메트릭</div></div>
</div>
:::

:::notes
{timing: 2min}
[요약]
- OpenAI 호환 API: 기존 SDK 코드 재사용, 마이그레이션 비용 최소
- Anthropic Messages API: Claude 네이티브 호출(tool use·비전)
- Projects API: 프로젝트별 격리·IAM·태그 / CloudWatch 메트릭

Mantle의 개발자 가치는 "표준 API 호환"입니다. OpenAI의 Chat Completions와 Responses API를 그대로 지원하므로, 기존 OpenAI SDK로 짠 앱을 엔드포인트만 바꿔 Bedrock으로 옮길 수 있습니다. 앱을 다시 쓰지 않고 Bedrock의 보안·거버넌스를 얻는 거죠.
Claude는 Anthropic Messages API로 네이티브하게 호출해 도구 사용과 비전까지 씁니다.
운영 측면에서는 Projects API로 앱·팀·환경을 격리하고 IAM 권한과 태그 기반 비용 가시성을 분리할 수 있으며, CloudWatch로 엔드포인트 트래픽을 모니터링합니다.
{cue: transition} 여기까지가 "모델"입니다. 이제 모델을 넘어 "에이전트"로 갑니다.
:::

---

## 1부 핵심 정리

@type: content
@theme: dark

:::html
<div class="col-2">
  <div class="callout callout-success fragment fade-up" data-fragment-index="1"><strong>단일 API·멀티 모델</strong><div class="metric-label">Claude·Nova·오픈웨이트 15+ 를 락인 없이</div></div>
  <div class="callout callout-success fragment fade-up" data-fragment-index="2"><strong>추론 옵션으로 비용·안정성</strong><div class="metric-label">Provisioned·Batch·Caching·Global</div></div>
  <div class="callout callout-info fragment fade-up" data-fragment-index="3"><strong>Mantle</strong><div class="metric-label">OpenAI 호환 + 자동 용량 + Projects</div></div>
  <div class="callout callout-info fragment fade-up" data-fragment-index="4"><strong>다음</strong><div class="metric-label">AgentCore로 프로덕션 에이전트</div></div>
</div>
:::

:::notes
{timing: 1min}
[요약]
- 모델은 골라 쓰고, 추론 옵션으로 비용·안정성을 잡는다
- Mantle이 호환성과 용량 관리를 끌어올린다
- 다음은 에이전트의 프로덕션화

1부를 정리하면, Bedrock은 모델을 골라 쓰게 해 주고, 추론 옵션으로 비용과 안정성을 조절하게 해 주며, Mantle이 그 추론을 표준 API와 자동 용량 관리로 끌어올립니다.
{cue: pause} 여기까지는 "똑똑한 모델을 잘 부르는" 이야기였습니다.
{cue: transition} 2부에서는 그 모델이 스스로 도구를 쓰고 일을 끝내는 "에이전트"를 어떻게 프로덕션으로 올리는지 보겠습니다.
:::
