"""Execute generated agents with local SDK-shaped stubs; no AWS requests."""
import asyncio
import copy
from contextlib import redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "plugins/agentcore-creator/skills/agentcore-create/scripts/convert_plugin_to_agentcore.py"
SPEC = importlib.util.spec_from_file_location("agentcore_converter_regression", SCRIPT)
CONVERTER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CONVERTER)
REGION = "ap-northeast-2"


class RequestContext:
    """SDK-shaped context intentionally has attributes, no mapping methods."""
    session_id = "11111111-1111-1111-1111-111111111111"
    request_headers = {}
    request = None


class ConversionTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="agentcore-conversion-")
        self.root = Path(self.directory.name)
        self.source = self.root / "source"
        (self.source / ".claude-plugin").mkdir(parents=True)
        (self.source / "agents").mkdir()
        (self.source / "agents/fixture-agent.md").write_text(
            "---\nname: fixture-agent\nmodel: haiku\n---\nAnswer the prompt.\n", encoding="utf-8")
        self.manifest = {
            "name": "fixture", "version": "1.0.0",
            "agents": ["./agents/fixture-agent.md"], "skills": [],
            "hooks": {
                "SessionStart": [{"hooks": [
                    {"type": "command", "command": "echo COMMAND_HOOK_MARKER"},
                    {"type": "prompt", "prompt": "PROMPT_HOOK_MARKER: check the result."},
                ]}],
                "PreToolUse": [{"matcher": "Bash", "hooks": [
                    {"type": "command", "command": "echo PRECHECK_MARKER"},
                ]}],
                "Stop": [{"hooks": [{"type": "prompt", "prompt": "STOP_HOOK_MARKER"}]}],
                "UnknownEvent": [{"hooks": [{"type": "unsupported", "command": "UNKNOWN_MARKER"}]}],
            },
        }
        self.write_manifest()

    def tearDown(self):
        self.directory.cleanup()

    def write_manifest(self):
        (self.source / ".claude-plugin/plugin.json").write_text(
            json.dumps(self.manifest), encoding="utf-8")

    def convert(self, framework):
        output = self.root / framework
        with redirect_stdout(io.StringIO()):
            CONVERTER.convert(self.source, output, REGION, framework, False, False, False)
        return output

    def load_generated(self, output, stubs):
        path = output / "agents/fixture-agent.py"
        spec = importlib.util.spec_from_file_location("generated_fixture_" + output.name, path)
        module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, stubs):
            spec.loader.exec_module(module)
        return module

    def model_module(self, model_id, framework, stubs):
        """Load a real generated module without importing any provider SDK."""
        directory = self.root / f"model-{len(list(self.root.glob('model-*')))}"
        (directory / "system-prompts").mkdir(parents=True)
        (directory / "system-prompts/fixture-agent.md").write_text("Offline model fixture.")
        path = directory / "agent.py"
        path.write_text(CONVERTER.generate_agent_code("fixture-agent", model_id, framework, REGION))
        spec = importlib.util.spec_from_file_location(directory.name, path)
        module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, stubs):
            spec.loader.exec_module(module)
        return module

    def sdk_stubs(self, framework, calls, response):
        if framework == "raw":
            class Client:
                def converse(self, **kwargs):
                    calls.append(("request", copy.deepcopy(kwargs)))
                    return copy.deepcopy(response)

            def client(service, *, region_name):
                calls.append(("client", service, region_name))
                return Client()

            boto3 = types.ModuleType("boto3")
            boto3.client = client
            return {"boto3": boto3}

        class BedrockAgentCoreApp:
            def entrypoint(self, handler):
                return handler

        class BedrockModel:
            def __init__(self, *, region_name=None, **model_config):
                calls.append(("model", region_name, model_config))

        class AgentResult:
            def __init__(self):
                self.stop_reason = response["stopReason"]
                self.message = response["output"]["message"]

            def __str__(self):
                # Match the public Strands AgentResult text-block behavior.
                return "".join(block["text"] + "\n" for block in self.message["content"]
                               if "text" in block)

        class Agent:
            def __init__(self, *, model, system_prompt):
                self.system_prompt = system_prompt

            def __call__(self, prompt):
                calls.append(("request", prompt, self.system_prompt))
                return AgentResult()

        runtime = types.ModuleType("bedrock_agentcore.runtime")
        runtime.BedrockAgentCoreApp = BedrockAgentCoreApp
        strands = types.ModuleType("strands")
        strands.Agent = Agent
        bedrock = types.ModuleType("strands.models.bedrock")
        bedrock.BedrockModel = BedrockModel
        return {
            "bedrock_agentcore": types.ModuleType("bedrock_agentcore"),
            "bedrock_agentcore.runtime": runtime,
            "strands": strands,
            "strands.models": types.ModuleType("strands.models"),
            "strands.models.bedrock": bedrock,
        }

    @staticmethod
    def model_response(content=None, stop_reason="end_turn"):
        if content is None:
            content = [{"text": "offline final answer"}]
        return {"stopReason": stop_reason,
                "output": {"message": {"role": "assistant", "content": content}}}

    def test_strands_handler_reaches_model_with_sdk_context_and_selected_region(self):
        calls = []

        class BedrockAgentCoreApp:
            def entrypoint(self, handler):
                return handler

        class BedrockModel:
            def __init__(self, **kwargs):
                calls.append(("model", kwargs))

        class Agent:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

            def __call__(self, prompt):
                calls.append(("invoke", prompt, self.kwargs["system_prompt"]))
                return "offline reply"

        runtime = types.ModuleType("bedrock_agentcore.runtime")
        runtime.BedrockAgentCoreApp = BedrockAgentCoreApp
        strands = types.ModuleType("strands")
        strands.Agent = Agent
        bedrock = types.ModuleType("strands.models.bedrock")
        bedrock.BedrockModel = BedrockModel
        stubs = {
            "bedrock_agentcore": types.ModuleType("bedrock_agentcore"),
            "bedrock_agentcore.runtime": runtime, "strands": strands,
            "strands.models": types.ModuleType("strands.models"), "strands.models.bedrock": bedrock,
        }
        output = self.convert("strands")
        module = self.load_generated(output, stubs)
        result = asyncio.run(module.invoke({"prompt": "offline request"}, RequestContext()))
        self.assertEqual(result, {"result": "offline reply"})
        self.assertEqual(calls[0][1]["region_name"], REGION)
        self.assertEqual(calls[0][1]["model_id"], CONVERTER.MODEL_MAP["haiku"])
        self.assertEqual(calls[1][1], "offline request")
        self.assertIn("PROMPT_HOOK_MARKER", calls[1][2])
        self.assertEqual(json.loads((output / "agent-config.json").read_text())["region"], REGION)

    def test_raw_local_handler_reaches_converse_in_selected_region(self):
        calls = []

        class Client:
            def converse(self, **kwargs):
                calls.append(("converse", kwargs))
                return {"stopReason": "end_turn",
                        "output": {"message": {"role": "assistant",
                                               "content": [{"text": "offline raw reply"}]}}}

        def client(service, **kwargs):
            calls.append(("client", service, kwargs))
            return Client()

        boto3 = types.ModuleType("boto3")
        boto3.client = client
        module = self.load_generated(self.convert("raw"), {"boto3": boto3})
        with patch.dict(sys.modules, {"boto3": boto3}):
            agent = module.LocalTestAgent()
            result = agent.invoke("offline raw request")
        self.assertEqual(result, "offline raw reply")
        self.assertEqual(calls[0], ("client", "bedrock-runtime", {"region_name": REGION}))
        self.assertEqual(calls[1][1]["modelId"], CONVERTER.MODEL_MAP["haiku"])
        self.assertEqual(calls[1][1]["messages"][0]["content"], [{"text": "offline raw request"}])
        self.assertEqual(calls[1][1]["inferenceConfig"]["maxTokens"], 16000)
        self.assertEqual(agent.messages[-1]["role"], "assistant")

    def test_generated_aliases_and_profile_syntax_dispatch_correct_model_effort(self):
        # Structural/profile preservation coverage does not certify regional access.
        prefixes = ("", "us.", "global.", "eu.", "apac.", "au.", "jp.", "ca.", "us-gov.")
        for alias, mapped in CONVERTER.MODEL_MAP.items():
            self.assertEqual(CONVERTER.resolve_model_id(alias), mapped)
            for prefix in prefixes:
                model_id = prefix + mapped[len("us."):]
                self.assertEqual(CONVERTER.resolve_model_id(model_id), model_id)
                for framework in ("raw", "strands"):
                    with self.subTest(alias=alias, prefix=prefix, framework=framework):
                        calls = []
                        stubs = self.sdk_stubs(framework, calls, self.model_response())
                        module = self.model_module(model_id, framework, stubs)
                        if framework == "raw":
                            agent = module.LocalTestAgent()
                            self.assertEqual(agent.invoke("offline request"), "offline final answer")
                            self.assertEqual(calls[0], ("client", "bedrock-runtime", REGION))
                            request = calls[1][1]
                            self.assertEqual(request["modelId"], model_id)
                            self.assertEqual(request["inferenceConfig"], {"maxTokens": 16000})
                            fields = request["additionalModelRequestFields"]
                        else:
                            result = asyncio.run(module.invoke({"prompt": "offline request"}, RequestContext()))
                            self.assertEqual(result, {"result": "offline final answer\n"})
                            self.assertEqual(calls[0][1], REGION)
                            request = calls[0][2]
                            self.assertEqual(request["model_id"], model_id)
                            self.assertEqual(request["max_tokens"], 16000)
                            fields = request["additional_request_fields"]
                        self.assertEqual(fields, {
                            "thinking": {"type": "adaptive"},
                            "output_config": {"effort": "medium" if alias == "haiku" else "high"},
                        })

    def test_pinned_legacy_haiku_omits_unsupported_reasoning_fields(self):
        model_id = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
        self.assertEqual(CONVERTER.resolve_model_id(model_id), model_id)
        for framework in ("raw", "strands"):
            with self.subTest(framework=framework):
                calls = []
                module = self.model_module(model_id, framework,
                                           self.sdk_stubs(framework, calls, self.model_response()))
                if framework == "raw":
                    module.LocalTestAgent().invoke("offline request")
                    request = calls[1][1]
                    self.assertEqual(request["modelId"], model_id)
                    self.assertNotIn("additionalModelRequestFields", request)
                else:
                    asyncio.run(module.invoke({"prompt": "offline request"}, RequestContext()))
                    self.assertEqual(calls[0][2]["model_id"], model_id)
                    self.assertNotIn("additional_request_fields", calls[0][2])

    def test_raw_reasoning_first_multitext_preserves_signed_history(self):
        response = self.model_response([
            {"reasoningContent": {"reasoningText": {
                "text": "synthetic reasoning", "signature": "synthetic signature"}}},
            {"text": "offline answer"}, {"text": " continued"},
        ])
        calls = []
        module = self.model_module(CONVERTER.MODEL_MAP["haiku"], "raw",
                                   self.sdk_stubs("raw", calls, response))
        agent = module.LocalTestAgent()
        self.assertEqual(agent.invoke("first request"), "offline answer continued")
        self.assertEqual(agent.messages[-1], response["output"]["message"])
        agent.invoke("second request")
        self.assertEqual(calls[2][1]["messages"][1], response["output"]["message"])

    def test_refusal_is_distinct_for_every_alias_in_both_frameworks(self):
        response = self.model_response([], "refusal")
        for alias, model_id in CONVERTER.MODEL_MAP.items():
            for framework in ("raw", "strands"):
                with self.subTest(alias=alias, framework=framework):
                    module = self.model_module(
                        model_id, framework, self.sdk_stubs(framework, [], response))
                    if framework == "raw":
                        with self.assertRaises(module.ModelRefusalError):
                            module.LocalTestAgent().invoke("offline request")
                    else:
                        result = asyncio.run(module.invoke({"prompt": "offline request"}, RequestContext()))
                        self.assertEqual(result, {"result": "", "refused": True})

    def test_empty_or_unsupported_model_output_cannot_report_success(self):
        for content in ([], [{"reasoningContent": {"redactedContent": b"synthetic"}}],
                        [{"text": ""}], [{"text": "   "}]):
            for framework in ("raw", "strands"):
                with self.subTest(content=content, framework=framework):
                    module = self.model_module(
                        CONVERTER.MODEL_MAP["opus"], framework,
                        self.sdk_stubs(framework, [], self.model_response(content)))
                    with self.assertRaisesRegex(ValueError, "no supported text content"):
                        if framework == "raw":
                            module.LocalTestAgent().invoke("offline request")
                        else:
                            asyncio.run(module.invoke({"prompt": "offline request"}, RequestContext()))

    def test_unsupported_model_selections_do_not_fall_back_to_us_sonnet(self):
        for selected in ("unknown", "amazon.nova-pro-v1:0", "anthropic.claude-haiku-5-5\"\nbad"):
            with self.subTest(selected=selected):
                with self.assertRaisesRegex(ValueError, "Unsupported model selection"):
                    CONVERTER.resolve_model_id(selected)

    def test_invalid_model_selection_precedes_output_mutation(self):
        (self.source / "agents/fixture-agent.md").write_text(
            "---\nname: fixture-agent\nmodel: unknown\n---\nAnswer the prompt.\n")
        for exists in (False, True):
            with self.subTest(exists=exists):
                output = self.root / ("prior-output" if exists else "no-output")
                if exists:
                    output.mkdir()
                    (output / "sentinel").write_bytes(b"prior artifact")
                with self.assertRaisesRegex(ValueError, "Unsupported model selection"):
                    CONVERTER.convert(self.source, output, REGION, "raw", False, False, False)
                if exists:
                    self.assertEqual(list(output.iterdir()), [output / "sentinel"])
                    self.assertEqual((output / "sentinel").read_bytes(), b"prior artifact")
                else:
                    self.assertFalse(output.exists())

    def test_hook_report_matches_generated_instructions_and_missing_handlers(self):
        output = self.convert("strands")
        prompt = (output / "agents/system-prompts/fixture-agent.md").read_text(encoding="utf-8")
        report = (output / "hooks-gap-analysis.md").read_text(encoding="utf-8")
        self.assertIn("PROMPT_HOOK_MARKER", prompt)
        self.assertIn("Advisory Only", prompt)
        for marker in ("COMMAND_HOOK_MARKER", "PRECHECK_MARKER", "STOP_HOOK_MARKER", "UNKNOWN_MARKER"):
            self.assertNotIn(marker, prompt)
            self.assertIn(marker, report)
        rows = {line.split("|")[1].strip(): line for line in report.splitlines() if line.startswith("| ")}
        self.assertIn("manual follow-up", rows["SessionStart/1/1"])
        self.assertIn("generated instruction", rows["SessionStart/1/2"])
        self.assertIn("manual follow-up", rows["PreToolUse/1/1"])
        self.assertIn("manual follow-up", rows["Stop/1/1"])
        self.assertIn("not migrated", rows["UnknownEvent/1/1"])
        self.assertIn("no hook adapter or enforcement", report)
        self.assertEqual(sorted(path.name for path in (output / "agents").glob("*.py")), ["fixture-agent.py"])

    def test_prompt_hook_with_no_agents_is_manual_follow_up(self):
        self.manifest["agents"] = []
        self.write_manifest()
        output = self.convert("strands")
        report = (output / "hooks-gap-analysis.md").read_text(encoding="utf-8")
        row = next(line for line in report.splitlines() if line.startswith("| SessionStart/1/2 "))
        self.assertIn("manual follow-up", row)
        self.assertNotIn("generated instruction", row)
        self.assertEqual(list((output / "agents/system-prompts").iterdir()), [])

    def test_lambda_flag_fails_before_creating_or_changing_output(self):
        for existing in (False, True):
            with self.subTest(existing=existing):
                output = self.root / ("existing" if existing else "missing")
                if existing:
                    output.mkdir()
                    (output / "keep.txt").write_text("unchanged", encoding="utf-8")
                result = subprocess.run(
                    [sys.executable, "-B", str(SCRIPT), "--source", str(self.source),
                     "--output", str(output), "--enable-lambda"],
                    capture_output=True, text=True, check=False,
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("--enable-lambda is not implemented", result.stderr)
                self.assertEqual(result.stdout, "")
                if existing:
                    self.assertEqual([p.name for p in output.iterdir()], ["keep.txt"])
                    self.assertEqual((output / "keep.txt").read_text(), "unchanged")
                else:
                    self.assertFalse(output.exists())

    def test_library_lambda_guard_precedes_source_and_output_access(self):
        output = self.root / "library-output"
        with self.assertRaisesRegex(ValueError, "--enable-lambda is not implemented"):
            CONVERTER.convert(self.root / "nonexistent", output, REGION, "strands", False, False, True)
        self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
