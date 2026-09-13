---
sidebar_position: 7
title: "콘텐츠 리뷰 에이전트"
---

{/* 영문 개편 전의 기존 섹션 링크를 유지합니다. */}
<span id="기본-정보" />
<span id="트리거-키워드" />
<span id="지원-콘텐츠-타입" />
<span id="16개-검사-카테고리" />
<span id="1-layout-inspection-레이아웃-검사" />
<span id="2-terminology-appropriateness-용어-적절성" />
<span id="3-hallucination-detection-환각-탐지" />
<span id="4-language-check-언어-검사" />
<span id="5-piisensitive-data-inspection-민감-데이터-검사" />
<span id="6-content-type-specific-quality-타입별-품질" />
<span id="7-16-추가-검사" />
<span id="visual-testing-html-콘텐츠" />
<span id="점수-체계-100점-만점" />
<span id="판정" />
<span id="자동-fail" />
<span id="리뷰-리포트-형식" />
<span id="리뷰-프로세스" />
<span id="step-1-file-collection" />
<span id="step-2-type-specific-inspection" />
<span id="step-3-visual-testing-html만" />
<span id="step-4-report-generation" />
<span id="리비전-루프" />
<span id="출력물" />


# 콘텐츠 리뷰 에이전트

프레젠테이션, 다이어그램, 문서, GitBook 페이지, 워크숍, 브로슈어와 프로필 페이지를 검토합니다. 보고서에는 실제 파일, 근거, 심각도, 수정 사항과 적용 점수를 명시합니다.

## 리뷰 범위 {#review-coverage}

레이아웃과 계층, 용어의 정확성, 근거 없는 사실 주장, 요청된 언어, 비밀 정보와 개인정보, 콘텐츠 유형별 규칙, 아이콘 참조, 가독성, 접근성, 구조의 완결성, 데이터 일관성, 권리·출처 표기, 메시지의 명확성, 중복·누락과 외부 참조를 확인합니다.

HTML 결과물은 브라우저에서도 확인합니다. 애플리케이션 오류 없이 로드되는지, 대표 화면 크기에서 탐색과 제어 기능이 작동하는지, 이미지·다이어그램·넘침·텍스트 대비에 문제가 없는지 검사합니다. 스크린샷만으로 퀴즈, 탭, 계산기나 애니메이션의 동작을 입증할 수 없으므로 직접 실행합니다.

## 콘텐츠별 검사 {#content-specific-checks}

Remarp는 소스, 프레임워크 초기화, 노트, 슬라이드 유형과 상호작용을 검증합니다. 다이어그램이 단순 Canvas 정책의 범위를 넘으면 HTML/CSS를 우선합니다. Draw.io는 XML, 중첩 구조, 기준 토큰, 레이아웃 검증과 내보내기의 완결성을 확인합니다. GitBook 탐색 구조는 실제 파일과 일치해야 합니다. 워크숍에는 Workshop Studio 지시문과 원본 평가 기준의 언어별 파일 검사를 적용합니다.

## 품질 게이트 {#quality-gate}

항목별 가중치와 형식별 처리 방식은 원본 평가 기준을 따릅니다. PASS를 받으려면 점수가 85 이상이고, Critical 지적이 없으며, Warning이 세 개 이하여야 합니다. 민감 정보 유출, 심각한 허위 주장 등 자동 실패 조건은 다른 항목의 점수로 상쇄할 수 없습니다. HTML이 아닌 결과물에는 평가 기준의 시각적 테스트 면제 규칙을 적용합니다.

점수, 판정, 근거와 수정 체크리스트를 제공합니다. REVIEW/FAIL 문제를 수정하고 작업 흐름의 반복 한도 안에서 다시 검토합니다. 해결하지 못한 차단 요인은 게시 준비가 끝났다고 주장하지 말고 명확히 보고합니다.

[기준 평가표와 보고서 명세](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-content-plugin/agents/content-review-agent.md)
