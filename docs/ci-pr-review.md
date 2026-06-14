# CI: Multi-AI PR Review Panel

이 repo의 PR은 self-hosted 러너(`<runner-label>`)에서 멀티 AI 패널 리뷰를 받습니다.

## 구성
- **패널**: Codex(`openai.gpt-5.5`) + Kiro(`claude-opus-4.8`/`kimi-k2.5`/`glm-5`) + Antigravity(`agy`, free-tier best-effort)
- **의장**: Claude Opus 4.8(`us.anthropic.claude-opus-4-8`)이 패널 findings를 종합해 단일 리뷰 + `VERDICT: PASS|FAIL`(fail-closed) 생성
- **데이터 거주성**: 패널마다 경로가 다름 —
  - **Codex / Claude(의장)**: Amazon Bedrock **us-east-1 In-Region**(gpt-5.5는 bedrock-mantle In-Region 전용, opus-4-8도 In-Region), AWS 인증은 EKS Pod Identity(SigV4).
  - **Kiro / Antigravity**: **외부 API-key 기반 서비스**(Antigravity=Google, agy free-tier) — PR diff가 외부로 전송됨. In-Region 아님.
  - **민감 diff 정책**: 외부 전송이 부적절한 변경은 외부 패널(Kiro/Antigravity)을 비활성화하고 Bedrock In-Region 패널만으로 리뷰할 것.

## 파일
- `.github/workflows/pr-review.yml` — `pull_request_target`(base-ref 체크아웃, diff는 데이터), fan-out→synthesize→게이트→코멘트 upsert
- `scripts/pr-review/{lib,run-panel,synthesize}.sh` — 패널 병렬 실행 + 의장 종합. 실패 패널은 graceful skip. 진단 로그는 **redact(auth/provider/프롬프트/diff 단편 제거) + 길이 제한**을 기본 동작으로 함(원시 stderr를 코멘트/로그로 노출하지 않음).

## 인증
- Kiro/Antigravity: `ai-panel-keys` ExternalSecret(`<secret-path>`) → 러너 env
- Codex/Claude: 노드 IAM(`<ci-runner-role>`, Bedrock) SigV4 — Pod Identity Association 필요
