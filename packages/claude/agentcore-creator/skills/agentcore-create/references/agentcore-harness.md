# AgentCore Harness Reference

The managed agent harness (GA 2026-06-17) runs the orchestration loop for you: you declare
what the agent is (model, instructions, tools, skills, memory, limits) as configuration, and
AgentCore assembles and runs it inside an isolated microVM per session — no Strands code, no
container build. Powered by Strands Agents under the hood; exportable to Strands code when
configuration stops being enough. There is no separate harness charge — you pay for the
underlying AgentCore capabilities.

**Why this matters for plugin conversion**: harness skills use the same open Agent Skills
standard as Claude Code — a `SKILL.md` with YAML frontmatter plus optional `scripts/`,
`references/`, `assets/`. A Claude Code plugin's `skills/` directories attach to a harness
**unchanged** via Git or S3 sources. That makes harness the config-only conversion path:
no code generation, no Memory chunking of reference docs (they ship inside the skill).

## Harness vs. Runtime — Decision Grid

Rule of thumb: **harness = configuration, Runtime = you write the code.** Pick Runtime only
when you hit a ❌ below.

| Capability | Harness | Runtime |
|---|---|---|
| Model selection (Bedrock / OpenAI / Gemini / LiteLLM) | ✅ config | 🔵 your code |
| Switch model provider mid-session | ✅ config | 🔵 your code |
| Built-in shell + `file_operations` tools | ✅ config | 🔵 your code |
| Agent Skills (SKILL.md) | ✅ config | 🔵 your code |
| Memory (STM/LTM, per-user actor scoping) | ✅ config | 🔵 your code |
| Gateway / Browser / Code Interpreter / remote MCP tools | ✅ config | 🔵 your code |
| Streaming responses, context truncation, execution limits | ✅ config | 🔵 your code |
| Filesystem (managed session storage, S3 Files, EFS) | ✅ | ✅ |
| Inbound auth (SigV4/OAuth), VPC, versioning + endpoints | ✅ | ✅ |
| Choice of agent framework (LangChain, ADK, ...) | ❌ | 🔵 |
| Custom orchestration (graph/workflow patterns) | ❌ | 🔵 |
| Hooks (Pre/PostToolUse equivalents) | ❌ | 🔵 |
| Bidirectional (WebSocket) streaming | ❌ | 🔵 |
| Inline / client-side tools | 🔵 client code | 🔵 |

Escape hatch: `agentcore export` emits the equivalent Strands code (Claude Agent SDK export
announced as coming) so a harness can graduate to Runtime without starting over.

## API Surface

Control-plane/data-plane operations, the minimal create -> poll `READY` -> invoke flow, the
`runtimeSessionId` (>=33 chars) rule, streaming events and `stopReason` values, versions and
named endpoints: see official `aws-core:amazon-bedrock` `references/agentcore-harness.md`
(Deployment Workflow, Versions and Endpoints, Streaming Response Format). Not repeated here.

## Skills — Four Sources

Skills follow the AgentSkills.io standard (SKILL.md + frontmatter — same as Claude Code).
Set as harness defaults (`CreateHarness`/`UpdateHarness`) or override per invocation
(invoke-time skills append after create-time; same-name → invoke-time wins). Fetched once
per session; re-fetched on new sessions for freshness. Failures are never silent — every
fetch error fails the invocation with a descriptive message.

| Source | Payload | Notes |
|---|---|---|
| AWS curated catalog | `{"awsSkills": {"paths": ["core-skills/*"]}}` | Glob patterns; `{}` = all. From [aws/agent-toolkit-for-aws](https://github.com/aws/agent-toolkit-for-aws/tree/main/skills) |
| Git (HTTPS) | `{"git": {"url": "https://github.com/org/repo", "path": "subdir"}}` | Sparse checkout of subdirs; private repos via `auth.credentialArn` (AgentCore Identity API-key provider holding a PAT); 60s fetch timeout |
| Amazon S3 | `{"s3": {"uri": "s3://bucket/prefix/"}}` | Execution role needs `s3:GetObject` + `s3:ListBucket`; ≤1 GB per skill; works via S3 VPC endpoint (no NAT) |
| Filesystem path | `{"path": ".agents/skills/xlsx"}` | Baked into a custom image or installed at session start via `InvokeAgentRuntimeCommand` |

**Converting a Claude Code plugin skill — attach it unchanged from its repo:**

```python
skills=[
    {"git": {"url": "https://github.com/Atom-oh/oh-my-cloud-skills",
             "path": "plugins/aws-ops-plugin/skills/ops-troubleshoot"}},
]
```

CLI equivalent:

```bash
agentcore add skill --harness my-harness \
  --git https://github.com/Atom-oh/oh-my-cloud-skills \
  --git-path plugins/aws-ops-plugin/skills/ops-troubleshoot
agentcore deploy
```

All four source types can coexist in one payload. AWS-skill paths must be relative (no
leading `/` or `..`); a glob matching nothing fails the invocation with a descriptive error.

### Security and compatibility caveats (read before attaching)

- **Git sources are unpinned.** The `git` payload has no commit/tag field, and skills are
  re-fetched on every new session — the deployed agent tracks the repo's current default
  branch, so an upstream change lands in production sessions without redeploy (skill
  markdown *and* `scripts/` run with the execution role's permissions). For production,
  prefer an **S3 source** (immutable, versioned, gated by the execution role) or a dedicated
  frozen release repo you control; review skill contents at attach time; for private repos,
  scope the PAT in AgentCore Identity to read-only on that one repo. AgentCore Identity
  Credential Providers can reference an *existing* Secrets Manager secret ARN directly (GA
  2026-06) instead of creating a new secret through Identity — keeps the PAT under your own
  Secrets Manager governance (custom CMKs, rotation, tagging). Grant the **AgentCore Identity
  service principal** (not the agent's execution role) `secretsmanager:GetSecretValue` via a
  resource policy on the secret, plus `kms:Decrypt` on the key if it's customer-managed —
  Identity itself retrieves the secret at runtime, not the agent's own role. Scope that
  resource policy with `aws:SourceAccount` (and `aws:SourceArn` where the calling
  workload's ARN is known) so another account's AgentCore Identity can't invoke the same
  service principal to read your secret — the same confused-deputy condition
  `agentcore-mapping-rules.md`'s gateway trust-policy hardening applies, just on the
  secret's resource policy instead of a role trust policy.
- **Sparse checkout fetches only the skill subdir.** A skill that reaches outside its own
  directory — `../` paths, `${CLAUDE_PLUGIN_ROOT}`, assets shared from a sibling skill
  (e.g. this repo's `aws-light-fcd` referencing `reactive-presentation`'s icon library
  in place) — breaks when attached alone. Vendor the shared files into the skill directory
  first, or use the Runtime path. Scan for this before recommending harness (see the
  Phase 4.2 eligibility gate in SKILL.md).
- **A fetchable source is required.** A local-only plugin (no public/private repo, no S3
  bucket) has nothing the harness can fetch — push it to a repo or upload the skill
  directories to S3 before the harness path is viable.

## Models, Memory, Filesystem and Operations

Providers (Bedrock, OpenAI, Gemini, LiteLLM), execution limits, filesystem mounts (S3 Files /
EFS), versions/endpoints, Step Functions, evaluations and observability: see official
`aws-core:amazon-bedrock` `references/agentcore-harness.md`, `agentcore-memory-observability.md`
and `agentcore-registry-evaluations.md`. Conversion-specific residue:

- Instructions (system prompt) are a config field — for plugin conversion, merge the agent
  `.md` body per the standard system-prompt rules in `agentcore-mapping-rules.md`.
- Harness ships memory by default, so reference docs inside attached skills need no Memory
  chunking (unlike the Runtime path).

## AgentCore CLI Flow (npm toolchain)

The harness path uses the Node-based AgentCore CLI (distinct from the Python
`bedrock-agentcore-starter-toolkit` used by the Runtime code path).

> **Executable-name collision**: both toolchains install a binary named `agentcore`. If the
> Python starter toolkit is also installed (or a venv is active), an unqualified `agentcore`
> may resolve to the wrong CLI and harness commands will fail confusingly. Disambiguate:
> run the Node CLI as `npx @aws/agentcore <cmd>`, or check `which agentcore` first and keep
> the Python one venv-scoped. Pin the install (`npm install -g @aws/agentcore@<version>`)
> for reproducible tooling.

```bash
npm install -g @aws/agentcore        # Node.js 20+; pin @<version> in CI

agentcore create --name myagent --model-provider bedrock   # or bare `agentcore create` for the TUI wizard
agentcore add skill --harness myagent --git <url> --git-path <subdir>
agentcore deploy

SESSION_ID="$(uuidgen)"              # standard hyphenated UUID (36 chars — the >=33-char rule needs the hyphens)
agentcore invoke --harness myagent --session-id "$SESSION_ID" "smoke test prompt"
agentcore invoke --harness myagent --session-id "$SESSION_ID" "follow-up"   # SAME id → verifies memory/session persistence
agentcore dev                        # local dev server + browser Agent Inspector
agentcore status
```

- `agentcore invoke --skills <sources>` overrides skills for a single call (comma-separated
  paths, `s3://` URIs, or `https://` Git URLs; no Git auth on the override).
- `agentcore invoke --exec` runs a shell command in the session (wraps
  `InvokeAgentRuntimeCommand`) — useful for installing path-source skills at session start.
- `agentcore export` — emit Strands code from the harness definition (graduate to Runtime).

## Availability

GA in all AWS Commercial Regions where AgentCore is available (SOC 1/2/3, ISO, CSA STAR in
scope; GovCloud US-West supported for AgentCore overall). Confirm current region coverage
via `search_agentcore_docs` at conversion time.
