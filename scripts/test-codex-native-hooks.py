#!/usr/bin/env python3
"""Prove native Kiro/patch hook execution using a loopback Responses fixture.

Requires Codex 0.154-compatible APIs and freshly generated Kiro adapters.
Only --report survives cleanup. No external inference or user-config writes.
The model name selects client tool capabilities; the fixture generates every reply.
"""
import argparse
from contextlib import ExitStack
import gzip
import http.server
import json
import os
from pathlib import Path
import runpy
import selectors
import shutil
import subprocess
import sys
import tempfile
import threading
import time

RPC = runpy.run_path(str(Path(__file__).with_name("test-codex-runtime.py")))
PATCH = "*** Begin Patch\n*** Add File: native-one.txt\n+one\n*** Add File: native-two.md\n+two\n*** End Patch\n"
DENY = {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                               "permissionDecisionReason": "fixture denied"}}
DENIALS = {
    "ask": [{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "ask"}}, {}],
    "deny-error": [DENY, {"fixtureExit": 1}],
    "stop": [{"continue": False, "stopReason": "fixture stopped"}, {}],
    "suppress-deny": [{**DENY, "suppressOutput": True}, {}],
}


def denial_patch(phase):
    return "*** Begin Patch\n" + "".join(
        f"*** Add File: {phase}-{i}.txt\n+MUST_NOT_EXIST\n" for i in range(2)
    ) + "*** End Patch\n"


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


class ResponsesFixture(http.server.BaseHTTPRequestHandler):
    def log_message(self, *_args):
        pass

    def do_POST(self):
        server = self.server
        item = {"type": "message", "id": "msg_" + str(server.requests + 1), "role": "assistant",
                "content": [{"type": "output_text", "text": "LOCAL_FIXTURE_DONE", "annotations": []}]}
        try:
            raw = self.rfile.read(int(self.headers["Content-Length"]))
            if self.headers.get("Content-Encoding") == "gzip":
                raw = gzip.decompress(raw)
            request = json.loads(raw)
            require(self.path == "/v1/responses", "Unexpected fixture endpoint")
            server.routing_seen |= "kiro loaded." in json.dumps(request.get("input", []))
            server.requests += 1
            if server.phase != "baseline" and server.phase not in server.sent:
                server.sent.add(server.phase)
                tools = [sub for tool in request["tools"]
                         for sub in (tool["tools"] if tool["type"] == "namespace" else [tool])]
                name = "exec_command" if server.phase == "bash" else "apply_patch"
                offered = next(tool for tool in tools if tool.get("name") == name)
                item = {"id": "tool_" + str(server.requests), "call_id": "call_" + server.phase, "name": name}
                if server.phase == "bash":
                    item.update(type="function_call", arguments=json.dumps({
                        "cmd": "printf 'NATIVE_KIRO_BRIDGE_EXECUTED\\n'",
                        "workdir": str(server.workspace), "login": False}))
                else:
                    require(offered["type"] == "custom", "apply_patch is not an offered custom tool")
                    server.patch_schema = offered
                    item.update(type="custom_tool_call",
                                input=PATCH if server.phase == "patch" else denial_patch(server.phase))
        except Exception as exc:
            server.error = str(exc)  # Finish the turn so the assertion fails without retry storms.
        response = {"id": "resp_" + str(server.requests), "object": "response", "created_at": 1,
                    "model": "gpt-5.4", "status": "completed", "output": [item],
                    "usage": {"input_tokens": 1, "output_tokens": 1, "total_tokens": 2}}
        events = [
            {"type": "response.created", "response": {**response, "status": "in_progress", "output": []}},
            {"type": "response.output_item.added", "output_index": 0, "item": item},
            {"type": "response.output_item.done", "output_index": 0, "item": item},
            {"type": "response.completed", "response": response},
        ]
        body = "".join("event: " + event["type"] + "\ndata: " +
                       json.dumps({**event, "sequence_number": i}) + "\n\n"
                       for i, event in enumerate(events)).encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def stop(process):
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)
    process.stdin.close()
    process.stdout.close()


def probe(root, temp_dir, report):
    source = root / "plugins/kiro"
    require((source / ".codex-plugin/hook.py").read_bytes() ==
            (root / "scripts/codex/hook.py").read_bytes(), "Regenerate Kiro adapters before this test")
    with tempfile.TemporaryDirectory(prefix="codex native hooks ", dir=temp_dir) as tmp, ExitStack() as stack:
        tmp = Path(tmp)
        state, workspace, market = tmp / "state", tmp / "consumer", tmp / "market"
        state.mkdir()
        workspace.mkdir()
        package = market / "plugins/kiro"
        shutil.copytree(source, package, ignore=shutil.ignore_patterns("__pycache__"))
        capture = market / "plugins/patch-capture"
        (capture / ".codex-plugin").mkdir(parents=True)
        payload_file, provider_called = tmp / "payload.jsonl", tmp / "provider-called"
        (capture / ".codex-plugin/plugin.json").write_text(json.dumps({
            "name": "patch-capture", "version": "0.0.1", "hooks": "./hooks.json"}))
        (capture / "capture.py").write_text(
            "import json,sys\np=json.load(sys.stdin)\n"
            f"with open({str(payload_file)!r}, 'a') as f: f.write(json.dumps(p)+'\\n')\n")
        shutil.copyfile(root / "scripts/codex/hook.py", capture / ".codex-plugin/hook.py")
        decisions = {f"{phase}-{i}.txt": value for phase, values in DENIALS.items()
                     for i, value in enumerate(values)}
        (capture / "decide.py").write_text(
            "import json,sys\nfrom pathlib import Path\np=json.load(sys.stdin)\n"
            f"values={decisions!r}\n"
            "value=values.get(Path(p['tool_input']['file_path']).name, {})\n"
            "if 'fixtureExit' in value:\n"
            "    print('fixture child error', file=sys.stderr)\n"
            "    sys.exit(value['fixtureExit'])\n"
            "print(json.dumps(value))\n")
        (capture / ".codex-plugin/hook-handlers.json").write_text(json.dumps({
            "plugin": "patch-capture", "handlers": [{"event": "PreToolUse", "matcher": "Edit|Write",
                "command": 'python3 "${PLUGIN_ROOT}/decide.py"'}]}))
        (capture / "hooks.json").write_text(json.dumps({"hooks": {"PreToolUse": [{
            "matcher": "apply_patch", "hooks": [{"type": "command",
                "command": 'python3 "${PLUGIN_ROOT}/.codex-plugin/hook.py" 0'}]}], "PostToolUse": [{
            "matcher": "apply_patch", "hooks": [{"type": "command",
                                               "command": 'python3 "${PLUGIN_ROOT}/capture.py"'}]}]}}))
        (market / ".agents/plugins").mkdir(parents=True)
        (market / ".agents/plugins/marketplace.json").write_text(json.dumps({
            "name": "native-proof", "plugins": [{"name": name,
                "source": {"source": "local", "path": "./plugins/" + name},
                "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"}}
                for name in ("kiro", "patch-capture")]}))
        fake = tmp / "bin"
        fake.mkdir()
        (fake / "kiro-cli").write_text(
            f"#!/usr/bin/env python3\nfrom pathlib import Path\nPath({str(provider_called)!r}).touch()\nexit(97)\n")
        (fake / "kiro-cli").chmod(0o755)
        env = {key: os.environ[key] for key in ("PATH", "HOME", "LANG", "LC_ALL") if key in os.environ}
        pattern = "^NATIVE_NO_ORPHANS_" + tmp.name.replace(" ", "_") + "$"
        require(subprocess.run(["pgrep", "-f", pattern], capture_output=True).returncode == 1,
                "Orphan fixture pattern unexpectedly matches a process")
        env.update(CODEX_HOME=str(state), PATH=str(fake) + os.pathsep + env["PATH"],
                   KIRO_REAP_PATTERN=pattern, TMPDIR=str(tmp), PYTHONDONTWRITEBYTECODE="1")
        subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "init", "-q", str(workspace)], check=True, env=env)
        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), ResponsesFixture)
        server.workspace, server.phase, server.sent = workspace, "baseline", set()
        server.routing_seen, server.requests, server.error = False, 0, None
        stack.callback(server.server_close)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        stack.callback(server.shutdown)
        (state / "config.toml").write_text(
            'model="gpt-5.4"\nmodel_provider="fixture"\n[model_providers.fixture]\n'
            f'name="Loopback fixture"\nbase_url="http://127.0.0.1:{server.server_port}/v1"\n'
            'wire_api="responses"\nrequires_openai_auth=false\n')

        def cli(*args):
            return subprocess.run(["codex", *args], cwd=workspace, env=env, check=True,
                                  capture_output=True, text=True, timeout=30).stdout

        report["version"] = cli("--version").strip()
        cli("plugin", "marketplace", "add", str(market))
        installed = {name: Path(json.loads(cli("plugin", "add", name + "@native-proof", "--json"))["installedPath"])
                     for name in ("kiro", "patch-capture")}
        files = [".codex-plugin/hook.py", ".codex-plugin/hooks.json", ".codex-plugin/hook-handlers.json",
                 "hooks/session-routing.sh", "hooks/pre-commit-review.sh", "hooks/pre-push-review.sh"]
        require(all((source / name).read_bytes() == (installed["kiro"] / name).read_bytes() for name in files),
                "Installed Kiro hook sources differ")
        log = stack.enter_context((tmp / "server.log").open("w"))
        process = subprocess.Popen(["codex", "app-server", "--stdio"], cwd=workspace, env=env,
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=log, text=True)
        stack.callback(stop, process)
        selector = selectors.DefaultSelector()
        selector.register(process.stdout, selectors.EVENT_READ)
        stack.callback(selector.close)
        events, request_id = [], 0

        def call(method, params):
            nonlocal request_id
            request_id += 1
            return RPC["request"](process, selector, request_id, method, params, events.append)

        def thread():
            return call("thread/start", {"cwd": str(workspace), "model": "gpt-5.4", "modelProvider": "fixture",
                        "ephemeral": True, "approvalPolicy": "on-request", "sandbox": "workspace-write"})["thread"]["id"]

        def turn(thread_id):
            result = call("turn/start", {"threadId": thread_id, "input": [{"type": "text", "text": "Local fixture stage."}]})
            deadline = time.monotonic() + 45
            while True:
                done = [e for e in events if e.get("method") == "turn/completed" and
                        e["params"]["turn"]["id"] == result["turn"]["id"]]
                if done:
                    require(done[-1]["params"]["turn"]["status"] == "completed" and server.error is None,
                            server.error or "Fixture turn failed")
                    return
                events.append(RPC["receive"](process, selector, deadline - time.monotonic()))

        call("initialize", {"clientInfo": {"name": "native-hook-proof", "version": "1"},
                            "capabilities": {"experimentalApi": True}})
        process.stdin.write('{"method":"initialized"}\n')
        process.stdin.flush()
        before = call("hooks/list", {"cwds": [str(workspace)]})["data"][0]["hooks"]
        require(len(before) == 7 and all(h["trustStatus"] == "untrusted" for h in before), "Unexpected initial trust")
        turn(thread())
        require(not server.routing_seen and not payload_file.exists(), "Untrusted hook executed")
        require(not any(e.get("method") == "hook/started" for e in events), "Untrusted hook started")
        for hook in before:
            require(hook["pluginId"] in {"kiro@native-proof", "patch-capture@native-proof"} and
                    any(Path(hook["sourcePath"]).is_relative_to(p) for p in installed.values()), "Unexpected hook source")
            call("config/value/write", {"filePath": str(state / "config.toml"),
                 "keyPath": "hooks.state." + json.dumps(hook["key"]) + ".trusted_hash",
                 "mergeStrategy": "upsert", "value": hook["currentHash"]})
        after = call("hooks/list", {"cwds": [str(workspace)]})["data"][0]["hooks"]
        require(all(h["trustStatus"] == "trusted" for h in after), "Trust write did not take effect")
        current = thread()
        report["denials"] = {}
        for phase in ("bash", "patch", *DENIALS):
            server.phase = phase
            start = len(events)
            turn(current)
            if phase in DENIALS:
                runs = [e["params"]["run"] for e in events[start:] if e.get("method") == "hook/completed"
                        and e["params"]["run"]["eventName"] == "preToolUse"
                        and str(installed["patch-capture"]) in e["params"]["run"]["sourcePath"]]
                absent = all(not (workspace / f"{phase}-{i}.txt").exists() for i in range(2))
                report["denials"][phase] = {"patch": denial_patch(phase), "source_outputs": DENIALS[phase],
                                           "runs": runs, "files_absent": absent}
        require(all(case["files_absent"] and len(case["runs"]) == 1 and
                    case["runs"][0]["status"] == "blocked" for case in report["denials"].values()),
                "Native denial failed: " + json.dumps(report["denials"]))
        completed = [e for e in events if e.get("method") == "hook/completed"]
        runs = [e["params"]["run"] for e in completed if
                str(installed["kiro"]) in e["params"]["run"]["sourcePath"]]
        require(all(r["status"] == "completed" for r in runs), "Kiro bridge failed")
        require(sum(r["eventName"] == "sessionStart" for r in runs) == 2 and
                sum(r["eventName"] == "preToolUse" for r in runs) == 2 and
                sum(r["eventName"] == "stop" for r in runs) == 2 + len(DENIALS), "Missing native Kiro dispatch")
        require(server.routing_seen and not provider_called.exists(), "Routing absent or provider invoked")
        payloads = [json.loads(line) for line in payload_file.read_text().splitlines()]
        require(len(payloads) == 1 and payloads[0]["tool_name"] == "apply_patch" and
                payloads[0]["hook_event_name"] == "PostToolUse" and
                payloads[0]["tool_input"]["command"] == PATCH, "Wrong native patch payload")
        require((workspace / "native-one.txt").read_text() == "one\n" and
                (workspace / "native-two.md").read_text() == "two\n", "Patch did not execute")
        report.update(passed=True, untrusted_hooks_ran=False, external_provider_calls=0,
                      source_files_verified=files, trust_before=before, trust_after=after,
                      completed_hooks=completed, patch_payload=payloads[0],
                      offered_patch_tool=server.patch_schema, loopback_requests=server.requests)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--tmp-dir", default="/var/tmp")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report = {"passed": False}
    try:
        probe(args.root.resolve(), args.tmp_dir, report)
    except Exception as exc:
        report["error"] = str(exc)
    if args.report:
        args.report.write_text(json.dumps(report, indent=2) + "\n")
    print("PASS: native Kiro hooks, apply_patch payload and four translated denials" if report["passed"]
          else "FAIL: " + report["error"])
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
