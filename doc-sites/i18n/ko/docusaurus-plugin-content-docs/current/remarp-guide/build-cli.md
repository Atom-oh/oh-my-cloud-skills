---
sidebar_position: 10
title: "빌드와 CLI"
---

{/* 영문 개편 전의 기존 섹션 링크를 유지합니다. */}
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


# 빌드와 CLI

마켓플레이스 체크아웃에서 변환기를 실행하거나 설치된 스킬의 해당 스크립트 경로를 사용합니다.

## 명령 {#commands}

```bash
python3 plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py validate ./my-presentation/
python3 plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py build ./my-presentation/
python3 plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py build my-talk.md -o /var/tmp/my-talk --lang en
python3 plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py build ./my-presentation/ --block 01-fundamentals
python3 plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py sync ./my-presentation/
python3 plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py migrate old-talk.md -o /var/tmp/migrated-talk
python3 plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py issues ./my-presentation/ --json
```

| 하위 명령 | 지원하는 인수 |
| --- | --- |
| `build` | 입력 경로, `-o/--output`, `--block`, `--lang` (`ko` 또는 `en`, 단일 파일 빌드에만 적용) |
| `sync` | 프로젝트 디렉터리, `-o/--output` |
| `migrate` | Marp 입력 파일, 필수 `-o/--output` |
| `issues` | 입력 경로, 선택적 `--json` |
| `validate` | 입력 경로, 선택적 `--json` |

파서는 `--watch`나 `--format`을 제공하지 않습니다. 설치된 스크립트의 `--help`로 정확한 인터페이스를 확인합니다. `--lang`은 단일 파일 처리에서만 언어를 선택하며, `--block`을 포함한 디렉터리 빌드에서는 무시됩니다. 프로젝트 출력과 `sync`에 영어를 사용하려면 `_presentation.md`에 `lang: en`을 지정하고 블록별 재정의도 일치시킵니다. 언어 메타데이터가 없으면 프로젝트 출력은 기본적으로 한국어입니다. 언어 메타데이터는 출력의 언어별 표기 방식을 선택할 뿐 소스의 설명을 번역하지는 않습니다.

단일 파일 결과물에도 제공된 `common/` 프레임워크 에셋이 필요합니다. HTML을 열기 전에 [전체 빠른 시작 절차](./quick-start.md)를 따릅니다.

## 여러 파일로 구성된 프로젝트 {#multi-file-projects}

`_presentation.md`에는 공유 메타데이터와 블록 목록을 저장합니다. 번호순 블록 파일에는 개별 프런트매터와 슬라이드가 있습니다. 전체 빌드는 병합된 `index.html`, `toc.html`, 개별 블록 HTML과 공유 에셋을 생성합니다. `--block`과 `sync`는 블록 페이지만 다시 빌드하며, `sync`는 블록 파일의 수정 시각으로 변경을 감지합니다. 새 출력 디렉터리를 만들 때, 전역 메타데이터·테마를 변경한 뒤, 병합 덱을 게시하기 전에는 전체 빌드를 실행합니다. 이미지와 로컬 에셋은 프로젝트에 함께 두고 생성 결과에서 접근할 수 있는 경로를 사용합니다.

## 내보내기 {#exports}

생성된 덱에 포함된 경우 웹 프레임워크의 PDF/ZIP 내보내기 제어 기능과 브라우저 내보내기 도구를 사용할 수 있습니다. 스크린샷 기반 PowerPoint는 제공된 `export_pptx.py` 작업 흐름을 사용합니다. 정적 내보내기에는 실시간 상호작용이 유지되지 않습니다. 편집 가능한 네이티브 PowerPoint에는 [aws-light-fcd](../aws-content-plugin/skills/aws-light-fcd.md)를 사용합니다.

## 게시 {#publication}

CSS, JavaScript, 이미지, 아이콘과 테마를 불러올 수 있도록 생성된 전체 디렉터리 트리를 서비스하거나 게시합니다. 소스를 검증하고 렌더링된 덱과 내보내기 결과를 테스트한 뒤 콘텐츠 리뷰를 통과하고 승인된 배포를 진행합니다.

[CLI 파서](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py) · [PPTX 내보내기 도구](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-content-plugin/skills/reactive-presentation/scripts/export_pptx.py)
