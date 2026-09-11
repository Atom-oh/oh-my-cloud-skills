#!/usr/bin/env python3
"""Install all plugins in disposable Codex state and verify actual skill discovery.

Requires a local `codex` CLI with plugin/app-server support. Does not invoke a
model, start a thread, trust hooks, or modify the user's installed plugins.
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


def request(process, selector, request_id, method, params):
    process.stdin.write(json.dumps({"id": request_id, "method": method, "params": params}) + "\n")
    process.stdin.flush()
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        if not selector.select(timeout=1):
            if process.poll() is not None:
                raise RuntimeError("Codex app-server exited before replying")
            continue
        line = process.stdout.readline()
        if not line:
            raise RuntimeError("Codex app-server closed stdout")
        message = json.loads(line)
        if message.get("id") == request_id:
            if "error" in message:
                raise RuntimeError(f"{method}: {message['error']}")
            return message["result"]
    raise RuntimeError(f"Timed out waiting for {method}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.root.resolve()
    cli = shutil.which("codex")
    if not cli:
        parser.error("codex CLI is not installed")
    marketplace = json.loads((root / ".agents/plugins/marketplace.json").read_text())
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
        for entry in marketplace["plugins"]:
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
                print(f"PASS: {len(marketplace['plugins'])} plugins, {len(actual)} installed skills; "
                      "no duplicate names or source-path fallbacks")
                helper = installed_roots["co-agent"] / ".codex-plugin/run.py"
                result = subprocess.run(
                    ["python3", str(helper), "skills/co-agent/scripts/co_agent_config.py",
                     "host", "--root", str(target)],
                    cwd=target, env=env, capture_output=True, text=True, timeout=15,
                )
                if result.returncode or result.stdout.strip() != "codex":
                    raise RuntimeError("Installed helper did not select the Codex host: " +
                                       result.stdout + result.stderr)
                helper = installed_roots["atlas"] / ".codex-plugin/run.py"
                result = subprocess.run(
                    ["python3", str(helper), "skills/atlas/scripts/atlas_drift.py",
                     "--json", "--root", str(target)],
                    cwd=target, env=env, capture_output=True, text=True, timeout=15,
                )
                if result.returncode:
                    raise RuntimeError("Installed Atlas helper failed: " + result.stderr)
                print("PASS: installed co-agent and Atlas helpers execute from the consumer repo")
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
