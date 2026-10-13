#!/usr/bin/env python3
"""Validate isolated host packages as data, without executing their generators/hooks."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys


IDENTITY_FIELDS = {"name", "version", "description", "author", "homepage",
                   "repository", "license", "keywords"}


def validate(root):
    errors = []
    def error(message):
        errors.append(message)

    def load(path):
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(value, dict):
                raise ValueError("expected an object")
            return value
        except (OSError, ValueError) as exc:
            error(f"{path.relative_to(root)}: {exc}")
            return {}

    def inside(package, relative):
        if not isinstance(relative, str) or Path(relative).is_absolute():
            error(f"{package.relative_to(root)}: invalid package path {relative!r}")
            return None
        path = package / relative
        if package.resolve() not in path.resolve().parents or path.is_symlink():
            error(f"{package.relative_to(root)}: escaping or linked path {relative!r}")
            return None
        return path

    catalog = load(root / "hosts/catalog.json").get("plugins", {})
    if not isinstance(catalog, dict) or not catalog:
        error("hosts/catalog.json: plugins must be a non-empty object")
        return errors
    sources = {p.parents[1].name for p in (root / "plugins").glob("*/.claude-plugin/plugin.json")}
    if set(catalog) != sources:
        error("host catalog does not match source plugin membership")
    marketplaces = {
        "claude": load(root / ".claude-plugin/marketplace.json"),
        "codex": load(root / ".agents/plugins/marketplace.json"),
    }
    for host in ("claude", "codex"):
        entries = marketplaces[host].get("plugins", [])
        if not isinstance(entries, list):
            error(f"{host}: marketplace plugins must be an array")
            entries = []
        names = [entry.get("name") for entry in entries if isinstance(entry, dict)]
        if len(names) != len(entries) or len(names) != len(set(names)) or set(names) != sources:
            error(f"{host}: marketplace membership must match the host catalog exactly")
        for entry in entries:
            if not isinstance(entry, dict) or entry.get("name") not in catalog:
                continue
            name = entry["name"]
            expected_source = f"./packages/{host}/{name}"
            actual = entry.get("source")
            if host == "codex":
                actual = actual.get("path") if isinstance(actual, dict) and actual.get("source") == "local" else None
            if actual != expected_source:
                error(f"{host}/{name}: marketplace must select {expected_source}")
            if entry.get("version") != catalog[name].get("version"):
                error(f"{host}/{name}: marketplace version differs from the host catalog")
        for name, identity in catalog.items():
            if not isinstance(identity, dict) or identity.get("name") != name:
                error(f"catalog: invalid identity for {name}")
                continue
            source = root / "plugins" / name
            package = root / "packages" / host / name
            config_root = root / "hosts" / host / name
            config = load(config_root / "plugin.json")
            policy = load(config_root / "package.json")
            excluded = policy.get("exclude")
            if not isinstance(excluded, list):
                error(f"{host}/{name}: package.exclude must be an array")
                excluded = []
            for relative in excluded:
                path = inside(package, relative)
                if path is None or path.exists():
                    error(f"{host}/{name}: excluded host files are present or invalid: {relative}")
            if set(config) & IDENTITY_FIELDS:
                error(f"{host}/{name}: host configuration cannot override shared identity")
            manifest = load(package / f".{host}-plugin/plugin.json")
            if manifest != {**identity, **config}:
                error(f"{host}/{name}: manifest differs from explicit host sources")
            other = "codex" if host == "claude" else "claude"
            if (package / f".{other}-plugin").exists():
                error(f"{host}/{name}: package exposes the other host's manifest")
            inventory = load(package / "package-inventory.json")
            if any(inventory.get(key) != value for key, value in
                   (("host", host), ("plugin", name), ("version", identity.get("version")))):
                error(f"{host}/{name}: invalid package inventory identity")
            files = inventory.get("files")
            if not isinstance(files, dict) or not files:
                error(f"{host}/{name}: missing package inventory files")
                continue
            actual_files = set()
            for path in package.rglob("*"):
                if path.is_symlink():
                    error(f"{host}/{name}: package contains a symlink")
                elif path.is_file() and path.name != "package-inventory.json":
                    actual_files.add(str(path.relative_to(package)))
            if set(files) != actual_files:
                error(f"{host}/{name}: untracked or missing packaged files")
            for relative, digest in files.items():
                path = inside(package, relative)
                if path is None or not path.is_file():
                    error(f"{host}/{name}: missing packaged file {relative}")
                    continue
                if not isinstance(digest, dict) or digest.get("sha256") != hashlib.sha256(path.read_bytes()).hexdigest():
                    error(f"{host}/{name}: content drift in {relative}")
                elif digest.get("executable") != bool(path.stat().st_mode & 0o111):
                    error(f"{host}/{name}: executable mode drift in {relative}")
            if host == "codex":
                execution = load(config_root / "execution.json")
                if not isinstance(execution.get("reasoning"), dict) or not isinstance(execution.get("explicit_skills"), list):
                    error(f"codex/{name}: invalid execution configuration")
                for field, filename in (("hooks", "hooks.json"), ("mcpServers", "mcp.json")):
                    if field in config:
                        if config[field] != "./.codex-plugin/" + filename:
                            error(f"codex/{name}: invalid native {field} path")
                        elif load(package / ".codex-plugin" / filename) != load(config_root / filename):
                            error(f"codex/{name}: {field} differs from the Codex-owned source")
                if "hooks" in config:
                    if load(package / ".codex-plugin/hook-handlers.json") != load(config_root / "hook-handlers.json"):
                        error(f"codex/{name}: hook handlers differ from Codex-owned source")
                if isinstance(execution.get("explicit_skills"), list):
                    skill_inventory = load(package / ".codex-plugin/inventory.json").get("skills", [])
                    for entry in skill_inventory if isinstance(skill_inventory, list) else []:
                        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
                            continue
                        path = inside(package, entry["path"])
                        if path is None:
                            continue
                        policy = path.parent / "agents/openai.yaml"
                        explicit = entry.get("name") in execution["explicit_skills"]
                        if explicit != policy.is_file():
                            error(f"codex/{name}: selection policy differs for {entry.get('name')}")
                        elif explicit and not re.search(
                            r"(?m)^\s+allow_implicit_invocation:\s*false\s*$", policy.read_text()
                        ):
                            error(f"codex/{name}: explicit entry permits implicit invocation")
            else:
                if isinstance(config.get("mcpServers"), str):
                    path = inside(package, config["mcpServers"])
                    expected = config_root / config["mcpServers"]
                    if path is None or not path.is_file() or load(path) != load(expected):
                        error(f"claude/{name}: MCP differs from the Claude-owned source")
                overrides = load(config_root / "agents.json")
                for filename, settings in overrides.items():
                    path = inside(package, "agents/" + filename)
                    if path is None or not path.is_file() or not isinstance(settings, dict):
                        error(f"claude/{name}: missing or invalid agent override {filename}")
                        continue
                    text = path.read_text()
                    for key, value in settings.items():
                        if isinstance(value, list):
                            block = re.search(rf"(?m)^{re.escape(key)}:\n((?:[ \t]+[^\n]*\n?)+)", text)
                            actual = [
                                json.loads(line.strip()[2:]) for line in block[1].splitlines()
                                if line.strip().startswith("- ")
                            ] if block else None
                            matches = actual == value
                        else:
                            expected = json.dumps(value, ensure_ascii=False)
                            matches = re.search(rf"^{re.escape(key)}: {re.escape(expected)}$", text, re.M)
                        if not matches:
                            error(f"claude/{name}: agent setting drift in {filename}/{key}")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    errors = validate(args.root.resolve())
    for error in errors:
        print(f"ERROR: {error}")
    print(f"Host package validation: {'FAIL' if errors else 'PASS'} ({len(errors)} errors)")
    return bool(errors)


if __name__ == "__main__":
    sys.exit(main())
