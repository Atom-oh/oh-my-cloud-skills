---
sidebar_position: 3
title: "사용자 지정 테마"
---

{/* 영문 개편 전의 기존 섹션 링크를 유지합니다. */}
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


# 사용자 지정 테마

프레임워크의 의미별 역할·표면 토큰을 유지하면서 프런트매터와 범위를 제한한 재정의 스타일시트로 브랜드를 적용합니다.

## 프런트매터 {#frontmatter}

```yaml
theme:
  source: "./company-template.pptx"
  footer: "Example team"
  pagination: true
  logo: auto
```

소스로 PPTX나 이전에 추출한 테마 디렉터리를 사용할 수 있습니다. 빌더는 PDF 경로를 인식하지만 현재 PDF 추출 경로는 미구현 상태라고 알립니다.

## CSS 사용자 지정 {#css-customization}

브랜드 색상에는 `--pptx-*`를 사용하고, 제목, 카드, 버튼, 코드, 로고 배치와 반응형 레이아웃은 의미 기반 토큰으로 스타일을 지정합니다. 테마 간에 스타일이 섞이지 않도록 선택자의 범위를 해당 덱이나 의도한 프리셋으로 제한합니다.

```css
:root { --pptx-accent1: #2563eb; }
.slide-deck .review-note {
  color: var(--on-surface-muted);
  background: var(--surface-2);
}
```

## 움직임과 반응형 동작 {#motion-and-responsiveness}

필수 콘텐츠를 숨기지 않으면서 지원되는 전환과 단계별 표시 클래스를 조정합니다. 덱의 크기 조절·레이아웃 모델을 사용하고 작은 화면, 텍스트 줄 바꿈, 대비와 로고·바닥글 배치를 테스트합니다. 라이트·다크 토큰 범위를 무시하는 고정된 어두운 텍스트·배경 재정의는 피합니다.

## 적용과 확인 {#apply-and-check}

기본 프레임워크 스타일, 추출된 브랜드 입력과 의도한 프로젝트 재정의를 생성된 순서대로 불러옵니다. 재정의가 예상과 다르게 동작하면 계산된 스타일과 실제 라이트·다크 렌더링을 확인합니다. 게시 전에 검증과 리뷰를 수행합니다.

## 관련 링크 {#related-links}

- [CSS 변수](./css-variables)
