---
sidebar_position: 1
title: "인터랙티브 프레젠테이션 스킬"
---

# 인터랙티브 프레젠테이션 스킬

**다른 사람이 만든 슬라이드로 발표하시나요?** [발표자용 안내](../presenter-guide.md)부터 보세요. 슬라이드 열기, 공유할 창 선택, 노트 읽기, 인터랙티브 장 조작, 발표 중 문제 해결을 설명합니다. 이 페이지는 덱을 만들고 관리하는 방법을 다룹니다.

{/* 영문 개편 전의 기존 섹션 링크를 유지합니다. */}
<span id="trigger-keywords" />
<span id="provided-resources" />
<span id="assets" />
<span id="scripts" />
<span id="references" />
<span id="icons" />
<span id="key-features" />
<span id="remarp-format-recommended" />
<span id="pptx-theme-extraction" />
<span id="data-visualization-patterns" />
<span id="typography-hierarchy" />
<span id="css-only-charts" />
<span id="kpi-card-layout" />
<span id="chartjs-integration" />
<span id="canvas-vs-html-decision-guide" />
<span id="the-4-box-rule" />
<span id="decision-matrix" />
<span id="html-architecture-pattern" />
<span id="remarp-workflow-detail" />
<span id="step-1-theme-setup-optional" />
<span id="step-2-content-planning" />
<span id="step-3-create-project-structure" />
<span id="step-4-write-remarp-content" />
<span id="step-5-build-html" />
<span id="step-6-review--iterate" />
<span id="step-7-enhancement" />
<span id="step-8-quality-review" />
<span id="step-9-deploy" />
<span id="interactive-pattern-guide" />
<span id="simulator-pattern" />
<span id="calculator-pattern" />
<span id="dashboard-pattern" />
<span id="speaker-notes-writing-guide" />
<span id="requirements" />
<span id="structure-template" />
<span id="good-example" />
<span id="bad-example-what-not-to-do" />
<span id="slide-types" />
<span id="keyboard-shortcuts" />
<span id="usage-example" />
<span id="quality-review-required" />

Remarp Markdown으로 인터랙티브 HTML 발표 자료를 만들고, 브라우저에서 발표하거나 정적인 슬라이드 이미지로 내보냅니다. 이 가이드는 작은 프로젝트 하나를 끝까지 만드는 방법과, 특히 L200 기술 교육에서 효과적인 설명을 만드는 선택 기준을 다룹니다.

**원본은 Remarp입니다.** 내용, 발표자 노트, 상호작용 코드는 원본 파일에서 관리합니다. HTML과 공통 프레임워크는 컴파일러가 생성합니다.

| 필요한 결과물 | 선택 |
| --- | --- |
| 탭, 퀴즈, 단계 제어, 입력값 변경이 가능한 브라우저 슬라이드 | reactive-presentation |
| 웹 덱의 모양을 유지한 PowerPoint 사본 | reactive-presentation 스크린샷 내보내기. 편집 가능한 슬라이드 개체는 아닙니다 |
| 텍스트, 도형, 레이아웃을 직접 편집할 수 있는 PowerPoint | [aws-light-fcd](./aws-light-fcd.md) |

처음에는 **도구 준비 → 첫 덱 만들기 → 검증과 미리보기** 순서로 진행하세요. 이후 섹션에서 상호작용을 확장하고 공개하는 방법을 설명합니다.

## 작업 흐름 {#workflow}

1. **요청 정리:** 청중, 수준, 언어, 시간, 출력 위치, 퀴즈 포함 여부, 참고 자료를 정합니다.
2. **기획:** 각 슬라이드의 메시지와 상호작용을 정하고, 긴 교육은 따로 봐도 이해되는 블록으로 나눕니다.
3. **작성:** 공통 메타데이터, 블록 파일, 구조화된 노트, 로컬 자산을 준비합니다.
4. **검증과 빌드:** 원본의 CRITICAL 항목을 해결한 뒤 HTML을 생성합니다.
5. **리허설과 리뷰:** 생성된 덱의 동작과 레이아웃을 확인하고 콘텐츠 리뷰 PASS를 받습니다.
6. **내보내기 또는 공개:** 승인받은 경우에만 정적 사본을 내보내거나 전체 출력을 배포합니다.

컴파일 성공은 원본을 빌드할 수 있다는 뜻입니다. 교육 내용, 데이터, 브라우저 상호작용이 올바르다는 증명은 아닙니다.

## 도구 준비 {#prepare-the-tools}

사용하는 호스트에 [aws-content-plugin을 설치](../installation.md)합니다. Claude Code에서는 인터랙티브/웹 발표 자료를 요청하면 발표 형식 선택 절차가 이 작업 흐름으로 연결합니다. Codex에서는 설치된 reactive-presentation 스킬을 선택하거나 요청에 이름을 명시합니다. 전문 절차를 실행하는 데 Claude 전용 네이티브 서브에이전트가 필요한 것은 아닙니다.

명령을 직접 실행하려면 Python 3와 설치한 스킬 버전의 스크립트 디렉터리를 사용합니다. 아래 예제는 **저장소 체크아웃** 기준이며 플러그인 캐시 버전을 고정하지 않습니다.

```bash
# From the oh-my-cloud-skills repository root:
export SKILL_DIR="$(pwd)/plugins/aws-content-plugin/skills/reactive-presentation"
python3 "$SKILL_DIR/scripts/remarp_to_slides.py" --help
mkdir -p my-talk/assets
cat > my-talk/assets/logo.svg <<'SVG'
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 48">
  <rect width="160" height="48" rx="8" fill="#232f3e"/>
  <text x="80" y="31" text-anchor="middle" fill="white" font-size="20">Example team</text>
</svg>
SVG
```

설치된 패키지에서는 scripts와 assets가 있는 실제 reactive-presentation 절차 디렉터리를 SKILL_DIR로 지정합니다. 삭제된 캐시 버전을 추측하거나 Codex에서 CLAUDE_PLUGIN_ROOT가 자동으로 제공된다고 가정하지 마세요. 도움말을 실행해 경로를 확인합니다.

샘플 로고는 독립된 팀의 교육 자료용 플레이스홀더입니다. 사용 권한이 있는 로고와 푸터로 바꾸세요. AWS 브랜드 자료에는 해당 AWS 브랜딩과 저작권 표시를 사용합니다.

전체 YAML 메타데이터 예제에는 PyYAML을 사용합니다. 브라우저 측정에는 Python Playwright 패키지와 **실제로 실행할 수 있는 Chromium**이 모두 필요합니다. PowerPoint 내보내기에는 python-pptx도 필요합니다. 필요한 경우에만 승인된 프로젝트 환경에 의존성을 설치하세요. Playwright MCP와 로컬 Python Playwright는 서로 다른 브라우저 설치를 사용할 수 있습니다.

## 요청 예시 {#request-examples}

“슬라이드를 예쁘게 만들어 줘”만 요청하기보다 구체적인 조건을 제시하세요. 아래 프롬프트는 공통 영문 예제입니다. 메타데이터가 본문을 번역해 준다고 생각하지 말고, 원하는 언어와 프로젝트 조건을 명시하세요.

**L200 입문 교육:**

```text
Use reactive-presentation to create a 30-minute L200 introduction to
event-driven applications for developers new to cloud architecture.
Language: Korean. Output: ./event-driven-intro/.
Include speaker notes, a knowledge check and a Key Takeaways slide.
Explain unfamiliar terms at first use with plain meanings and examples.
Use stepwise request flows, a before/after comparison and one input-driven
simulation. Prefer an explorable Archify diagram for grouped architecture.
Use official AWS icons for AWS services. Keep essential meaning visible
in static exports. Validate and review before publication.
Do not deploy or overwrite an existing deck without my confirmation.
```

**여러 블록으로 나눈 기술 교육:**

```text
Create a 90-minute reactive-presentation training in ./platform-training/.
Audience: platform engineers. Level: L300. Language: English.
Plan three 30-minute blocks: fundamentals, architecture and operations.
Include a session cover and Thank You slide in each block, shared branding,
structured speaker notes and one knowledge check per block.
Use the supplied reference documents as evidence; do not invent benchmarks.
Show the outline and interaction plan before authoring the Remarp sources.
```

**기존 덱의 특정 범위만 수정:**

```text
Update ./event-driven-intro/02-architecture.md only:
turn the request-flow slide into three controllable steps and add a
plain-language detail panel for the first use of "event".
Preserve the existing theme, notes, quiz answers and unrelated slides.
Edit Remarp source, not generated HTML. Validate, sync the complete project,
then check the changed slide in both themes. Do not deploy.
```

## 프로젝트 구조 {#project-layout}

```text
my-talk/
  _presentation.md       # Shared metadata, branding and block list
  01-basics.md           # Remarp slides and speaker notes
  assets/
    logo.svg             # Project-local image, kept with the output
  index.html             # Generated merged deck
  toc.html               # Generated block agenda and export controls
  01-basics.html         # Generated block deck
  common/                # Generated framework and referenced AWS icons
```

공통 presentation 파일에는 메타데이터만 넣습니다. 번호가 붙은 각 블록에는 별도의 Remarp frontmatter와 슬라이드가 필요합니다. 블록 이름을 공통 목록 및 파일명에서 확장자를 뺀 이름과 맞추세요. 블록 시간의 합은 전체 시간과 같아야 하며, 휴식 시간을 포함할지는 별도로 정합니다.

프로젝트 빌드는 기본적으로 원본 옆에 HTML을 생성합니다. 사용자 이미지가 자동으로 묶이지는 않습니다. 기본 출력 위치를 유지하면 샘플 로고를 찾을 수 있습니다. 출력 디렉터리를 분리할 경우 로컬 자산을 복사하고 모든 상대 경로를 확인하세요.

## 첫 덱 만들기 {#first-deck}

전체 예제는 표지, 순차 표시, 탭, 퀴즈, 마무리로 구성된 **12분 분량의 5장짜리** 교육 골격입니다. 의도적으로 작은 예제이므로 실제 교육에 사용하기 전에는 내용과 상호작용을 확장하세요.

공통 설정을 **my-talk/_presentation.md**로 저장합니다.

```yaml
---
remarp: true
version: 1
title: "Requests in motion"
ratio: "16:9"
speaker:
  name: "Alex Morgan"
  title: "Engineer"
  company: "Example team"
audience: "Developers new to request processing"
level: "200"
quiz: true
duration: 12
lang: en
blocks:
  - name: 01-basics
    title: "Request basics"
    duration: 12
theme:
  footer: "© 2026 Example team. All rights reserved."
  logo: "./assets/logo.svg"
transition:
  default: fade
  duration: 400
---
```

화면 비율, 청중 수준, 언어, 퀴즈 선택, 브랜딩, 시간을 명시했습니다. 예제는 영어입니다. 한국어 덱은 언어 메타데이터를 ko로 바꾸고 슬라이드 본문과 노트를 한국어로 작성하세요. 메타데이터만으로 내용이 번역되지는 않습니다.

블록을 **my-talk/01-basics.md**로 저장합니다. 노트가 영어여도 필수 요약 표식은 [요약] 그대로 유지합니다.

```markdown
---
remarp: true
block: 01-basics
title: "Request basics"
---

<!-- Slide 1: Session cover -->
@type: cover

# Requests in motion

Follow a request from an action to a result.

:::notes
{timing: 1min}
[요약]
- Introduce the request journey.
- Ask for a familiar application.
- Preview the knowledge check.

Ask the audience to imagine pressing Save in an application.
Explain that the session follows the work triggered by that action.
The aim is to identify where work starts, where it is processed and
how the result reaches the user, without needing a cloud background.
:::

---
<!-- Slide 2: Reveal a sequence -->
@type: content

## Every request has a path

- The client sends a request. {.click order=1}
- A worker processes the request. {.click order=2}
- The client receives the result. {.click order=3}

:::notes
{timing: 3min}
[요약]
- Reveal one action at a time.
- Connect each action to Save.
- Separate a request from its result.

Define the client as the part of an application asking for work.
Reveal the worker only after asking who performs that work.
Use saving a document as the running example: the client asks to save,
the worker stores the change and the client shows confirmation.
{cue: question}
Ask what the user might see while waiting for the result.
:::

---
<!-- Slide 3: Compare explanations -->
@type: tabs

## Choose when to wait

### Wait
The client waits for the worker's result before continuing.

### Continue
The client continues while work finishes separately.
It needs a way to discover whether the work succeeded.

:::notes
{timing: 3min}
[요약]
- Show both interaction choices.
- Compare what the user sees.
- Avoid promising that all work becomes faster.

Select each tab and describe the user experience, not just the labels.
Waiting can be appropriate when the result is needed for the next action.
Continuing can help when work takes longer, but the application still
needs to communicate progress and report failures to the user.
:::

---
<!-- Slide 4: Knowledge check -->
@type: quiz

## Check the request path

**What starts the work in this example?**
- [x] The client sends a request.
- [ ] The result appears before any request.
- [ ] The worker never receives an input.

:::notes
{timing: 3min}
[요약]
- Let the audience choose first.
- Explain why the request starts work.
- Revisit the sequence if needed.

Pause before selecting an answer. Ask someone to describe the Save
example in their own words. Choose the correct answer and explain
why a visible result follows processing rather than preceding it.
Use an incorrect answer to revisit the sequence without judging the learner.
:::

---
<!-- Slide 5: Closing -->
@type: thankyou
@toc: toc.html

# Thank You

Trace one request in your own application.

:::notes
{timing: 2min}
[요약]
- Recap the request journey.
- Invite one practical next step.
- Leave time for questions.

Ask the audience to choose one action in their own application and name
the client, the work performed and the visible result.
Use the agenda link to return to the block list, then invite questions
about where waiting or progress reporting would help that example.
:::
```

## 검증과 미리보기 {#validate-and-preview}

```bash
python3 "$SKILL_DIR/scripts/remarp_to_slides.py" validate ./my-talk/
python3 "$SKILL_DIR/scripts/remarp_to_slides.py" build ./my-talk/
python3 -m http.server 8080 --bind 127.0.0.1 --directory ./my-talk/
```

[합쳐진 덱](http://127.0.0.1:8080/index.html)이나 [블록 목차와 내보내기](http://127.0.0.1:8080/toc.html)를 확인합니다. 끝나면 Ctrl+C로 서버를 종료하세요. 8080 포트가 사용 중이면 다른 포트를 선택합니다.

입력이 잘못되었거나 CRITICAL 항목이 있으면 검증은 0이 아닌 종료 코드를 반환합니다. build와 sync에도 같은 게이트가 적용됩니다. 작성 중 스타일 경고도 해결하되, 권고 경고와 컴파일 거부를 혼동하지 마세요.

다음 결과를 직접 확인합니다.
- 빈 슬라이드 없이 5장이 순서대로 나타납니다.
- 오른쪽/Space로 요청의 세 동작을 표시한 뒤 다음 장으로 이동합니다. 왼쪽 키로 되돌립니다.
- 클릭과 등록된 위/아래 키 동작으로 탭이 전환됩니다.
- 오답과 정답을 각각 선택했을 때 적절한 퀴즈 피드백이 나옵니다.
- 마지막 버튼으로 목차에 돌아가며 로고와 푸터가 표시됩니다.

디렉티브는 슬라이드 구분선 다음에 놓고 또 다른 frontmatter 구분선으로 감싸지 마세요. 단일 파일 빌드는 기본 출력이 다릅니다. slides/default.html과 slides/common/이 생성됩니다.

## 내용과 상호작용 선택 {#content-and-interaction}

| 목적 | 패턴 | 확인할 동작 |
| --- | --- | --- |
| 한 가지 개념 설명 | 순서가 있는 fragment를 넣은 content | 의도한 읽기 순서로 나타나고 되돌아가는지 |
| 대안 비교 | compare 또는 tabs | 각 버튼과 위/아래 키 전환 |
| 이해도 확인 | 정답 하나를 표시한 quiz | 정답 및 오답 피드백 |
| 완료 여부 표시 | 명시적인 checklist | 퀴즈 채점이 아닌 체크 상태 |
| 짧은 직선형 과정 설명 | 박스/아이콘 최대 4개의 Canvas DSL | 모든 단계의 진행 및 되돌리기 |
| 그룹 또는 분기 탐색 | HTML/CSS 또는 Archify | 레이블, 포커스, 탐색, 양쪽 테마 |
| 매개변수 효과 확인 | HTML 입력 컨트롤과 script | 초기값, 경계값, 값 변경, 초기화 |

정보가 누적되는 설명에는 순서가 있는 fragment를 쓰고, 대안들이 같은 공간을 나눠 써야 할 때는 탭을 사용합니다. 중요한 결론 전체를 컨트롤 뒤에 숨기지 말고 보이는 슬라이드에 남겨 두세요. 블록 HTML은 HTML 원본 블록에, 스크립트는 script 원본 블록에 넣습니다. 퀴즈에서는 체크된 항목이 정답입니다. 여러 항목에 체크하는 것만으로 다중 선택 채점 규칙이 보장되지는 않습니다.

## L200 설명을 동적으로 만들기 {#l200-teaching}

L200에서는 장식을 늘리는 대신 **원인과 결과**를 드러내는 데 상호작용을 사용합니다. 다음 순서로 설명해 보세요.
1. 익숙한 상황을 보여 주고 새로운 용어를 풉니다.
2. 다음에 무슨 일이 일어날지 청중이 예측하게 합니다.
3. 한 단계를 표시하거나 입력값 하나를 바꿉니다.
4. 눈에 보이는 결과와 그 결과가 바뀐 이유를 설명합니다.
5. 초기화하거나 되돌린 뒤 이해도를 확인합니다.

30분 입문 교육은 짧은 상황 설명, 제어 가능한 요청 흐름, 비교, 입력 기반 예제 하나, 이해도 확인, 정리 순서로 기획할 수 있습니다. 이는 작성 제안이지 자동 컴파일 규칙이 아닙니다. 수준을 200으로 설정해도 애니메이션이나 시뮬레이션이 자동 생성되지는 않습니다.

끝없이 자동 재생하는 대신 발표자가 진행하는 정지 상태의 시퀀스를 권장합니다. 정적 내보내기에서도 읽을 수 있는 최종 상태와 설명을 남기세요. 사용자 모션에는 움직임 줄이기 설정과 일시 정지/초기화를 지원하고, 프레임워크가 자동 제공한다고 가정하지 말고 실제 동작을 검증합니다.

## 단계를 제어하는 Canvas 흐름 추가 {#canvas-steps}

다음 슬라이드를 퀴즈 앞에 삽입하고 예정 시간을 조정합니다. 일반적인 박스 3개를 960 × 400 설계 좌표에 배치했습니다. 박스 너비가 160픽셀이므로 가로 간격은 (880 − 3 × 160) / 2 = 200이며, 왼쪽 좌표는 40, 400, 760입니다. 같은 색상은 동등한 요소라는 뜻이며 심각도 순위가 아닙니다.

```markdown
---
<!-- Slide: Stepwise request flow -->
@type: canvas
@canvas-id: request-steps

## Follow one request

:::canvas
box client "Client" at 40,180 size 160,55 color blue step 1
box worker "Worker" at 400,180 size 160,55 color blue step 2
box result "Result" at 760,180 size 160,55 color blue step 3
arrow client -> worker "request" step 2
arrow worker -> result "complete" step 3
:::

:::notes
{timing: 3min}
[요약]
- Identify the client.
- Advance to the worker.
- End with the visible result.

Start with the client alone and ask what happens after the Save action.
Advance to the worker, then to the result. Reverse the steps once so the
audience can explain the sequence rather than memorize a finished picture.
The arrows show an illustrative order, not a measured latency.
:::
```

아래/위 키로 모든 단계를 진행하고 되돌려 보세요. FHD와 4K에서 화살표 레이블, 여백, 글자를 확인합니다. Canvas는 박스/아이콘 최대 4개의 직선 흐름으로 제한하고, 그룹, 분기, 큰 다이어그램에는 HTML/CSS 또는 Archify를 사용합니다. AWS 서비스를 시각화할 때는 일반 박스로 대체하지 말고 공통 번들의 검증된 공식 아이콘 별칭을 사용하세요.

## 입력값으로 달라지는 설명 추가 {#input-driven-example}

다음 예제는 평균 처리 시간을 고정하고 예시 요청률을 바꿉니다. 새 슬라이드로 추가한 뒤 노트와 전체/블록 시간을 조정하세요. 교육용 위젯이지 AWS 리소스 규모 산정 계산기는 아닙니다.

```markdown
---
<!-- Slide: Input-driven explanation -->
@type: content

## Waiting keeps work active

:::html
<section id="load-lab" class="card">
  <label for="request-rate">Requests per second</label>
  <input id="request-rate" type="range" min="10" max="100" step="10" value="50">
  <p>Rate: <output id="rate-value">50</output> requests/s</p>
  <p>Assumed average time: 200 ms</p>
  <p>Average in-flight requests: <output id="inflight-value" aria-live="polite">10</output></p>
  <button id="reset-load" type="button">Reset</button>
  <p>Illustrative steady-state estimate: rate × time in seconds.
     This is not a capacity benchmark or a scaling recommendation.</p>
</section>
:::

:::script
const root = document.getElementById('load-lab');
const input = root.querySelector('#request-rate');
const update = () => {
  const rate = Number(input.value);
  root.querySelector('#rate-value').textContent = String(rate);
  root.querySelector('#inflight-value').textContent = (rate * 0.2).toFixed(0);
};
input.addEventListener('input', update);
root.querySelector('#reset-load').addEventListener('click', () => {
  input.value = '50';
  update();
});
update();
:::

:::notes
{timing: 3min}
[요약]
- Change only the request rate.
- Keep average time fixed.
- Explain the estimate's limitation.

Ask the audience to predict what doubling the rate does to work in flight.
Move the slider from 50 to 100 requests per second, then reset it.
The estimate assumes a steady flow and a 200 ms average time per request.
It does not prove that a real application has enough resources or that
an AWS service should scale at a particular threshold.
:::
```

10, 50, 100 requests/s에서 평균 처리 중 요청 수가 2, 10, 20으로 표시되는지 확인합니다. 키보드 값 조정과 Reset도 테스트하세요. 다른 위젯을 추가할 때는 고유한 DOM ID를 사용하고, 모든 입력에 레이블을 붙이며 가정을 보이게 남깁니다. 스크립트는 덱의 페이지에서 실행됩니다. 원본 HTML/JavaScript를 실행 코드로 취급하고 신뢰할 수 없는 스크립트를 붙여 넣지 마세요.

## 아키텍처 다이어그램과 선 그리기 모션 {#architecture-and-line-art}

설명할 질문에 맞춰 다이어그램을 선택합니다.
- **“다음에 무슨 일이 생기나요?”** 요청/트래픽 흐름에 제어 가능한 Canvas 단계 또는 animated-diagram SVG를 사용합니다.
- **“무엇이 무엇과 연결되나요?”** 그룹 탐색, 확대, 경로 강조에는 Archify를 사용하고, 공식 아이콘 기반 HTML/CSS 레이아웃도 활용할 수 있습니다.
- **“정적인 파일로 공유해야 하나요?”** Draw.io와 PNG/SVG 출력에는 [architecture-diagram](./architecture-diagram.md)을 사용합니다.

Archify를 쓰려면 참조 경로에 유효한 architecture JSON 스펙을 먼저 준비합니다. 아래는 완성된 슬라이드나 JSON 스펙이 아닌 **삽입 구문 예시**입니다. 빌드 전에 파일, 노트, 프로젝트 메타데이터를 추가하세요.

```markdown
---
@type: content

## Explore the request route

:::archify id=request-map height=680px
./assets/request-map.json
:::
```

빌더에는 Node.js와 지정된 커밋의 Archify 체크아웃이 필요합니다. 버전 고정값은 설치한 스킬의 아이콘 헬퍼가 관리합니다. 최초 설정 시 네트워크 접근 승인을 받고 새 의존성 디렉터리에서 실행합니다.

```bash
# Read the pin from the same skill version used to build the deck.
PIN="$(python3 - "$SKILL_DIR/scripts/archify_icons.py" <<'PY'
import runpy
import sys
print(runpy.run_path(sys.argv[1])["ARCHIFY_PIN"])
PY
)"
git clone https://github.com/tt-a1i/archify ./archify-dependency
git -C ./archify-dependency checkout "$PIN"
export ARCHIFY_DIR="$(pwd)/archify-dependency"
python3 "$SKILL_DIR/scripts/remarp_to_slides.py" build ./my-talk/
```

기존 체크아웃이 있으면 덮어쓰며 복제하지 말고 커밋을 확인한 뒤 ARCHIFY_DIR로 지정합니다. 빌드 문제를 “해결”하려고 버전 검사를 우회하지 마세요. 각 다이어그램에 고유 ID를 부여합니다. alb, eks, s3 같은 AWS 어휘 ID에는 공식 아이콘이 자동 삽입될 수 있습니다. 매핑되지 않은 노드 메시지와 최종 다이어그램을 확인하세요.

생성된 다이어그램은 archify/에 저장되므로 덱과 함께 제공해야 합니다. HTTP로 덱을 열면 클릭한 다이어그램의 iframe이 포커스를 받고, 같은 출처에서는 Esc로 덱에 돌아옵니다. 파일 URL에서는 바깥을 클릭하세요. 브라우저 내보내기는 다이어그램을 정적으로 만듭니다. PowerPoint 내보내기의 배포 URL 옵션을 사용하면 노트에 인터랙티브 링크를 넣을 수 있습니다.

[line-art-animation 같은](https://github.com/JDhruv14/line-art-animation) 효과가 필요하면 HTML 원본 블록 안의 SVG 경로 표시 또는 연결 강조를 요청하고 스타일/스크립트도 원본에서 관리하세요. **기본 line-art 디렉티브나 해당 저장소의 자동 설치 기능은 없습니다.** SVG 트래픽 모션에는 [animated-diagram 스킬](./animated-diagram.md)도 사용할 수 있습니다. 외부 코드나 자산을 복사하기 전에 라이선스를 검토하세요. 모션 없이도 최종 그림이 의미를 전달하도록 하고, 사용자 재생에 일시 정지/초기화를 제공하며 움직임 줄이기 설정을 존중합니다.

## 탐색과 상세 설명 레이어 {#navigation-and-detail-layers}

오른쪽 위에 마우스를 올리면 목차를 열 수 있습니다. Cmd+K, Ctrl+K 또는 /로 제목, 보이는 내용, 상세 설명을 검색합니다. 발표자 노트는 검색하지 않습니다. 목차와 검색은 오버뷰, 발표자 미리보기, 측정, 내보내기 캡처에서 제외됩니다.

한 문장 정의에는 툴팁을 사용합니다.

```markdown
[Worker]{tip="The part of the application that performs the requested work."}
```

긴 설명은 트리거와 상세 블록을 같은 슬라이드에 둡니다.

```markdown
[API]{detail=api}

:::detail api "How an API connects applications"
tip: API (Application Programming Interface): an agreed way for programs to request data or actions.

An API defines which requests a program accepts and what it returns.
For example, a weather app requests a forecast instead of collecting sensor data itself.
:::
```

상세 블록은 최상위에 두고, 슬라이드 안에서 고유한 ID와 일치하는 참조를 사용합니다. ID 중복이나 참조 누락은 CRITICAL DETAIL_REF 항목입니다. 마우스 올리기/포커스로 요약을 보고 클릭, Enter, Space로 상세 패널을 엽니다. 툴팁만 있는 용어도 터치를 지원합니다. 툴팁 위로 이동해 읽을 수 있고 Esc로 닫습니다. 상세 패널은 Esc, 바깥 클릭, 슬라이드 이동으로 닫힙니다. 포커스가 돌아오는지와 활성화 시 다음 장으로 넘어가지 않는지도 확인하세요.

## 청중 수준에 맞춘 설명 {#audience-aware-explanations}

따로 볼 수 있는 각 블록에서 용어, 약어, 업계 표현이 처음 의미 있게 등장할 때 설명합니다. API, JSON, EKS, S3처럼 흔한 이름도 입문자가 안다고 가정하지 마세요. 오랜 간격이 지난 뒤 문맥을 잃기 쉬운 경우에만 정의를 다시 제공합니다.

**L100/L200**에서는 전체 이름, 쉬운 의미, 실제 예시 또는 중요한 이유를 제공합니다. L300/L400은 더 간결하게 설명할 수 있지만 새로운 분야의 개념은 여전히 풀어야 합니다. 발표자 노트는 이런 설명을 보충할 뿐, 청중에게 보이는 설명을 대신하지 않습니다.

- **차트:** 포커스를 받을 수 있는 텍스트 캡션으로 축, 단위, 대상/기간, 기준선, 결론, 관련 한계/출처를 설명합니다. 예시 데이터임을 표시하고 벤치마크 결과를 지어내지 않습니다.
- **인용문:** 출처를 보이게 유지하고 문맥을 제공합니다. 예시 또는 검증되지 않은 인용이면 명시합니다.
- **정적 사본:** 마우스를 올리거나 패널을 열지 않아도 핵심 의미, 차트 레이블/단위, 결론, 출처가 보여야 합니다.

컴파일러는 주석 구조를 검사합니다. 청중이 실제로 설명을 이해할 수 있는지는 콘텐츠 리뷰에서 판단합니다.

## 문장과 표현 검사 {#copy-gates}

원본 작성 중 EM_DASH, AI_TONE, AUDIENCE_TONE 경고를 해결합니다. SENTENCE_RUNON은 렌더링 측정 경고입니다. 카드에는 주장 한 줄과 필요한 경우 이유 한 줄을 두고, 긴 설명은 상세 패널로 옮깁니다. 발표 자료 본문과 노트에서 긴 대시와 가운데점을 피하고 자연스러운 문장, 쉼표, 괄호, 줄바꿈을 사용하세요.

## 디자인, 브랜딩, 발표자 노트 {#design-and-notes}

의미 기반 색상 토큰과 클래스 기반 라이트/다크 테마를 사용합니다. 색상에 설명 가능한 범주 의미가 없다면 동등한 카드마다 다른 심각도 색상을 배정하지 마세요. 각 블록은 세션 표지로 시작하고 목차에 돌아갈 수 있는 Thank You 슬라이드로 끝납니다.

사용 권한이 있는 PowerPoint 템플릿을 적용하려면 예제의 테마 설정을 바꿉니다.

```yaml
theme:
  source: "./company-template.pptx"
  footer: auto
  logo: auto
```

프로젝트에서 템플릿 경로에 접근할 수 있게 유지합니다. 명시적으로 추출하고 확인하려면 다음 명령을 사용합니다.

```bash
python3 "$SKILL_DIR/scripts/extract_pptx_theme.py" ./company-template.pptx \
  -o ./my-talk/common/pptx-theme/
```

manifest, 추출된 로고, theme-override.css를 확인한 뒤 최종 덱이 override를 연결하고 이미지도 포함하는지 검증합니다. 브랜드 입력에는 --pptx-* 변수를 사용합니다. 추출은 글꼴을 설치하지 않으므로 글꼴 사용 가능 여부와 양쪽 테마를 확인하세요. PDF 테마 추출은 현재 구현되지 않았습니다. PDF/이미지는 시각 참고 자료로 사용하고 동일한 브랜딩 추출을 약속하지 마세요.

모든 슬라이드에는 시간, 정확한 요약 표식, 요약 항목, 발표용 설명, 필요한 진행 큐를 포함한 유용한 구조화 노트가 필요합니다. 전체 예제를 참고하되 화면의 글머리표만 반복하지 마세요. 발표자 뷰는 P가 아닌 **N**으로 엽니다. P는 펜/레이저 제어에 사용됩니다.

## 안전하게 수정하고 다시 빌드 {#edit-and-rebuild}

영향받는 Remarp 원본만 수정하고 노트, 퀴즈 정답, Canvas, script 블록을 보존합니다. 생성된 HTML만 별도로 수정하지 마세요. 원본, 테마, 공통 메타데이터, 자산을 바꾼 뒤 실행합니다.

```bash
python3 "$SKILL_DIR/scripts/remarp_to_slides.py" validate ./my-talk/ --json
python3 "$SKILL_DIR/scripts/remarp_to_slides.py" sync ./my-talk/
# Only the named block; this does not refresh the merged deck or agenda.
python3 "$SKILL_DIR/scripts/remarp_to_slides.py" build ./my-talk/ --block 01-basics
python3 "$SKILL_DIR/scripts/remarp_to_slides.py" issues ./my-talk/ --json
```

sync는 전체 프로젝트, 목차, 프레임워크 자산을 다시 생성합니다. 타임스탬프 기반 증분 빌드가 아닙니다. 수정 중에는 블록 빌드를 사용하고 리허설이나 내보내기 전에 전체 sync를 실행하세요.

수정을 요청할 때는 해당 원본 슬라이드에 issue 주석을 남깁니다.

```markdown
<!-- issue: Explain this term at first use and reveal the flow in three steps. -->
```

issues 명령은 주석을 조회할 뿐 수정하지 않습니다. [slide-fix](./slide-fix.md)에 피드백 반영을 요청하세요. 컴파일러는 생성된 슬라이드에서 issue 주석을 제거합니다.

VS Code에서는 근사 텍스트 미리보기와 컴파일된 HTML 미리보기를 구분하세요. 확장 0.2.0 이상에서 Design Studio는 컴파일러 기반 스냅샷과 제한된 원본 수정을 지원하며, 복잡한 상호작용은 원본에서 수정합니다. AI 요청은 클립보드로 전달하는 방식이지 자동 모델 호출이 아닙니다. 미리보기나 Studio가 검증 및 콘텐츠 리뷰를 대신하지는 않습니다.

## 발표 중 조작 {#presenter-controls}

| 키 | 현재 기본 동작 |
| --- | --- |
| 오른쪽 / Space, 왼쪽 | 순차 표시/다음 이동, 되돌리기/이전 이동 |
| 아래 / 위 | 등록된 Canvas 단계, 탭 전환, 슬라이드별 동작 |
| N | 발표자 창과 노트 |
| F / G / S | 전체 화면 / 오버뷰 / 사이드바 |
| T / H | 덱 테마 전환 / 현재 슬라이드를 로컬에서 숨기기 |
| P / O / I / U / Y | 레이저 / 펜 / 형광펜 / 지우개 / 확대경 |
| C / Esc | 현재 장의 잉크 지우기 / 먼저 펜 모드 종료 |

사용자 키 매핑으로 일부 기본 동작을 바꿀 수 있습니다. 펜 모드에서는 오버레이가 포인터 입력을 받으므로 탭, 퀴즈, 상세 링크를 쓰기 전에 끄세요. 발표자 노트 편집은 브라우저에만 저장되며 Remarp를 바꾸지 않습니다. 영구적으로 반영하려면 원본을 수정하고 sync합니다. 전체 동작과 전체 화면 주의사항은 [현재 키보드 레퍼런스](/docs/remarp-guide/keyboard-shortcuts)를 확인하세요.

## 공유 전 품질 확인 {#quality-checklist}

원본 검증 후 **공통 자산을 포함한 빌드 프로젝트**에 두 출력 게이트를 실행합니다.

```bash
python3 "$SKILL_DIR/scripts/check_deck.py" ./my-talk/
python3 "$SKILL_DIR/scripts/measure_deck.py" ./my-talk/ \
  --viewports 1920x1080,1280x720,3840x2160 --themes light,dark
```

측정에는 FAIL 항목이 없어야 하며 해결하지 않은 UNDERFILL 항목도 없어야 합니다. 경고는 실제 문맥에 맞게 수정하세요. 정적 검사가 깨끗하다고 상호작용이나 사실의 정확성이 증명되지는 않습니다.

공유 전에 다음을 확인합니다.
- 브라우저가 실행되고 모든 CSS, 스크립트, 이미지, iframe이 로드됩니다.
- 모든 인터랙티브/Canvas 슬라이드를 1920 × 1080과 3840 × 2160에서 확인하며, Canvas의 모든 단계를 양방향으로 진행합니다.
- 탭, 퀴즈 정답/오답, 슬라이더, 초기화, 키보드/포커스/터치 기반 설명을 테스트합니다.
- 양쪽 테마, 전체 화면, 발표자 동기화, 마지막 목차 링크를 확인합니다.
- 기술 주장을 공식 출처로 확인하고 예시 숫자를 표시하며 비밀값이나 민감한 계정 정보를 검사합니다.
- 실제 내보내기에서 최종 상태의 가독성, 노트, 차트 레이블, 출처를 확인합니다.
- 숫자 점수만이 아닌 **콘텐츠 리뷰 PASS**를 받습니다. 일반 100점 척도에서는 점수 ≥85, Critical 0, Warning ≤3이어야 합니다. Visual Testing 면제 대상은 문서화된 90점 척도를 사용하고 면제 사실을 명시합니다. 사용할 수 없는 도구를 통과한 테스트로 취급하지 마세요.

“./my-talk/의 콘텐츠를 리뷰하고 척도, 발견 사항, 판정을 알려 줘”라고 요청하세요. 공개 전 발견 사항을 해결하고 다시 리뷰합니다.

## 내보내기와 기존 덱 {#tools-and-exports}

생성된 목차에는 PDF, ZIP, PPTX 내보내기 컨트롤이 있지만 보존하는 내용은 서로 다릅니다.

- **브라우저 PDF:** 인쇄 과정에서 Canvas 그림을 숨기고 인터랙티브 애니메이션 플레이스홀더로 대체합니다. Canvas의 마지막 단계를 보존하지 않습니다. 완성된 그림을 정적 사본에 넣어야 한다면 검증한 스크린샷 기반 경로를 사용하세요.
- **브라우저 ZIP:** 헬퍼는 상위 디렉터리에 common이 있는 예전 구조를 가정하며 Archify iframe 문서를 수집하지 않습니다. 이 가이드의 프로젝트를 그대로 옮길 수 있는 압축본으로 신뢰하지 마세요. 생성된 전체 트리와 자산을 직접 압축하고, 압축을 푼 뒤 상대 경로와 동작을 다시 확인합니다.
- **브라우저 PPTX:** CDN의 html2canvas와 PptxGenJS를 사용하므로 오프라인 발표 전에 의존성 접근을 확인하세요.

Remarp 원본과 노트를 포함한 전체 샘플 프로젝트는 Python 표준 ZIP 도구로 압축할 수 있습니다. 공유 전에 원본과 노트에 민감한 정보가 없는지 검사하세요.

```bash
python3 -m zipfile -c ./my-talk.zip ./my-talk/
```

더 안정적인 스크린샷 기반 PowerPoint 내보내기는 다음과 같습니다.

```bash
# Use your project's approved Python environment.
python3 -m pip install 'playwright>=1.40' 'python-pptx>=1.0'
python3 -m playwright install chromium
python3 "$SKILL_DIR/scripts/export_pptx.py" ./my-talk/ -o ./my-talk.pptx
```

직접 만들고 신뢰하는 덱만 내보내세요. 캡처 중 HTML/JavaScript가 실행되기 때문입니다. fragment는 모두 표시하고 Canvas는 마지막 단계로 캡처하며 발표자 노트도 유지합니다. 결과 PowerPoint에서 퀴즈 선택, 탭, 시뮬레이션, 상세 패널은 동작하지 않습니다. 선택된 상태를 점검하고 필수 설명을 보이게 유지하세요. 편집 가능한 개체가 필요하면 네이티브 PowerPoint 스킬을 선택합니다.

내보낸 노트에 Archify 링크를 넣으려면 플레이스홀더를 실제 배포된 덱 위치로 바꿉니다.

```bash
python3 "$SKILL_DIR/scripts/export_pptx.py" ./my-talk/ -o ./my-talk.pptx \
  --base-url "https://YOUR_USER.github.io/YOUR_REPO/my-talk/"
```

기존 PowerPoint로 시작하려면 다음 명령을 사용합니다.

```bash
python3 "$SKILL_DIR/scripts/convert_to_remarp.py" ./existing-deck.pptx \
  -o ./converted-talk/ --lang ko
```

변환은 시작점이지 애니메이션이나 레이아웃 보존을 보장하지 않습니다. PDF 입력에는 PyMuPDF도 필요하며 이미지 배경과 추출 텍스트를 사용합니다. Remarp를 검토하고 다듬은 뒤 청중 설명과 상호작용을 추가하고 검증/빌드합니다. 변환기의 force 옵션은 백업을 남기며 덮어쓰므로 승인 없이 사용하지 마세요.

## 전체 덱 공개 {#publish-the-complete-deck}

다른 사람이 발표한다면 덱 링크와 함께 [발표자 안내와 인수인계 양식](../presenter-guide.md#author-handoff)을 보내세요. 청중, 시간, 슬라이드별 발표 설명, 정확한 조작 순서, 퀴즈 해설, 확인한 초기화 방법, 검증한 정적 백업을 포함합니다. 작성자에게 익숙한 덱도 다음 발표자에게는 진행표가 필요합니다.

생성된 HTML, common/, 프로젝트 로컬 자산, archify/를 함께 공개합니다. 저장소의 Pages 하위 경로에서도 상대 경로가 맞아야 합니다. 인증 없는 상태로 배포된 덱을 확인하고 목차, 모든 블록 링크, 내보내기를 검증하세요.

생성 요청이 배포 승인은 아닙니다. 커밋하거나 push하기 전에 대상 저장소/사이트, 공개 범위, 덮어쓰기 범위를 확인합니다. 해당 저장소의 기존 GitHub Pages 작업 흐름을 사용하거나 원하는 출력에 맞게 Pages를 설정하세요. 플러그인 마켓플레이스의 문서 배포가 별도의 발표 덱까지 공개한다고 가정하지 마세요. 승인 없이 민감한 원본 자료와 노트를 공개 사이트에 올리지 않습니다.

## 문제 해결 {#troubleshooting}

| 증상 | 확인과 해결 |
| --- | --- |
| 슬라이드가 없거나 빈 장이 생김 | 블록 frontmatter에 Remarp 표시를 넣고, 슬라이드 구분선과 메타데이터/디렉티브를 구분합니다 |
| 블록 빌드 후 합쳐진 덱이 예전 상태임 | 전체 sync를 실행합니다. 블록 빌드는 index와 목차를 갱신하지 않습니다 |
| 업그레이드 후 스크립트 경로가 사라짐 | 예전 캐시 버전 대신 현재 설치된 절차 경로를 찾습니다 |
| 출력 분리 후 로고/이미지가 없음 | 사용자 자산을 복사하고 각 출력 페이지 기준의 상대 경로를 확인합니다 |
| CRITICAL DETAIL_REF | 같은 장의 트리거/상세 ID를 맞추고 중복을 제거합니다 |
| CRITICAL Canvas 복잡도 또는 겹침 | 좌표를 다시 계산하고 그룹/큰 그림은 HTML/CSS 또는 Archify로 옮깁니다 |
| Archify 체크아웃을 찾지 못하거나 거부함 | ARCHIFY_DIR, Node.js, 스킬이 관리하는 고정 커밋을 확인합니다. 검증을 우회하지 않습니다 |
| Chromium을 실행할 수 없음 | 로컬 Playwright 패키지와 맞는 실행 파일을 확인합니다. MCP 준비 상태는 별개입니다 |
| 클릭이나 마우스 올리기가 동작하지 않음 | 펜/확대경 모드를 종료하고 iframe 포커스를 확인합니다 |
| 발표 제어 키가 예상과 다름 | 현재 N/P 기본값과 사용자 키 매핑을 대조합니다 |
| 글자가 잘리거나 밀도가 맞지 않음 | 생성 HTML을 수정하지 말고 측정 결과에 따라 내용/레이아웃을 수정합니다 |
| 내보내기에서 상호작용이나 상세 설명이 사라짐 | 정적 사본의 한계입니다. 필수 정보를 화면에 남기고 웹 덱 링크를 제공합니다 |

컴파일러에는 watch 또는 출력 형식 옵션이 없습니다. 옵션을 추측하지 말고 도움말과 [CLI 레퍼런스](/docs/remarp-guide/build-cli)를 사용하세요.

## 추가 참고와 데모 {#further-reading}

- [Remarp 빠른 시작](/docs/remarp-guide/quick-start), [frontmatter](/docs/remarp-guide/syntax/frontmatter), [디렉티브](/docs/remarp-guide/syntax/directives), [CLI](/docs/remarp-guide/build-cli).
- [Fragment](/docs/remarp-guide/syntax/fragments), [Canvas DSL](/docs/remarp-guide/syntax/canvas-dsl), [발표자 노트](/docs/remarp-guide/syntax/speaker-notes), [키보드 레퍼런스](/docs/remarp-guide/keyboard-shortcuts).
- [VS Code 확장과 Design Studio](/docs/remarp-guide/vscode-extension), [테마 추출](/docs/remarp-guide/themes/pptx-extraction), [디자인 토큰](/docs/remarp-guide/themes/css-variables).
- [기본 발표 데모](../demos/basic-presentation.mdx), [전체 기능 데모](../demos/full-presentation-demo.mdx). 동결된 데모는 기능 예시이며, 현재 버전의 검증 통과를 증명하지는 않습니다.
- [유지보수되는 스킬과 작성 자료](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-content-plugin/skills/reactive-presentation/SKILL.md), [Archify 블록 규약](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-content-plugin/skills/reactive-presentation/references/remarp-format-guide.md#archify--explorable-archify-diagram-adr-020), [콘텐츠 리뷰 평가표](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-content-plugin/agents/content-review-agent.md).
