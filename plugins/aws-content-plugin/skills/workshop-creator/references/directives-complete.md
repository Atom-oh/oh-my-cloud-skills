# Workshop Studio Directives Complete Reference

Workshop Studio에서 지원하는 모든 Directive 문법 레퍼런스입니다. Alert/Code/Tabs/Image는 전용 레퍼런스 파일(`alert-reference.md`/`code-reference.md`/`tabs-reference.md`/`image-reference.md`)에 상세 문법이 있으니 이 문서에서는 요약만 다룹니다.

---

## Directive 기본 문법

Directive는 Markdown을 확장하여 더 풍부한 콘텐츠 경험을 제공합니다.

### 구성 요소

- **콜론 (`:`)**: Directive 시작
- **대괄호 `[]`**: 인라인 콘텐츠 (한 줄)
- **중괄호 `{}`**: 키/값 속성 (값에 공백이 없으면 인용부호 생략 가능)

```markdown
:directive[content]{key1="value1" key2='value2' key3=value3}
```

### Directive 유형 3가지

| 유형 | 콜론 개수 | 설명 |
|------|-----------|------|
| **Text** | `:` | 텍스트 흐름 안에 인라인으로 렌더링 |
| **Leaf** | `::` | 자체 블록으로 렌더링 (콘텐츠는 `[]` 안에) |
| **Container** | `:::` | 내부에 다른 마크다운 블록을 포함 가능 |

```markdown
Workshop Studio Wiki :link[여기]{href="https://example.com" external="true"}를 참조하세요.

::code[console.log('Hello world!');]{showCopyAction=true language="js"}

:::alert{type="success" header="성공"}
내용을 여기에 작성합니다.
:::
```

### 중첩 Directive (`::::`)

중첩 시 **외부 directive가 내부보다 더 많은 콜론**을 가져야 합니다 — 콜론 개수가 부족하면 파싱이 깨진다.

```markdown
::::tabs
:::tab{label="First"}
첫 번째 탭 내용
:::
:::tab{label="Second"}
두 번째 탭 내용
:::
::::
```

`code` 디렉티브를 tab 안에 넣는 등 3단 이상 중첩할 때는 콜론을 한 단계씩 늘린다 (`:::::tabs` → `::::tab` → `:::code`).

> ⚠️ **Hugo shortcode(`{{% notice %}}` 등)는 Workshop Studio에서 전혀 지원되지 않는다.** 반드시 위의 콜론 기반 directive 문법만 사용한다 — `workshop-agent.md`의 "CRITICAL: Correct Directive Syntax" 경고 참조.

### 확장 파싱(Extended Parsing) — 코드 블록/링크 href 안에서도 동작

일부 directive(`:param`, `:assetUrl`)는 일반 마크다운이 파싱되지 않는 영역(코드 블록 등)에서도 동작하도록, 마크다운 처리 이전에 먼저 값이 치환된다. 반대로 그 외 directive(`:button`, `[link](url)` 등)는 코드 블록 안에서 문자 그대로 표시된다.

---

## Alert

정보/경고 메시지. Leaf/Container만 지원 (Text 불가). 속성: `header`, `type`(`success`|`error`|`warning`|`info`, 기본 `"info"`). 상세: `alert-reference.md`

```markdown
::alert[간단한 메시지]{type="warning"}
```

## Code

코드/터미널 출력 블록. Text/Leaf/Container 모두 지원. 속성: `language`, `showLineNumbers`, `showCopyAction`, `copyAutoReturn`, `highlightLines`, `highlightLinesStart`, `lineNumberStart`. 상세: `code-reference.md`

```markdown
:::code{language=bash showCopyAction=true}
kubectl get pods -n vllm
:::
```

## Tabs / Tab

`Tabs`는 하나 이상의 `Tab`을 담는 Container 전용 directive (둘 다 Text/Leaf 불가). `Tabs` 속성: `activeTabId`, `variant`(`default`|`container`), `groupId`(여러 탭 그룹을 동기화). `Tab` 속성: `id`, `label`, `disabled`. **`Tabs` 자체에는 `labels` 배열 속성이 없다** — 각 라벨은 개별 `:::tab{label="..."}`에 지정한다. 상세: `tabs-reference.md`

```markdown
::::tabs{variant="container"}
:::tab{label="Console"}
콘솔 안내
:::
:::tab{label="CLI"}
CLI 안내
:::
::::
```

## Image

이미지 표시. Text만 지원. 속성: `src`, `width`(px 숫자), `height`(px 숫자), `disableZoom`, `title`. **`width`는 픽셀 숫자이며 `"90%"` 같은 퍼센트 문자열이 아니다.** `signedUrl` 같은 속성은 존재하지 않는다. 상세: `image-reference.md`

```markdown
:image[아키텍처]{src="/static/images/architecture.png" width=800}
```

---

## Param

contentspec.yaml의 `params` 값을 콘텐츠에서 참조. Text만 지원. 속성: `key`(점/배열 인덱스 표기 지원), `defaultValue`. 전역 값 `globals.baseUrl`/`globals.locale`도 사용 가능. 상세: `event-params-guide.md`

```markdown
클러스터 이름: :param{key="clusterName"}
```

## Asset URL

`/static` 또는 S3 assets 버킷의 자산에 대한 절대(서명) URL을 생성. **Text 전용** (Leaf/Container 불가) — 대괄호 없이 중괄호 속성만 사용한다. 속성: `path`(자산 상대 경로), `source`(`repo`|`s3`, 기본 `repo`). 코드 블록 등 마크다운이 파싱되지 않는 영역에서도 값이 먼저 치환되므로 `curl` 명령 등에 안전하게 쓸 수 있다. `&` 문자가 포함된 서명 URL이 셸에서 백그라운드 실행으로 해석되지 않도록, 이런 명령에서는 값을 단일 인용부호로 감싼다.

```markdown
:::code{language=bash}
curl ':assetUrl{path="/resources/setup.yaml"}' --output setup.yaml
curl ':assetUrl{path="/resources/dataset.zip" source=s3}' --output dataset.zip
:::
```

## Button

클릭 가능한 버튼 UI. Text 전용 (Leaf/Container 불가) — 대괄호 안에 버튼 라벨을 넣는다(`variant="icon"`처럼 라벨이 없는 아이콘 버튼은 대괄호를 비워둔다). 속성: `disabled`, `href`(지정하면 링크 역할, `variant="link"`로 링크형 버튼 스타일 적용), `iconAlign`(`left`|`right`), `iconName`, `target`(`href`가 있을 때만 적용), `variant`(`normal`|`primary`|`link`|`icon`|`inline-icon`, 기본 `normal`), `wrapText`(기본 `true`), `action`(`navigate`|`download`, 기본 `navigate`).

```markdown
:button[콘솔 열기]{href="https://console.aws.amazon.com" variant="primary"}
:button[템플릿 다운로드]{href="/static/files/template.yaml" action=download}
:button[]{variant="icon" iconName="settings"}
```

## Link

인라인 하이퍼링크/다운로드 링크. Text 전용. 속성: `href`(없으면 버튼 role로 렌더링), `external`(외부 링크 아이콘 표시), `target`(`_blank` 지정 시 `rel="noopener"` 자동 추가), `action`(`navigate`|`download`, 기본 `navigate`).

```markdown
자세한 내용은 :link[AWS 문서]{href="https://docs.aws.amazon.com" external=true}를 참조하세요.

:link[CloudFormation 템플릿 다운로드]{href="/static/files/template.yaml" action=download}
```

> 대부분의 경우 표준 마크다운 링크(`[텍스트](url)`)로 충분하다 — `http(s)://`로 시작하는 링크는 자동으로 새 탭에서 열린다. Link directive는 다운로드 동작이나 외부 링크 아이콘처럼 표준 마크다운으로 표현할 수 없는 동작이 필요할 때만 사용한다.

## Expand

접을 수 있는 섹션(아코디언). Leaf/Container 지원 (Text 불가). 속성: `header`, `defaultExpanded`(기본 `false`), `variant`(`default`|`container`).

```markdown
::expand[짧은 답변]{header="자세히 보기"}

::::expand{header="설정 예시" defaultExpanded=false}
:::code{language=yaml}
region: ap-northeast-2
:::
::::
```

## Children

현재 페이지의 하위 페이지 목록을 자동 생성. Leaf 전용 (Text/Container 불가). 속성: `depth`(몇 단계까지 표시할지, 기본 `1`), `variant`(`list`|`normal`, 기본 `list`).

```markdown
::children{depth=2}
```

## Video

YouTube/Vimeo 비디오를 프라이버시 강화 모드로 임베드. Leaf 전용 (Text/Container 불가). **`src` 속성은 존재하지 않는다** — 대신 `id`(임베드 ID)와 `type`을 쓴다. 속성: `id`, `type`(`youTube`|`vimeo`, 기본 `youTube`), `autoplay`, `start`(시작 시간, 초).

```markdown
::video{id=a9__D53WsUs}
::video{id=395869376 type=vimeo start=63}
```

---

## Markdown 문법 주의사항

- Workshop Studio는 **원시 HTML을 렌더링하지 않는다** (보안 정책).
- 콘텐츠 안의 **콜론(`:`)은 directive 문법과 충돌하므로 백슬래시로 이스케이프**해야 한다 — 예: `AWS re\:Invent` → `AWS re:Invent`. 시간(`10\:30`), 비율(`3\:1`) 등 실수하기 쉬운 콜론 사용에 특히 주의.
- 헤더 앵커는 자동 슬러그화되며, 비-ASCII 헤더(한국어 등)는 `## 제목 {#custom-id}` 형식으로 앵커 ID를 직접 지정할 수 있다.
- 페이지 간 링크는 로케일 코드를 제외한 경로로 참조한다 — 절대 경로(`/introduction/getting-started`) 또는 상대 경로(`../getting-started`) 모두 지원.

---

## Multilingual (다국어)

지원 로케일 15개: `en-US`, `es-US`, `ja-JP`, `fr-FR`, `ko-KR`, `pt-BR`, `de-DE`, `it-IT`, `zh-CN`, `zh-TW`, `uk-UA`, `pl-PL`, `id-ID`, `nl-NL`, `ar-AE`. `contentspec.yaml`의 `localeCodes`에 정의한 각 로케일마다 콘텐츠 폴더 전체에 `index.[localeCode].md` 파일이 필요하다. 동일 페이지의 로케일별 파일은 같은 `weight`를 가져야 네비게이션 순서가 어긋나지 않는다 — 상세: `front-matter.md`

---

## 자주 사용하는 패턴

### 1. 명령어 실행 + 예상 출력

````markdown
다음 명령어를 실행합니다:

:::code{language="bash" showCopyAction=true}
kubectl get nodes
:::

예상 출력:

```
NAME                                           STATUS   ROLES    AGE   VERSION
ip-192-168-xx-xx.ap-northeast-2.compute.internal   Ready    <none>   5m    v1.28.x
```
````

### 2. 단계별 안내 + 주의사항

```markdown
## 클러스터 생성

다음 명령어로 EKS 클러스터를 생성합니다:

:::code{language="bash" showCopyAction=true}
eksctl create cluster \
  --name my-cluster \
  --region ap-northeast-2 \
  --nodegroup-name workers \
  --node-type t3.medium \
  --nodes 3
:::

::alert[클러스터 생성에 약 15-20분이 소요됩니다.]{type="info"}
```

### 3. 옵션 선택 + 설명

````markdown
::::tabs{variant="container"}
:::tab{label="기본 설치"}
빠른 시작을 위한 기본 설정입니다.

```bash
helm install my-release bitnami/nginx
```
:::
:::tab{label="고급 설치"}
커스텀 값을 적용한 설치입니다.

```bash
helm install my-release bitnami/nginx \
  --set replicaCount=3 \
  --set service.type=LoadBalancer
```
:::
::::
````
