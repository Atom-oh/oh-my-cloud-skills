# Runbook: PR Review Panel 동작 확인

PR을 열면 self-hosted 러너(`oh-my-cloud-skills-claude-arm`)에서 멀티 AI 패널이 자동 리뷰합니다.

## 정상 동작 체크
1. PR 코멘트의 `_Panel:_` 줄에 `codex`, `kiro-opus`, `kiro-kimi`, `kiro-glm`, `antigravity`가 보이면 정상(일부 모델은 등급/쿼터로 간헐 skip 가능).
2. 마지막 줄 `VERDICT: PASS|FAIL`로 게이트 결정(fail-closed).

## 리전/모델 (us-east-1 통일)
- Claude 의장: `us.anthropic.claude-opus-4-8` (US geo, on-demand) · endpoint/region `us-east-1`
- codex: `openai.gpt-5.5` (bedrock-mantle, In-Region us-east-1; 이미지 `~/.codex/config.toml`의 region이 결정)
- AWS 인증: EKS Pod Identity(ci-runner 역할) SigV4

## 패널이 비면(skip) 진단
- 러너 로그의 `[<panel>] skipped; stderr` 블록에서 원인 확인(404 Engine not found = 모델/리전 불일치, credentials 에러 = Pod Identity 누락 등).
