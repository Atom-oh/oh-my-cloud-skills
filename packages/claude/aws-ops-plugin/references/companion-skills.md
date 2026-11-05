# Companion skill preflight

Official companion skills are not bundled or automatically installed by this
marketplace. Apply this preflight before every official-plugin handoff, on either
Claude Code or Codex. A plugin namespace is a routing label, not a shell command.

| Requested workflow | Companion plugin / example skill |
|--------------------|----------------------------------|
| Bedrock, CloudWatch, billing, CDK | `aws-core`: `amazon-bedrock`, `aws-observability`, `aws-billing-and-cost-management`, `aws-cdk` |
| Node AgentCore deployment/debugging | `aws-agents`: `agents-deploy`, `agents-debug` (not Python starter-toolkit deployment) |
| Security Agent or DevOps Agent | `aws-agents-for-devsecops`: the exact setup/scan/pentest/investigate/chat skill named at the handoff |
| OpenSearch, lakehouse, S3 Vectors | `aws-data-analytics`: the exact skill named at the handoff |
| Aurora DSQL | `databases-on-aws`: the exact DSQL skill named at the handoff |
| Lambda / Step Functions | `aws-serverless`: the exact skill named at the handoff |

1. **Discover** the required skill in the active session's skill catalog. Resolve
   and read its actual installed procedure. A standalone skill may satisfy the
   handoff only if its loaded procedure covers the requested workflow; a matching
   name alone is not proof. A Claude installation or files in a plugin cache do
   not establish availability in Codex, or vice versa.
2. **Check compatibility** with the current project, CLI family and prerequisites.
   In particular, Node `@aws/agentcore` and Python starter-toolkit both name their
   executable `agentcore`; do not substitute one for the other.
3. **If missing, stop** the dependent section. Name the required companion plugin
   and skill, explain that this host must install/enable it and establish required
   trust, and ask the user to do so via the host's supported installer. Do not
   automatically install plugins, bypass trust or invent slash-command shell calls.
   A documented local alternative can proceed within its own prerequisites and
   approval boundary; independent bundled diagnostics may continue.
4. **Report coverage**: label an unavailable handoff as blocked/not run. Do not
   report an external workflow as executed or verified merely because routing,
   package validation or skill discovery succeeded. Installation is not permission
   to mutate AWS resources; retain the user's scope and explicit approval gates.
