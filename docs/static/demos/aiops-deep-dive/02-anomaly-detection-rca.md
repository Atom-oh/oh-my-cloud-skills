---
remarp: true
block: 2
title: "AI 기반 이상 탐지와 근본 원인 분석"
---

## AI 기반 이상 탐지와 근본 원인 분석

@type: section

이상 탐지 · 상관분석 · GenAI RCA

:::notes
{timing: 1min}
두 번째 블록을 시작하겠습니다. 이번에는 수집된 관측성 데이터를 AI로 분석하는 방법을 다룹니다.
정적 임계값 기반 알림의 한계부터 시작해서, ML 기반 이상 탐지, 그리고 GenAI로 근본 원인을 자동 분석하는 것까지 살펴보겠습니다.
{cue: transition} 먼저 왜 정적 임계값이 부족한지 알아보겠습니다.
:::

---

## 정적 임계값의 한계

@type: content

::: left

### 정적 알림의 문제 {.click}

- **False Positive 폭주** — 트래픽 패턴에 따라 정상 범위가 달라짐 {.click}
- **느린 변화 탐지 불가** — Memory Leak 같은 점진적 이상 놓침 {.click}
- **알림 피로** — 의미 없는 알림 반복 → 중요 알림도 무시 {.click}

:::

::: right

### ML 기반 이상 탐지 {.click}

- **동적 밴드** — 시계열 패턴을 학습하여 적응형 임계값 {.click}
- **계절성 반영** — 주간/월간 트래픽 패턴을 자동 학습 {.click}
- **상관분석** — 여러 메트릭 간 연관 관계 감지 {.click}

:::

:::notes
{timing: 3min}
정적 임계값의 가장 큰 문제는 False Positive입니다. CPU 80% 알림을 걸어놓으면, 블랙 프라이데이에는 정상인데도 알림이 울리고, 새벽에는 진짜 이상인 60%도 놓칩니다.
{cue: pause} Memory Leak처럼 천천히 올라가는 이상도 감지하기 어렵습니다. 임계값에 도달하기 전까지는 정상으로 판단하니까요.
그리고 가장 위험한 건 알림 피로입니다. 의미 없는 알림이 하루 수십 건 오면, 사람은 알림을 무시하기 시작합니다. 정작 중요한 알림도 놓치게 되죠.
ML 기반 이상 탐지는 이 문제를 해결합니다. 시계열 패턴을 학습해서 동적 밴드를 만들고, 주간/월간 계절성도 자동 반영합니다.
{cue: transition} CloudWatch Anomaly Detection이 어떻게 동작하는지, 밴드 시뮬레이터로 직접 체험해 보겠습니다.
:::

---

## CloudWatch Anomaly Detection 개요

@type: content

:::html
<div style="display:grid; grid-template-columns:1fr 1fr; gap:24px; margin-top:12px;">
  <div>
    <div style="font-size:1.1rem; font-weight:600; color:var(--accent1); margin-bottom:12px;">동작 원리</div>
    <div style="font-size:0.9rem; line-height:1.9; color:var(--text-secondary);">
      • <strong style="color:#fff;">Random Cut Forest (RCF)</strong> 알고리즘 기반<br>
      • 최대 <strong style="color:#fff;">2주 학습 기간</strong> 후 이상 탐지 시작<br>
      • <strong style="color:#fff;">계절성 자동 감지</strong>: 시간별, 요일별, 월별 패턴<br>
      • <strong style="color:#fff;">밴드 폭 조절</strong>: 표준편차 배수(1x-5x)로 민감도 설정<br>
      • <strong style="color:#fff;">알림 조건</strong>: ANOMALY_DETECTION_BAND 함수 사용
    </div>
    <div style="margin-top:16px; padding:12px; background:rgba(65,179,255,0.08); border-radius:8px;">
      <div style="font-size:0.8rem; font-family:monospace; color:var(--accent1);">
        ANOMALY_DETECTION_BAND(<br>
        &nbsp;&nbsp;m1, // target metric<br>
        &nbsp;&nbsp;2   // band width (σ multiplier)<br>
        )
      </div>
    </div>
  </div>
  <div>
    <div style="font-size:1.1rem; font-weight:600; color:var(--accent2); margin-bottom:12px;">지원 메트릭</div>
    <div style="display:flex; flex-direction:column; gap:8px;">
      <div style="background:rgba(65,179,255,0.1); padding:10px 16px; border-radius:8px;">
        <div style="font-size:0.85rem; font-weight:600; color:#fff;">EC2/ECS/EKS</div>
        <div style="font-size:0.75rem; color:var(--text-secondary);">CPUUtilization, NetworkIn/Out, MemoryUtilization</div>
      </div>
      <div style="background:rgba(173,92,255,0.1); padding:10px 16px; border-radius:8px;">
        <div style="font-size:0.85rem; font-weight:600; color:#fff;">ALB/NLB</div>
        <div style="font-size:0.75rem; color:var(--text-secondary);">RequestCount, TargetResponseTime, 5XXCount</div>
      </div>
      <div style="background:rgba(0,229,0,0.1); padding:10px 16px; border-radius:8px;">
        <div style="font-size:0.85rem; font-weight:600; color:#fff;">RDS/DynamoDB</div>
        <div style="font-size:0.75rem; color:var(--text-secondary);">ReadLatency, WriteLatency, ThrottledRequests</div>
      </div>
      <div style="background:rgba(251,211,50,0.1); padding:10px 16px; border-radius:8px;">
        <div style="font-size:0.85rem; font-weight:600; color:#fff;">Lambda</div>
        <div style="font-size:0.75rem; color:var(--text-secondary);">Duration, Errors, ConcurrentExecutions</div>
      </div>
    </div>
  </div>
</div>
:::

:::notes
{timing: 3min}
CloudWatch Anomaly Detection은 Random Cut Forest 알고리즘을 사용합니다. 이건 Amazon이 개발한 비지도 학습 알고리즘으로, 시계열 데이터에서 이상치를 탐지하는 데 특화되어 있습니다.
최초 2주 정도 데이터를 학습하면, 시간별, 요일별, 월별 계절성 패턴을 자동으로 감지합니다. 예를 들어 월요일 오전 9시에 트래픽이 급증하는 패턴을 학습하면, 그 시간대에는 밴드가 넓어지죠.
{cue: pause} 밴드 폭은 표준편차 배수로 조절합니다. 2x가 기본인데, 너무 좁으면 False Positive가 많고, 너무 넓으면 진짜 이상을 놓칩니다.
알림 설정은 ANOMALY_DETECTION_BAND 함수를 사용합니다. 메트릭이 밴드 밖으로 나가면 알림이 발동되는 구조입니다.
{cue: transition} 밴드 폭에 따라 탐지 결과가 어떻게 달라지는지, 시뮬레이터로 직접 체험해 보겠습니다.
:::

---

## Anomaly Detection 밴드 시뮬레이터

@type: content

:::html
<div style="display:grid; grid-template-columns:2fr 1fr; gap:24px; margin-top:8px;">
  <div>
    <canvas id="anomaly-canvas" width="800" height="340" style="width:100%; background:rgba(0,0,0,0.3); border-radius:8px;"></canvas>
  </div>
  <div>
    <div style="font-size:0.9rem; color:var(--text-secondary); margin-bottom:4px;">밴드 폭 (표준편차 배수)</div>
    <div style="display:flex; align-items:center; gap:12px;">
      <input type="range" id="band-width" min="1" max="5" step="0.5" value="2" style="flex:1;">
      <span id="band-val" style="font-size:1.5rem; font-weight:700; color:var(--accent1); min-width:40px; text-align:right;">2x</span>
    </div>
    <div style="margin-top:16px;">
      <div style="font-size:0.9rem; color:var(--text-secondary); margin-bottom:8px;">🔴 이상치 주입</div>
      <button id="inject-btn" style="width:100%; padding:10px; background:rgba(255,92,133,0.2); border:1px solid var(--accent4); color:var(--accent4); border-radius:6px; cursor:pointer; font-size:0.85rem;">이상치 3개 주입</button>
      <button id="reset-btn" style="width:100%; padding:10px; margin-top:8px; background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.2); color:var(--text-secondary); border-radius:6px; cursor:pointer; font-size:0.85rem;">초기화</button>
    </div>
    <div style="margin-top:16px; font-size:0.85rem; line-height:1.8;">
      <div>🟢 감지된 이상: <strong id="detected" style="color:var(--accent3);">0건</strong></div>
      <div>⚠️ False Positive: <strong id="fp" style="color:var(--accent6);">0건</strong></div>
      <div>🔴 False Negative: <strong id="fn" style="color:var(--accent4);">0건</strong></div>
    </div>
    <div style="margin-top:8px; padding-top:8px; border-top:1px solid rgba(255,255,255,0.1);">
      <span id="advice" style="color:var(--accent1);">밴드 폭을 조절해 보세요</span>
    </div>
  </div>
</div>
:::

:::script
(function() {
  var el = document.querySelector('.slide-deck #anomaly-canvas');
  if (!el) return;
  var slide = el.closest('.slide');
  if (!slide) return;
  var canvas = slide.querySelector('#anomaly-canvas');
  var ctx = canvas.getContext('2d');
  var bandSlider = slide.querySelector('#band-width');
  var bandVal = slide.querySelector('#band-val');
  var injectBtn = slide.querySelector('#inject-btn');
  var resetBtn = slide.querySelector('#reset-btn');
  var W = 800, H = 340, N = 100;
  var baseData = [], anomalies = [];
  function initData() {
    baseData = []; anomalies = [];
    for (var i = 0; i < N; i++) {
      var t = i / N * Math.PI * 4;
      var seasonal = Math.sin(t) * 20 + Math.sin(t * 3) * 8;
      var noise = (Math.random() - 0.5) * 16;
      baseData.push(50 + seasonal + noise);
    }
  }
  function draw() {
    var bw = +bandSlider.value;
    ctx.clearRect(0, 0, W, H);
    var mean = [], upper = [], lower = [];
    for (var i = 0; i < N; i++) {
      var t = i / N * Math.PI * 4;
      var m = 50 + Math.sin(t) * 20 + Math.sin(t * 3) * 8;
      mean.push(m);
      upper.push(m + bw * 12);
      lower.push(m - bw * 12);
    }
    ctx.fillStyle = 'rgba(65,179,255,0.08)';
    ctx.beginPath();
    for (var i = 0; i < N; i++) {
      var x = i / (N - 1) * (W - 40) + 20;
      ctx.lineTo(x, H - (upper[i] / 100 * (H - 40) + 20));
    }
    for (var i = N - 1; i >= 0; i--) {
      var x = i / (N - 1) * (W - 40) + 20;
      ctx.lineTo(x, H - (lower[i] / 100 * (H - 40) + 20));
    }
    ctx.closePath(); ctx.fill();
    ctx.strokeStyle = 'rgba(65,179,255,0.3)'; ctx.lineWidth = 1; ctx.setLineDash([4, 4]);
    ctx.beginPath();
    for (var i = 0; i < N; i++) { var x = i / (N - 1) * (W - 40) + 20; i === 0 ? ctx.moveTo(x, H - (upper[i] / 100 * (H - 40) + 20)) : ctx.lineTo(x, H - (upper[i] / 100 * (H - 40) + 20)); }
    ctx.stroke();
    ctx.beginPath();
    for (var i = 0; i < N; i++) { var x = i / (N - 1) * (W - 40) + 20; i === 0 ? ctx.moveTo(x, H - (lower[i] / 100 * (H - 40) + 20)) : ctx.lineTo(x, H - (lower[i] / 100 * (H - 40) + 20)); }
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.strokeStyle = '#41B3FF'; ctx.lineWidth = 2;
    ctx.beginPath();
    var detected = 0, fp = 0, fn = 0;
    for (var i = 0; i < N; i++) {
      var x = i / (N - 1) * (W - 40) + 20;
      var y = H - (baseData[i] / 100 * (H - 40) + 20);
      i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    }
    ctx.stroke();
    for (var i = 0; i < N; i++) {
      var x = i / (N - 1) * (W - 40) + 20;
      var y = H - (baseData[i] / 100 * (H - 40) + 20);
      var isAnomaly = anomalies.indexOf(i) >= 0;
      var outsideBand = baseData[i] > upper[i] || baseData[i] < lower[i];
      if (outsideBand) {
        ctx.fillStyle = isAnomaly ? '#FF5C85' : '#FBD332';
        ctx.beginPath(); ctx.arc(x, y, 5, 0, Math.PI * 2); ctx.fill();
        detected++;
        if (!isAnomaly) fp++;
      }
      if (isAnomaly && !outsideBand) { fn++; ctx.strokeStyle = '#FF693C'; ctx.lineWidth = 2; ctx.beginPath(); ctx.arc(x, y, 7, 0, Math.PI * 2); ctx.stroke(); ctx.strokeStyle = '#41B3FF'; ctx.lineWidth = 2; }
    }
    slide.querySelector('#detected').textContent = detected + '건';
    slide.querySelector('#fp').textContent = fp + '건';
    slide.querySelector('#fn').textContent = fn + '건';
    var advice = bw <= 1.5 ? '밴드가 좁음 → FP 증가 주의' : bw >= 4 ? '밴드가 넓음 → FN 증가 주의' : '적정 범위 (2-3x 권장)';
    slide.querySelector('#advice').textContent = advice;
  }
  bandSlider.addEventListener('input', function() {
    bandVal.textContent = bandSlider.value + 'x';
    draw();
  });
  injectBtn.addEventListener('click', function() {
    var indices = [];
    for (var j = 0; j < 3; j++) {
      var idx = Math.floor(Math.random() * (N - 20)) + 10;
      indices.push(idx);
      anomalies.push(idx);
      baseData[idx] = baseData[idx] + (Math.random() > 0.5 ? 1 : -1) * (40 + Math.random() * 30);
    }
    draw();
  });
  resetBtn.addEventListener('click', function() { initData(); draw(); });
  initData();
  draw();
})();
:::

:::notes
{timing: 4min}
이제 Anomaly Detection 밴드를 직접 체험해 보겠습니다.
왼쪽 캔버스에 시계열 데이터가 보입니다. 파란 선이 실제 메트릭, 파란 영역이 ML이 학습한 정상 밴드입니다.
오른쪽 슬라이더로 밴드 폭을 조절해 보겠습니다. 1x로 좁히면 — 정상 데이터도 밴드 밖으로 나가서 False Positive가 급증합니다.
{cue: pause} 5x로 넓히면? 밴드가 너무 넓어서 진짜 이상도 놓칩니다. False Negative가 생기죠.
이상치를 주입해 보겠습니다. [이상치 주입] 버튼을 누르면 — 빨간 점이 나타납니다. 이걸 밴드가 잡아내는지 확인해 보세요.
{cue: question} 밴드 폭을 2x에서 3x 사이로 조절해 보세요. 어디가 FP와 FN의 적절한 균형점인지 찾아보시겠습니까?
실제 프로덕션에서는 서비스 특성에 따라 다릅니다. 결제 시스템처럼 FN이 치명적인 경우 좁게, 로그 분석처럼 FP가 짜증나는 경우 넓게 설정합니다.
{cue: transition} DevOps Guru가 이런 이상 탐지를 어떻게 서비스 레벨에서 자동화하는지 보겠습니다.
:::

---

## Amazon DevOps Guru — 서비스 레벨 이상 탐지

@type: content

:::html
<div style="display:grid; grid-template-columns:1fr 1fr; gap:24px; margin-top:12px;">
  <div>
    <div style="font-size:1.1rem; font-weight:600; color:var(--accent1); margin-bottom:12px;">핵심 기능</div>
    <div style="font-size:0.9rem; line-height:1.9; color:var(--text-secondary);">
      • <strong style="color:#fff;">Proactive Insights</strong>: 장애 발생 전 예측 알림<br>
      • <strong style="color:#fff;">Reactive Insights</strong>: 현재 이상 탐지 + 관련 리소스 그룹핑<br>
      • <strong style="color:#fff;">자동 상관분석</strong>: 관련 메트릭/로그/이벤트를 하나의 Insight로 묶음<br>
      • <strong style="color:#fff;">권장 조치</strong>: ML 기반 해결 방안 제안<br>
      • <strong style="color:#fff;">통합 범위</strong>: CloudFormation Stack / Tag 기반 범위 설정
    </div>
  </div>
  <div>
    <div style="font-size:1.1rem; font-weight:600; color:var(--accent2); margin-bottom:12px;">Insight 구조 예시</div>
    <div style="background:rgba(0,0,0,0.3); padding:16px; border-radius:8px; font-family:monospace; font-size:0.75rem; line-height:1.8; color:var(--accent1);">
      <div style="color:var(--accent4);">🔴 Reactive Insight #247</div>
      <div style="color:var(--text-secondary);">─────────────────────</div>
      <div><span style="color:var(--accent6);">Anomalies:</span></div>
      <div>&nbsp;&nbsp;• ALB 5XX ↑320% (p99: 4.2s → 18.7s)</div>
      <div>&nbsp;&nbsp;• ECS TaskCount ↓ (desired: 10, running: 4)</div>
      <div>&nbsp;&nbsp;• RDS ReadLatency ↑ (2ms → 89ms)</div>
      <div style="color:var(--accent6);">Related Events:</div>
      <div>&nbsp;&nbsp;• ECS Deployment 14:32 UTC</div>
      <div>&nbsp;&nbsp;• RDS Storage Full 14:28 UTC</div>
      <div style="color:var(--accent3);">Recommendation:</div>
      <div>&nbsp;&nbsp;→ RDS storage 확장 + ECS rollback 검토</div>
    </div>
  </div>
</div>
:::

:::notes
{timing: 3min}
Amazon DevOps Guru는 서비스 레벨에서 이상 탐지를 자동화합니다.
가장 강력한 기능은 자동 상관분석입니다. ALB 5XX 급증, ECS Task 감소, RDS 레이턴시 증가 — 이 3개가 동시에 발생하면, DevOps Guru가 하나의 Insight로 묶어서 보여줍니다.
{cue: pause} 예시를 보시면 — Reactive Insight가 ALB, ECS, RDS의 이상을 하나로 묶고, 관련 이벤트로 ECS 배포와 RDS 스토리지 Full을 연결합니다. 그리고 "RDS 스토리지 확장 + ECS 롤백 검토"라는 권장 조치까지 제안합니다.
사람이 하면 로그 3개 뒤지고, 타임라인 맞추고, 인과 관계 추론하는 데 30분-1시간 걸리는 작업입니다. DevOps Guru는 이걸 자동으로 합니다.
Proactive Insights는 더 흥미로운데, 장애가 발생하기 전에 "이 패턴이면 곧 문제가 생길 것 같다"고 예측 알림을 보냅니다.
{cue: transition} DevOps Guru가 상관분석까지 해주지만, 근본 원인을 깊이 파고드는 건 GenAI가 더 잘합니다.
:::

---

## GenAI 기반 근본 원인 분석 (RCA)

@type: tabs

### 아키텍처

:::html
<div style="display:flex; flex-direction:column; gap:12px; margin-top:8px;">
  <div style="display:flex; align-items:center; gap:12px;">
    <div style="background:rgba(65,179,255,0.15); padding:12px 20px; border-radius:8px; min-width:160px; text-align:center;">
      <div style="font-size:0.9rem; font-weight:600; color:var(--accent1);">DevOps Guru Insight</div>
      <div style="font-size:0.75rem; color:var(--text-secondary);">이상 탐지 + 상관분석</div>
    </div>
    <div style="color:var(--accent1); font-size:1.2rem;">→</div>
    <div style="background:rgba(173,92,255,0.15); padding:12px 20px; border-radius:8px; min-width:160px; text-align:center;">
      <div style="font-size:0.9rem; font-weight:600; color:var(--accent2);">Amazon Bedrock</div>
      <div style="font-size:0.75rem; color:var(--text-secondary);">Claude + RAG 분석</div>
    </div>
    <div style="color:var(--accent2); font-size:1.2rem;">→</div>
    <div style="background:rgba(0,229,0,0.15); padding:12px 20px; border-radius:8px; min-width:160px; text-align:center;">
      <div style="font-size:0.9rem; font-weight:600; color:var(--accent3);">RCA Report</div>
      <div style="font-size:0.75rem; color:var(--text-secondary);">근본 원인 + 복구 계획</div>
    </div>
  </div>
  <div style="display:flex; gap:12px; margin-top:8px;">
    <div style="flex:1; background:rgba(255,255,255,0.03); padding:12px; border-radius:8px; font-size:0.8rem; color:var(--text-secondary);">
      <strong style="color:#fff;">Input:</strong> Anomaly 메트릭, 관련 로그, 배포 이력, 변경 이벤트
    </div>
    <div style="flex:1; background:rgba(255,255,255,0.03); padding:12px; border-radius:8px; font-size:0.8rem; color:var(--text-secondary);">
      <strong style="color:#fff;">RAG:</strong> 과거 인시던트 DB, 런북, 아키텍처 문서, 변경 로그
    </div>
    <div style="flex:1; background:rgba(255,255,255,0.03); padding:12px; border-radius:8px; font-size:0.8rem; color:var(--text-secondary);">
      <strong style="color:#fff;">Output:</strong> 근본 원인 분석, 영향 범위, 복구 단계, 재발 방지책
    </div>
  </div>
</div>
:::

### 프롬프트 패턴

```
당신은 AWS 운영 전문가입니다. 다음 인시던트를 분석해 주세요.

## 인시던트 컨텍스트
- 발생 시각: {timestamp}
- 영향 서비스: {affected_services}
- DevOps Guru Insight: {insight_summary}

## 관련 데이터
- 이상 메트릭: {anomaly_metrics}
- 최근 변경 사항: {recent_changes}
- 관련 로그 (최근 30분): {relevant_logs}

## 분석 요청
1. 근본 원인 (Root Cause) — 가장 가능성 높은 원인 3가지
2. 인과 관계 체인 — 어떤 순서로 장애가 전파되었는지
3. 영향 범위 — 어떤 서비스/사용자에 영향을 미치는지
4. 즉시 복구 단계 — 우선순위 순서로
5. 재발 방지 — 장기적 개선 방안
```

### 출력 예시

```
## 근본 원인 분석 보고서

### 🔴 Root Cause (신뢰도: 92%)
RDS Aurora 스토리지 Full (99.7%) → 쓰기 작업 실패
→ ECS 헬스체크 실패 → Task 재시작 반복
→ ALB 5XX 급증

### 인과 관계 체인
14:28 RDS storage 99.7% → WriteIOPS 0으로 감소
14:30 App write 실패 → error log 급증
14:31 ECS healthcheck timeout → Task restart
14:32 Running task 10→4 → ALB 503 응답

### 즉시 복구 단계
1. [긴급] RDS 스토리지 확장: 100GB → 200GB
2. [긴급] ECS desired count 임시 증가: 10 → 15
3. [확인] 데이터 정합성 확인 쿼리 실행
4. [모니터] 30분간 메트릭 안정화 관찰
```

:::notes
{timing: 4min}
GenAI 기반 RCA의 아키텍처입니다. DevOps Guru Insight가 이상을 감지하면, Amazon Bedrock의 Claude 모델이 근본 원인을 분석합니다.
핵심은 RAG — Retrieval Augmented Generation입니다. 과거 인시던트 기록, 런북, 아키텍처 문서를 참조해서 분석하기 때문에, 단순 로그 분석보다 훨씬 정확합니다.
{cue: pause} 프롬프트 패턴을 보시면 — 인시던트 컨텍스트, 관련 데이터, 그리고 분석 요청을 구조화합니다. 특히 "가장 가능성 높은 원인 3가지"처럼 복수의 가설을 요청하는 게 중요합니다. LLM이 단일 원인에 확신을 갖는 것보다, 여러 가설을 제시하고 신뢰도를 매기는 게 더 안전합니다.
출력 예시를 보면 — 근본 원인부터 인과 관계 체인, 즉시 복구 단계까지 한 번에 나옵니다. 이걸 사람이 하면 1시간, GenAI는 30초입니다.
{cue: question} 이런 분석을 자동화하면 어떤 가치가 있을까요? MTTR 단축입니다. 다음 블록에서 실제 수치를 계산해 보겠습니다.
{cue: transition} DevOps Guru + Bedrock으로 이상 탐지와 RCA를 통합하는 실전 구현을 보겠습니다.
:::

---

## DevOps Guru + Bedrock 통합 구현

@type: tabs

### EventBridge 연동

```yaml
# DevOps Guru → EventBridge → Lambda → Bedrock
Resources:
  DevOpsGuruRule:
    Type: AWS::Events::Rule
    Properties:
      EventPattern:
        source:
          - aws.devops-guru
        detail-type:
          - DevOps Guru New Insight Open
      Targets:
        - Arn: !GetAtt RCAFunction.Arn
          Id: trigger-rca
```

### Lambda (RCA)

```python
import boto3, json

bedrock = boto3.client('bedrock-runtime')
cw_logs = boto3.client('logs')

def handler(event, context):
    insight = event['detail']['insightDescription']
    anomalies = event['detail'].get('anomalies', [])

    # 관련 로그 수집
    logs = collect_recent_logs(anomalies)

    # Bedrock Claude로 RCA 실행
    response = bedrock.invoke_model(
        modelId='anthropic.claude-sonnet-4-6',
        body=json.dumps({
            'messages': [{
                'role': 'user',
                'content': build_rca_prompt(
                    insight, anomalies, logs)
            }],
            'max_tokens': 2000
        })
    )
    return parse_rca_response(response)
```

### 결과 전송

```python
# RCA 결과 → Slack + OpsCenter
def send_results(rca_report):
    # Slack 알림
    slack.post_message(
        channel='#incident',
        blocks=format_rca_blocks(rca_report)
    )

    # SSM OpsCenter OpsItem 생성
    ssm.create_ops_item(
        Title=f"RCA: {rca_report['root_cause']}",
        Description=rca_report['full_report'],
        Severity='2',
        Source='DevOpsGuru-Bedrock-RCA'
    )

    # 자동 복구 트리거 (Block 3에서 상세)
    if rca_report['confidence'] > 0.85:
        trigger_auto_remediation(
            rca_report['remediation_steps'])
```

:::notes
{timing: 3min}
실제 구현은 EventBridge → Lambda → Bedrock 파이프라인입니다.
DevOps Guru가 새 Insight를 생성하면 EventBridge 규칙이 Lambda를 트리거합니다. Lambda는 Insight 상세 정보와 관련 로그를 수집해서 Bedrock Claude에 전달합니다.
{cue: pause} Lambda 코드를 보시면 — collect_recent_logs로 최근 30분 로그를 수집하고, build_rca_prompt로 구조화된 프롬프트를 생성합니다.
결과는 Slack으로 알림을 보내고, SSM OpsCenter에 OpsItem을 생성합니다. 그리고 — 이 부분이 핵심인데 — confidence가 85% 이상이면 자동 복구를 트리거합니다. 이게 Block 3에서 다룰 내용입니다.
사람 개입 없이 이상 탐지 → 근본 원인 분석 → 자동 복구까지 이어지는 파이프라인입니다.
{cue: transition} Block 2를 정리하겠습니다.
:::

---

## Block 2 핵심 정리

@type: content

:::html
<div style="display:grid; grid-template-columns:1fr 1fr; gap:24px; margin-top:24px;">
  <div>
    <div style="font-size:1.1rem; font-weight:600; color:var(--accent1); margin-bottom:16px;">🔑 Key Takeaways</div>
    <div style="font-size:0.9rem; line-height:2.2; color:var(--text-secondary);">
      <div>✅ <strong style="color:#fff;">정적 임계값 탈피</strong> — ML 기반 동적 밴드로 전환</div>
      <div>✅ <strong style="color:#fff;">CloudWatch AD</strong> — RCF 알고리즘, 밴드 폭 2-3x 권장</div>
      <div>✅ <strong style="color:#fff;">DevOps Guru</strong> — 서비스 레벨 자동 상관분석</div>
      <div>✅ <strong style="color:#fff;">GenAI RCA</strong> — Bedrock + RAG로 근본 원인 30초 분석</div>
      <div>✅ <strong style="color:#fff;">자동화 파이프라인</strong> — EventBridge → Lambda → Bedrock</div>
    </div>
  </div>
  <div>
    <div style="font-size:1.1rem; font-weight:600; color:var(--accent2); margin-bottom:16px;">💡 실무 적용 포인트</div>
    <div style="font-size:0.9rem; line-height:2.2; color:var(--text-secondary);">
      <div>→ 핵심 메트릭 10개부터 Anomaly Detection 적용</div>
      <div>→ 밴드 폭은 서비스 특성에 맞게 (결제: 좁게, 로그: 넓게)</div>
      <div>→ DevOps Guru는 CloudFormation Stack 단위로 활성화</div>
      <div>→ RCA 프롬프트에 과거 인시던트 DB를 RAG로 연결</div>
      <div>→ confidence 85% 이상일 때만 자동 복구 트리거</div>
    </div>
  </div>
</div>
:::

:::notes
{timing: 2min}
Block 2 핵심을 정리합니다.
정적 임계값에서 ML 기반 동적 밴드로 전환하세요. CloudWatch Anomaly Detection은 밴드 폭 2-3x가 대부분의 경우에 적절합니다.
DevOps Guru로 서비스 레벨 상관분석을 자동화하고, GenAI RCA로 근본 원인 분석을 30초 만에 완료할 수 있습니다.
{cue: pause} 실무 적용은 점진적으로 — 핵심 메트릭 10개부터 시작해서 범위를 넓히세요. RCA 프롬프트에 과거 인시던트 DB를 RAG로 연결하면 분석 정확도가 크게 올라갑니다.
그리고 자동 복구는 confidence 85% 이상일 때만 트리거하세요. 이 부분은 다음 블록에서 자세히 다루겠습니다.
{cue: transition} 5분 쉬고 마지막 블록, 자동 복구와 AIOps 성숙도 로드맵을 시작하겠습니다.
:::
