---
sidebar_position: 5
title: "슬라이드 수정 스킬"
---

# 슬라이드 수정 스킬

{/* 영문 개편 전의 기존 섹션 링크를 유지합니다. */}
<span id="trigger-keywords" />
<span id="워크플로우" />
<span id="작동-방식" />
<span id="1-issue-삽입-vscode-extension" />
<span id="2-issue-추출" />
<span id="3-수정-및-정리" />
<span id="vscode-extension-연동" />
<span id="사용-예시" />
<span id="quality-review" />

Remarp나 편집기의 이슈 주석을 실제 슬라이드 소스에 반영합니다.

## 주석 기반 수정 반복 {#annotation-loop}

```markdown
<!-- issue: The comparison labels overlap at the mobile viewport. -->
```

`remarp_to_slides.py issues <path>`로 주석을 확인하며, 구조화된 출력에는 `--json`을 사용합니다. 각 주석을 해당 슬라이드와 대조해 소스·CSS·다이어그램을 수정합니다. 해결된 주석은 제거하고 미해결 주석은 명확한 보고와 함께 보존합니다. 영향을 받는 블록을 다시 빌드하고 문제가 있었던 상호작용이나 레이아웃을 재현해 확인한 뒤 해결되었다고 보고합니다.

VS Code 확장에서는 Remarp나 생성된 HTML을 미리 보면서 주석을 추가할 수 있습니다. 소스와 생성 결과를 일치시켜야 하며, 그렇지 않으면 HTML에 직접 반영한 수정이 덮어써질 수 있습니다. 최종 후보에 콘텐츠 리뷰를 적용합니다.


[스킬, 리소스와 품질 요구 사항](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-content-plugin/skills/slide-fix/SKILL.md)
