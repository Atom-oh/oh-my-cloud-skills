---
sidebar_position: 2
title: "설치"
---

# 설치

## Marketplace에서 설치

```bash
/plugin marketplace add https://github.com/Atom-oh/oh-my-cloud-skills
/plugin install co-agent@oh-my-cloud-skills
```

## 로컬에서 직접 로드

```bash
claude --plugin-dir ./plugins/co-agent
```

## 사전 요구사항 (선택적 — 있는 것만 사용)

외부 AI CLI 중 **설치된 것만** 패널로 활용합니다. 하나도 없으면 현재 host 단독 수행 + 그 사실을 명시 (절대 hard-fail 안 함).

| AI | CLI 설치 확인 | 비고 |
|----|---------------|------|
| Kiro | `command -v kiro-cli` | 인터랙티브 로그인 **또는** `KIRO_API_KEY`로 헤드리스 인증 (둘 중 하나면 됨) |
| Claude | `command -v claude` | Codex host에서 peer reviewer로 사용 |
| Codex | `command -v codex` | Claude Code host에서 `codex exec -s read-only`로 사용 |
| Agy | `command -v agy` | 우선 사용 |
| Gemini | `command -v gemini` | `agy`가 없을 때만 legacy fallback |

```bash
# 패널 감지 예시
command -v kiro-cli
command -v codex
command -v agy || command -v gemini
```

:::tip
설치된 AI가 많을수록 second opinion 패널이 풍부해집니다. 하나만 있어도, 혹은 전부 없어도(host 단독) 동작합니다.
:::

> (선택) 대화형 Kiro 래퍼 슬래시 커맨드를 쓰려면: `/plugin marketplace add https://github.com/whchoi98/kiro-cli-plugin`

## 제거

```bash
/plugin uninstall co-agent@oh-my-cloud-skills
```
