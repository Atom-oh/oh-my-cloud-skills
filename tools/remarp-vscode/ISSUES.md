# Remarp VSCode Extension Issues

## How to Add Issues

각 이터레이션 후 아래 형식으로 이슈를 추가하세요.
스킬이 이 문서를 파싱하여 Open 이슈를 자동으로 처리합니다.

### Issue Format

```markdown
### ISSUE-NNN: [제목]
- **Category**: preview | visual-editor | completions | detection | navigation | build
- **Severity**: critical | major | minor
- **Affected**: `src/file.ts` (line ~100)
- **Description**: 문제 설명
- **Expected**: 기대 동작
- **Screenshot**: (optional) 스크린샷 파일명
```

### Categories

| Category | Target Files |
|----------|-------------|
| preview | `src/preview.ts`, `src/htmlPreview.ts` |
| visual-editor | `src/visualEditor.ts`, `src/cssEditor.ts`, `src/canvasEditor.ts`, `media/edit-mode.js`, `media/canvas-editor.js` |
| completions | `src/completions.ts` |
| detection | `src/extension.ts` (file detection, language ID switching) |
| navigation | `src/preview.ts` (slide nav, scroll sync) |
| build | `package.json`, `tsconfig.json`, packaging |

---

## Open

(현재 오픈된 이슈 없음)

---

## In Progress

(수정 중인 이슈가 여기로 이동)

---

## Resolved

### ISSUE-001: Edit 모드에서 내부 레이어 선택 불가
- **Category**: visual-editor
- **Severity**: major
- **Affected**: `media/edit-mode.js` (line ~134)
- **Description**: 중첩된 `[data-remarp-id]` 요소에서 내부 레이어를 클릭하면 외부 요소의 `_setupDrag` mousedown 핸들러가 먼저 발동되어 드래그를 시작하므로, 내부 요소를 선택할 수 없었음
- **Expected**: 내부 레이어 클릭 시 해당 요소가 선택되어야 함
- **Fix**: mousedown에서 클릭 대상이 중첩된 `[data-remarp-id]`인지 확인하여, 내부 요소면 드래그 대신 `selectElement(innerTarget)` 호출

### ISSUE-002: 프리뷰 탭 제목에 파일명 미표시
- **Category**: preview
- **Severity**: minor
- **Affected**: `src/preview.ts` (line ~56)
- **Description**: 프리뷰 패널 제목이 "Remarp Preview"로 하드코딩되어 어떤 파일의 프리뷰인지 구분 불가
- **Expected**: "Remarp Preview - filename.md" 형태로 파일명 표시
- **Fix**: `createOrShow`에서 `path.basename(document.uri.fsPath)`를 사용하여 패널 생성 및 재사용 시 모두 파일명 포함 제목 설정

### ISSUE-003: preview에서 이미지 렌더링 안되는 문제
- **Category**: preview
- **Severity**: major
- **Affected**: `src/preview.ts` (line ~349)
- **Description**: 마크다운 프리뷰에서 상대 경로 이미지가 렌더링되지 않음. `_renderMarkdown` 반환 HTML의 `<img src>` 상대 경로가 webview URI로 변환되지 않아 보안 정책에 의해 차단됨
- **Expected**: 상대 경로 이미지가 webview에서 정상 렌더링
- **Fix**: `_getHtmlForSlide`에서 `_renderMarkdown` 반환 후 `<img src>` 상대 경로를 `asWebviewUri()`로 변환

### ISSUE-004: Canvas "preview unavailable" 대신 프롬프트 내용 표시
- **Category**: preview
- **Severity**: minor
- **Affected**: `src/preview.ts` (line ~1443)
- **Description**: Canvas 블록이 "preview unavailable" 메시지만 표시하여 DSL 소스 내용을 확인할 수 없었음
- **Expected**: Canvas DSL 소스 코드가 `<pre>` 블록으로 표시되어 내용 확인 가능
- **Fix**: canvas case에서 HTML-escaped DSL 소스를 `<pre class="canvas-source">` 블록으로 표시

### ISSUE-005: HTML title에 파일명 미표시
- **Category**: preview
- **Severity**: minor
- **Affected**: `src/preview.ts` (lines ~322, ~411)
- **Description**: 웹뷰 HTML 문서의 `<title>` 태그가 "Remarp Preview"로 하드코딩. ISSUE-002에서 패널 탭 제목은 수정했으나 HTML 내부 title은 미수정
- **Expected**: `<title>Remarp Preview - filename.md</title>` 형태로 파일명 포함
- **Fix**: `_getEmptyHtml`과 `_getHtmlForSlide`의 `<title>` 태그에 `path.basename()` 사용하여 파일명 포함
