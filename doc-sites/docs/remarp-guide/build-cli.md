---
sidebar_position: 10
title: "Build and CLI"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="빌드--cli" />
<span id="기본-명령어" />
<span id="build---html-생성" />
<span id="sync---증분-빌드" />
<span id="migrate---marp-변환" />
<span id="빌드-옵션" />
<span id="멀티파일-프로젝트-구조" />
<span id="_presentationmd" />
<span id="블록-파일" />
<span id="빌드-명령어-예제" />
<span id="내보내기-옵션" />
<span id="pdf-내보내기" />
<span id="zip-내보내기" />
<span id="pptx-내보내기" />
<span id="toc-페이지" />
<span id="github-pages-배포" />


# Build and CLI

Run the converter from the marketplace checkout, or use the corresponding installed skill script path.

## Commands {#commands}

```bash
python3 plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py validate ./my-presentation/
python3 plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py build ./my-presentation/
python3 plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py build my-talk.md -o /var/tmp/my-talk --lang en
python3 plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py build ./my-presentation/ --block 01-fundamentals
python3 plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py sync ./my-presentation/
python3 plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py migrate old-talk.md -o /var/tmp/migrated-talk
python3 plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py issues ./my-presentation/ --json
```

| Subcommand | Supported arguments |
| --- | --- |
| `build` | Input path, `-o/--output`, `--block`, `--lang` (`ko` or `en`) |
| `sync` | Project directory, `-o/--output` |
| `migrate` | Marp input file, required `-o/--output` |
| `issues` | Input path, optional `--json` |
| `validate` | Input path, optional `--json` |

The parser does not expose `--watch` or `--format`. Use `--help` on the installed script to check its exact interface. `build --lang` overrides the source language. For consistent English project output, including `sync`, set `lang: en` in `_presentation.md` and keep block-level overrides consistent. Without language metadata, output defaults to Korean. Language metadata selects output language conventions; it does not translate the source prose.

`validate` exits nonzero for invalid or missing input, missing slides, or CRITICAL findings; `--json` returns machine-readable diagnostics. Both `build` and `sync` run the same validation gate and reject CRITICAL findings before generating output. Style warnings remain advisory.

A single source without named blocks produces `slides/default.html` beside the source, with framework assets in `slides/common/`. `-o` changes the output directory; assets are copied automatically. See the [complete quick start](./quick-start.md).

## Multi-file projects {#multi-file-projects}

`_presentation.md` (or `_presentation.remarp.md`) contains shared metadata and the blocks list. Numbered block files contain local frontmatter and slides. Project builds write merged `index.html`, `toc.html`, individual block HTML and `common/` alongside the source files, unless `-o` selects another output directory.

`sync` fully regenerates these outputs and their assets, including the merged index and TOC. It does not rely on Markdown modification times, so changes to global metadata, themes and referenced dependencies are rebuilt too. `build --block` generates only the selected block page and its assets; use `build` or `sync` to refresh the complete deck. Keep images and local assets at paths valid from the generated output.

## Exports {#exports}

The web framework provides PDF/ZIP export controls and browser export helpers where included by the generated deck. Screenshot-based PowerPoint uses the supplied `export_pptx.py` workflow; static exports cannot retain live interactions. For editable native PowerPoint, use [aws-light-fcd](../aws-content-plugin/skills/aws-light-fcd.md).

## Publication {#publication}

Serve or publish the complete generated tree so CSS, JavaScript, images, icons, and themes resolve. Validate source, test the rendered deck and exports, then pass content review before authorized deployment.

[CLI parser](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py) · [PPTX export helper](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-content-plugin/skills/reactive-presentation/scripts/export_pptx.py)
