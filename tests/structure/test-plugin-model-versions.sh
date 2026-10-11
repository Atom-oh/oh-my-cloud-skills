MODEL_VERSION_RESULT=$(python3 - <<'PY'
import ast
import json
import runpy
from pathlib import Path

converter = runpy.run_path('plugins/agentcore-creator/skills/agentcore-create/scripts/convert_plugin_to_agentcore.py')
expected = {
    'opus': 'us.anthropic.claude-opus-5-5',
    'sonnet': 'us.anthropic.claude-sonnet-5-5',
    'haiku': 'us.anthropic.claude-haiku-5-5',
    'fable': 'us.anthropic.claude-fable-5-1',
}
assert converter['MODEL_MAP'] == expected
assert converter['DEFAULT_MODEL'] == expected['sonnet']
for alias, model_id in expected.items():
    assert converter['resolve_model_id'](alias) == model_id
    # This checks literal/profile parsing, not availability in every geography.
    for prefix in ('us.', 'global.', 'eu.', 'apac.', 'au.', 'jp.', 'ca.', 'us-gov.', ''):
        selected_model = prefix + model_id[len('us.'):]
        assert converter['resolve_model_id'](selected_model) == selected_model
        for framework in ('strands', 'raw'):
            generated = converter['generate_agent_code']('model_check', selected_model, framework)
            ast.parse(generated)
            assert selected_model in generated
            assert '"type": "adaptive"' in generated
            expected_effort = 'medium' if alias == 'haiku' else 'high'
            assert '"effort": "{}"'.format(expected_effort) in generated
            if alias in ('opus', 'fable'):
                assert '"refusal"' in generated
            assert 'budget_tokens' not in generated
            assert 'temperature=' not in generated

for legacy_model in ('us.anthropic.claude-opus-5', 'global.anthropic.claude-fable-5', 'us.anthropic.claude-opus-4-8'):
    assert converter['resolve_model_id'](legacy_model) == legacy_model
    generated = converter['generate_agent_code']('legacy_check', legacy_model, 'strands')
    assert '"type": "adaptive"' in generated
legacy_haiku = converter['generate_agent_code']('legacy_check', 'us.anthropic.claude-haiku-4-5-20251001-v1:0', 'strands')
assert 'additional_request_fields=' not in legacy_haiku
for invalid in ('us.anthropic.claude-opus-5-5"\nmalformed', 'unknown', 'amazon.nova-pro-v1:0'):
    try:
        converter['resolve_model_id'](invalid)
    except ValueError:
        pass
    else:
        raise AssertionError('unsupported selection silently changed models')

defaults = json.loads(Path('plugins/co-agent/skills/co-agent/co-agent.defaults.json').read_text())
assert defaults['panel']['codex']['model'] == 'openai.gpt-6.1-sol'
runtime = Path('scripts/codex/runtime.md').read_text()
for model in ('gpt-6.1-sol', 'gpt-6-luna', 'gpt-6-astra', 'gpt-5.6-terra'):
    assert model in runtime
print('PASS')
PY
)
assert_eq "PASS" "$MODEL_VERSION_RESULT" "current plugin model aliases, generated compatibility, and Codex routing"
