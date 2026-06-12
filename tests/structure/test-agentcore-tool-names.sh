#!/usr/bin/env bash
# Tests that agentcore-creator references REAL Bedrock AgentCore MCP tool names.
# The `manage_agentcore_*` names never existed on the MCP server; the real API
# exposes verb-specific tools (create_agent_runtime, gateway_create, memory_create, …).
# See ADR-009 (F6 follow-up).

ACC="plugins/agentcore-creator"

# --- Guard: the non-existent placeholder names must be fully eradicated ---
HITS=$(grep -rn "manage_agentcore_" "$ACC" 2>/dev/null || true)
assert_eq "" "$HITS" "no manage_agentcore_* placeholder remains in agentcore-creator"

# --- The real, canonical MCP tool names must be present where management is described ---
MAP="$ACC/skills/agentcore-create/references/agentcore-mapping-rules.md"
FMT="$ACC/skills/agentcore-create/references/agentcore-format-reference.md"
AGENT="$ACC/agents/agentcore-creator-agent.md"

for real in create_agent_runtime get_agent_runtime gateway_create gateway_target_create memory_create; do
  FOUND=$(grep -rl "$real" "$ACC" 2>/dev/null | head -1)
  assert_contains "$FOUND" "$ACC" "real MCP tool referenced somewhere: $real"
done

# --- Already-correct doc tools must remain intact (regression guard) ---
assert_contains "$(cat "$MAP")" "search_agentcore_docs" "search_agentcore_docs still referenced"
assert_contains "$(cat "$MAP")" "fetch_agentcore_doc" "fetch_agentcore_doc still referenced"

# --- The post-deploy management tables/prose must name runtime/gateway/memory real tools ---
assert_contains "$(cat "$FMT")" "memory_create" "format-reference: memory_create in post-deploy table"
assert_contains "$(cat "$FMT")" "gateway_create" "format-reference: gateway_create in post-deploy table"
assert_contains "$(cat "$AGENT")" "get_agent_runtime" "agent: get_agent_runtime in MCP integration"
