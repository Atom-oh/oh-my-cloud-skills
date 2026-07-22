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

Control plane (`bedrock-agentcore-control`): `CreateHarness`, `GetHarness`, `UpdateHarness`,
`DeleteHarness`, `ListHarnesses`, `ListHarnessVersions`, plus endpoint CRUD
(`CreateHarnessEndpoint` / `GetHarnessEndpoint` / `UpdateHarnessEndpoint` /
`DeleteHarnessEndpoint` / `ListHarnessesEndpoints`).
Data plane (`bedrock-agentcore`): `InvokeHarness`, `InvokeAgentRuntimeCommand` (direct shell
into the session's microVM).

Minimal create + invoke:

```bash
aws bedrock-agentcore-control create-harness \
  --harness-name "MyHarness" \
  --execution-role-arn "arn:aws:iam::<account>:role/MyHarnessRole"

# create-harness returns harnessId (name + generated suffix) and arn — use those below
# Poll until "status": "READY"
aws bedrock-agentcore-control get-harness --harness-id "MyHarness-XyZ123"
```

```python
import boto3
client = boto3.client("bedrock-agentcore", region_name="us-west-2")

response = client.invoke_harness(
    harnessArn="arn:aws:bedrock-agentcore:us-west-2:<account>:harness/MyHarness-XyZ123",
    runtimeSessionId="1234abcd-12ab-34cd-56ef-1234567890ab",  # MUST be >= 33 chars
    messages=[{"role": "user", "content": [{"text": "..."}]}],
)
for event in response["stream"]:
    if "contentBlockDelta" in event:
        delta = event["contentBlockDelta"].get("delta", {})
        if "text" in delta:
            print(delta["text"], end="", flush=True)
```

- `runtimeSessionId` must be **at least 33 characters** (use a UUID). Reuse the same ID to
  continue the conversation in the same environment; sessions are stateful by default.
- If no model is specified, the harness defaults to **Claude Sonnet 4.6 on Bedrock**.

### InvokeHarness streaming events

`messageStart` → `contentBlockStart` → `contentBlockDelta` (text / `toolUse` input /
`reasoningContent`) → `contentBlockStop` → `messageStop` (+ `metadata` usage/latency,
`runtimeClientError` on failure). `stopReason` values in `messageStop`:

| stopReason | Meaning |
|---|---|
| `end_turn` | Finished normally |
| `tool_use` | Waiting on a client-side inline tool result |
| `max_tokens` | Per-turn model token limit hit |
| `max_iterations_exceeded` | `maxIterations` limit hit |
| `timeout_exceeded` | `timeoutSeconds` limit hit |
| `max_output_tokens_exceeded` | `maxTokens` budget exhausted |

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
  Secrets Manager governance (custom CMKs, rotation, tagging). The execution role still needs
  `secretsmanager:GetSecretValue` on that secret's resource policy, plus `kms:Decrypt` if it's
  encrypted with a customer-managed key.
- **Sparse checkout fetches only the skill subdir.** A skill that reaches outside its own
  directory — `../` paths, `${CLAUDE_PLUGIN_ROOT}`, assets shared from a sibling skill
  (e.g. this repo's `aws-light-fcd` referencing `reactive-presentation`'s icon library
  in place) — breaks when attached alone. Vendor the shared files into the skill directory
  first, or use the Runtime path. Scan for this before recommending harness (see the
  Phase 4.2 eligibility gate in SKILL.md).
- **A fetchable source is required.** A local-only plugin (no public/private repo, no S3
  bucket) has nothing the harness can fetch — push it to a repo or upload the skill
  directories to S3 before the harness path is viable.

## Models and Instructions

- Providers: Amazon Bedrock (default), OpenAI, Google Gemini, or any LiteLLM-compatible
  provider. **Bedrock Mantle** unlocks non-Anthropic frontier models (e.g. GPT-5.5 / GPT-5.4)
  on Bedrock through the same config.
- **Mid-session provider switching** without losing context — plan with one model, execute
  with another; harness preserves the conversation.
- Instructions (system prompt) are a config field — for plugin conversion, merge the agent
  `.md` body per the standard system-prompt rules in `agentcore-mapping-rules.md`.
- Execution limits are config: `maxIterations`, `timeoutSeconds`, `maxTokens`, idle/lifetime
  timeouts, context-window truncation.

## Memory and Filesystem

- **Built-in memory by default** (GA behavior): short-term and long-term memory persist
  across sessions even after the microVM expires. Bring-your-own AgentCore Memory resource
  is supported for shared/custom strategies; per-user scoping via actor ID.
- Each session gets its own filesystem and shell. Beyond managed session storage, mount
  **S3 Files** (round-trip with a bucket) and/or **EFS access points** (low-latency shared
  storage) — up to **5 mounts per harness**, attached at `CreateHarness`/`UpdateHarness`,
  mounted into every session at a path you choose.

## Operations

- **Versioning + named endpoints**: versions are immutable; point an endpoint (e.g. `prod`)
  at a version, roll back instantly by re-pointing.
- **Step Functions**: native `InvokeHarness` state — run harnesses in parallel/sequence,
  wrap with human approval or error handling; per-invocation overrides of model, system
  prompt, and tools from the workflow.
- **Evaluations / Optimization**: score live traffic with built-in evaluators, get prompt and
  tool-description recommendations, validate with batch evaluations and A/B tests — all GA
  and wired into harness without extra plumbing.
- **Observability**: every action traced automatically with a unified cross-capability view;
  `ActiveSessionCount` CloudWatch metric (`AWS/Bedrock-AgentCore` namespace, `Service`
  dimension) for capacity monitoring.

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
