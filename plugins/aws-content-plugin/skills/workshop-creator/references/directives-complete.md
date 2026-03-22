# Workshop Studio Directives Complete Reference

Workshop Studio에서 지원하는 모든 Directive 문법 레퍼런스입니다.

---

## Directive 기본 문법

Directive는 Markdown을 확장하여 더 풍부한 콘텐츠 경험을 제공합니다.

### 구성 요소

- **콜론 (`:`)**: Directive 시작
- **대괄호 `[]`**: 인라인 콘텐츠 (한 줄)
- **중괄호 `{}`**: 키/값 속성

```markdown
:directive[content]{key="value" key2='value2' key3=value3}
```

---

## Directive 유형

### 1. Text Directive (`:`)

텍스트와 인라인으로 렌더링됩니다.

```markdown
Workshop Studio Wiki :link[링크]{href="https://example.com" external="true"}를 참조하세요.
```

### 2. Leaf Directive (`::`)

블록 레벨 요소로 자체 줄에 렌더링됩니다.

```markdown
::code[console.log('Hello world!');]{showCopyAction=true language="js"}
```

### 3. Container Directive (`:::`)

마크다운 블록을 포함할 수 있습니다.

```markdown
:::alert{type="success" header="성공"}
내용을 여기에 작성합니다.
:::
```

### 4. Nested Directives (`::::`)

중첩 시 **외부 directive가 더 많은 콜론**을 가져야 합니다.

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

---

## Alert / Notice

알림, 경고, 팁 등을 표시합니다.

### Hugo 스타일 (권장)

```markdown
{{% notice info %}}
정보성 내용입니다.
{{% /notice %}}

{{% notice tip %}}
유용한 팁입니다.
{{% /notice %}}

{{% notice warning %}}
경고: 주의가 필요합니다.
{{% /notice %}}

{{% notice note %}}
참고 사항입니다.
{{% /notice %}}
```

### Directive 스타일

```markdown
::::alert{type="info" header="정보"}
정보성 내용입니다.
::::

::::alert{type="success" header="성공"}
성공 메시지입니다.
::::

::::alert{type="warning" header="경고"}
경고 메시지입니다.
::::
```

| type 값 | 설명 |
|---------|------|
| `info` | 정보 (파란색) |
| `success` | 성공 (녹색) |
| `warning` | 경고 (주황색) |
| `error` | 오류 (빨간색) |

---

## Code Block

코드 블록을 표시합니다.

### 기본 사용

```markdown
:::code{language="bash" showCopyAction=true showLineNumbers=true}
#!/bin/bash
export AWS_REGION=ap-northeast-2
kubectl get nodes
:::
```

### 줄 강조

```markdown
:::code{language="python" showCopyAction=true highlightLines="2-4"}
import boto3

client = boto3.client('s3')
response = client.list_buckets()

print(response)
:::
```

### 속성

| 속성 | 설명 | 값 |
|------|------|-----|
| `language` | 언어 | bash, python, yaml, json, go, java 등 |
| `showCopyAction` | 복사 버튼 표시 | true / false |
| `showLineNumbers` | 줄 번호 표시 | true / false |
| `highlightLines` | 강조할 줄 | "2-4", "1,3,5" |

---

## Tabs

탭으로 콘텐츠를 구분합니다.

```markdown
::::tabs{labels=["Linux/macOS", "Windows"]}
:::tab{label="Linux/macOS"}
```bash
export AWS_REGION=ap-northeast-2
```
:::
:::tab{label="Windows"}
```powershell
$env:AWS_REGION="ap-northeast-2"
```
:::
::::
```

### Console vs CLI 예제

```markdown
::::tabs{labels=["AWS Console", "AWS CLI"]}
:::tab{label="AWS Console"}
1. AWS 콘솔에서 S3로 이동합니다.
2. **버킷 생성**을 클릭합니다.
3. 버킷 이름을 입력합니다.
:::
:::tab{label="AWS CLI"}
```bash
aws s3 mb s3://my-bucket --region ap-northeast-2
```
:::
::::
```

---

## Expand (Accordion)

접을 수 있는 섹션을 만듭니다.

```markdown
::::expand{header="클릭하여 자세히 보기" defaultExpanded=false}
숨겨진 상세 내용입니다.

- 목록 항목
- 코드 블록
- 테이블도 포함 가능
::::
```

| 속성 | 설명 | 기본값 |
|------|------|--------|
| `header` | 헤더 텍스트 | 필수 |
| `defaultExpanded` | 기본 펼침 상태 | false |

---

## Image

이미지를 표시합니다.

### 기본 사용

```markdown
:image[이미지 설명]{src="/static/images/example.png"}
```

### 크기 조절

```markdown
:image[아키텍처]{src="/static/images/architecture.png" width="90%"}
```

### 다국어 이미지

```markdown
:image[다이어그램]{src="/static/images/diagrams/flow.ko.png" signedUrl=false}
```

| 속성 | 설명 |
|------|------|
| `src` | 이미지 경로 (static/ 하위) |
| `width` | 너비 (%, px) |
| `signedUrl` | S3 서명 URL 사용 여부 |

---

## Button

버튼 링크를 표시합니다.

```markdown
::button[AWS 콘솔 열기]{href="https://console.aws.amazon.com"}

::button[템플릿 다운로드]{href="/static/files/template.yaml" action="primary"}
```

| 속성 | 설명 |
|------|------|
| `href` | 링크 URL |
| `action` | 스타일 (primary, secondary) |

---

## Link

인라인 링크를 만듭니다.

```markdown
자세한 내용은 :link[AWS 문서]{href="https://docs.aws.amazon.com" external="true"}를 참조하세요.
```

| 속성 | 설명 |
|------|------|
| `href` | 링크 URL |
| `external` | 새 창에서 열기 (true/false) |

---

## Video

YouTube 등 비디오를 임베드합니다.

```markdown
::video{src="https://www.youtube.com/embed/VIDEO_ID"}
```

---

## Asset URL

S3 자산 URL을 생성합니다.

```markdown
::assetUrl[/path/to/asset.zip]
```

---

## Children

하위 페이지 목록을 자동 생성합니다.

```markdown
::children
```

---

## Param

contentspec.yaml의 파라미터를 참조합니다.

```markdown
클러스터 이름: :param{key="clusterName"}
```

---

## 자주 사용하는 패턴

### 1. 명령어 실행 + 예상 출력

```markdown
다음 명령어를 실행합니다:

:::code{language="bash" showCopyAction=true}
kubectl get nodes
:::

예상 출력:

```
NAME                                           STATUS   ROLES    AGE   VERSION
ip-192-168-xx-xx.ap-northeast-2.compute.internal   Ready    <none>   5m    v1.28.x
```
```

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

{{% notice info %}}
클러스터 생성에 약 15-20분이 소요됩니다.
{{% /notice %}}
```

### 3. 옵션 선택 + 설명

```markdown
::::tabs{labels=["기본 설치", "고급 설치"]}
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
```
