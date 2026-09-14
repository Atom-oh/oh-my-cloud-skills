---
sidebar_position: 2
title: "테마 토큰"
---

{/* 영문 개편 전의 기존 섹션 링크를 유지합니다. */}
<span id="css-변수--토큰-디자인-시스템-v190" />
<span id="테마-스코프--light가-기본" />
<span id="1-역할-색상-토큰-role-tokens" />
<span id="2-서피스--텍스트-토큰" />
<span id="3-간격--반경--그림자--타이포-토큰" />
<span id="4-브랜드-입력----pptx-" />
<span id="5-토큰-클래스-직접-var-쓰기-전에" />
<span id="6-canvas에서-토큰-쓰기" />
<span id="관련-문서" />


# 테마 토큰

의미 기반 CSS 변수와 재사용 가능한 클래스로 콘텐츠가 프레임워크의 기본 라이트 테마와 `.theme-dark` 범위에 맞게 표시되도록 합니다. 이 문서 사이트는 별도의 Docusaurus 테마를 사용하며, 여기서는 생성된 Remarp 덱의 토큰을 설명합니다.

## 테마 범위 {#theme-scopes}

```html
<div class="slide-deck theme-light"></div>
<div class="slide-deck theme-dark"></div>
```

## 역할과 표면 {#roles-and-surfaces}

역할에는 `--accent`, `--info`, `--success`, `--warning`, `--danger`가 있으며 `-subtle`과 `-on` 변형도 제공합니다. 표면에는 `--surface-1`, `--surface-2`, `--surface-3`을, 텍스트에는 `--on-surface`와 `--on-surface-muted`를 사용합니다. 기존 배경·텍스트 별칭도 프레임워크에서 계속 매핑합니다.

제공된 테마의 간격, 반경, 그림자와 굵기 변수를 사용합니다. 정확한 값은 별도 표로 복제하지 않고 theme.css에서 관리합니다.

## 브랜드 입력 {#brand-inputs}

추출한 브랜드 색상을 `--pptx-*` 변수로 전달합니다. 프레임워크가 테마별 의미 역할에 매핑합니다. 밝은 배경에 다크 테마용 텍스트 색상을 직접 덮어쓰면 내용을 읽기 어려울 수 있습니다.

```css
:root {
  --pptx-accent1: #2563eb;
}
.review-card {
  background: var(--surface-1);
  color: var(--on-surface);
  padding: var(--space-4);
}
```

## 레이아웃 클래스 {#layout-classes}

필요에 따라 `.card-grid`, `.metric-card`, `.metric-label`, `.callout`과 역할별 변형, `.flow-h`, `.flow-group`, `.flow-box`, `.flow-arrow`, `.tab-bar`, `.tab-btn`, `.tab-content`를 사용합니다. 지원되는 두 테마에서 대비와 레이아웃을 확인합니다.

## Canvas {#canvas}

Canvas 그리기 API는 CSS 변수를 직접 해석하지 않습니다. 사용자 지정 그리기 코드는 덱의 계산된 값을 읽어 그리기 반복문 밖에 캐시하고 테마가 바뀌면 갱신해야 합니다. 지원되는 DSL 경로의 토큰 처리는 컴파일러가 제공합니다.

[기준 테마 변수와 클래스](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-content-plugin/skills/reactive-presentation/assets/theme.css)

## 관련 링크 {#related-links}

- [사용자 지정 테마](./custom-themes)
- [PPTX 추출](./pptx-extraction)
- [빌드 CLI](../build-cli)
