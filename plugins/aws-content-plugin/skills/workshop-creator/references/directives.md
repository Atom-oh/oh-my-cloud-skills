# Workshop Studio Directives Quick Reference

## Directive 기본 구조

| 타입 | 문법 | 예시 |
|------|------|------|
| Text | `:name` | `:image[alt text]{src="..."}` |
| Leaf | `::name` | `::button[텍스트]{href="..."}` |
| Container | `:::name` ~ `:::` | `:::tab{label="탭명"}` ... `:::` |
| Nested | `::::name` ~ `::::` | 탭 그룹 등 중첩 구조 |

---

## Alert / Notice

```markdown
{{% notice info %}}
정보성 내용
{{% /notice %}}

{{% notice tip %}}
유용한 팁
{{% /notice %}}

{{% notice warning %}}
경고: 주의가 필요한 내용
{{% /notice %}}

{{% notice note %}}
참고 사항
{{% /notice %}}
```

---

## Code Block

```markdown
:::code{language="bash" showCopyAction=true showLineNumbers=true highlightLines="2-4"}
#!/bin/bash
export AWS_REGION=ap-northeast-2
export CLUSTER_NAME=my-cluster

kubectl get nodes
:::
```

### 옵션

| 속성 | 설명 | 값 |
|------|------|-----|
| `language` | 언어 | bash, python, yaml, json 등 |
| `showCopyAction` | 복사 버튼 | true / false |
| `showLineNumbers` | 줄번호 | true / false |
| `highlightLines` | 강조 줄 | "2-4", "1,3,5" |

---

## Tabs

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

---

## Expand (Accordion)

```markdown
::::expand{header="클릭하여 자세히 보기" defaultExpanded=false}
숨겨진 상세 내용

- 목록
- 코드 블록
- 테이블 포함 가능
::::
```

---

## Image

```markdown
:image[이미지 설명]{src="/static/images/example.png" width="90%"}

# 다이어그램 (다국어)
:image[아키텍처 다이어그램]{src="/static/images/diagrams/architecture.ko.png" signedUrl=false}
```

---

## Button

```markdown
::button[AWS 콘솔 열기]{href="https://console.aws.amazon.com"}

::button[다운로드]{href="/static/files/template.yaml" action="primary"}
```

---

## Video

```markdown
::video{src="https://www.youtube.com/embed/VIDEO_ID"}
```

---

## 자주 사용하는 패턴

### 콘솔 vs CLI 비교

```markdown
::::tabs{labels=["AWS Console", "AWS CLI"]}
:::tab{label="AWS Console"}
1. AWS 콘솔에서 S3로 이동
2. 버킷 생성 클릭
3. ...
:::
:::tab{label="AWS CLI"}
```bash
aws s3 mb s3://my-bucket --region ap-northeast-2
```
:::
::::
```

### 코드와 설명

```markdown
다음 명령어로 클러스터를 생성합니다:

:::code{language="bash" showCopyAction=true}
eksctl create cluster \
  --name my-cluster \
  --region ap-northeast-2 \
  --nodegroup-name standard-nodes \
  --node-type t3.medium \
  --nodes 3
:::

{{% notice info %}}
클러스터 생성에 약 15-20분이 소요됩니다.
{{% /notice %}}
```

### 확인 및 예상 출력

```markdown
## 확인

다음 명령어로 결과를 확인합니다:

```bash
kubectl get nodes
```

예상 출력:
```
NAME                                           STATUS   ROLES    AGE   VERSION
ip-192-168-xx-xx.ap-northeast-2.compute.internal   Ready    <none>   5m    v1.28.x
ip-192-168-yy-yy.ap-northeast-2.compute.internal   Ready    <none>   5m    v1.28.x
```
```
