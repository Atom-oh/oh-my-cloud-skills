---
sidebar_position: 6
title: "Workshop Agent"
---

# Workshop Agent

AWS Workshop Studio 콘텐츠를 생성하는 전문 에이전트입니다. 적절한 구조, 디렉티브, 다국어 지원, Mermaid 다이어그램, CloudFormation 인프라가 포함된 워크샵 콘텐츠를 만듭니다.

## 기본 정보

| 항목 | 값 |
|------|-----|
| **도구** | Read, Write, Glob, Grep, Bash, AskUserQuestion |

## 트리거 키워드

다음 키워드가 감지되면 자동으로 활성화됩니다:

| 키워드 | 설명 |
|--------|------|
| "workshop", "lab content" | 워크샵 콘텐츠 |
| "hands-on guide", "workshop create" | 핸즈온 가이드 |
| "module content" | 모듈 콘텐츠 |

## 핵심 기능

1. **Workshop Structure** — AWS Workshop Studio 규약에 따른 디렉토리 구성
2. **Content Generation** — front matter, 디렉티브, 검증 단계가 포함된 랩 콘텐츠
3. **Multi-language Support** — 한국어 (.ko.md) 및 영어 (.en.md) 버전
4. **Mermaid Diagrams** — 워크샵 페이지 내 아키텍처 시각화
5. **Infrastructure Templates** — CloudFormation 템플릿과 IAM 정책

## 디렉토리 구조

```
workshop-name/
├── contentspec.yaml
├── content/
│   ├── index.en.md
│   ├── introduction/
│   │   └── index.en.md
│   ├── module1-topic/
│   │   ├── index.en.md
│   │   ├── subtopic1/
│   │   │   └── index.en.md
│   │   └── subtopic2/
│   │       └── index.en.md
│   └── summary/
│       └── index.en.md
├── static/
│   ├── images/
│   ├── code/
│   ├── workshop.yaml
│   └── iam-policy.json
└── assets/
```

## Front Matter (필수)

```yaml
---
title: "Page Title"
weight: 10
---
```

:::warning 중요
`chapter: true`는 Workshop Studio에서 지원하지 않습니다. 절대 사용하지 마세요.
:::

## Workshop Studio 디렉티브

:::danger 주의
Workshop Studio는 자체 Directive 문법을 사용합니다. Hugo shortcode가 아닙니다!
:::

### 잘못된 예 (Hugo)

```markdown
{{% notice info %}}
This is wrong!
{{% /notice %}}
```

### 올바른 예 (Workshop Studio)

```markdown
::alert[This is correct!]{type="info"}

::::tabs
:::tab{label="Console"}
Content
:::
:::tab{label="CLI"}
Content
:::
::::
```

### Alert

```markdown
::alert[Simple message]{type="info"}
::alert[With header]{header="Important" type="warning"}

:::alert{header="Prerequisites" type="warning"}
Complex content with lists and code blocks
:::
```

| Type | 용도 |
|------|------|
| `info` | 일반 팁 (기본값) |
| `success` | 성공 확인 |
| `warning` | 주의, 사전 요구사항 |
| `error` | 심각한 경고 |

### Code

```markdown
:::code{language=bash showCopyAction=true}
kubectl get pods -n vllm
:::

::code[aws s3 ls]{showCopyAction=true copyAutoReturn=true}
```

### Tabs

```markdown
::::tabs
:::tab{label="Console"}
Console instructions
:::
:::tab{label="CLI"}
CLI instructions
:::
::::
```

코드 블록 포함 시 (콜론 추가):

```markdown
:::::tabs{variant="container"}
::::tab{id="python" label="Python"}
:::code{language=python}
import boto3
:::
::::
:::::
```

### Image

```markdown
:image[Alt text]{src="/static/images/module-1/screenshot.png" width=800}
```

### Mermaid Diagrams

````markdown
```mermaid
graph LR
    subgraph "User Interface"
        UI[Open WebUI]
    end
    subgraph "API Gateway"
        API[LiteLLM]
    end
    UI --> API
    style UI fill:#e1f5fe
    style API fill:#fff3e0
```
````

## 베스트 프랙티스

### DO

- Mermaid 다이어그램으로 아키텍처 시각화
- 섹션 헤더에 이모지 사용
- `showCopyAction=true`로 복사 가능한 명령어 제공
- 각 액션 후 검증 단계 포함
- 섹션 끝에 Key Takeaways
- 명확한 Previous/Next 네비게이션

### DON'T

- Hugo shortcode 사용 금지 (`{{% notice %}}`)
- `chapter: true` 사용 금지
- 계정 ID나 자격 증명 하드코딩 금지
- 검증 없는 단계 작성 금지
- 긴 코드를 heredoc으로 작성 금지

## 이중언어 콘텐츠 가이드라인

| 요소 | 한국어 (.ko.md) | 영어 (.en.md) |
|------|-----------------|---------------|
| 기술 용어 | 영어 유지 (AWS, Lambda, S3) | 그대로 |
| 설명 텍스트 | 한국어 | 영어 |
| 명령어/코드 | 동일 | 동일 |
| 이미지 경로 | 동일 | 동일 |
| Front matter weight | 일치해야 함 | 일치해야 함 |

## 출력물

| 산출물 | 형식 | 위치 |
|--------|------|------|
| Homepage | .md | `content/index.{ko,en}.md` |
| Module index | .md | `content/moduleN-topic/index.{ko,en}.md` |
| Lab content | .md | `content/moduleN/section/index.{ko,en}.md` |
| Content spec | .yaml | `contentspec.yaml` |
| CloudFormation | .yaml | `static/workshop.yaml` |
| IAM policy | .json | `static/iam-policy.json` |

## 사용 예시

```
사용자: "EKS 기초 핸즈온 워크샵 만들어줘"

에이전트:
1. 요구사항 수집 (주제, 대상, 시간, 모듈, 언어)
2. 구조 설계
3. contentspec.yaml 생성
4. 모듈별 콘텐츠 작성 (Mermaid 다이어그램 포함)
5. CloudFormation 템플릿 작성
6. content-review-agent로 품질 검토
```

## 협업 워크플로우

```mermaid
flowchart LR
    A[workshop-agent] --> B[content-review-agent]
    B --> C[Workshop Studio deployment]
```
