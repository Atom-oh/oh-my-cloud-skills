---
sidebar_position: 11
title: "VS Code와 code-server"
---

{/* 영문 개편 전의 기존 섹션 링크를 유지합니다. */}
<span id="vscode-확장" />
<span id="기능" />
<span id="구문-하이라이팅" />
<span id="라이브-프리뷰" />
<span id="visual-edit-모드" />
<span id="canvas-editor" />
<span id="css-writeback" />
<span id="canvas-writeback" />
<span id="이슈-어노테이션--ai-리뷰" />
<span id="html-파일-지원" />
<span id="문서-아웃라인" />
<span id="intellisense" />
<span id="설치-방법" />
<span id="vs-code-marketplace에서-설치" />
<span id="vsix에서-설치-로컬" />
<span id="개발-모드" />
<span id="사용법" />
<span id="키보드-단축키" />
<span id="슬라이드-네비게이션" />
<span id="프리뷰-내-네비게이션" />
<span id="명령어" />
<span id="설정" />
<span id="예제" />
<span id="요구-사항" />
<span id="알려진-제한-사항" />
<span id="marketplace-배포" />
<span id="사전-준비" />
<span id="1-publisher-생성" />
<span id="2-패키지--배포" />
<span id="3-버전-업데이트" />


# VS Code와 code-server

**Remarp Slides**로 발표 원본을 편집하고, 컴파일된 슬라이드를 확인하거나 Design Studio를 열 수 있습니다. 이 안내는 덱을 만들거나 수정하는 사람을 위한 것입니다. 발표할 자료를 전달받았다면 확장 설치 없이 [발표자 가이드](/docs/aws-content-plugin/presenter-guide)를 사용하세요.

## 먼저 버전 확인하기 {#check-your-version}

확장 버전은 cloud-skills 플러그인 버전과 별개입니다. 편집기의 **Extensions**에서 **Remarp Slides**를 열어 게시자, 버전, 설치 위치를 확인하세요.

| 패키지 | 리뷰에서 확인한 내용 |
| --- | --- |
| 저장소에 들어 있는 0.1.0 VSIX | Design Studio 명령이 없는 이전 패키지 |
| 현재 저장소 소스 0.2.0 | Studio와 두 미리보기 명령, 수동 AI 전달 지원. code-server의 실제 호스트에서는 Studio 메시지/리소스 전달 문제가 있음 |
| 별도로 검토한 로컬 0.3.0 개발 빌드 | 새로운 code-server 렌더러와 명시적 AI 생성 지원. main의 0.2.0 소스와 다르며 이 문서는 공개 출시를 보증하지 않음 |

code-server에서 Studio를 쓰려면 유지보수자가 실제 code-server Extension Host에서 확인한 빌드를 받으세요. 예전 VSIX를 설치하고 Studio가 있을 것이라고 생각하거나, 예제 파일명에 맞추려고 더 최신 설치본을 낮추지 마세요. 설치본의 명령이 다르면 아래 모든 기능이 있다고 가정하기보다 설치된 매니페스트와 비교합니다.

0.3.0 개발 빌드에는 [리뷰에서 확인한 문제](#reviewed-limitations)가 남아 있습니다. 기본 동작 테스트를 통과했다고 완성된 릴리스가 되는 것은 아닙니다.

## 실제 사용하는 편집기에 설치하기 {#install-in-your-editor}

1. 유지보수자에게 사용할 VSIX를 받고 버전을 확인합니다.
2. **데스크톱 VS Code**에서는 그 컴퓨터의 Extensions 메뉴에서 **Install from VSIX...** 명령을 사용합니다.
3. **code-server**에서는 브라우저 편집기 안에서 같은 명령을 사용합니다. 서버의 설치 과정에서 해당 파일에 접근할 수 있어야 합니다. 데스크톱 VS Code 설치가 code-server 설치를 대신하지는 않습니다.
4. **Developer: Reload Window**를 실행하고 그 편집기에서 Remarp Slides가 활성화되었는지 확인합니다.

code-server 호스트에 VSIX를 전달받았다면 그 서버의 터미널에서도 설치할 수 있습니다.

```bash
code-server --install-extension /absolute/path/to/remarp-vscode.vsix
code-server --list-extensions --show-versions
```

확장 ID는 **aws-cloud-skills.remarp-vscode**입니다. VSIX는 편집기 확장 패키지이며 슬라이드 덱이나 Claude/Codex 플러그인이 아닙니다. 특정 버전이 Marketplace에 올라가 있다는 사실은 이 저장소만으로 확인할 수 없습니다.

## 원본 파일 열고 컴파일러 연결하기 {#open-and-configure}

1. 발표 원본이 있는 폴더를 엽니다. 다중 파일 프로젝트라면 발표 설정과 번호가 붙은 블록들이 있는 폴더를 엽니다.
2. 실제 슬라이드 Markdown 원본을 편집기에서 엽니다. 새 파일은 빌드나 Studio를 쓰기 전에 한 번 저장합니다. 인식하는 파일명과 Remarp 프런트매터는 [지원 범위](#boundaries)를 참고하세요.
3. 언어 표시가 **Remarp**인지 확인합니다. 프런트매터를 넣었는데 계속 Markdown이면 저장한 뒤 필요할 때 언어 선택기에서 Remarp를 선택합니다.
4. 빌드와 Studio에는 신뢰하는 작업 영역과 **확장 호스트**에서 실행할 수 있는 Python 3가 필요합니다. code-server에서는 노트북이 아니라 서버를 뜻합니다.
5. 자동 탐색으로 원하는 컴파일러를 찾지 못하면 경로를 지정합니다.

편집기 설정에서 **Remarp Build Script Path**를 검색하거나, 적절한 사용자/원격 설정 JSON에 아래 경로를 실제 값으로 바꿔 넣습니다.

```json
{
  "remarp.buildScriptPath": "/absolute/path/to/oh-my-cloud-skills/plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py"
}
```

확장이 실행되는 호스트에 실제로 있는 경로를 사용하세요. 확장이 Python을 설치하거나 컴파일러를 포함하지는 않습니다. Studio용 컴파일러는 studio 명령을 지원해야 합니다. 자동 탐색은 주변/작업 영역의 스크립트, 작업 영역의 플러그인 디렉터리, 제한된 상위 디렉터리를 확인하며 모든 Claude/Codex 플러그인 캐시를 찾는다고 보장하지 않습니다.

## 맞는 화면 선택하기 {#choose-a-view}

편집기 메뉴나 **F1**, 브라우저에서 허용하는 **Ctrl+Shift+P / Command+Shift+P**로 Command Palette를 엽니다. 아래 명령 제목을 검색하세요.

| 명령 제목 | 사용할 때 | 저장/빌드 동작 |
| --- | --- | --- |
| Remarp: Approximate Text Preview | 문장, 슬라이드 순서, 노트, 이슈 주석을 빠르게 확인 | 입력하며 갱신. 최종 컴파일 결과와 같은 레이아웃은 아님 |
| Remarp: Build and Preview Compiled HTML | 실제 생성된 슬라이드와 런타임 확인 | 관련 원본을 저장하고 빌드해 결과를 엶. 수정 뒤 다시 실행 |
| Remarp: Open Design Studio | 원본과 연결된 지원 요소를 선택하고 수정 | 원본 버퍼의 임시 스냅샷을 빌드. 지원되는 편집은 버퍼에 반영되며 저장은 직접 수행 |

컴파일 미리보기에는 Studio의 시각적 원본 편집이 없습니다. 간이 미리보기는 이슈 주석을 쓸 수 있으므로 모든 미리보기 조작이 읽기 전용이라고 생각하지 마세요. code-server의 Studio는 버전 설명에 따라 검증한 빌드를 사용합니다.

## Design Studio에서 첫 수정하기 {#first-studio-edit}

1. 원본을 열고 **Remarp: Open Design Studio**를 실행한 뒤 스냅샷 컴파일 성공을 기다립니다. 실패하면 진단 메시지를 확인하세요. 오래된 미리보기가 남아 있어도 편집 준비가 된 것은 아닙니다.
2. **Slides**에서 장을 고르고 **Layers** 또는 슬라이드 오버레이에서 편집 가능한 요소를 선택합니다.
3. **Selection**의 **Text / Markdown** 등 표시되는 필드를 수정합니다. 요소가 연결된 원본에 따라 필드가 달라집니다. 처음에는 짧은 제목을 일반 텍스트로 바꿔 보세요.
4. 필드 밖을 클릭해 편집을 반영합니다. 다시 그려진 미리보기와 바뀐 Markdown 버퍼를 함께 확인합니다. **Reveal in source**로 해당 원본을 찾을 수 있습니다.
5. **Undo**로 되돌릴 수 있는지 확인합니다. 원하는 상태가 되면 원본을 직접 저장합니다.
6. **Play**로 슬라이드 상호작용을 시험하고 **Design**으로 돌아와 선택/편집합니다. Play에서 이동하기 전에 아직 제출하지 않은 제안은 마무리하거나 따로 복사해 두세요.
7. 전체 발표 자료를 빌드한 뒤 독립된 브라우저에서 확인하고 발표하거나 공유합니다.

원본 옆의 Studio가 좁다면 편집기 그룹을 넓히거나 두 그룹 사이의 분할 폭을 조정하세요. **Zoom / Fit**은 편집기에서 보이는 크기를 바꾸며 덱의 화면 비율이나 글꼴을 바꾸지 않습니다.

### 시각적으로 수정할 수 있는 것 {#editable-elements}

| 요소 | 지원하는 편집 |
| --- | --- |
| 원본과 연결된 제목/카드 | 텍스트와 첫 번째 안전한 카드 본문 구간. 해당 필드가 있을 때 사용 |
| 선택한 요소의 로컬 스타일 | 허용된 색상, 글자 크기/굵기, 안쪽 여백, 아래 여백, 모서리 반경 |
| 슬라이드 설정 | 제공되는 fit, columns, layout 선택 |
| 단순 Canvas 박스/아이콘 | 지원 범위의 위치, 크기, 레이블, 표시 단계 |
| 복잡한 HTML, 화살표, 서비스 아이콘 이름, 지원하지 않는 구조 | Reveal in source로 원본에서 직접 편집 |

아무 요소나 끌어 놓는 자유 배치 도구는 아닙니다. 필드가 없다고 내용이 사라진 것은 아니며, 원본의 해당 구간을 안전하게 시각 편집할 수 없다는 뜻일 수 있습니다. 특히 검토한 개발 빌드에서는 Markdown 구조 변경을 원본 편집기에서 하세요.

원본/설정 변경은 스냅샷 재빌드를 일으킵니다. 이미지나 다른 자산을 바꾼 뒤에는 **Refresh**를 사용합니다. Studio가 배포된 HTML을 자동 교체하지는 않습니다. 재빌드가 실패하면 마지막으로 성공한 스냅샷을 남기고 시각 편집을 비활성화할 수 있습니다.

## AI에게 한 장 개선 요청하기 {#ai-editing}

### 현재 저장소 소스에서 쓰는 수동 전달 {#manual-ai-handoff}

1. 슬라이드를 선택하고 구체적인 개선 요청을 입력합니다.
2. **Copy AI request**를 누릅니다. 선택한 원본과 요청을 클립보드에 복사하며 AI 서비스를 호출하지는 않습니다.
3. 사용하는 AI 도구에 붙여 넣고 해당 슬라이드의 대체 원본만 요청합니다.
4. 받은 원본을 **Selected slide source / AI response**에 붙여 넣습니다.
5. **Preview candidate & diff**로 후보와 원본 차이를 확인한 뒤 **Apply proposal** 또는 **Reject**를 선택합니다.
6. 바뀐 원본을 확인하고 원하는 상태가 되면 저장합니다.

예를 들어 “기술적 의미, 발표자 노트, 표시 순서를 유지하면서 두 카드의 문장을 줄여 줘”라고 요청할 수 있습니다. 장을 바꾸기 전에 아직 제출하지 않은 응답은 별도로 복사해 두세요.

### 검토한 0.3.0 개발 빌드의 명시적 생성 {#development-ai-generation}

이 절은 설치본에 **Generate with AI**가 있을 때만 적용합니다. 현재 저장소의 0.2.0에는 이 버튼이 구현되어 있지 않습니다.

장과 제공자를 고르고 요청을 입력한 뒤 **Generate with AI**를 누릅니다. 개발 빌드는 선택한 Claude, Kiro, Codex CLI를 확장 호스트에서 실행합니다. Studio를 여는 것만으로 생성이 시작되지는 않습니다. 생성을 실행하면 선택한 원본이 해당 제공자에게 전달되며 사용량이 소모되거나 요금이 발생할 수 있습니다.

**AI settings**는 관련 편집기 설정을 엽니다. CLI 실행 파일과 인증은 code-server 호스트에서 확장과 같은 사용자에게 준비되어 있어야 합니다. 확장이 CLI를 설치하거나 로그인하지는 않습니다. 모델과 effort 지원 범위는 제공자와 CLI에 따라 다르며 모델을 비워 두면 기본값을 사용합니다.

**Apply proposal** 전에 컴파일된 후보와 diff를 확인합니다. **Cancel AI**는 진행 중인 요청을 멈추고 **Reject**는 원본을 유지합니다. 제안 적용은 원본 버퍼 편집이며 덱을 자동 저장하거나 공개하는 동작이 아닙니다. 실제 호스트 리뷰에서는 가짜 제공자 CLI로 이 흐름을 검증했으며, 실제 계정 인증이나 모델 접근까지 검증한 것은 아닙니다.

## 로컬 설정 {#local-setup}

선택한 소스 체크아웃에서 확장을 빌드하는 사람을 위한 절입니다. 결과물을 기존 설치본 위에 설치하기 전에 그 체크아웃의 패키지 버전을 확인하세요.

```bash
cd tools/remarp-vscode
npm ci
npm run compile
npx @vscode/vsce package --no-dependencies --out /tmp/remarp-vscode.vsix
```

패키징 도구가 설치되어 있지 않으면 패키징 중 다운로드할 수 있습니다. 또는 데스크톱 VS Code에서 확장 프로젝트를 열어 Extension Development Host로 실행합니다. 어느 방법이든 code-server에서 동작한다는 증명은 아니므로 실제 사용할 호스트에서도 확인하세요.

## 명령과 단축키 {#commands-and-shortcuts}

| 명령 ID | 기능 |
| --- | --- |
| `remarp.studio` | Design Studio 열기 |
| `remarp.preview` | 간이 텍스트 미리 보기 열기 |
| `remarp.previewCompiled` | 저장·빌드 후 컴파일된 HTML 미리 보기 |
| `remarp.nextSlide` | 다음 슬라이드로 이동 |
| `remarp.prevSlide` | 이전 슬라이드로 이동 |
| `remarp.build` | HTML 빌드 |
| `remarp.submitIssues` | slide-fix 가이드 표시 |

매니페스트에는 편집기 언어가 Remarp일 때 원본 슬라이드 탐색에 사용하는 Ctrl/Cmd+Shift+Right와 Left, 빌드에 사용하는 Ctrl/Cmd+Shift+B가 등록되어 있습니다. 과거 문서에 있던 Ctrl/Cmd+Shift+E는 등록되어 있지 않습니다. 이는 편집기 단축키이며 [브라우저 발표 조작](/docs/aws-content-plugin/presenter-guide#essential-controls)과 다릅니다. 브라우저가 키를 가로채면 편집기 메뉴나 Command Palette를 사용하세요.

## 설정 {#settings}

| 설정 | 기본값 | 목적 |
| --- | --- | --- |
| `remarp.buildScriptPath` | 비어 있음 | 자동 탐색보다 우선하는 변환기의 명시적 절대 경로 |
| `remarp.scrollSync` | true | 소스 커서와 미리 보기 슬라이드 동기화 |

현재 소스 0.2.0에는 `remarp.autoPreview`와 `remarp.buildOnSave`가 등록되어 있지 않습니다. 개발 빌드에 AI 설정이 더 있다고 이전 설치본에도 같은 설정이 있는 것은 아닙니다.

## 편집과 이슈 {#editing-and-issues}

미리 보기는 노트와 슬라이드별 이슈 주석을 제공합니다. `<!-- issue: ... -->`로 slide-fix에 전달할 수정 요청을 기록합니다. **Show Slide Fix Guide**는 전달 방법을 안내하며 AI 리뷰어를 자동 실행하거나 수정을 적용하지 않습니다. AI 도구에서 [slide-fix](/docs/aws-content-plugin/skills/slide-fix)를 사용하고 원본을 검증해 다시 빌드하세요.

발표 화면의 브라우저 전용 노트 편집과 확장 원본 편집은 별개입니다. 브라우저에서 바꾼 노트는 확장이 여는 Markdown을 갱신하지 않습니다.

## 첫 실행에서 막혔을 때 {#troubleshooting}

| 증상 | 다음 확인 |
| --- | --- |
| Open Design Studio 명령이 없음 | 설치 버전과 편집기 위치 확인. 저장소의 0.1.0 VSIX에는 Studio가 없습니다. 원하는 패키지 설치 뒤 편집기를 다시 로드합니다 |
| Markdown 파일을 인식하지 못함 | Remarp 파일명/프런트매터, 최초 저장 여부, 언어 모드 확인 |
| 컴파일러를 찾지 못함 | 서버의 명시적 컴파일러 경로와 Extension Host에서 실행 가능한 Python 3 확인 |
| studio 명령을 모른다는 오류 | 설정된 컴파일러가 Studio 인터페이스보다 오래됨. 맞는 컴파일러 선택 |
| code-server에서 Studio가 계속 빈 화면 | 설치 버전과 진단 확인. main 0.2.0에는 실제 호스트의 시작 문제가 있으므로 검증된 새 빌드 또는 독립된 컴파일 덱 사용 |
| 원본을 고쳤는데 컴파일 미리보기가 그대로임 | Build and Preview Compiled HTML을 다시 실행. 이 패널은 계속 자동 빌드하지 않음 |
| 이미지를 고쳤는데 Studio가 예전 그림을 보여 줌 | Refresh 사용. 참조 자산은 프로젝트 안에 유지 |
| 필드나 다이어그램을 수정할 수 없음 | Reveal in source 사용. 모든 원본 구조에 안전한 시각 편집 기능이 있는 것은 아님 |
| AI 버튼이나 설정이 없음 | 버전 확인. 현재 소스 0.2.0은 클립보드 수동 전달 사용 |
| 개발 빌드에서 AI가 실패 | 서버의 CLI, 인증, 지원 옵션/모델, 시간 제한 확인. 노트북의 인증이 공유된다고 가정하지 않기 |

## 리뷰에서 확인한 제한 {#reviewed-limitations}

[날짜별 유지보수 리뷰 기록](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/docs/reference/2026-11-14-remarp-code-server-review.md)에서 현재 main 소스와 별도로 설치된 개발 빌드를 구분해 검토했습니다.

- **code-server의 main 0.2.0:** 브라우저 API를 모사한 테스트가 통과해도 Studio의 호스트 메시지와 중첩 리소스 전달이 실패할 수 있습니다. Studio에는 실제 호스트에서 확인한 패키지를 사용하고 최종 확인은 독립된 컴파일 덱에서 하세요.
- **로컬 0.3.0 카드 본문 편집:** 코드 펜스 같은 구조 문법이 뒤 슬라이드 구조를 바꿀 수 있습니다. 범위를 제한한 시각 편집에는 일반 텍스트를 쓰고 구조 변경은 원본에서 한 뒤 전체 덱을 검증하세요.
- **로컬 0.3.0 CSS import:** 따옴표를 쓴 로컬 import가 스테이징에서 빠져 Studio 렌더링을 막을 수 있습니다. 그 경로가 수정되기 전에는 직접 사용할 수 있는 스타일시트나 독립된 출력물을 사용하세요.
- **제출 전 제안 초안:** Play에서 이동하면 초안이 사라질 수 있습니다. 다른 장으로 가기 전에 따로 복사하거나 후보 확인/적용 결정을 마치세요.

이는 검토한 구현의 결과이며 모든 설치본이 같다는 뜻은 아닙니다. 개발 빌드의 Studio 렌더러도 임의의 중첩 문서와 동적인 로컬 리소스 로딩을 번들에 포함하지 않습니다. 삽입된 다이어그램과 최종 발표 동작은 독립된 덱에서 확인하세요.

## 지원 범위 {#boundaries}

확장은 `.remarp.md`, `_presentation.md`, `_presentation.remarp.md`와 `remarp: true`가 있는 `.md`를 인식합니다. 빌드는 변경된 프로젝트 소스를 저장한 뒤 프레젠테이션 설정 파일이 있는 디렉터리를 빌드합니다. **Build HTML**은 빌드만 하며, **Build and Preview Compiled HTML**은 프로젝트의 `index.html` 또는 컴파일러가 보고한 단독 소스 출력 파일을 엽니다. 단독 소스의 기본값은 보통 `slides/default.html`이지만 이름을 지정한 블록은 `slides/lesson.html`처럼 다른 경로를 사용할 수 있습니다. 저장·빌드 실패 시 오류를 표시하고 컴파일 미리 보기를 중단합니다. 빌드와 미리 보기 스크립트에는 작업 영역 신뢰가 필요합니다. 미리 보기·개요·탐색은 코드 펜스 안의 구분자를 무시합니다.

선언된 VS Code 최소 엔진은 1.85입니다. Node와 로컬 파일을 사용하는 호스트 확장이며 브라우저 탭 안에서만 독립 실행되는 편집기가 아닙니다. 발표자에게는 편집기 작업 공간 대신 브라우저 덱과 [발표 안내](/docs/aws-content-plugin/presenter-guide)를 전달하세요.

[명령, 설정과 키 바인딩](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/tools/remarp-vscode/package.json) · [편집기 구현](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/tools/remarp-vscode/src/)
