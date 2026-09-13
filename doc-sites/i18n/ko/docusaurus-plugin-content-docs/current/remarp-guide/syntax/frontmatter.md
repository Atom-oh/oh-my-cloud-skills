---
sidebar_position: 1
title: "프런트매터"
---

{/* 영문 개편 전의 기존 섹션 링크를 유지합니다. */}
<span id="글로벌-frontmatter" />
<span id="필드-레퍼런스" />
<span id="기본-필드" />
<span id="speaker-객체" />
<span id="blocks-배열" />
<span id="theme-객체" />
<span id="transition-객체" />
<span id="keys-객체" />
<span id="블록-파일-frontmatter" />
<span id="로컬-frontmatter-필드" />
<span id="pptx-테마-소스" />
<span id="예제-완전한-글로벌-frontmatter" />


# 프런트매터

단일 파일 덱은 파일 맨 앞에, 다중 파일 프로젝트는 `_presentation.md`에 YAML 프런트매터를 작성합니다.

```yaml
---
remarp: true
version: 1
title: "Architecture review"
speaker:
  name: "Alex Morgan"
  title: "Engineer"
  company: "Example team"
audience: "Platform engineers"
level: "300"
quiz: true
duration: 30
lang: en
blocks:
  - name: fundamentals
    title: "Fundamentals"
    duration: 15
  - name: patterns
    title: "Patterns"
    duration: 15
theme:
  source: "./company-template.pptx"
  footer: auto
  pagination: true
  logo: auto
transition:
  default: slide
  duration: 400
---
```

## 메타데이터 {#metadata}

`remarp: true`는 Remarp 소스를 식별합니다. `title`, `speaker`, `audience`, `level`, `quiz`, `duration`으로 발표와 기획 요구 사항을 설명합니다. `version`, `date`, `event`, `lang`에는 선택적인 형식·행사 메타데이터를 지정합니다. `speaker` 객체를 사용하며 기존 `author`는 지원되는 경우에만 대체값으로 사용합니다.

## 블록 {#blocks}

블록 메타데이터에는 name, title, duration을 지정할 수 있습니다. 빌더는 프로젝트 디렉터리에서 표시가 있는 `.md` 파일과 기존 `.remarp.md` 파일을 확장자를 제외한 파일명으로 찾습니다. 블록 메타데이터 항목으로 임의의 소스 파일을 선택하는 것은 아닙니다. 개별 블록 프런트매터에는 `remarp: true`, `block`과 선택적인 제목을 지정합니다. 블록 이름은 전역 목록과, 총 시간은 계획과 일치시킵니다.

## 테마 {#theme}

`theme`은 source, primary/accent/font/codeTheme, footer, pagination, logo 설정을 지원합니다. 소스로 PPTX 경로나 추출된 테마 디렉터리를 지정할 수 있습니다. PDF 경로도 인식하지만 PDF 추출은 현재 구현되지 않았습니다. 브랜드 CSS는 `--pptx-*` 입력 변수를 사용하며, 표면·텍스트의 의미별 역할은 프레임워크의 라이트·다크 범위에서 관리합니다.

## 전환과 키 {#transitions-and-keys}

전환 메타데이터로 기본 효과와 지속 시간을 지정합니다. 키 설정은 다음과 같은 키·동작 매핑으로 런타임에 전달합니다.

```yaml
keys:
  n: next
  p: presenter
```

실제 키보드 이벤트 키와 런타임 동작을 사용합니다. 동작을 배열에 연결하는 예제는 현재 런타임 명세가 아닙니다. 지원되는 기본값은 [키보드 참고 문서](/docs/remarp-guide/keyboard-shortcuts)에 정리되어 있습니다.
