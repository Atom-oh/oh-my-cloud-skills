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

## Commands

```bash
python3 plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py validate ./my-presentation/
python3 plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py build ./my-presentation/ --lang en
python3 plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py build my-talk.md -o /var/tmp/my-talk --lang en
python3 plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py build ./my-presentation/ --block 01-fundamentals --lang en
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

The parser does not expose `--watch` or `--format`. Use `--help` on the installed script to check its exact interface. Build defaults to Korean unless English is selected; set `lang: en` in authored source and use `--lang en` for the build.

## Multi-file projects

`_presentation.md` contains shared metadata and the blocks list. Numbered block files contain local frontmatter and slides. Build creates a table-of-contents page and block HTML; sync rebuilds changed blocks. Keep images and local assets alongside the project using paths valid from the generated output.

## Exports

The web framework provides PDF/ZIP export controls and browser export helpers where included by the generated deck. Screenshot-based PowerPoint uses the supplied `export_pptx.py` workflow; static exports cannot retain live interactions. For editable native PowerPoint, use aws-light-fcd.

## Publication

Serve or publish the complete generated tree so CSS, JavaScript, images, icons, and themes resolve. Validate source, test the rendered deck and exports, then pass content review before authorized deployment.

[CLI parser](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py) · [PPTX export helper](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-content-plugin/skills/reactive-presentation/scripts/export_pptx.py)
