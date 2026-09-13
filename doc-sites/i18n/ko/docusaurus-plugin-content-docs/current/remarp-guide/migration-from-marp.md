---
sidebar_position: 12
title: "Marp에서 마이그레이션"
---

{/* 영문 개편 전의 기존 섹션 링크를 유지합니다. */}
<span id="marp에서-마이그레이션" />
<span id="자동-변환" />
<span id="변환-테이블" />
<span id="하위-호환성" />
<span id="상세-변환-예제" />
<span id="frontmatter" />
<span id="블록-지정" />
<span id="슬라이드-타입" />
<span id="스피커-노트" />
<span id="canvas-슬라이드" />
<span id="무엇이-바뀌나요" />
<span id="바뀌는-것" />
<span id="그대로-유지되는-것" />
<span id="마이그레이션-체크리스트" />
<span id="1-frontmatter-업데이트" />
<span id="2-블록-분리-선택사항" />
<span id="3-디렉티브-변환" />
<span id="4-스피커-노트-변환" />
<span id="5-레이아웃-변환" />
<span id="6-인터랙티브-기능-추가-선택사항" />
<span id="점진적-마이그레이션" />


# Marp에서 마이그레이션

변환기로 기존 Marp 파일을 Remarp 프로젝트로 옮길 수 있습니다. 마이그레이션은 소스를 준비하는 과정이며, 시각적 결과나 동작의 완전한 일치를 보장하지는 않습니다.

```bash
python3 plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py migrate old-talk.md -o /var/tmp/remarp-talk
```

프로젝트를 빌드하기 전에 `/var/tmp/remarp-talk/_presentation.md`를 만들거나 수정해 원하는 전역 언어를 지정하고, 블록별 `lang` 재정의도 일치시킵니다.

```yaml
---
remarp: true
lang: en
---
```

필요하면 원본 덱의 다른 공유 메타데이터도 복사합니다. 마이그레이션은 원본 설명을 유지하며 `lang` 설정이 이를 번역하지는 않습니다. 프로젝트 빌드와 `sync`는 단일 파일용 `--lang`이 아닌 프런트매터를 읽습니다.

```bash
python3 plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py validate /var/tmp/remarp-talk
python3 plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py build /var/tmp/remarp-talk
```

## 변환 매핑 검토 {#review-the-mapping}

덱 표시를 `remarp: true`로 바꿉니다. 블록을 분리할 때는 전역 메타데이터를 `_presentation.md`로 옮기고, 기존 슬라이드 주석을 지원되는 `@type`, `@layout`, 배경과 시간 지시문으로 바꿉니다. 발표 안내는 `:::notes`로 변환하고 열·레이아웃 블록을 확인합니다.

일반 제목, 목록, 코드와 이미지는 대부분 알아볼 수 있는 Markdown 형태로 유지됩니다. 인터랙티브 퀴즈, 탭, Canvas 단계와 단계별 표시 동작은 의도에 맞게 작성하고 브라우저에서 확인해야 합니다. 필수 노트 표시와 기존 게시 링크를 보존합니다.

## 점진적 마이그레이션 {#incremental-migration}

원본을 참고용으로 보관하고 블록 하나를 옮긴 뒤 검증·빌드하고 렌더링 결과를 비교하며 진행합니다. 새 소스에는 Remarp 프런트매터가 있는 `.md`를 사용하며 `.remarp.md`도 계속 지원합니다. 기존 덱을 교체하기 전에 에셋 경로, 테마 호환성, 노트, 탐색과 내보내기를 확인합니다.
