---
sidebar_position: 0
title: "pr-dash 개요"
---
# pr-dash

Claude에게 묻지 않고도 풀 리퀘스트의 CI 검사와 AI 리뷰 결과를 확인합니다. Claude
Code에서 `pr-dash`는 모드(mod)로 동작하며 패널, 프롬프트 아래 상태 줄, 토스트
알림을 표시합니다. Codex처럼 화면을 그릴 수 없는 곳에서는 `pr-status` 스킬이 같은
내용을 텍스트로 보고합니다.

## 표시하는 내용 {#what-it-shows}

패널에는 PR 제목, 상태, 브랜치와 헤드 커밋, 검사별 한 줄, AI 리뷰 상태와
Critical·Major·Minor 발견 사항이 나타납니다. 리뷰가 현재 헤드 커밋을 대상으로 했는지
이전 커밋을 대상으로 했는지 표시하고, PR과 리뷰 코멘트 링크를 제공합니다.

## 작동 방식 {#how-it-runs}

현재 브랜치의 PR은 `/pr-dash`, 다른 PR은 `/pr-dash <number>`로 열고, 감시를 멈추려면
`/pr-dash stop`을 실행합니다. Claude가 `gh pr create` 또는 `git push`를 성공적으로
실행하면 pr-dash가 해당 브랜치의 PR 감시를 시작합니다. 60초마다 확인하여 상태 줄을
최신으로 유지하고, 검사가 끝나거나 리뷰 결과가 바뀌면 토스트로 알립니다. PR이
병합되거나 닫히면 감시를 멈춥니다.

`r`을 누르면 새로 고칩니다. 리뷰에 발견 사항이 있으면 `f`가 co-agent의 pr-autofix
스킬로 수정하도록 Claude에게 요청합니다. 모든 검사가 통과하고 PASSED 리뷰가 현재
헤드를 대상으로 하면 `m`이 저장소 규칙에 따라 다시 확인한 뒤 병합하도록 Claude에게
요청합니다.

## 한계 {#limits}

pr-dash는 `gh pr view`로 GitHub를 읽기만 합니다. 버튼은 Claude에게 프롬프트를
전달할 뿐 직접 병합, 푸시, 승인하지 않으므로 Claude의 권한 확인과 저장소의 병합
규칙이 그대로 적용됩니다. 패널은 표시용이며 병합 게이트는 CI입니다. 리뷰 코멘트는
저장소의 리뷰 마커가 있는 `github-actions` 작성 코멘트만 신뢰합니다.

패널은 Claude Code 터미널과 Desktop 앱에서 그려집니다. VS Code 채팅 패널과
`claude -p`에서는 한 줄 요약을 대신 받습니다. 모드는 사용자 권한으로 Claude Code
안에서 실행되는 코드입니다. `claude plugin validate`로 동작을 확인할 수 있고
`--safe-mode`로 끌 수 있습니다.

## 시작하기 {#get-started}

`/plugin install pr-dash@oh-my-cloud-skills`로 설치하고 `gh auth login`으로 GitHub
CLI에 로그인한 뒤 새 세션을 시작합니다. 모드는 Claude Code 2.1.287 이상이
필요합니다. Codex에서는 스킬 선택기에서 `pr-dash:pr-status`를 고릅니다. 소스는
`plugins/pr-dash/`에 있습니다.
