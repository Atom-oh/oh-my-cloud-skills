---
sidebar_position: 1
title: "명령 목록"
---

# co-agent 명령

5개의 슬래시 명령으로 패널 설정, AI 컨텍스트 동기화, 자율 구현 파이프라인, 패널 준비도 확인을 지원합니다.

## /co-agent:configure

호스트 인지형 멀티-AI 패널을 설정합니다. 설정은 `co-agent.defaults.json`(커밋) ← `~/.claude/co-agent.user.json`(유저 스코프) ← `.claude/co-agent.local.json`(레포 로컬, gitignore) 레이어로 병합됩니다.

```bash
/co-agent:configure show                             # 현재 설정 보기
/co-agent:configure set codex model gpt-5-codex
/co-agent:configure set codex effort high             # effort는 Codex 전용
/co-agent:configure set kiro-cli model claude-opus-4.8
/co-agent:configure set agy enabled false             # 패널에서 제외
/co-agent:configure set timeout 300                   # CLI별 타임아웃(초)
/co-agent:configure set codex context_limit 400000    # 모델 컨텍스트 윈도 조정
/co-agent:configure set autosync on                   # CLAUDE.md 변경 시 자동 sync-context
/co-agent:configure set codex model gpt-5.5 --scope user  # 모든 레포에 적용
```

CLI가 헤드리스로 실제 받는 옵션만 노출합니다(죽은 설정 없음): `model`, `effort`(Codex 전용), `enabled`, `timeout`, `context_limit`, 글로벌 `autosync`. `--host codex`로 호스트가 Codex일 때의 패널 구성(Kiro/Claude/Agy)도 설정할 수 있습니다.

## /co-agent:sync-context

`CLAUDE.md`를 **한 번만 증류**해 `AGENTS.md`를 생성하고, Kiro 스티어링을 이 같은 파일에 연결합니다. Agy는 자동로드가 없어 fan-out 시점에 컨텍스트로 fold-in됩니다.

```bash
/co-agent:sync-context
```

생성 마커(`claude-md-sha`)로 staleness를 추적하고, 마커 없는 수기 파일(`AGENTS.override.md` 포함)은 절대 덮어쓰지 않습니다. `check_ai_context.py`가 마커·크기 캡(~32 KiB)·staleness·시크릿 스캔을 검증합니다.

## /co-agent:consensus

**cross-family 멀티모델 합의 게이트**가 걸린 자율 doc→plan→구현 파이프라인. **host(Claude/Codex) 자신이 TDD로 구현**하고 패널은 리뷰만 합니다.

```bash
/co-agent:consensus plan <doc...>       # P0–P2: 입력 감지 → plan 로드/생성 → 패널 게이트
/co-agent:consensus review [diff base]  # 팬아웃 리뷰 게이트만 단독 실행
/co-agent:consensus implement <plan>    # P3: 리뷰된 plan을 자율 구현(TDD 루프, 멀티모델 게이트)
/co-agent:consensus                     # 기본값: 전체 P0→P5 파이프라인, resumable
```

**플래그**: `--deep`(각 AI의 전체 모델 리스트로 게이트 실행), `--trust-plan`(plan이 이미 리뷰됐다면 P2 게이트 스킵). 라운드/호출 한도는 `consensus.max_rounds`/`consensus.max_calls` 설정을 따릅니다.

로컬 커밋만 수행(push/reset/rebase 없음). **non-degraded** — gate-eligible peer가 0이면 solo로 강등하지 않고 멈춰서 `/co-agent:setup`을 안내합니다.

## /co-agent:harness

**host-designs / peer-implements / panel-reviews** 오케스트레이터. host가 설계·실패 테스트·검증을 담당하고 **모든 커밋의 유일한 주체**입니다. 크로스벤더 **peer**(Codex 또는 Agy)가 **격리된 git worktree** 안에서만 코드를 작성합니다.

```bash
/co-agent:harness <adr|spec|plan|task>  [--implementer codex|agy]
```

**신뢰 경계**: host는 peer worktree에서 `git add -A && git diff --cached`로 캡처한 diff만 적용 — worktree 밖 쓰기는 절대 메인 트리에 반영되지 않습니다. 캡처된 각 경로는 `scope_guard.py`로 plan 범위를 벗어나지 않는지 검증됩니다. Opt-in, 로컬 커밋만.

> **consensus vs harness**: 둘 다 같은 패널 게이트를 재사용하지만 **누가 코드를 쓰는가**가 다릅니다. consensus는 host 자신이 메인 트리에 직접 쓰고 패널은 리뷰만; harness는 크로스벤더 peer가 격리 worktree에서 쓰고 host는 검증된 diff만 적용합니다.

## /co-agent:setup

**패널 준비도 preflight**. 각 peer의 접근경로를 `plugin` → `raw CLI` → `none` 순으로 감지하고, 접근 가능한 peer는 실제로 짧은 프롬프트를 보내 헤드리스 usability를 프로브합니다.

```bash
/co-agent:setup
```

결과(READY / AUTH / NO_INGEST / TIMEOUT / ERROR / ABSENT)를 `.claude/co-agent-panel.local.json`에 기록합니다. review/decide/adr은 이 결과가 없어도 solo로 강등되지만, **`/co-agent:consensus`·`/co-agent:harness`는 gate-eligible peer(`status==READY` **and** raw CLI 보유)가 0이면 이 명령을 먼저 실행하도록 안내**합니다. 인증 문제는 가이드만 제공하며 자동으로 로그인을 시도하지 않습니다.
