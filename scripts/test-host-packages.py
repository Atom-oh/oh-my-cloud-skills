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


def canonical_yaml(text):
    """Parse the assembler's YAML subset; reject ambiguous YAML rather than guess."""
    lines = [(len(line) - len(line.lstrip(" ")), line.lstrip(" "))
             for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")]

    def scalar(value):
        if not value or "\t" in value:
            raise ValueError("invalid scalar")
        if value.startswith('"'):
            result = json.loads(value)
            if not isinstance(result, str):
                raise ValueError("quoted scalar must be text")
            return result
        if value.startswith("'"):
            if not re.fullmatch(r"'(?:[^']|'')*'", value):
                raise ValueError("multi-line quoted scalar is not canonical")
            return value[1:-1].replace("''", "'")
        if (value[0] in "|>{[&*!`@#" or ": " in value or " #" in value or
                value in {"yes", "no", "on", "off", "True", "False", "Null", "~"}):
            raise ValueError("unsupported YAML scalar")
        if value in {"true", "false", "null"} or re.fullmatch(r"-?(?:0|[1-9][0-9]*)", value):
            return json.loads(value)
        return value

    def mapping(index, indent):
        result = {}
        while index < len(lines) and lines[index][0] == indent:
            match = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_-]*):(?: (.*))?", lines[index][1])
            if match is None or match[1] in result:
                raise ValueError("invalid mapping or duplicate key")
            key, value = match[1], match[2]
            index += 1
            if value not in (None, ""):
                result[key] = scalar(value)
            elif index < len(lines) and lines[index][0] == indent + 2:
                if lines[index][1].startswith("- "):
                    items = []
                    while index < len(lines) and lines[index][0] == indent + 2:
                        if not lines[index][1].startswith("- "):
                            raise ValueError("mixed collection")
                        items.append(scalar(lines[index][1][2:]))
                        index += 1
                    result[key] = items
                else:
                    result[key], index = mapping(index, indent + 2)
            else:
                raise ValueError("empty mapping value")
            if index < len(lines) and lines[index][0] > indent:
                raise ValueError("unsupported continuation or indentation")
        return result, index

    result, consumed = mapping(0, 0)
    if consumed != len(lines):
        raise ValueError("unexpected indentation")
    return result


def validate(root):
    errors = []
    def error(message):
        errors.append(message)

    def load(path):
        try:
            if path.is_symlink() or root.resolve() not in path.resolve().parents:
                raise ValueError("linked or escaping data file")
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
    identities = {}
    for name, identity in catalog.items():
        if not isinstance(identity, dict) or identity.get("name") != name:
            error(f"catalog: invalid identity for {name}")
        elif set(identity) - IDENTITY_FIELDS:
            error(f"catalog: non-identity fields for {name}")
        else:
            identities[name] = identity
    catalog = identities
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
        valid_names = all(isinstance(name, str) for name in names)
        if (not valid_names or len(names) != len(entries) or
                len(names) != len(set(names)) or set(names) != sources):
            error(f"{host}: marketplace membership must match the host catalog exactly")
        for entry in entries:
            if (not isinstance(entry, dict) or not isinstance(entry.get("name"), str)
                    or entry["name"] not in catalog):
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
            package = root / "packages" / host / name
            host_root = root / "packages" / host
            if (package.is_symlink() or host_root.is_symlink() or
                    host_root.resolve() not in package.resolve().parents):
                error(f"{host}/{name}: linked or escaping package root")
                continue
            config_root = root / "hosts" / host / name
            config = load(config_root / "plugin.json")
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
                elif path.is_file() and path != package / "package-inventory.json":
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
                    skill_names = {
                        entry["name"] for entry in skill_inventory
                        if isinstance(entry, dict) and isinstance(entry.get("name"), str)
                    } if isinstance(skill_inventory, list) else set()
                    if any(not isinstance(name, str) or name not in skill_names
                           for name in execution["explicit_skills"]):
                        error(f"codex/{name}: explicit_skills references unknown inventory entries")
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
                        elif explicit:
                            text = policy.read_text(encoding="utf-8")
                            try:
                                parsed = canonical_yaml(text)
                                valid = (isinstance(parsed.get("policy"), dict) and
                                         parsed["policy"].get("allow_implicit_invocation") is False)
                            except ValueError:
                                valid = False
                            if not valid:
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
                    text = path.read_text(encoding="utf-8")
                    opening = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)", text, re.S)
                    if opening is None:
                        error(f"claude/{name}: agent has no opening frontmatter: {filename}")
                        continue
                    try:
                        active = canonical_yaml(opening[1])
                    except ValueError:
                        error(f"claude/{name}: non-canonical agent frontmatter: {filename}")
                        continue
                    for key, value in settings.items():
                        if key not in active or active[key] != value:
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
