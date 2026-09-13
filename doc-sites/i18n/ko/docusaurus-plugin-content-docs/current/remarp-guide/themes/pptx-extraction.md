---
sidebar_position: 1
title: "PowerPoint 테마 추출"
---

{/* 영문 개편 전의 기존 섹션 링크를 유지합니다. */}
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


# PowerPoint 테마 추출

Remarp 웹 덱에 사용할 브랜드 색상, 글꼴, 로고, 레이아웃·배경 메타데이터와 바닥글 정보를 PPTX 템플릿에서 추출합니다.

## CLI {#cli}

```bash
python3 plugins/aws-content-plugin/skills/reactive-presentation/scripts/extract_pptx_theme.py template.pptx -o /var/tmp/pptx-theme
python3 plugins/aws-content-plugin/skills/reactive-presentation/scripts/extract_pptx_theme.py template.pptx --list-masters
python3 plugins/aws-content-plugin/skills/reactive-presentation/scripts/extract_pptx_theme.py template.pptx --master 1 -o /var/tmp/pptx-theme-alt
```

파서는 레이아웃 목록, JSON 전용 출력, CSS 파일명 재정의와 디자인 문서 옵션도 제공합니다. 현재의 정확한 옵션은 `--help`로 확인합니다. 결과에는 `theme-manifest.json`, `theme-override.css`와 추출한 이미지가 포함됩니다.

## 브랜드 매핑 {#brand-mapping}

생성된 CSS는 theme.css에서 사용하는 `--pptx-*` 입력 변수를 제공합니다. `dk1`이라는 슬롯이 항상 어둡다고 가정하지 말고 실제 색상 값과 휘도를 확인합니다. 역할·텍스트·표면의 지정은 프레임워크의 테마 범위 안에서 유지합니다.

## 로고, 바닥글과 배경 {#logos-footers-and-backgrounds}

추출 과정은 마스터·레이아웃 메타데이터와 휴리스틱으로 로고와 배경 에셋을 식별합니다. 바닥글·날짜·슬라이드 번호 후보에는 자리 표시자 유형과 위치 필터를 적용합니다. 매니페스트와 이미지를 확인해야 하며, 추출된 메타데이터가 모든 템플릿에서 올바른 배치를 보장하지는 않습니다.

단색, 그림, 그라데이션, 상속된 배경과 색상 구성표를 참조하는 배경은 서로 다른 경로로 처리됩니다. 다중 마스터 템플릿에서 기본값이 적절하지 않으면 마스터를 명시적으로 선택합니다. 레이아웃 메타데이터와 생성된 CSS를 함께 검토합니다.

## 통합과 문제 해결 {#integration-and-troubleshooting}

`theme.source`를 PPTX나 추출된 디렉터리로 지정하고 필요에 따라 바닥글·로고 옵션을 설정합니다. 빌더는 PDF 소스를 인식하지만 PDF 추출은 현재 미구현 상태이므로 같은 수준의 PDF 추출을 약속하지 않습니다.

색상이 잘못되면 브랜드 입력과 계산된 의미 토큰을 확인합니다. 로고가 없으면 매니페스트 경로와 복사된 파일을 확인합니다. 글꼴이 없으면 브라우저가 사용할 수 있고 사용 권한이 있는 로컬·웹 글꼴을 제공합니다. 추출 과정은 글꼴을 설치하지 않습니다. 최종 덱을 라이트·다크 모드에서 모두 검증합니다.

[추출기](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-content-plugin/skills/reactive-presentation/scripts/extract_pptx_theme.py) · [빌더 통합](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py)

## 관련 링크 {#related-links}

- [CSS 변수](./css-variables)
