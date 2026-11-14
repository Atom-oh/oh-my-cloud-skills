# Removed plugins must not remain installable in either host marketplace.
_retired_plugins='agentcore-creator atlas token-saver kiro-power-converter kiro'
for _plugin in $_retired_plugins; do
  for _tree in plugins hosts/claude hosts/codex packages/claude packages/codex; do
    assert_eq "absent" "$(test ! -e "$_tree/$_plugin" && echo absent || echo present)" \
      "retired plugin $_plugin is absent from $_tree"
  done
done
for _registry in hosts/catalog.json .claude-plugin/marketplace.json .agents/plugins/marketplace.json; do
  _remaining=$(python3 - "$_registry" <<'PY'
import json, sys
removed = {"agentcore-creator", "atlas", "token-saver", "kiro-power-converter", "kiro"}
plugins = json.load(open(sys.argv[1]))["plugins"]
names = set(plugins) if isinstance(plugins, dict) else {item["name"] for item in plugins}
print(" ".join(sorted(names & removed)))
PY
)
  assert_eq "" "$_remaining" "$_registry excludes retired plugins"
done
unset _retired_plugins _plugin _tree _registry _remaining
