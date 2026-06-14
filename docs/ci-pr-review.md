# CI: Multi-AI PR Review Panel

이 repo의 PR은 self-hosted 러너(`oh-my-cloud-skills-claude-arm`)에서 멀티 AI 패널 리뷰를 받습니다.

## 구성
- **패널**: Codex(`openai.gpt-5.5`) + Kiro(`claude-opus-4.8`/`kimi-k2.5`/`glm-5`) + Antigravity(`agy`, free-tier best-effort)
- **의장**: Claude Opus 4.8(`anthropic.claude-opus-4-8`)이 패널 findings를 종합해 단일 리뷰 + `VERDICT: PASS|FAIL`(fail-closed) 생성
- **리전**: 전부 **us-east-1 In-Region**(gpt-5.5는 bedrock-mantle In-Region 전용, opus-4-8도 In-Region). AWS 인증은 EKS Pod Identity(ci-runner 역할, SigV4).

## 파일
- `.github/workflows/pr-review.yml` — `pull_request_target`(base-ref 체크아웃, diff는 데이터), fan-out→synthesize→게이트→코멘트 upsert
- `scripts/pr-review/{lib,run-panel,synthesize}.sh` — 패널 병렬 실행 + 의장 종합. 실패 패널은 graceful skip(+stderr 로그 노출)

## 인증
- Kiro/Antigravity: `ai-panel-keys` ExternalSecret(`/demo-platform/actions/AI-key`) → 러너 env
- Codex/Claude: 노드 IAM(ci-runner, Bedrock) SigV4 — Pod Identity Association 필요
