---
sidebar_position: 1
title: "token-saver 설치"
---
# token-saver 설치

## Claude Code {#claude-code}

```text
/plugin marketplace add Atom-oh/oh-my-cloud-skills
/plugin install token-saver@oh-my-cloud-skills
```

저장소 체크아웃에서 로컬로 개발할 때는 다음과 같이 실행합니다:

```bash
claude --plugin-dir ./plugins/token-saver
```

호스트의 훅 관리 기능에서 플러그인을 확인하고 신뢰한 뒤 새 세션을 시작합니다.
`/token-saver:concise-responses`로 수동 활성화할 수도 있습니다.

## Codex {#codex}

`/plugins`에서 이 저장소의 마켓플레이스를 통해 `token-saver`를 설치합니다.
사용 중인 Codex 버전에 필요하다면 훅 지원을 활성화하고, `/hooks`에서
플러그인의 훅을 확인해 신뢰한 뒤 새 스레드를 시작합니다. 설치 성공만으로
훅 실행이 확인되는 것은 아닙니다.

수동으로 적용하려면 `/skills` 또는 스킬 선택기에서
`token-saver:concise-responses`를 선택합니다. 생성된 패키지는 설치된
플러그인 위치에서 공유 지침을 찾습니다.

## 검증 {#verify}

자동 적용에는 Python 3이 필요하며, 생성된 Codex 훅 연결 코드는 Bash도
사용합니다. 호스트에서 플러그인의 `SessionStart` 훅이 활성화되고 신뢰된
상태인지 확인합니다. 일반 설명 요청과 명시적으로 자세한 답변이나 정해진
스키마를 요구하는 요청을 비교합니다. 대화 문장은 짧게 유지하되 필수 내용과
형식은 완전해야 합니다.

저장소 루트에서 오프라인 검사를 실행합니다:

```bash
python3 tests/structure/test-token-saver.py
python3 scripts/test-plugins.py -p token-saver
python3 scripts/test-codex-plugins.py -p token-saver
python3 scripts/sync-codex-plugins.py --check --plugin token-saver
```

이 검사는 패키지와 훅 동작을 확인하며, 모든 작업에 적용되는 절감률을
입증하지는 않습니다.

## 기존 전역 지침 {#existing-global-rules}

이미 같은 응답 스타일 규칙을 `~/.codex/AGENTS.md` 또는
`~/.claude/CLAUDE.md`에 넣었다면, 플러그인 로딩을 확인한 후 해당 구역만
제거합니다. 다른 지침은 유지합니다. 두 사본을 유지하면 문맥에 중복으로
들어갈 수 있습니다. 플러그인은 이 파일들을 수정하거나 제거하지 않습니다.

## 비활성화 또는 제거 {#disable-or-remove}

호스트의 플러그인 관리자에서 비활성화한 뒤 새 세션을 시작합니다. 제거하려면
Claude Code에서 `/plugin uninstall token-saver@oh-my-cloud-skills`를 사용하거나
Codex `/plugins`에서 삭제합니다. 기존 전역 규칙은 별개이므로 직접 변경하기
전까지 계속 적용됩니다.
