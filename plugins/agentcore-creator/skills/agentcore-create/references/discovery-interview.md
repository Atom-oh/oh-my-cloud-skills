# Phase 1 Discovery — Interview Question Flow

The question list for Phase 1 (Discovery). Interview conduct rules — one question at a
time, plain text (no AskUserQuestion), adapt and skip — live in `SKILL.md` →
"Conversational Interview"; this file holds only the questions.

1. **Purpose**: "What problem should this agent solve? For example:
   a) Automate a repetitive workflow
   b) Provide expert diagnosis/troubleshooting
   c) Generate content or artifacts
   d) Integrate with external services
   e) Something else — describe it"

2. **Users**: "Who will use this agent?
   a) Developers on the team
   b) DevOps/SRE engineers
   c) Non-technical stakeholders
   d) End users via API
   e) Other"

3. **Core capabilities**: "What are the 3-5 key things this agent must be able to do?
   List them, or I can suggest based on what you've described."

4. **External tools**: "Does this agent need to call external services?
   a) AWS services (which ones?)
   b) Third-party APIs (which ones?)
   c) MCP servers (existing or new?)
   d) No external tools needed"

5. **Knowledge sources**: "What knowledge does this agent need?
   a) Existing documentation (point me to it)
   b) Runbooks or SOPs
   c) Code patterns from this repo
   d) Domain expertise (I'll create reference docs)
   e) No special knowledge needed"

6. **Deployment target**: "Where should this agent run?
   a) AgentCore (cloud-hosted — harness config or Runtime code; we pick in Phase 2)
   b) Claude Code skill first, then AgentCore later
   c) Both — build skill first, then deploy
   d) Not sure yet"

7. **Success criteria**: "How will you know this agent is working well? For example:
   a) Resolves X% of issues without escalation
   b) Produces output matching a quality bar
   c) Responds within N seconds
   d) Other metric"
