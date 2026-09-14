---
sidebar_position: 2
title: "빠른 시작"
---

{/* 영문 개편 전의 기존 섹션 링크를 유지합니다. */}
<span id="빠른-시작" />
<span id="1-파일-만들기" />
<span id="2-html-빌드" />
<span id="3-브라우저에서-열기" />
<span id="기본-조작법" />
<span id="핵심-문법-요약" />
<span id="슬라이드-구분" />
<span id="디렉티브" />
<span id="프래그먼트" />
<span id="컬럼-레이아웃" />
<span id="다음-단계" />


# 빠른 시작

## 소스 만들기 {#create-the-source}

아래 내용을 `my-talk.md`로 저장합니다. `[요약]` 표시는 요약을 뜻하며 현재 구조화된 노트 검증기가 확인하는 리터럴입니다. 이 표시가 없으면 `NOTE_STRUCTURE` 경고가 발생합니다. 노트 본문은 영어로 유지합니다.

```markdown
---
remarp: true
title: "Build with evidence"
speaker:
  name: "Alex Morgan"
  title: "Engineer"
  company: "Example team"
audience: "Project contributors"
level: "200"
quiz: false
duration: 5
lang: en
---

# Build with evidence

A short introduction to the review loop.

:::notes
{timing: 2min}
[요약]
- Introduce the review loop.
- Connect each change to observable behavior.
- Explain how the checks support the conclusion.

Introduce the example and ask the audience to keep one recent change in mind.
Explain that the next slide separates reading the code, exercising its behavior,
and recording what the result proves. This keeps the review concrete and gives
the next reviewer enough evidence to reproduce the conclusion.
:::

---
@type: content

## Verify each change

- Read the affected code {.click order=1}
- Run the relevant checks {.click order=2}
- Record the result {.click order=3}

:::notes
{timing: 3min}
[요약]
- Start from the changed behavior.
- Choose checks that exercise it.
- Report evidence and limits.

Explain why a successful build alone may not exercise the changed behavior.
Walk through one relevant test and describe what its passing result proves.
{cue: transition}
Next, use the same method when reviewing a teammate's change.
:::

```

## 검증과 빌드 {#validate-and-build}

마켓플레이스 저장소 루트에서 실행합니다.

```bash
python3 plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py validate my-talk.md
python3 plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py build my-talk.md --lang en
```

`validate`는 유효하지 않거나 없는 입력 또는 CRITICAL 지적이 있으면 0이 아닌 종료 코드를 반환합니다. `build`와 `sync`도 같은 검증을 적용하며 스타일 경고는 참고 사항으로 유지됩니다. 프로그램에서 읽을 수 있는 진단이 필요하면 `validate`에 `--json`을 추가합니다.

이 소스는 `slides/default.html`로 빌드되며 CSS와 JavaScript는 `slides/common/`에 자동으로 복사됩니다. `-o /var/tmp/my-talk`을 지정하면 해당 디렉터리에 `default.html`과 `common/`을 생성합니다. `slides/default.html`을 열어 단계별 표시를 확인합니다. Right/Space로 앞으로 진행하고, Left로 되돌아가며, P로 발표자 보기를 엽니다. 게시 전에 콘텐츠 리뷰를 수행합니다.

## 덱 확장 {#extend-the-deck}

compare/tabs/quiz/checklist/timeline/Canvas 슬라이드에는 `@type`, 열 구성에는 `@layout`, 발표 안내에는 `:::notes`를 사용합니다. 여러 파일로 구성된 덱의 공유 프런트매터는 `_presentation.md` 또는 `_presentation.remarp.md`에 둡니다. 프로젝트 디렉터리를 빌드하면 `-o`로 다른 디렉터리를 지정하지 않는 한 소스 옆에 `index.html`, `toc.html`, 블록 HTML과 `common/`을 생성합니다.

소스, 메타데이터 또는 의존성을 수정한 뒤에는 프로젝트 디렉터리에 `sync`를 실행해 전체 덱, TOC와 에셋을 다시 생성합니다. 이 작업은 Markdown 타임스탬프에 의존하지 않습니다. 명령과 옵션은 [CLI 참고 문서](./build-cli.md)를 확인합니다.

## 관련 링크 {#related-links}

- [프런트매터](./syntax/frontmatter.md)
- [지시문](./syntax/directives.md)
- [단계별 표시](./syntax/fragments.md)
- [Canvas DSL](./syntax/canvas-dsl.md)
