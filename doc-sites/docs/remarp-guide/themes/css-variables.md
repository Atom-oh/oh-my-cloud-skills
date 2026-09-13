---
sidebar_position: 2
title: "Theme tokens"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="css-변수--토큰-디자인-시스템-v190" />
<span id="테마-스코프--light가-기본" />
<span id="1-역할-색상-토큰-role-tokens" />
<span id="2-서피스--텍스트-토큰" />
<span id="3-간격--반경--그림자--타이포-토큰" />
<span id="4-브랜드-입력----pptx-" />
<span id="5-토큰-클래스-직접-var-쓰기-전에" />
<span id="6-canvas에서-토큰-쓰기" />
<span id="관련-문서" />


# Theme tokens

Use semantic CSS variables and reusable classes so content adapts to the framework's light default and `.theme-dark` scope. The site itself has its own Docusaurus theme; these tokens describe generated Remarp decks.

## Theme scopes

```html
<div class="slide-deck theme-light"></div>
<div class="slide-deck theme-dark"></div>
```

## Roles and surfaces

Roles include `--accent`, `--info`, `--success`, `--warning`, and `--danger`, with `-subtle` and `-on` variants. Surfaces use `--surface-1`, `--surface-2`, `--surface-3`; text uses `--on-surface` and `--on-surface-muted`. Legacy background/text aliases remain mapped by the framework.

Use spacing, radius, shadow, and weight variables from the shipped theme. Exact values belong in theme.css rather than a duplicated table.

## Brand inputs

Inject extracted brand colors through `--pptx-*` variables. The framework maps those inputs to semantic roles for each theme. Directly overriding a light background with a dark-theme text color can make content unreadable.

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

## Layout classes

Use `.card-grid`, `.metric-card`, `.metric-label`, `.callout` and role variants, `.flow-h`, `.flow-group`, `.flow-box`, `.flow-arrow`, `.tab-bar`, `.tab-btn`, and `.tab-content` where appropriate. Check contrast and layout in both supported themes.

## Canvas

Canvas drawing APIs do not resolve CSS variables directly. Custom drawing code must read computed values from the deck, cache them outside the draw loop, and refresh them when the theme changes. The compiler supplies token handling for supported DSL paths.

[Canonical theme variables and classes](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-content-plugin/skills/reactive-presentation/assets/theme.css)

## Related links

- [custom themes](./custom-themes)
- [pptx extraction](./pptx-extraction)
- [Build CLI](../build-cli)
