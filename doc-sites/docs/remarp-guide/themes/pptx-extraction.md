---
sidebar_position: 1
title: "Extract a PowerPoint theme"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="pptx-테마-추출" />
<span id="빠른-시작" />
<span id="cli-옵션" />
<span id="frontmatter에서-테마-지정" />
<span id="테마-소스-타입" />
<span id="색상-매핑" />
<span id="배경텍스트-색상-휘도-기반-선택" />
<span id="강조색-고정-매핑" />
<span id="로고-감지" />
<span id="로고-통합" />
<span id="푸터-추출" />
<span id="배경-타입" />
<span id="레이아웃-배경-추출" />
<span id="테마-매니페스트" />
<span id="멀티-마스터-템플릿" />
<span id="트러블슈팅" />
<span id="색상이-잘못-표시되는-경우" />
<span id="로고가-표시되지-않는-경우" />
<span id="폰트가-로드되지-않는-경우" />


# Extract a PowerPoint theme

Extract brand colors, fonts, logos, layout/background metadata, and footer information from a PPTX template for a Remarp web deck.

## CLI

```bash
python3 plugins/aws-content-plugin/skills/reactive-presentation/scripts/extract_pptx_theme.py template.pptx -o /var/tmp/pptx-theme
python3 plugins/aws-content-plugin/skills/reactive-presentation/scripts/extract_pptx_theme.py template.pptx --list-masters
python3 plugins/aws-content-plugin/skills/reactive-presentation/scripts/extract_pptx_theme.py template.pptx --master 1 -o /var/tmp/pptx-theme-alt
```

The parser also exposes layout listing, JSON-only output, a CSS filename override, and design-document options. Use `--help` for the exact current options. Output includes `theme-manifest.json`, `theme-override.css`, and extracted images.

## Brand mapping

The generated CSS supplies `--pptx-*` input variables consumed by theme.css. Inspect actual color values and luminance rather than assuming a slot named `dk1` is always dark. Keep role/text/surface assignments inside the framework's theme scopes.

## Logos, footers, and backgrounds

Extraction uses master/layout metadata and heuristics to identify logos and background assets. Footer/date/slide-number candidates use placeholder type and position filters. Inspect the manifest and images: extracted metadata is not a guarantee of correct placement in every template.

Solid, picture, gradient, inherited, and scheme-referenced backgrounds follow different paths. Multi-master templates need explicit master selection where the default is inappropriate. Layout metadata and generated CSS should be reviewed together.

## Integration and troubleshooting

Set `theme.source` to the PPTX or extracted directory, with footer/logo options as needed. The builder recognizes PDF sources but currently leaves PDF extraction unimplemented; do not promise equivalent PDF extraction.

For incorrect colors, inspect brand inputs and computed semantic tokens. For missing logos, check manifest paths and copied files. For missing fonts, provide licensed local/web fonts available to the browser; extraction does not install fonts. Verify the final deck in both light and dark modes.

[Extractor](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-content-plugin/skills/reactive-presentation/scripts/extract_pptx_theme.py) · [Builder integration](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py)

## Related links

- [css variables](./css-variables)
