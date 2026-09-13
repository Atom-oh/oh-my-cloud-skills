---
sidebar_position: 2
title: "아키텍처 다이어그램 스킬"
---

# 아키텍처 다이어그램 스킬

{/* 영문 개편 전의 기존 섹션 링크를 유지합니다. */}
<span id="trigger-keywords" />
<span id="supported-modes" />
<span id="provided-resources" />
<span id="references" />
<span id="templates" />
<span id="scripts" />
<span id="canvas-size-for-ppt" />
<span id="drawio-xml-code-examples" />
<span id="empty-canvas-ppt-1600x900" />
<span id="aws-cloud-container" />
<span id="vpc-container" />
<span id="public-subnet-green" />
<span id="private-subnet-blue" />
<span id="ec2-instance-icon" />
<span id="lambda-function-icon" />
<span id="aurora-database-icon" />
<span id="connection-arrow" />
<span id="layout-patterns-detail" />
<span id="3-tier-architecture-pattern" />
<span id="hybrid-cloud-pattern" />
<span id="serverless-architecture-pattern" />
<span id="aws-icon-label-rules" />
<span id="aws-color-guide" />
<span id="service-category-colors" />
<span id="best-practices-checklist" />
<span id="layout" />
<span id="colors--style" />
<span id="connections" />
<span id="completeness" />
<span id="png-export" />
<span id="usage-example" />
<span id="drawio-mcp-setup-optional" />
<span id="quality-review-required" />
<span id="validation-checklist" />

편집 가능한 AWS Draw.io 다이어그램과 내보내기 이미지를 만듭니다. 표준 VPC/Multi-AZ/계층형, 서버리스·파이프라인, 멀티 리전과 하이브리드 패턴은 YAML 명세와 `layout_aws.py`를 사용합니다. 지원하지 않는 도형은 XML을 직접 작성합니다.

## 생성과 검증 {#generate-and-validate}

```bash
python3 plugins/aws-content-plugin/skills/architecture-diagram/scripts/layout_aws.py my-spec.yaml -o output.drawio
python3 plugins/aws-content-plugin/skills/architecture-diagram/scripts/validate_drawio.py output.drawio
python3 plugins/aws-content-plugin/skills/architecture-diagram/scripts/lint_layout.py output.drawio
drawio -x -f png -s 2 -t -o output.png output.drawio
```

내보내기 전에 레이아웃 점수 80 이상을 확인합니다. 헤드리스 Linux에서는 `xvfb-run -a`로 내보낼 수 있습니다. 이미지를 다시 열어 의도한 아키텍처의 서비스와 셀이 빠짐없이 포함되었는지 확인합니다. 내보내기 성공 상태만으로 잘림을 발견할 수는 없습니다.

## 구조와 토큰 {#structure-and-tokens}

Cloud/Region/VPC/Subnet 포함 관계에 맞게 정점을 중첩합니다. 연결선은 parent="1"과 명시적인 직교 앵커를 사용합니다. 올바른 AWS 그룹 스타일로 퍼블릭·프라이빗 서브넷을 구분합니다. 크기, 색상, 글꼴, 배치 간격과 레이블 규칙은 별도 표로 관리하지 말고 기준 토큰 파일에서 가져옵니다.

장식용 XML 주석과 잘못된 엔터티를 피합니다. 경계를 명확히 표시하고 같은 종류의 리소스를 정렬하며 서비스 레이블을 붙이고 교차를 최소화합니다. 선택적인 Draw.io MCP는 대화형 편집을 도울 수 있지만 스크립트 생성에는 필요하지 않습니다.

[기준 토큰](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-content-plugin/skills/architecture-diagram/references/design-tokens.md) · [예제 명세와 다이어그램](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-content-plugin/skills/architecture-diagram/examples/)

XML과 레이아웃 검사 외에도, 게시 전에 해당 평가 기준에 따라 콘텐츠 리뷰를 통과해야 합니다.

[스킬, 리소스와 품질 요구 사항](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-content-plugin/skills/architecture-diagram/SKILL.md)
