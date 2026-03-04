---
sidebar_position: 4
title: "GitBook"
---

# GitBook Skill

적절한 구조, 네비게이션, 풍부한 컴포넌트를 갖춘 구조화된 GitBook 문서화 사이트를 생성하는 스킬입니다.

## 트리거 키워드

다음 키워드로 활성화됩니다:
- "gitbook", "documentation site"
- "create docs site", "gitbook project"
- "knowledge base"

## 사용 케이스

- AWS 아키텍처 또는 서비스 문서화 사이트
- 기술 지식 베이스
- 풍부한 포맷팅이 있는 프로젝트 문서
- 네비게이션이 있는 멀티 챕터 가이드

## 제공 리소스

### reference/

| 참조 문서 | 설명 |
|----------|------|
| `structure-guide.md` | 프로젝트 구조 패턴 및 규약 |
| `component-patterns.md` | GitBook 컴포넌트 문법 및 사용법 |

## 프로젝트 구조

```
docs/
├── .gitbook.yaml           # GitBook 설정
├── SUMMARY.md              # 네비게이션 구조 (필수)
├── README.md               # 랜딩 페이지
├── chapter-1/
│   ├── README.md           # 챕터 인덱스
│   ├── page-1.md
│   └── page-2.md
└── .gitbook/
    └── assets/             # 이미지와 다이어그램
```

## GitBook 컴포넌트

### Hints

```markdown
{% raw %}
{% hint style="info" %}
정보성 힌트입니다.
{% endhint %}

{% hint style="warning" %}
경고 메시지입니다.
{% endhint %}

{% hint style="danger" %}
위험 알림입니다.
{% endhint %}

{% hint style="success" %}
성공 메시지입니다.
{% endhint %}
{% endraw %}
```

### Tabs

````markdown
{% raw %}
{% tabs %}
{% tab title="Linux" %}
```bash
sudo apt install kubectl
```
{% endtab %}

{% tab title="macOS" %}
```bash
brew install kubectl
```
{% endtab %}
{% endtabs %}
{% endraw %}
````

### Code with Title

````markdown
{% raw %}
{% code title="deployment.yaml" lineNumbers="true" %}
```yaml
apiVersion: apps/v1
kind: Deployment
```
{% endcode %}
{% endraw %}
````

### Expandable

```markdown
<details>
<summary>클릭하여 펼치기</summary>

상세 내용입니다.

</details>
```

### Images with Caption

```markdown
<figure>
  <img src=".gitbook/assets/diagram.png" alt="System Architecture">
  <figcaption><p>Figure 1: System Architecture</p></figcaption>
</figure>
```

### Embed

```markdown
{% raw %}
{% embed url="https://www.youtube.com/watch?v=..." %}

{% file src=".gitbook/assets/template.yaml" %}
{% endraw %}
```

## Quick Start

1. SUMMARY.md (네비게이션 구조) 생성
2. .gitbook.yaml (설정) 생성
3. 챕터 디렉토리와 README.md 인덱스 페이지 생성
4. GitBook 컴포넌트로 콘텐츠 페이지 추가
5. GitBook에 연결된 git 저장소에 push

## 네비게이션 베스트 프랙티스

- `SUMMARY.md`를 네비게이션의 단일 진실 소스로 사용
- 섹션 헤더(`## Section Name`)로 논리적 챕터 그룹화
- 각 챕터에 `README.md`를 인덱스 페이지로 포함
- 네비게이션 깊이는 최대 3 레벨
- 설명적인 페이지 제목 사용 ("Page 1" 금지)

## 다이어그램 통합

### Draw.io PNG

```markdown
![VPC Architecture](.gitbook/assets/vpc-architecture.png)
```

### Animated SVG

```html
<iframe src="../assets/traffic-flow.html" width="100%" height="500" frameborder="0"></iframe>
```

## 한국어 헤딩 앵커

GitBook은 헤딩에서 앵커를 생성합니다. 한국어 헤딩의 경우:

- `## 1. 관측성 스택 아키텍처` → `#1-관측성-스택-아키텍처`
- 숫자 뒤 점은 제거됨
- 한국어 문자 유지
- 공백은 하이픈으로 변환

## 사용 예시

```
사용자: "EKS 운영 가이드 GitBook 만들어줘"

1. gitbook-agent 호출
2. 요구사항 수집 (주제, 대상, 챕터 구조)
3. 프로젝트 초기화
4. SUMMARY.md 생성
5. 챕터별 콘텐츠 작성
6. content-review-agent 검토
7. git push → GitBook 배포
```

## Quality Review (필수)

콘텐츠 완성 후 반드시:
1. `content-review-agent` 호출
2. PASS (85점 이상) 획득 후에만 완료 선언
