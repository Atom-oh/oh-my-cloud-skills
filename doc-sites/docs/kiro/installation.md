---
sidebar_position: 2
title: "설치"
---

# 설치

## Marketplace에서 설치

```bash
/plugin marketplace add https://github.com/Atom-oh/oh-my-cloud-skills
/plugin install kiro@oh-my-cloud-skills
```

## 로컬에서 직접 로드

```bash
claude --plugin-dir ./plugins/kiro
```

## 사전 요구사항 (필수)

co-agent의 외부 AI 패널과 달리, kiro 플러그인은 **kiro-cli가 없으면 동작하지
않습니다** — 세션 예산을 아끼는 대상 자체가 Kiro의 구독 크레딧이기 때문입니다.

| 항목 | 확인 방법 |
|------|-----------|
| kiro-cli 설치 | `command -v kiro-cli` (없으면 [kiro.dev](https://kiro.dev)에서 설치) |
| 인증 | 인터랙티브 로그인(`kiro-cli` 실행 후 로그인) **또는** `KIRO_API_KEY` 환경변수 |

## 첫 실행: `/kiro:setup`

```bash
/kiro:setup
```

다음을 순서대로 처리합니다:

1. **감지 + 실사용 프로브** — `kiro_setup.py probe`가 PATH 존재 확인 + 실제로 짧은
   프롬프트를 보내 `READY`/`AUTH`/`NO_INGEST`/`TIMEOUT`/`ERROR`/`ABSENT`로 분류
2. **모델 목록 + 두 모델 선택** — 구현(delegate) 모델과 리뷰(review) 모델을 각각
   고릅니다. 리뷰 모델은 목록에서 **최신/최강 모델을 권장**(예: `gpt-5.6-sol`)
3. **신뢰 결정(필수, 매번 명시적으로 확인)** — `execute_bash`를 구현자에게
   허용할지 묻습니다. worktree 격리 + capture-diff + scope_guard는 **메인 트리에
   도달하는 것**만 보장하며, 셸 명령의 호스트 부작용(자격 증명 읽기, worktree 밖
   파일 삭제, 네트워크 호출)은 전혀 막지 않습니다
   - **셸 접근 없음 (시작 시 권장)** — `fs_read`/`fs_write`만 허용. 셸 명령이
     꼭 필요한 태스크는 Claude 직접 구현으로 폴백
   - **`execute_bash` 부여** — 이 CLI에 셸 접근을 허용하는 별도의 신뢰 결정을
     내리는 것과 같습니다
4. **커스텀 에이전트 파일 작성** — `.kiro/agents/kiro-implementer.json`
   (worktree-write-only preToolUse 훅), `.kiro/agents/kiro-reviewer.json`
   (fs_read only)
5. **default delegation 여부** — 트리거 문구 없이도 구현 요청을 자동으로
   Kiro로 라우팅할지(기본 off, 시작 시 off 권장)
6. **pre-commit 리뷰 훅 여부** — 커밋 시 staged diff를 자동으로 Kiro가 리뷰할지
   (기본 off — staged diff **내용**이 Kiro 백엔드로 전송되기 때문)

```bash
# 최종 유효 설정 확인
/kiro:configure
```

:::tip
`/kiro:setup`은 위 5·6번 옵션을 **항상 명시적으로 묻습니다** — 조용히 켜지는 일이
없습니다. 시작 시에는 둘 다 off를 권장하고, 필요할 때 `/kiro:configure`로 나중에
켤 수 있습니다.
:::

## 제거

```bash
/plugin uninstall kiro@oh-my-cloud-skills
```
