---
sidebar_position: 1
title: "Remarp"
---

{/* 영문 개편 전의 기존 섹션 링크를 유지합니다. */}
<span id="remarp-소개" />
<span id="왜-remarp인가" />
<span id="비교표" />
<span id="핵심-장점" />
<span id="1-사람이-읽을-수-있는-마크다운" />
<span id="2-프래그먼트-애니메이션" />
<span id="3-canvas-dsl" />
<span id="4-스피커-노트--타이밍" />
<span id="5-pptx-테마-통합" />
<span id="6-멀티파일-프로젝트" />
<span id="7-인터랙티브-패턴" />
<span id="8-vscode-visual-edit" />
<span id="하위-호환성" />
<span id="다음-단계" />


# Remarp

Remarp는 Markdown을 브라우저 발표 자료로 만드는 형식입니다. 텍스트 파일에 내용과 발표자 노트를 작성하고 빌드하면 단계별 설명, 탭, 퀴즈, 다이어그램이 있는 슬라이드가 만들어집니다. **덱**은 발표에 쓰는 슬라이드 묶음입니다.

AI에게 초안을 만들게 하거나 VS Code/code-server에서 직접 수정한 뒤, 다른 발표자에게 발표 링크를 보낼 수 있습니다. 배포된 덱을 발표하는 사람에게는 제작 도구 대신 브라우저가 필요합니다.

## 내가 하려는 일부터 선택하기 {#choose-your-path}

| 하려는 일 | 먼저 볼 안내 | 알 수 있는 것 |
| --- | --- | --- |
| 다른 사람이 준 슬라이드로 발표 | [발표자 가이드](/docs/aws-content-plugin/presenter-guide) | 덱 열기, 공유할 창 선택, 노트 사용, 상호작용 진행 |
| AI로 첫 발표 자료 만들기 | [자세한 작성자 가이드](/docs/aws-content-plugin/skills/reactive-presentation) | 요청, 원본 준비, 빌드, 리허설, 내보내기 |
| Markdown 직접 작성 | [빠른 시작](./quick-start.md) | 원본 파일 생성과 컴파일러 실행 |
| VS Code/code-server에서 수정 | [편집기 가이드](./vscode-extension.md) | 적절한 확장 설치, 미리보기 선택, Studio가 지원하는 요소 편집 |
| 기존 슬라이드 한 장 수정 | [원본 편집 흐름](./workflow.md) | 해당 원본 찾기, 범위를 정해 수정, 다시 빌드하고 확인 |

처음부터 모든 지시문을 배울 필요는 없습니다. 위에서 한 경로를 골라 따라 하고, 특정 상호작용이 필요할 때 문법 레퍼런스로 돌아오세요.

## 무엇을 만들 수 있나요? {#what-you-can-make}

| 설명하려는 것 | 청중이 보거나 조작하는 것 |
| --- | --- |
| 처리 순서 이해 | 발표자가 내용이나 다이어그램을 한 단계씩 표시 |
| 대안 비교 | 탭이나 비교 컨트롤로 설명 전환 |
| 이해도 확인 | 퀴즈에서 답을 선택한 뒤 피드백 표시 |
| 원인과 결과 확인 | 슬라이더나 입력값을 바꾸면 작성된 시뮬레이션/계산 결과 변화 |
| 본문을 복잡하게 만들지 않고 배경 설명 | 용어의 짧은 설명이나 상세 패널 열기 |
| 아키텍처 탐색 | 작성된 다이어그램에서 경로 강조 또는 자체 탐색 컨트롤 사용 |

모든 슬라이드에 자동으로 추가되는 효과는 아닙니다. L200 입문 자료라면 이해하기 쉬운 상호작용 몇 가지에 집중하세요. 상황을 설명하고, 결과를 예측하게 한 뒤, 한 가지를 바꾸고 결과를 이야기하는 식입니다.

주된 결과물은 **브라우저에서 여는 HTML**입니다. 스크린샷 기반 PowerPoint는 캡처한 모양을 보존하지만 탭, 퀴즈, 시뮬레이션은 동작하지 않습니다. PowerPoint의 텍스트와 도형을 직접 편집해야 한다면 [aws-light-fcd](/docs/aws-content-plugin/skills/aws-light-fcd)를 사용하세요. 정적인 백업을 고르기 전에는 [내보내기 안내](/docs/aws-content-plugin/skills/reactive-presentation#tools-and-exports)를 확인합니다.

## 작성 방식 {#authoring-model}

프런트매터에 `remarp: true`가 지정된 `.md` 파일을 사용합니다. 짧은 덱은 단일 파일로 작성하고, 긴 발표는 `_presentation.md`와 번호순 블록 파일로 구성합니다. 기존 소스와 편집기 연동을 위해 `.remarp.md`도 계속 지원합니다.

**프런트매터**는 원본 파일 맨 위에서 구분선으로 감싼 설정 부분입니다. Remarp 문서임을 표시하고 제목, 언어, 테마, 발표 블록 등을 정합니다. **블록**은 슬라이드 여러 장을 묶은 단위로, 긴 발표를 세션이나 주제별로 나눌 때 유용합니다.

슬라이드는 `---`로 구분합니다. `@type: tabs` 같은 지시문은 콘텐츠 앞에 둡니다. `{.click}`으로 내용을 단계별로 표시하고 `:::notes`에 발표 안내를 작성합니다. 작은 Canvas DSL의 범위를 넘는 레이아웃과 인터랙티브 도구에는 HTML/CSS/script 블록을 사용합니다.

여러 파일로 만든 프로젝트는 보통 다음과 같습니다.

```text
my-talk/
  _presentation.md   # Shared presentation settings and block list
  01-basics.md       # Slide content, interaction instructions and notes
  assets/           # Local logos, images and diagram specifications
  index.html        # Generated complete deck
  toc.html          # Generated session menu
  common/           # Generated runtime and styles
```

내용이나 발표자 노트를 바꾸려면 Markdown 원본을 수정합니다. 동작하는 덱을 전달할 때는 생성된 HTML과 리소스 폴더를 함께 유지하세요. 발표만 맡았다면 프로젝트를 다시 빌드하기보다 바로 열 수 있는 링크를 작성자에게 받습니다.

## 첫 발표 자료 한 번 만들어 보기 {#try-a-first-presentation}

### 1. 작고 구체적인 발표 요청하기 {#describe-your-talk}

AI 도구에 [콘텐츠 플러그인](/docs/aws-content-plugin/installation)을 준비한 뒤 다음처럼 요청합니다. 주제, 청중, 시간, 출력 위치를 원하는 값으로 바꿔 보세요.

> reactive-presentation으로 이 주제를 처음 접하는 개발자를 위한 15분짜리 L200 요청 처리 입문 자료를 만들어 줘. 지금 대화에서 쓰는 언어로 작성하고 ./my-talk/에 저장해 줘. 먼저 슬라이드 제목과 각 장에서 사용할 상호작용을 보여 줘.
>
> 직접 진행할 수 있는 3단계 설명, 비교 화면, 퀴즈 하나를 넣어 줘. 낯선 용어는 처음 나올 때 설명해 줘. 다른 사람이 발표할 수 있도록 각 장의 노트에 할 말, 키나 버튼을 누를 시점, 화면에서 바뀔 것, 다음 장으로 이어지는 말을 써 줘.
>
> 원본 검증과 빌드, 실제 브라우저 동작 확인, 콘텐츠 리뷰까지 하고 미리보기 링크와 발표 조작 안내를 알려 줘. 아직 공개하지는 마.

[완성된 예제를 직접 따라 만들기](/docs/aws-content-plugin/skills/reactive-presentation#first-deck)도 가능합니다. 원본 내용, 저장할 파일 위치, 빌드 명령이 함께 있습니다.

### 2. 받은 결과 확인하기 {#check-the-result}

원본 폴더, 생성된 발표 자료 또는 로컬 미리보기 링크, 상호작용에 대한 짧은 안내를 받으세요. 슬라이드 제목 목록만으로는 완성된 덱이 아닙니다.

받은 링크를 엽니다. 내용을 한 단계 진행했다가 되돌리고, 탭이나 퀴즈 하나를 조작하고, 독립된 슬라이드 창에서 **N**으로 노트를 열어 보세요. 청중에게 보여 줄 창과 리허설 방법은 [발표자 가이드](/docs/aws-content-plugin/presenter-guide#start-your-presentation)에 있습니다.

### 3. 한 가지를 구체적으로 수정하기 {#make-one-revision}

작성자나 AI에게 슬라이드 제목, 문제, 청중에게 어떻게 보였으면 하는지를 전달합니다. 예를 들어 다음과 같습니다.

> 요청 흐름 슬라이드에서 작업자를 보여 주기 전에 클라이언트가 무엇인지 먼저 설명해 줘. 세 동작은 한 번에 하나씩 표시하고, 청중에게 질문하며 멈출 시점을 발표자 노트에 넣어 줘. 테마, 다른 슬라이드, 퀴즈 정답은 유지하고 원본을 수정한 뒤 전체 덱을 다시 빌드해 줘.

다시 빌드한 뒤 생성된 발표 자료를 다시 열거나 새로고침합니다. 원본을 저장하면 모든 미리보기가 자동으로 바뀐다고 생각하지 말고 수정한 동작을 직접 확인하세요.

## 작업 흐름 {#workflow}

| 단계 | 하는 일 | 다음으로 가기 전 확인 |
| --- | --- | --- |
| 기획 | 청중, 시간, 메시지, 상호작용 결정 | 각 상호작용이 설명에 도움이 되는지 |
| 작성 | 원본, 노트, 로컬 자산 준비 | 다른 발표자도 노트를 따라갈 수 있는지 |
| 검증 | 원본 구조와 필수 작성 규칙 검사 | 컴파일을 막는 오류를 해결했는지 |
| 빌드 | HTML과 런타임 자산 생성 | 필요한 전체 덱과 세션 목차가 있는지 |
| 리허설 | 실제 브라우저 결과물 열기 | 키, 입력, 다이어그램, 노트, 테마가 의도대로 동작하는지 |
| 리뷰와 전달 | 품질 확인과 발표자 안내 준비 | 진행표와 확인한 백업을 전달했는지 |

수정은 원본에서 하고 다시 빌드합니다. 생성된 HTML을 계속 편집할 원본으로 삼지 마세요. Studio는 지원하는 시각적 콘텐츠 편집을 Markdown에 반영할 수 있지만 일반 미리보기에는 그 시각 편집 기능이 없습니다. 간이 텍스트 미리보기에서도 이슈 주석은 추가하거나 제거할 수 있습니다. [Marp 마이그레이션](./migration-from-marp.md)은 시작점을 만들 때 사용할 수 있으며 변환 결과도 검증과 리뷰가 필요합니다.

## VS Code와 code-server에서 사용하기 {#editor-and-code-server}

Remarp Slides 확장에는 서로 다른 세 화면이 있습니다.

| 화면 | 사용할 때 |
| --- | --- |
| Approximate Text Preview | 입력하면서 원본의 순서와 문장을 빠르게 확인 |
| Build and Preview Compiled HTML | 저장한 원본을 실제 컴파일러로 빌드해 확인 |
| Open Design Studio | 컴파일된 스냅샷을 보며 원본과 연결된 지원 요소를 선택하고 수정 |

실제 Remarp 원본 파일을 연 뒤 명령을 선택하세요. Studio의 Design은 선택/편집에, Play는 슬라이드 상호작용을 시험하는 데 사용합니다. Preview와 Studio는 별도 명령이므로 미리보기만 열었다고 시각적 편집이 켜지는 것은 아닙니다.

**code-server**에서는 브라우저로 편집기를 사용하더라도 확장과 Python 컴파일러가 서버에서 실행됩니다. 컴파일러 경로도 그 서버에 있어야 합니다. 데스크톱 VS Code에 설치한 확장이 code-server에 자동 설치되지는 않습니다. 설치된 확장 버전, 작업 영역 신뢰, 컴파일러 설정을 [편집기 단계별 안내](./vscode-extension.md)에서 확인하세요.

실제 발표와 최종 상호작용 확인에는 독립된 브라우저 덱을 사용합니다. 편집기 미리보기에는 팝업, 삽입된 문서, 리소스에 다른 제한이 있을 수 있습니다.

## 다른 사람에게 발표 맡기기 {#present-and-share}

덱 URL과 함께 청중과 시간, 시작할 슬라이드, 유용한 발표자 노트, 인터랙티브 장의 정확한 조작, 퀴즈 해설, 확인한 정적 백업을 전달하세요.

[바로 채워 보낼 수 있는 인수인계 문구와 진행표](/docs/aws-content-plugin/presenter-guide#author-handoff)를 사용합니다. 인터랙티브 장마다 **할 말 → 조작 → 바뀌어야 할 화면 → 초기화 방법 → 소요 시간**을 적으세요. 새 발표자가 완성된 그림만 보고 설명을 역으로 짐작하게 하지 않는 것이 중요합니다.

## 다음 단계 {#next-steps}

1. 지금 발표해야 한다면 [발표자 가이드](/docs/aws-content-plugin/presenter-guide)를 따라갑니다.
2. 첫 덱을 만든다면 [전체 작성 과정](/docs/aws-content-plugin/skills/reactive-presentation)을 사용합니다.
3. 브라우저 기반 개발 환경에서 편집한다면 [VS Code/code-server 안내](/docs/remarp-guide/vscode-extension)를 따릅니다.
4. 직접 작성하고 빌드한다면 [빠른 시작](/docs/remarp-guide/quick-start) 다음에 [빌드 CLI](/docs/remarp-guide/build-cli)를 확인합니다.

## 관련 링크 {#related-links}

- [빠른 시작](./quick-start.md)
- [프런트매터](./syntax/frontmatter.md)
- [VS Code와 code-server](./vscode-extension.md)
- [Canvas DSL](./syntax/canvas-dsl.md)
