---
remarp: true
block: 1
title: "관측성 파이프라인"
---

# AIOps Deep Dive
## 관측성에서 자동 복구까지

@type: cover
@speaker: Junseok Oh | Sr. Solutions Architect, AWS
@date: 2026-04-10

:::notes
{timing: 1min}
안녕하세요, AWS Solutions Architect 오준석입니다. 오늘은 AIOps Deep Dive 세션을 진행하겠습니다.
이 세션에서는 관측성 데이터 수집부터 AI 기반 이상 탐지, 그리고 자동 복구까지 — AIOps의 전체 여정을 실습 중심으로 다룹니다.
300 레벨 세션인 만큼, AWS 서비스 경험이 있으시다는 전제로 아키텍처 설계와 구현 패턴에 집중하겠습니다.
{cue: transition} 먼저 오늘 다룰 내용을 한눈에 살펴보겠습니다.
:::

---

## 세션 아젠다

@type: agenda

- 관측성 파이프라인 {30min}
- AI 기반 이상 탐지와 RCA {30min}
- 자동 복구와 AIOps 로드맵 {30min}

:::notes
{timing: 1min}
총 90분 세션으로, 3개 블록으로 나눠 진행합니다.
첫 번째 블록에서는 관측성 파이프라인을 구축합니다 — 모니터링과 관측성의 차이부터 시작해서, OpenTelemetry 기반 데이터 수집, 비용 최적화까지 다룹니다.
두 번째 블록에서는 수집된 데이터를 AI로 분석합니다 — CloudWatch Anomaly Detection, DevOps Guru, 그리고 GenAI 기반 근본 원인 분석까지.
세 번째 블록에서는 분석 결과를 기반으로 자동 복구하는 방법을 다루고, AIOps 성숙도 로드맵으로 마무리합니다.
{cue: transition} 그럼 첫 번째 블록, 관측성 파이프라인부터 시작하겠습니다.
:::

---

## 관측성 vs 모니터링

@type: content

::: left

### 모니터링 (Monitoring) {.click}

- **Known-unknowns** — 미리 정의한 메트릭/임계값 감시 {.click}
- CPU > 80%, 응답시간 > 3초 같은 **정적 규칙** {.click}
- "무엇이 고장났는가?" 에 답함 {.click}

:::

::: right

### 관측성 (Observability) {.click}

- **Unknown-unknowns** — 예측 못한 장애도 탐지 {.click}
- 시스템 **내부 상태**를 외부 출력으로 추론 {.click}
- "**왜** 고장났는가?" 에 답함 {.click}

:::

:::notes
{timing: 3min}
AIOps를 이야기하기 전에, 모니터링과 관측성의 차이를 명확히 해야 합니다.
모니터링은 Known-unknowns를 다룹니다. CPU가 80%를 넘으면 알림, 응답 시간이 3초를 넘으면 알림 — 이렇게 미리 알고 있는 문제를 감시하는 거죠.
{cue: pause} 반면 관측성은 Unknown-unknowns까지 커버합니다. 예상치 못한 장애가 발생했을 때, 시스템이 내보내는 데이터만으로 내부 상태를 추론할 수 있어야 합니다.
쉽게 말하면 — 모니터링은 "뭐가 고장났어?"에 답하고, 관측성은 "왜 고장났어?"에 답합니다.
{cue: question} 현재 운영 환경에서 장애가 발생하면 "왜"를 찾는 데 얼마나 걸리시나요? 그 시간을 줄이는 것이 관측성의 핵심 가치입니다.
{cue: transition} 관측성을 구현하려면 3가지 데이터가 필요합니다.
:::

---

## 관측성 데이터 3대 축

@type: content

:::html
<div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:24px; margin-top:24px;">
  <div style="background:rgba(65,179,255,0.08); border:1px solid rgba(65,179,255,0.3); border-radius:12px; padding:24px; text-align:center;">
    <div style="font-size:2.5rem; margin-bottom:12px;">📊</div>
    <div style="font-size:1.3rem; font-weight:700; color:var(--accent1); margin-bottom:8px;">Metrics</div>
    <div style="font-size:0.85rem; color:var(--text-secondary); line-height:1.7;">
      수치형 시계열 데이터<br>
      CPU, Memory, 응답시간<br>
      <strong style="color:#fff;">CloudWatch Metrics</strong><br>
      <strong style="color:#fff;">Amazon Managed Prometheus</strong>
    </div>
  </div>
  <div style="background:rgba(173,92,255,0.08); border:1px solid rgba(173,92,255,0.3); border-radius:12px; padding:24px; text-align:center;">
    <div style="font-size:2.5rem; margin-bottom:12px;">📝</div>
    <div style="font-size:1.3rem; font-weight:700; color:var(--accent2); margin-bottom:8px;">Logs</div>
    <div style="font-size:0.85rem; color:var(--text-secondary); line-height:1.7;">
      이벤트 기록 (텍스트)<br>
      에러 스택트레이스, 감사 로그<br>
      <strong style="color:#fff;">CloudWatch Logs</strong><br>
      <strong style="color:#fff;">OpenSearch Service</strong>
    </div>
  </div>
  <div style="background:rgba(0,229,0,0.08); border:1px solid rgba(0,229,0,0.3); border-radius:12px; padding:24px; text-align:center;">
    <div style="font-size:2.5rem; margin-bottom:12px;">🔗</div>
    <div style="font-size:1.3rem; font-weight:700; color:var(--accent3); margin-bottom:8px;">Traces</div>
    <div style="font-size:0.85rem; color:var(--text-secondary); line-height:1.7;">
      요청 흐름 추적<br>
      서비스 간 호출 체인<br>
      <strong style="color:#fff;">AWS X-Ray</strong><br>
      <strong style="color:#fff;">CloudWatch ServiceLens</strong>
    </div>
  </div>
</div>
<div style="margin-top:24px; padding:16px; background:rgba(255,255,255,0.03); border-radius:8px; text-align:center;">
  <span style="color:var(--accent1);">Metrics</span>이 "무엇이" 문제인지 알려주고, <span style="color:var(--accent2);">Logs</span>가 "왜" 발생했는지 설명하고, <span style="color:var(--accent3);">Traces</span>가 "어디서" 발생했는지 보여줍니다.
</div>
:::

:::notes
{timing: 3min}
관측성의 3대 축입니다 — Metrics, Logs, Traces.
Metrics는 수치형 시계열 데이터입니다. CPU 사용률, 메모리, 응답 시간 같은 것들이죠. CloudWatch Metrics나 Amazon Managed Prometheus로 수집합니다.
Logs는 텍스트 기반 이벤트 기록입니다. 에러 스택트레이스, 감사 로그 등. CloudWatch Logs나 OpenSearch에 저장합니다.
Traces는 분산 시스템에서 요청이 어떤 경로로 흘러가는지 추적합니다. X-Ray가 대표적이죠.
{cue: pause} 핵심은 — 이 3가지가 서로 연결되어야 진정한 관측성이 됩니다. Metric 이상 → 관련 Log 확인 → Trace로 정확한 호출 지점 파악. 이 상관분석이 가능해야 "왜?"에 빠르게 답할 수 있습니다.
{cue: transition} 이 데이터를 효율적으로 수집하려면 통합 에이전트가 필요합니다. OpenTelemetry를 살펴보겠습니다.
:::

---

## OpenTelemetry 기반 수집 아키텍처

@type: content

:::html
<div style="display:grid; grid-template-columns:1fr 1fr; gap:24px; margin-top:12px;">
  <div>
    <div style="font-size:1.1rem; font-weight:600; color:var(--accent1); margin-bottom:12px;">ADOT (AWS Distro for OpenTelemetry)</div>
    <div style="font-size:0.9rem; line-height:1.9; color:var(--text-secondary);">
      • <strong style="color:#fff;">벤더 중립</strong>: OTel 표준 기반 — 백엔드 교체 시 코드 변경 불필요<br>
      • <strong style="color:#fff;">통합 에이전트</strong>: Metrics + Logs + Traces를 하나의 Collector로 수집<br>
      • <strong style="color:#fff;">자동 계측</strong>: Java/Python/Node.js SDK로 코드 변경 최소화<br>
      • <strong style="color:#fff;">EKS 네이티브</strong>: DaemonSet 또는 Sidecar 배포<br>
      • <strong style="color:#fff;">AWS 최적화</strong>: X-Ray, CloudWatch, AMP 익스포터 내장
    </div>
  </div>
  <div>
    <div style="font-size:1.1rem; font-weight:600; color:var(--accent2); margin-bottom:12px;">수집 아키텍처 패턴</div>
    <div style="display:flex; flex-direction:column; gap:8px;">
      <div style="background:rgba(65,179,255,0.1); padding:12px 16px; border-radius:8px; display:flex; align-items:center; gap:12px;">
        <span style="font-size:1.5rem;">📦</span>
        <div>
          <div style="font-size:0.9rem; font-weight:600; color:#fff;">DaemonSet (권장)</div>
          <div style="font-size:0.8rem; color:var(--text-secondary);">노드당 1개 Collector → 리소스 효율적</div>
        </div>
      </div>
      <div style="background:rgba(173,92,255,0.1); padding:12px 16px; border-radius:8px; display:flex; align-items:center; gap:12px;">
        <span style="font-size:1.5rem;">🔄</span>
        <div>
          <div style="font-size:0.9rem; font-weight:600; color:#fff;">Sidecar</div>
          <div style="font-size:0.8rem; color:var(--text-secondary);">Pod별 격리 필요 시 → 보안 민감 워크로드</div>
        </div>
      </div>
      <div style="background:rgba(0,229,0,0.1); padding:12px 16px; border-radius:8px; display:flex; align-items:center; gap:12px;">
        <span style="font-size:1.5rem;">🌐</span>
        <div>
          <div style="font-size:0.9rem; font-weight:600; color:#fff;">Gateway</div>
          <div style="font-size:0.8rem; color:var(--text-secondary);">중앙 집중 처리 → 필터링/샘플링 로직 통합</div>
        </div>
      </div>
    </div>
  </div>
</div>
:::

:::notes
{timing: 3min}
관측성 데이터를 수집하는 핵심 도구가 ADOT — AWS Distro for OpenTelemetry입니다.
OTel 표준 기반이라 벤더 종속 없이 백엔드를 자유롭게 교체할 수 있고, 하나의 Collector로 Metrics, Logs, Traces를 모두 수집합니다.
Java, Python, Node.js 자동 계측 SDK가 있어서 코드 변경을 최소화할 수 있습니다.
{cue: pause} EKS 환경에서 배포 패턴은 3가지입니다. 대부분 DaemonSet이 권장됩니다 — 노드당 하나만 띄우면 되니까 리소스 효율적이죠. 보안이 민감한 워크로드는 Sidecar로 격리하고, 필터링이나 샘플링 같은 중앙 로직이 필요하면 Gateway 패턴을 씁니다.
실무에서는 DaemonSet + Gateway 조합을 많이 쓰는데, DaemonSet이 수집하고 Gateway가 필터링/라우팅하는 구조입니다.
{cue: transition} ADOT Collector의 실제 설정을 보겠습니다.
:::

---

## ADOT Collector 파이프라인 설정

@type: tabs

### Receivers

```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318
  prometheus:
    config:
      scrape_configs:
        - job_name: 'kubernetes-pods'
          kubernetes_sd_configs:
            - role: pod
```

### Processors

```yaml
processors:
  batch:
    timeout: 10s
    send_batch_size: 1024
  memory_limiter:
    check_interval: 5s
    limit_mib: 512
    spike_limit_mib: 128
  filter/severity:
    logs:
      include:
        severity_number:
          min: 9  # INFO 이상만 수집
```

### Exporters

```yaml
exporters:
  awsxray:
    region: ap-northeast-2
  awsemf:
    region: ap-northeast-2
    namespace: AnyCompany/AIOps
  prometheusremotewrite:
    endpoint: https://aps-workspaces.ap-northeast-2
      .amazonaws.com/workspaces/ws-xxx/api/v1/remote_write
    auth:
      authenticator: sigv4auth
```

:::notes
{timing: 3min}
ADOT Collector 설정은 Receivers → Processors → Exporters 3단계 파이프라인입니다.
Receivers에서 OTLP gRPC/HTTP로 트레이스와 메트릭을 받고, Prometheus 스크래핑으로 Kubernetes Pod 메트릭을 수집합니다.
Processors 단계가 중요한데 — batch로 네트워크 효율을 높이고, memory_limiter로 OOM을 방지합니다. filter/severity는 INFO 이상 로그만 수집하는 필터입니다. 이게 비용 최적화의 첫 단추죠.
{cue: pause} Exporters는 X-Ray로 트레이스, CloudWatch EMF로 커스텀 메트릭, AMP로 Prometheus 메트릭을 보냅니다.
핵심 팁 — send_batch_size를 1024로 설정하면 API 호출 횟수가 줄어 비용이 절감됩니다. 너무 크면 지연이 생기니 1000~2000 사이가 적당합니다.
{cue: transition} 다음은 로그 분석의 핵심, CloudWatch Logs Insights 쿼리를 실전 예제로 보겠습니다.
:::

---

## CloudWatch Logs Insights 실전 쿼리

@type: tabs

### 에러 분석

```
# Top 10 에러 패턴 (서비스별 그룹핑)
fields @timestamp, @message, service_name
| filter @message like /(?i)(error|exception|fatal)/
| stats count(*) as error_count by service_name,
    substr(@message, 0, 100) as error_pattern
| sort error_count desc
| limit 10
```

💡 **팁**: `substr(@message, 0, 100)`으로 에러 메시지를 자르면 유사 에러가 자동 그룹됩니다. `parse` 명령으로 정규식 추출도 가능합니다.

### 지연 분석

```
# P99 레이턴시 by API endpoint
filter ispresent(duration_ms)
| stats avg(duration_ms) as avg_ms,
    pct(duration_ms, 95) as p95,
    pct(duration_ms, 99) as p99,
    count(*) as req_count
  by endpoint
| filter req_count > 100
| sort p99 desc
```

💡 **팁**: `req_count > 100` 필터로 노이즈를 제거합니다. 트래픽이 적은 엔드포인트의 P99는 의미 없는 경우가 많습니다.

### 비용 최적화

```
# 로그 그룹별 일일 수집량 (비용 추정)
stats sum(strlen(@message)) as total_bytes by @logStream
| sort total_bytes desc
| limit 20
```

💡 **팁**: `strlen(@message)` × `$0.50/GB` 로 일일 비용을 추정합니다. DEBUG 로그가 전체의 60-80%를 차지하는 경우가 흔합니다.

:::notes
{timing: 3min}
CloudWatch Logs Insights는 관측성의 핵심 쿼리 도구입니다. 3가지 실전 패턴을 보겠습니다.
첫 번째, 에러 분석입니다. error, exception, fatal을 필터링하고 서비스별로 그룹핑합니다. substr로 메시지 앞 100자만 잘라서 유사 에러를 자동 그룹핑하는 게 포인트입니다.
두 번째, 지연 분석. P95, P99 레이턴시를 엔드포인트별로 계산합니다. 여기서 req_count 필터가 중요한데, 트래픽이 적은 API의 P99는 의미가 없거든요.
{cue: pause} 세 번째가 비용 최적화인데 — 로그 그룹별 수집량을 확인합니다. 실제로 해보시면 놀라실 겁니다. DEBUG 로그가 전체의 60-80%를 차지하는 경우가 대부분이거든요.
{cue: question} 현재 CloudWatch Logs 비용이 월 얼마 정도 나오시나요?
{cue: transition} 이 비용을 얼마나 줄일 수 있는지, 직접 계산해 보겠습니다.
:::

---

## 로그 비용 최적화 계산기

@type: content

:::html
<div style="display:grid; grid-template-columns:1fr 1fr; gap:32px; margin-top:12px;">
  <div>
    <div style="font-size:1rem; font-weight:600; color:var(--accent1); margin-bottom:16px;">파라미터 조정</div>
    <div style="margin-bottom:16px;">
      <div style="font-size:0.85rem; color:var(--text-secondary);">일일 로그 볼륨</div>
      <div style="display:flex; align-items:center; gap:12px; margin-top:4px;">
        <input type="range" id="log-vol" min="10" max="1000" value="200" style="flex:1;">
        <span id="log-vol-val" style="min-width:60px; text-align:right; font-weight:600;">200 GB</span>
      </div>
    </div>
    <div style="margin-bottom:16px;">
      <div style="font-size:0.85rem; color:var(--text-secondary);">DEBUG 로그 비율</div>
      <div style="display:flex; align-items:center; gap:12px; margin-top:4px;">
        <input type="range" id="debug-pct" min="0" max="90" value="65" style="flex:1;">
        <span id="debug-pct-val" style="min-width:60px; text-align:right; font-weight:600;">65%</span>
      </div>
    </div>
    <div style="margin-bottom:16px;">
      <div style="font-size:0.85rem; color:var(--text-secondary);">Trace 샘플링 비율</div>
      <div style="display:flex; align-items:center; gap:12px; margin-top:4px;">
        <input type="range" id="sample-rate" min="1" max="100" value="100" style="flex:1;">
        <span id="sample-rate-val" style="min-width:60px; text-align:right; font-weight:600;">100%</span>
      </div>
    </div>
    <div style="margin-bottom:16px;">
      <div style="font-size:0.85rem; color:var(--text-secondary);">보관 기간</div>
      <div style="display:flex; align-items:center; gap:12px; margin-top:4px;">
        <input type="range" id="retention" min="1" max="365" value="90" style="flex:1;">
        <span id="retention-val" style="min-width:60px; text-align:right; font-weight:600;">90일</span>
      </div>
    </div>
  </div>
  <div>
    <div style="font-size:1rem; font-weight:600; color:var(--accent2); margin-bottom:16px;">비용 비교</div>
    <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-bottom:16px;">
      <div style="background:rgba(255,92,133,0.15); padding:16px; border-radius:8px; text-align:center;">
        <div style="font-size:0.8rem; color:var(--text-secondary);">현재 월 비용</div>
        <div id="cost-before" style="font-size:1.8rem; font-weight:700; color:var(--accent4);">$5,040</div>
      </div>
      <div style="background:rgba(0,229,0,0.15); padding:16px; border-radius:8px; text-align:center;">
        <div style="font-size:0.8rem; color:var(--text-secondary);">최적화 후</div>
        <div id="cost-after" style="font-size:1.8rem; font-weight:700; color:var(--accent3);">$2,739</div>
      </div>
    </div>
    <div style="background:rgba(255,255,255,0.05); border-radius:8px; padding:8px 16px; margin-bottom:12px;">
      <div style="height:24px; background:rgba(255,255,255,0.1); border-radius:4px; overflow:hidden;">
        <div id="savings-fill" style="height:100%; background:linear-gradient(90deg, var(--accent3), var(--accent1)); border-radius:4px; width:45%; transition:width 0.3s;"></div>
      </div>
      <div id="savings-label" style="font-size:0.85rem; text-align:center; margin-top:4px; color:var(--accent3);">절감: 45.7%</div>
    </div>
    <div style="font-size:0.8rem; line-height:1.8; color:var(--text-secondary);">
      <div id="detail-log">• 로그 레벨 최적화: —</div>
      <div id="detail-trace">• Trace 샘플링: —</div>
      <div id="detail-monthly">• 월간 절감액: —</div>
      <div id="detail-annual">• 연간 절감: —</div>
    </div>
  </div>
</div>
:::

:::script
(function() {
  var el = document.querySelector('.slide-deck #log-vol');
  if (!el) return;
  var slide = el.closest('.slide');
  if (!slide) return;
  var logVol = slide.querySelector('#log-vol');
  var debugPct = slide.querySelector('#debug-pct');
  var sampleRate = slide.querySelector('#sample-rate');
  var retention = slide.querySelector('#retention');
  var CW_INGEST = 0.50, CW_STORE = 0.03, XRAY_TRACE = 0.000005, TRACES_PER_GB = 50000;
  function calc() {
    var vol = +logVol.value, dbg = +debugPct.value / 100, smp = +sampleRate.value / 100, ret = +retention.value;
    var beforeLog = vol * 30 * CW_INGEST + vol * ret * CW_STORE;
    var beforeTrace = vol * TRACES_PER_GB * 30 * XRAY_TRACE;
    var before = beforeLog + beforeTrace;
    var optVol = vol * (1 - dbg);
    var afterLog = optVol * 30 * CW_INGEST + optVol * ret * CW_STORE;
    var afterTrace = vol * TRACES_PER_GB * smp * 30 * XRAY_TRACE;
    var after = afterLog + afterTrace;
    var pct = before > 0 ? ((before - after) / before * 100) : 0;
    var saved = before - after;
    slide.querySelector('#log-vol-val').textContent = vol + ' GB';
    slide.querySelector('#debug-pct-val').textContent = debugPct.value + '%';
    slide.querySelector('#sample-rate-val').textContent = sampleRate.value + '%';
    slide.querySelector('#retention-val').textContent = retention.value + '일';
    slide.querySelector('#cost-before').textContent = '$' + Math.round(before).toLocaleString();
    slide.querySelector('#cost-after').textContent = '$' + Math.round(after).toLocaleString();
    slide.querySelector('#savings-fill').style.width = Math.min(pct, 100) + '%';
    slide.querySelector('#savings-label').textContent = '절감: ' + pct.toFixed(1) + '%';
    slide.querySelector('#detail-log').textContent = '• 로그 레벨 최적화: DEBUG ' + debugPct.value + '% 제거 → ' + optVol + ' GB/일';
    slide.querySelector('#detail-trace').textContent = '• Trace 샘플링: ' + sampleRate.value + '% → 에러 트레이스 100% 유지';
    slide.querySelector('#detail-monthly').textContent = '• 월간 절감액: $' + Math.round(saved).toLocaleString() + ' (' + pct.toFixed(0) + '% 절감)';
    slide.querySelector('#detail-annual').textContent = '• 연간 절감: $' + Math.round(saved * 12).toLocaleString();
  }
  [logVol, debugPct, sampleRate, retention].forEach(function(el) { el.addEventListener('input', calc); });
  calc();
})();
:::

:::notes
{timing: 4min}
이제 실제로 비용이 얼마나 줄어드는지 계산기로 확인해 보겠습니다.
왼쪽 슬라이더를 조절하면 오른쪽에서 실시간으로 비용이 계산됩니다.
일일 200GB 로그를 수집하고 있다고 가정하겠습니다. DEBUG 로그가 65%를 차지하고 있으면요...
{cue: pause} DEBUG 로그를 제거하면 일일 볼륨이 200GB에서 70GB로 줄어듭니다. Trace 샘플링을 20%로 조절하면 — tail_sampling이 에러 트레이스는 100% 유지하면서 정상 트레이스만 샘플링하니까 분석 품질은 유지됩니다.
결과를 보시면 월 비용이 크게 줄어드는 것을 확인할 수 있습니다. 연간으로 환산하면 상당한 금액입니다.
{cue: question} 현재 일일 로그 볼륨이 얼마나 되시나요? 수치를 알고 계시면 직접 넣어보시면 됩니다.
{cue: transition} 이런 관측성 데이터를 실시간으로 통합 조회하려면 어떤 아키텍처가 필요할까요?
:::

---

## 통합 관측성 대시보드 아키텍처

:::html
<div style="display:grid; grid-template-columns:1fr 1fr; gap:24px; margin-top:12px;">
  <div>
    <div style="font-size:1.1rem; font-weight:600; color:var(--accent1); margin-bottom:12px;">Amazon Managed Grafana (AMG)</div>
    <div style="font-size:0.9rem; line-height:1.9; color:var(--text-secondary);">
      • <strong style="color:#fff;">Multi-source</strong>: CloudWatch + AMP + X-Ray + OpenSearch를 단일 대시보드에 통합<br>
      • <strong style="color:#fff;">SSO 연동</strong>: IAM Identity Center로 팀별 접근 제어<br>
      • <strong style="color:#fff;">알림 통합</strong>: SNS, Slack, PagerDuty 연동<br>
      • <strong style="color:#fff;">관리형</strong>: Grafana 서버 운영 불필요, 자동 스케일링<br>
      • <strong style="color:#fff;">플러그인</strong>: 150+ 데이터 소스 플러그인 지원
    </div>
  </div>
  <div>
    <div style="font-size:1.1rem; font-weight:600; color:var(--accent2); margin-bottom:12px;">권장 대시보드 구성</div>
    <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px;">
      <div style="background:rgba(65,179,255,0.1); padding:12px; border-radius:6px; text-align:center;">
        <div style="font-size:0.8rem; color:var(--accent1);">L1 — Overview</div>
        <div style="font-size:0.75rem; color:var(--text-secondary); margin-top:4px;">SLO 상태 + 핵심 KPI<br>Golden Signals</div>
      </div>
      <div style="background:rgba(173,92,255,0.1); padding:12px; border-radius:6px; text-align:center;">
        <div style="font-size:0.8rem; color:var(--accent2);">L2 — Service</div>
        <div style="font-size:0.75rem; color:var(--text-secondary); margin-top:4px;">서비스별 상세 메트릭<br>에러율 + 레이턴시</div>
      </div>
      <div style="background:rgba(0,229,0,0.1); padding:12px; border-radius:6px; text-align:center;">
        <div style="font-size:0.8rem; color:var(--accent3);">L3 — Debug</div>
        <div style="font-size:0.75rem; color:var(--text-secondary); margin-top:4px;">트레이스 + 로그 상관<br>Pod/Node 레벨</div>
      </div>
      <div style="background:rgba(251,211,50,0.1); padding:12px; border-radius:6px; text-align:center;">
        <div style="font-size:0.8rem; color:var(--accent6);">L4 — Business</div>
        <div style="font-size:0.75rem; color:var(--text-secondary); margin-top:4px;">비즈니스 KPI<br>매출 영향도 + 사용자 경험</div>
      </div>
    </div>
  </div>
</div>
:::

:::notes
{timing: 3min}
수집한 데이터를 통합 조회하는 핵심 도구가 Amazon Managed Grafana입니다.
CloudWatch, AMP, X-Ray, OpenSearch를 하나의 대시보드에서 볼 수 있고, IAM Identity Center로 팀별 접근 제어도 가능합니다.
{cue: pause} 대시보드는 4단계 계층으로 구성하는 것을 권장합니다.
L1은 전체 시스템 Overview — SLO 상태와 Golden Signals를 한눈에 봅니다. 온콜 담당자가 가장 먼저 보는 화면이죠.
L2는 서비스별 상세 — 각 마이크로서비스의 에러율과 레이턴시를 보여줍니다.
L3은 디버그 레벨 — 트레이스와 로그를 상관분석하는 화면입니다. 장애 원인을 파악할 때 사용합니다.
L4는 비즈니스 KPI — 장애가 매출이나 사용자 경험에 미치는 영향을 보여줍니다. 경영진 보고용이기도 하죠.
{cue: transition} Block 1을 정리하겠습니다.
:::

---

## Block 1 핵심 정리

@type: content

:::html
<div style="display:grid; grid-template-columns:1fr 1fr; gap:24px; margin-top:24px;">
  <div>
    <div style="font-size:1.1rem; font-weight:600; color:var(--accent1); margin-bottom:16px;">🔑 Key Takeaways</div>
    <div style="font-size:0.9rem; line-height:2.2; color:var(--text-secondary);">
      <div>✅ <strong style="color:#fff;">관측성 ≠ 모니터링</strong> — "왜?"에 답하는 능력</div>
      <div>✅ <strong style="color:#fff;">3대 축 통합</strong> — Metrics + Logs + Traces 상관분석</div>
      <div>✅ <strong style="color:#fff;">ADOT</strong> — 벤더 중립 통합 수집 에이전트</div>
      <div>✅ <strong style="color:#fff;">비용 최적화</strong> — 로그 레벨 + 샘플링으로 40-60% 절감 가능</div>
      <div>✅ <strong style="color:#fff;">대시보드 계층화</strong> — L1~L4 4단계 구성</div>
    </div>
  </div>
  <div>
    <div style="font-size:1.1rem; font-weight:600; color:var(--accent2); margin-bottom:16px;">💡 실무 적용 포인트</div>
    <div style="font-size:0.9rem; line-height:2.2; color:var(--text-secondary);">
      <div>→ OTel 자동 계측부터 시작 (코드 변경 최소)</div>
      <div>→ DEBUG 로그 비율 확인 → filter/severity 적용</div>
      <div>→ tail_sampling으로 에러 100% + 정상 10% 수집</div>
      <div>→ AMG L1 대시보드 먼저 구축 → 점진적 확장</div>
      <div>→ CloudWatch Logs Insights 쿼리 라이브러리 구축</div>
    </div>
  </div>
</div>
:::

:::notes
{timing: 2min}
Block 1 핵심을 정리하겠습니다.
첫째, 관측성은 모니터링이 아닙니다. "왜?"에 답할 수 있어야 진짜 관측성입니다.
둘째, Metrics, Logs, Traces 3대 축이 서로 연결되어야 합니다.
셋째, ADOT으로 벤더 중립적인 수집 파이프라인을 구축하세요.
넷째, 비용 최적화가 중요합니다 — 방금 계산기에서 보신 것처럼, 로그 레벨 조정과 샘플링만으로 40-60% 절감이 가능합니다.
{cue: pause} 실무에서 바로 적용하실 거라면 — OTel 자동 계측으로 시작하시고, DEBUG 로그 비율을 확인해서 filter를 적용하세요. 그리고 AMG L1 대시보드를 먼저 만들어서 전체 현황을 파악하는 것부터 시작하시면 됩니다.
{cue: transition} 5분 쉬고 나서, 수집된 데이터를 AI로 분석하는 두 번째 블록을 시작하겠습니다.
:::
