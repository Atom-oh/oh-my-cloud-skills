#!/usr/bin/env python3
"""Install all plugins in disposable Codex state and verify actual skill discovery.

Requires a local `codex` CLI with plugin/app-server support. Does not invoke a
model, start a thread, trust hooks, or modify the user's installed plugins.
Run sync-codex-plugins.py first to produce the adapters being tested.
"""
import argparse
import json
import os
from pathlib import Path
import selectors
import shutil
import subprocess
import tempfile
import time


def receive(process, selector, timeout=30):
    """Read one frame, retaining coalesced/partial frames for subsequent calls."""
    deadline = time.monotonic() + timeout
    buffer = getattr(process, "_codex_rpc_buffer", b"")
    while True:
        while b"\n" in buffer:
            line, buffer = buffer.split(b"\n", 1)
            process._codex_rpc_buffer = buffer
            if not line.strip():
                continue
            return json.loads(line)
        if time.monotonic() >= deadline:
            raise RuntimeError("Timed out waiting for an app-server frame")
        if not selector.select(timeout=1):
            if process.poll() is not None:
                raise RuntimeError("Codex app-server exited before replying")
            continue
        chunk = os.read(process.stdout.fileno(), 65536)
        if not chunk:
            raise RuntimeError("Codex app-server closed stdout")
        buffer += chunk
        process._codex_rpc_buffer = buffer


def request(process, selector, request_id, method, params, on_event=None):
    process.stdin.write(json.dumps({"id": request_id, "method": method, "params": params}) + "\n")
    process.stdin.flush()
    deadline = time.monotonic() + 30
    while True:
        message = receive(process, selector, deadline - time.monotonic())
        if message.get("id") == request_id:
            if "error" in message:
                raise RuntimeError(f"{method}: {message['error']}")
            return message["result"]
        if on_event is not None:
            on_event(message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--plugin", action="append", help="Test a published plugin; repeat to select several")
    args = parser.parse_args()
    root = args.root.resolve()
    cli = shutil.which("codex")
    if not cli:
        parser.error("codex CLI is not installed")
    marketplace = json.loads((root / ".agents/plugins/marketplace.json").read_text())
    entries = marketplace["plugins"]
    if args.plugin:
        names = set(args.plugin)
        unknown = names - {entry["name"] for entry in entries}
        if unknown:
            parser.error("Unknown plugins: " + ", ".join(sorted(unknown)))
        entries = [entry for entry in entries if entry["name"] in names]
    missing = [entry["name"] for entry in entries
               if not (root / "plugins" / entry["name"] / ".codex-plugin/inventory.json").is_file()]
    if missing:
        parser.error("Generate adapters first with scripts/sync-codex-plugins.py; "
                     "missing: " + ", ".join(missing))
    with tempfile.TemporaryDirectory(prefix="codex marketplace test ") as tmp:
        tmp = Path(tmp)
        state = tmp / "config"
        state.mkdir()
        target = tmp / "consumer"
        target.mkdir()
        env = {**os.environ, "CODEX_HOME": str(state),
               "CO_AGENT_USER_CONFIG": str(state / "no-user-co-agent.json")}
        subprocess.run(["git", "init", "-q", str(target)], check=True)
        def run(*arguments):
            result = subprocess.run([cli, *arguments], env=env, cwd=target,
                                    capture_output=True, text=True, timeout=30)
            if result.returncode:
                raise RuntimeError(result.stdout + result.stderr)
            return result.stdout
        print(run("--version").strip())
        run("plugin", "marketplace", "add", str(root))
        expected = {}
        installed_roots = {}
        for entry in entries:
            name = entry["name"]
            installed = json.loads(run("plugin", "add", f"{name}@{marketplace['name']}", "--json"))
            installed_roots[name] = Path(installed["installedPath"])
            inventory = json.loads((root / "plugins" / name / ".codex-plugin/inventory.json").read_text())
            for skill in inventory["skills"]:
                expected[f"{name}:{skill['name']}"] = Path(installed["installedPath"]) / skill["path"]
            print(f"installed {name}: {len(inventory['skills'])} skills")
        with (tmp / "server.log").open("w") as log:
            process = subprocess.Popen([cli, "app-server", "--stdio"], env=env, cwd=target,
                                       stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=log, text=True)
            selector = selectors.DefaultSelector()
            selector.register(process.stdout, selectors.EVENT_READ)
            try:
                request(process, selector, 1, "initialize", {
                    "clientInfo": {"name": "codex-portability-test", "version": "1.0"},
                    "capabilities": {"experimentalApi": True},
                })
                process.stdin.write(json.dumps({"method": "initialized"}) + "\n")
                process.stdin.flush()
                result = request(process, selector, 2, "skills/list",
                                 {"cwds": [str(target)], "forceReload": True})
                actual = {}
                for data in result["data"]:
                    for error in data.get("errors", []):
                        if str(state) in json.dumps(error):
                            raise RuntimeError(f"plugin skill discovery error: {error}")
                    for skill in data["skills"]:
                        if (skill.get("pluginId") or "").endswith("@" + marketplace["name"]):
                            if skill["name"] in actual:
                                raise RuntimeError(f"duplicate skill: {skill['name']}")
                            actual[skill["name"]] = Path(skill["path"])
                if actual != expected:
                    raise RuntimeError(f"discovery mismatch: missing={expected.keys() - actual.keys()}, "
                                       f"unexpected={actual.keys() - expected.keys()}, "
                                       f"wrong paths={[k for k in actual.keys() & expected.keys() if actual[k] != expected[k]]}")
                for name, path in actual.items():
                    if not path.is_file():
                        raise RuntimeError(f"missing installed entry: {name}")
                print(f"PASS: {len(entries)} plugins, {len(actual)} installed skills; "
                      "no duplicate names or source-path fallbacks")
                shared_commands = sorted(name for name in actual
                                         if name.rsplit(":", 1)[-1] in {"configure", "setup"})
                if shared_commands:
                    print("Names returned by Codex: " + ", ".join(shared_commands))
                hook_result = request(process, selector, 3, "hooks/list",
                                      {"cwds": [str(target)]})
                expected_hooks = {}
                for name, installed_root in installed_roots.items():
                    handlers = installed_root / ".codex-plugin/hook-handlers.json"
                    expected_hooks[name] = (
                        len(json.loads(handlers.read_text())["handlers"]) if handlers.is_file() else 0
                    )
                actual_hooks = dict.fromkeys(expected_hooks, 0)
                for data in hook_result["data"]:
                    for error in data.get("errors", []):
                        if str(state) in json.dumps(error):
                            raise RuntimeError(f"plugin hook discovery error: {error}")
                    for hook in data["hooks"]:
                        plugin_id = hook.get("pluginId") or ""
                        if plugin_id.endswith("@" + marketplace["name"]):
                            name = plugin_id.split("@", 1)[0]
                            actual_hooks[name] = actual_hooks.get(name, 0) + 1
                if actual_hooks != expected_hooks:
                    raise RuntimeError(f"hook discovery mismatch: expected={expected_hooks}, actual={actual_hooks}")
                print(f"PASS: {sum(actual_hooks.values())} configured plugin hooks discovered; "
                      "no hook trust bypass or execution")
                helpers = {
                    "co-agent": ["skills/co-agent/scripts/co_agent_config.py", "panel"],
                    "atlas": ["skills/atlas/scripts/atlas_drift.py", "--json"],
                    "kiro": ["skills/kiro-delegate/scripts/kiro_config.py", "show"],
                }
                for name, arguments in helpers.items():
                    if name not in installed_roots:
                        continue
                    helper = installed_roots[name] / ".codex-plugin/run.py"
                    result = subprocess.run(
                        ["python3", str(helper), *arguments, "--root", str(target)],
                        cwd=target, env=env, capture_output=True, text=True, timeout=15,
                    )
                    if result.returncode:
                        raise RuntimeError(f"Installed {name} helper failed: " + result.stderr)
                    if name == "co-agent":
                        peers = result.stdout.split()
                        if "codex" in peers or "claude" not in peers:
                            raise RuntimeError("Installed helper selected the wrong host panel")
                    print(f"PASS: installed {name} helper executes from the consumer repo")
                    if name == "kiro":
                        result = subprocess.run(
                            ["python3", str(helper), "skills/kiro-delegate/scripts/kiro_codex.py",
                             "review", "--root", str(target), "--diff", "-"],
                            input="", cwd=target, env=env, capture_output=True, text=True, timeout=15,
                        )
                        if result.returncode or json.loads(result.stdout).get("status") != "NO_CHANGES":
                            raise RuntimeError("Installed Kiro review entry failed: " + result.stdout + result.stderr)
                        print("PASS: installed Kiro native review returns structured results without setup")
            finally:
                selector.close()
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)


if __name__ == "__main__":
    main()
