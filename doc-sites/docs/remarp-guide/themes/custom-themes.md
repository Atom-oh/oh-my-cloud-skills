---
sidebar_position: 3
title: "Custom themes"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="커스텀-테마" />
<span id="frontmatter에서-테마-정의" />
<span id="테마-필드" />
<span id="css-오버라이드-파일-생성" />
<span id="컴포넌트별-스타일링" />
<span id="타이틀-슬라이드" />
<span id="카드-컴포넌트" />
<span id="버튼-스타일" />
<span id="코드-블록" />
<span id="로고-위치-조정" />
<span id="애니메이션-커스터마이징" />
<span id="슬라이드-전환" />
<span id="프래그먼트-애니메이션" />
<span id="반응형-조정" />
<span id="테마-프리셋" />
<span id="aws-스타일" />
<span id="modern-dark" />
<span id="corporate-blue" />
<span id="테마-적용-순서" />


# Custom themes

Apply a brand through frontmatter and a scoped override stylesheet while keeping the framework's semantic role/surface tokens intact.

## Frontmatter {#frontmatter}

```yaml
theme:
  source: "./company-template.pptx"
  footer: "Example team"
  pagination: true
  logo: auto
```

The source can be a PPTX or a previously extracted theme directory. The builder recognizes PDF paths but its PDF extraction path currently reports that extraction is unimplemented.

## CSS customization {#css-customization}

Use `--pptx-*` for brand colors, then style titles, cards, buttons, code, logo placement, and responsive layout with semantic tokens. Keep selectors scoped to the deck or intentional preset so one theme does not leak into another.

```css
:root { --pptx-accent1: #2563eb; }
.slide-deck .review-note {
  color: var(--on-surface-muted);
  background: var(--surface-2);
}
```

## Motion and responsiveness {#motion-and-responsiveness}

Customize supported transitions and fragment classes without hiding essential content. Use the deck's scaling/layout model and test small viewports, text wrapping, contrast, and logo/footer placement. Avoid fixed dark text/background overrides that defeat the light/dark token scopes.

## Apply and check {#apply-and-check}

Load base framework styles, extracted brand input, and intentional project overrides in the generated order. Inspect computed styles and the actual light/dark render when an override behaves unexpectedly. Validate and review before publication.

## Related links {#related-links}

- [css variables](./css-variables)
