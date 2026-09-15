#!/usr/bin/env python3
"""Verify token-saver in native clients with loopback-only model fixtures.

Uses disposable homes and explicit trust for the copied Codex hook. No external
inference, customer configuration changes, or inference-quality claims.
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


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from strings(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from strings(item)


class Fixture(http.server.BaseHTTPRequestHandler):
    def log_message(self, *_args):
        pass

    def send(self, content, content_type="application/json"):
        body = content.encode()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        raw = self.rfile.read(int(self.headers["Content-Length"]))
        if self.headers.get("Content-Encoding") == "gzip":
            raw = gzip.decompress(raw)
        request = json.loads(raw)
        if self.path.endswith("/count_tokens"):
            self.send('{"input_tokens":1}')
            return
        self.server.requests.append({
            "path": self.path,
            "policy_seen": any(self.server.policy in s for s in strings(request)),
        })
        if self.path.startswith("/v1/responses"):
            item = {"type": "message", "id": "msg_fixture", "role": "assistant",
                    "content": [{"type": "output_text", "text": "LOCAL_FIXTURE_DONE",
                                 "annotations": []}]}
            response = {"id": "resp_fixture", "object": "response", "created_at": 1,
                        "model": "gpt-5.4", "status": "completed", "output": [item],
                        "usage": {"input_tokens": 1, "output_tokens": 1, "total_tokens": 2}}
            events = [
                {"type": "response.created",
                 "response": {**response, "status": "in_progress", "output": []}},
                {"type": "response.output_item.added", "output_index": 0, "item": item},
                {"type": "response.output_item.done", "output_index": 0, "item": item},
                {"type": "response.completed", "response": response},
            ]
        elif self.path.startswith("/v1/messages"):
            message = {"id": "msg_fixture", "type": "message", "role": "assistant",
                       "model": request["model"],
                       "content": [{"type": "text", "text": "LOCAL_FIXTURE_DONE"}],
                       "stop_reason": "end_turn", "stop_sequence": None,
                       "usage": {"input_tokens": 1, "output_tokens": 1}}
            if not request.get("stream"):
                self.send(json.dumps(message))
                return
            events = [
                {"type": "message_start",
                 "message": {**message, "content": [], "stop_reason": None}},
                {"type": "content_block_start", "index": 0,
                 "content_block": {"type": "text", "text": ""}},
                {"type": "content_block_delta", "index": 0,
                 "delta": {"type": "text_delta", "text": "LOCAL_FIXTURE_DONE"}},
                {"type": "content_block_stop", "index": 0},
                {"type": "message_delta",
                 "delta": {"stop_reason": "end_turn", "stop_sequence": None},
                 "usage": {"output_tokens": 1}},
                {"type": "message_stop"},
            ]
        else:
            self.server.error = "Unexpected fixture endpoint: " + self.path
            self.send("{}")
            return
        body = "".join("event: " + event["type"] + "\ndata: " +
                       json.dumps({**event, "sequence_number": i}) + "\n\n"
                       for i, event in enumerate(events))
        self.send(body, "text/event-stream")


def stop(process):
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)
    process.stdin.close()
    process.stdout.close()


def codex_probe(root, tmp, server, report):
    state, workspace, market = tmp / "codex", tmp / "consumer", tmp / "market"
    for path in (state, workspace):
        path.mkdir()
    package = market / "plugins/token-saver"
    shutil.copytree(root / "plugins/token-saver", package,
                    ignore=shutil.ignore_patterns("__pycache__"))
    registry = market / ".agents/plugins/marketplace.json"
    registry.parent.mkdir(parents=True)
    registry.write_text(json.dumps({"name": "token-saver-fixture", "plugins": [{
        "name": "token-saver", "source": {"source": "local", "path": "./plugins/token-saver"},
        "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
        "category": "Productivity",
    }]}))
    env = {k: os.environ[k] for k in ("PATH", "LANG", "LC_ALL") if k in os.environ}
    env.update(HOME=str(tmp / "home"), CODEX_HOME=str(state), TMPDIR=str(tmp))
    Path(env["HOME"]).mkdir(exist_ok=True)
    (state / "config.toml").write_text(
        'model="gpt-5.4"\nmodel_provider="fixture"\n[model_providers.fixture]\n'
        f'name="Loopback fixture"\nbase_url="http://127.0.0.1:{server.server_port}/v1"\n'
        'wire_api="responses"\nrequires_openai_auth=false\n')

    def cli(*args):
        return subprocess.run(["codex", *args], cwd=workspace, env=env, check=True,
                              capture_output=True, text=True, timeout=30).stdout

    subprocess.run(["git", "init", "-q", str(workspace)], env=env, check=True)
    report["codex_version"] = cli("--version").strip()
    cli("plugin", "marketplace", "add", str(market))
    installed = Path(json.loads(cli("plugin", "add",
        "token-saver@token-saver-fixture", "--json"))["installedPath"])
    policy_path = Path("skills/concise-responses/references/policy.md")
    require((installed / policy_path).read_bytes() ==
            (package / policy_path).read_bytes(), "Installed policy differs")
    with ExitStack() as stack:
        log = stack.enter_context((tmp / "codex.log").open("w"))
        process = subprocess.Popen(["codex", "app-server", "--stdio"],
            cwd=workspace, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=log, text=True)
        stack.callback(stop, process)
        selector = selectors.DefaultSelector()
        selector.register(process.stdout, selectors.EVENT_READ)
        stack.callback(selector.close)
        events, counter = [], 0

        def call(method, params):
            nonlocal counter
            counter += 1
            return RPC["request"](process, selector, counter, method, params, events.append)

        def thread():
            return call("thread/start", {"cwd": str(workspace), "model": "gpt-5.4",
                "modelProvider": "fixture", "ephemeral": True,
                "approvalPolicy": "on-request", "sandbox": "workspace-write"})["thread"]["id"]

        def turn(thread_id):
            result = call("turn/start", {"threadId": thread_id,
                "input": [{"type": "text", "text": "Reply with the fixture marker."}]})
            deadline = time.monotonic() + 45
            while True:
                done = [e for e in events if e.get("method") == "turn/completed"
                        and e["params"]["turn"]["id"] == result["turn"]["id"]]
                if done:
                    require(done[-1]["params"]["turn"]["status"] == "completed",
                            "Fixture turn did not complete")
                    return
                events.append(RPC["receive"](process, selector, deadline - time.monotonic()))

        call("initialize", {"clientInfo": {"name": "token-saver-test", "version": "1"},
                            "capabilities": {"experimentalApi": True}})
        process.stdin.write('{"method":"initialized"}\n')
        process.stdin.flush()
        hooks = call("hooks/list", {"cwds": [str(workspace)]})["data"][0]["hooks"]
        require(len(hooks) == 1 and hooks[0]["trustStatus"] == "untrusted",
                "Unexpected initial hook trust")
        turn(thread())
        require(not any(r["policy_seen"] for r in server.requests),
                "Untrusted hook injected context")
        hook = hooks[0]
        require(Path(hook["sourcePath"]).is_relative_to(installed),
                "Hook source is outside the installed fixture")
        call("config/value/write", {"filePath": str(state / "config.toml"),
            "keyPath": "hooks.state." + json.dumps(hook["key"]) + ".trusted_hash",
            "mergeStrategy": "upsert", "value": hook["currentHash"]})
        before = len(server.requests)
        current = thread()
        turn(current)
        turn(current)
        require(all(r["policy_seen"] for r in server.requests[before:]),
                "Trusted policy missing from model context")
        runs = [e["params"]["run"] for e in events if e.get("method") == "hook/completed"]
        require(len(runs) == 1 and runs[0]["eventName"] == "sessionStart"
                and runs[0]["status"] == "completed", "Expected one hook, not a per-turn loop")
        report["codex"] = {"untrusted_skipped": True, "trusted_context_seen": True,
                           "session_hook_runs_for_two_turns": len(runs)}


def claude_probe(root, tmp, server, report):
    home = tmp / "claude-home"
    home.mkdir()
    workspace = tmp / "claude-consumer"
    workspace.mkdir()
    env = {k: os.environ[k] for k in ("PATH", "LANG", "LC_ALL") if k in os.environ}
    env.update(HOME=str(home), CLAUDE_CONFIG_DIR=str(home / ".claude"), TMPDIR=str(tmp),
               ANTHROPIC_API_KEY="local-fixture",
               ANTHROPIC_BASE_URL=f"http://127.0.0.1:{server.server_port}",
               CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC="1")
    report["claude_version"] = subprocess.check_output(["claude", "--version"],
                                                       text=True, env=env).strip()
    before = len(server.requests)
    result = subprocess.run(["claude", "-p", "Reply with the fixture marker.",
        "--model", "claude-sonnet-4-5", "--tools", "", "--no-session-persistence",
        "--output-format", "json", "--setting-sources", "",
        "--plugin-dir", str(root / "plugins/token-saver")],
        cwd=workspace, env=env, capture_output=True, text=True, timeout=60)
    require(result.returncode == 0, "Claude fixture failed: " + result.stderr[-1000:])
    require("LOCAL_FIXTURE_DONE" in result.stdout, "Claude did not complete the fixture turn")
    require(any(r["policy_seen"] for r in server.requests[before:]),
            "Claude plugin SessionStart policy was not supplied")
    report["claude"] = {"session_context_seen": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--host", choices=("codex", "claude", "both"), default="both")
    parser.add_argument("--tmp-dir", default="/var/tmp")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report = {"passed": False, "external_model_calls": 0}
    try:
        with tempfile.TemporaryDirectory(prefix="token saver native ", dir=args.tmp_dir) as tmp:
            with ExitStack() as stack:
                server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Fixture)
                server.policy = (args.root / "plugins/token-saver/skills/"
                                 "concise-responses/references/policy.md").read_text().strip()
                server.requests, server.error = [], None
                stack.callback(server.server_close)
                threading.Thread(target=server.serve_forever, daemon=True).start()
                stack.callback(server.shutdown)
                if args.host in ("codex", "both"):
                    codex_probe(args.root.resolve(), Path(tmp), server, report)
                if args.host in ("claude", "both"):
                    claude_probe(args.root.resolve(), Path(tmp), server, report)
                require(server.error is None, server.error)
                report["fixture_requests"] = server.requests
                report["passed"] = True
    except Exception as exc:
        report["error"] = str(exc)
    if args.report:
        args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
