#!/usr/bin/env python3
"""Assemble host-specific plugins from shared procedures and explicit host sources."""
from __future__ import annotations

import argparse
from collections import defaultdict
import json
import hashlib
import stat
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {"README.md", "CLAUDE.md", "AGENTS.md"}
OPTIONAL_ARTIFACTS = ("hook.py", "hooks.json", "hook-handlers.json", "mcp.json", "workflow.md")
# Codex 0.154 also migrates these argument-free source commands automatically.
# Reuse its stable names so the explicit, host-adapted skill wins deduplication.
COMMAND_ALIASES = {
    ("project-init", "health-check"): "source-command-health-check",
}
IDENTITY_FIELDS = ("name", "version", "description", "author", "homepage",
                   "repository", "license", "keywords")
CLAUDE_AGENT_FIELDS = {"tools", "model", "effort", "memory", "maxTurns", "skills",
                       "mcpServers", "color", "permissionMode", "background", "isolation"}


def host_json(root, host, name, filename):
    path = root / "hosts" / host / name / filename
    if root.resolve() not in path.resolve().parents or any(
        ancestor.is_symlink() for ancestor in (path, *path.parents) if ancestor != root
    ):
        raise ValueError(f"{path}: host sources must not contain symlinks")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected a JSON object")
    return value


def package_sources(plugin):
    """Materialize assets inside each package; never ship links to the source tree."""
    ignored = {".git", ".omc", "__pycache__", "node_modules", ".pytest_cache"}
    for path in sorted(plugin.rglob("*")):
        relative = path.relative_to(plugin)
        if relative.parts[0] in {".codex-plugin", ".claude-plugin"}:
            continue
        if any(part in ignored or part.endswith("-workspace") for part in relative.parts):
            continue
        if path.is_symlink():
            raise ValueError(f"{path}: package sources must not contain symlinks")
        if path.is_file() and path.name != ".DS_Store" and relative != Path(".mcp.json"):
            yield path, relative


def package_mode(root, path):
    relative = path.relative_to(root)
    if len(relative.parts) < 4 or relative.parts[0] != "packages":
        return None
    source = root / "plugins" / relative.parts[2] / Path(*relative.parts[3:])
    return stat.S_IMODE(source.stat().st_mode) if source.is_file() else 0o644


def package_exclusions(root, host, name):
    policy = host_json(root, host, name, "package.json")
    values = policy.get("exclude")
    if not isinstance(values, list):
        raise ValueError(f"{host}/{name}: package.exclude must be an array")
    paths = []
    for value in values:
        if not isinstance(value, str) or not value or Path(value).is_absolute() or ".." in Path(value).parts:
            raise ValueError(f"{host}/{name}: invalid package exclusion")
        path = Path(value)
        if path == Path("."):
            raise ValueError(f"{host}/{name}: cannot exclude the entire package")
        paths.append(path)
    return paths


def agent_settings(content, settings):
    """Apply Claude-owned frontmatter without modifying shared/upstream procedures."""
    match = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)", content, re.S)
    if not match:
        raise ValueError("Claude agent override requires frontmatter")
    frontmatter = match[1]
    # Strip host execution fields from the shared reference before applying the
    # host source. A missing optional setting means absent, rather than inherited.
    for key in CLAUDE_AGENT_FIELDS:
        frontmatter = re.sub(
            rf"(?m)^{key}:[^\n]*(?:\n[ \t]+[^\n]*)*(?:\n|$)", "", frontmatter)
    for key, value in settings.items():
        if key not in CLAUDE_AGENT_FIELDS:
            raise ValueError(f"Invalid Claude agent setting: {key}")
        if isinstance(value, list) and all(isinstance(item, str) and "\n" not in item for item in value):
            line = f"{key}:\n" + "\n".join(
                "  - " + json.dumps(item, ensure_ascii=False) for item in value)
        elif isinstance(value, (str, int, bool)) and "\n" not in str(value):
            line = f"{key}: " + json.dumps(value, ensure_ascii=False)
        else:
            raise ValueError(f"Invalid Claude agent setting value: {key}")
        frontmatter = frontmatter.rstrip("\n") + "\n" + line
    return "---\n" + frontmatter + "\n---\n" + content[match.end():]


def package_files(root, selected, outputs, catalog, full):
    """Each marketplace selects a self-contained package with one host's manifest."""
    claude_market = json.loads((root / ".claude-plugin/marketplace.json").read_text())
    if full:
        claude_market["plugins"] = [
            entry for entry in claude_market["plugins"] if entry["name"] in catalog]
    for name in sorted(selected):
        plugin = root / "plugins" / name
        for host in ("claude", "codex"):
            package = root / "packages" / host / name
            config = host_json(root, host, name, "plugin.json")
            manifest = {**catalog[name], **config}
            if set(config) & set(IDENTITY_FIELDS):
                raise ValueError(f"{host}/{name}: identity belongs in hosts/catalog.json")
            package_manifest = package / f".{host}-plugin/plugin.json"
            outputs[package_manifest] = dump(manifest)
            if host == "claude" and name != "project-init":
                outputs[plugin / ".claude-plugin/plugin.json"] = dump(manifest)
            agents = host_json(root, "claude", name, "agents.json") if host == "claude" else {}
            exclusions = package_exclusions(root, host, name)
            for source, relative in package_sources(plugin):
                if any(relative == path or path in relative.parents for path in exclusions):
                    continue
                content = source.read_bytes()
                if host == "claude" and relative.parts[0] == "agents" and source.name in agents:
                    content = agent_settings(content.decode("utf-8"), agents[source.name]).encode("utf-8")
                outputs[package / relative] = content
            if host == "codex":
                for path, content in list(outputs.items()):
                    if (plugin / ".codex-plugin") in path.parents:
                        outputs[package / path.relative_to(plugin)] = content
            elif isinstance(manifest.get("mcpServers"), str):
                host_root = root / "hosts/claude" / name
                source = host_root / manifest["mcpServers"]
                if host_root.resolve() not in source.resolve().parents or source.is_symlink():
                    raise ValueError(f"{name}: Claude MCP path escapes the plugin")
                outputs[package / manifest["mcpServers"]] = source.read_bytes()
                if name != "project-init":
                    outputs[plugin / manifest["mcpServers"]] = source.read_bytes()
            provenance = {
                str(path.relative_to(package)): {
                    "sha256": hashlib.sha256(
                        content.encode("utf-8") if isinstance(content, str) else content
                    ).hexdigest(),
                    "executable": bool(package_mode(root, path) & 0o111),
                }
                for path, content in outputs.items() if package in path.parents
            }
            outputs[package / "package-inventory.json"] = dump({
                "host": host, "plugin": name, "version": catalog[name]["version"],
                "files": provenance,
            })
        if not any(entry["name"] == name for entry in claude_market["plugins"]):
            claude_market["plugins"].append({
                "name": name, "version": catalog[name]["version"],
                "source": f"./packages/claude/{name}",
                "description": catalog[name]["description"],
            })
        for entry in claude_market["plugins"]:
            if entry["name"] == name:
                entry["source"] = f"./packages/claude/{name}"
                entry["version"] = catalog[name]["version"]
    outputs[root / ".claude-plugin/marketplace.json"] = dump(claude_market)

# Explicit applicability avoids advertising Claude-only operations as Codex migration.
PROJECT_INIT_DESCRIPTIONS = {
    "init-project": "Initialize project documentation, instructions and reusable skills for Codex or Claude Code.",
    "project-scaffolder": "Scaffold project documentation and host-adapted instruction and skill files.",
    "doc-sync-checker": "Check documentation freshness, references and the selected host's project instructions.",
    "sync-docs": "Synchronize project documentation with current code and the selected host's instructions.",
    "add-module": "Add a module and document its structure with the selected host's scoped instructions.",
    "add-adr": "Record an architecture decision in the project's ADR structure.",
    "add-runbook": "Add an operational runbook using the project's documentation structure.",
    "add-reference-doc": "Add a technical reference document using the project's documentation structure.",
    "generate-readme": "Generate a README from verified project structure, capabilities and evidence.",
    "generate-changelog": "Generate a changelog from the project's actual changes.",
    "source-command-health-check": "Assess project health using checks applicable to the selected host.",
    "migrate-hooks": "Migrate legacy Claude Code project hooks and subagent files; Codex hooks require a separate target check.",
}


def dump(value):
    return json.dumps(value, indent=2, ensure_ascii=False) + "\n"


def frontmatter(path):
    text = path.read_text(encoding="utf-8")
    match = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)", text, re.S)
    if not match:
        raise ValueError(f"{path}: missing frontmatter")
    result = {}
    for key in ("name", "description"):
        field = re.search(rf"^{key}:\s*(.+)$", match[1], re.M)
        if field:
            value = field[1].strip()
            if value.startswith('"'):
                value = json.loads(value)
            elif value.startswith("'") and value.endswith("'"):
                value = value[1:-1].replace("''", "'")
            if value in ("|", ">"):
                raise ValueError(f"{path}: unsupported multiline {key}; extend parser")
            result[key] = value
    if not result.get("description"):
        raise ValueError(f"{path}: missing description")
    return result


def generated_files(root, plugins=None):
    # Template content is data. --root never imports or executes code from that
    # tree, so trusted validation can inspect a different checkout safely.
    templates = root / "scripts/codex"
    catalog = json.loads((root / "hosts/catalog.json").read_text(encoding="utf-8"))["plugins"]
    outputs = {}
    manifests = sorted((root / "plugins").glob("*/.claude-plugin/plugin.json"))
    known = {path.parents[1].name for path in manifests}
    if known != set(catalog):
        raise ValueError("hosts/catalog.json must cover every source plugin exactly once")
    if plugins and plugins - known:
        raise ValueError(f"Unknown plugins: {', '.join(sorted(plugins - known))}")
    selected = known if plugins is None else plugins
    for manifest_path in manifests:
        plugin = manifest_path.parents[1]
        name = plugin.name
        if name not in selected:
            continue
        host_manifest = host_json(root, "codex", name, "plugin.json")
        execution = host_json(root, "codex", name, "execution.json")
        source_manifest = catalog[name]
        adapter = plugin / ".codex-plugin"
        groups = defaultdict(list)
        for pattern in ("skills/*/SKILL.md", "commands/*.md", "agents/*.md"):
            for source in sorted(plugin.glob(pattern)):
                if source.name in EXCLUDED:
                    continue
                meta = frontmatter(source)
                skill_name = meta.get("name") or source.stem
                if source.parent.name == "commands":
                    skill_name = COMMAND_ALIASES.get((name, source.stem), skill_name)
                if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", skill_name):
                    raise ValueError(f"{source}: invalid skill name {skill_name!r}")
                groups[skill_name].append((source, meta))
        inventory = {"plugin": name, "skills": []}
        if not set(execution["explicit_skills"]) <= set(groups) or not set(execution["reasoning"]) <= set(groups):
            raise ValueError(f"codex/{name}: execution settings refer to unknown skills")
        for skill_name, sources in sorted(groups.items()):
            # Skills are visited before commands: a command that is just an alias
            # augments the existing skill instead of becoming a duplicate.
            description = sources[0][1]["description"]
            if name == "project-init":
                description = PROJECT_INIT_DESCRIPTIONS.get(skill_name, description)
            path = adapter / "skills" / skill_name / "SKILL.md"
            source_paths = [str(s.relative_to(plugin)) for s, _ in sources]
            inventory["skills"].append({
                "name": skill_name, "path": str(path.relative_to(plugin)),
                "sources": source_paths,
            })
            native_entry = templates / f"{name}-skills" / f"{skill_name}.md"
            procedure_guidance = (
                "then follow this entry's Codex procedure. Shared links are reference only.\n\n"
                if native_entry.is_file() else
                "then the relevant shared procedure below. Keep references relative to that source.\n\n"
            )
            body = (
                f"---\nname: {skill_name}\ndescription: {json.dumps(description, ensure_ascii=False)}\n---\n\n"
                "<!-- Generated by scripts/sync-codex-plugins.py; edit the shared source. -->\n\n"
                f"# {skill_name}\n\n"
                "Read [Codex runtime guidance](../../runtime.md) first — unless already "
                "read earlier this session, it does not change between skills — "
                + procedure_guidance
            )
            if (templates / f"{name}.md").is_file():
                body += "Apply [this plugin's Codex workflow](../../workflow.md).\n\n"
            if native_entry.is_file():
                body += native_entry.read_text(encoding="utf-8").rstrip() + "\n\n"
                body += "Shared reference (the Codex procedure above owns invocation):\n\n"
            for source_path in source_paths:
                body += f"- [{source_path}](../../../{source_path})\n"
            reasoning = execution["reasoning"].get(skill_name)
            if reasoning:
                if reasoning not in {"minimal", "low", "medium", "high", "xhigh", "max"}:
                    raise ValueError(f"{name}/{skill_name}: invalid Codex reasoning intent")
                body += (
                    f"\nCodex reasoning intent: {reasoning}. This is advisory; the skill runs "
                    "with the current session's model and reasoning effort. Select a model "
                    "or delegate explicitly when the task requires a different configuration.\n"
                )
            outputs[path] = body
            if skill_name in execution["explicit_skills"]:
                # codex-cli's own plugin validator REQUIRES `interface` on any skill
                # that ships agents/openai.yaml at all (verified against 0.154.0's
                # validate_skill_agent_manifest: it runs whenever the file exists, and
                # rejects a missing/non-dict `interface` before even reaching `policy`)
                # — a policy-only file, which is all this ever emitted before, fails
                # Codex's own validation outright. display_name/short_description are
                # the two required interface fields; both derived from this skill's own
                # name/description, never invented content.
                display_name = skill_name.replace("-", " ").title()
                short_description = description if len(description) <= 200 else (
                    description[:197].rsplit(" ", 1)[0] + "...")
                # Hand-rolled YAML (this script has no YAML dependency, by repo
                # convention). json.dumps produces a double-quoted scalar whose escaping YAML's
                # double-quoted flow style also accepts, so any colon/quote/unicode in
                # the derived text stays a single valid scalar.
                outputs[path.parent / "agents/openai.yaml"] = (
                    "interface:\n"
                    f"  display_name: {json.dumps(display_name, ensure_ascii=False)}\n"
                    f"  short_description: {json.dumps(short_description, ensure_ascii=False)}\n"
                    "policy:\n"
                    "  allow_implicit_invocation: false\n"
                )
        outputs[adapter / "inventory.json"] = dump(inventory)
        outputs[adapter / "runtime.md"] = (templates / "runtime.md").read_text(encoding="utf-8")
        outputs[adapter / "run.py"] = (templates / "run.py").read_text(encoding="utf-8")
        if (templates / f"{name}.md").is_file():
            outputs[adapter / "workflow.md"] = (templates / f"{name}.md").read_text(encoding="utf-8")
        project_template = templates / f"{name}-project"
        if project_template.is_dir():
            for source in project_template.rglob("*"):
                if source.is_file() and "__pycache__" not in source.parts:
                    outputs[adapter / "project-template" / source.relative_to(project_template)] = (
                        source.read_text(encoding="utf-8")
                    )
        manifest = {**source_manifest, **host_manifest}
        if set(host_manifest) & set(IDENTITY_FIELDS):
            raise ValueError(f"codex/{name}: identity belongs in hosts/catalog.json")
        for field, filename in (("mcpServers", "mcp.json"), ("hooks", "hooks.json")):
            if field in host_manifest:
                expected = f"./.codex-plugin/{filename}"
                if host_manifest[field] != expected:
                    raise ValueError(f"codex/{name}: {field} must be {expected}")
                outputs[adapter / filename] = dump(host_json(root, "codex", name, filename))
        if "hooks" in host_manifest:
            outputs[adapter / "hook-handlers.json"] = dump(
                host_json(root, "codex", name, "hook-handlers.json"))
            outputs[adapter / "hook.py"] = (templates / "hook.py").read_text(encoding="utf-8")
        outputs[adapter / "plugin.json"] = dump(manifest)
    marketplace_path = root / ".agents/plugins/marketplace.json"
    marketplace = json.loads(marketplace_path.read_text(encoding="utf-8"))
    if plugins is None:
        marketplace["plugins"] = [
            entry for entry in marketplace["plugins"] if entry["name"] in catalog]
    existing = {entry["name"]: entry for entry in marketplace["plugins"]}
    for plugin in sorted(selected):
        version = catalog[plugin]["version"]
        if plugin not in existing:
            marketplace["plugins"].append({
                "name": plugin,
                "source": {"source": "local", "path": f"./packages/codex/{plugin}"},
                "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                "category": host_json(root, "codex", plugin, "plugin.json")["interface"]["category"],
                "version": version,
            })
        else:
            existing[plugin]["version"] = version
            existing[plugin]["source"] = {"source": "local", "path": f"./packages/codex/{plugin}"}
    outputs[marketplace_path] = dump(marketplace)
    package_files(root, selected, outputs, catalog, plugins is None)
    return outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--plugin", action="append", help="Generate/check one plugin; repeat to select several")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    args.root = args.root.resolve()
    selected = set(args.plugin) if args.plugin else None
    try:
        outputs = generated_files(args.root, selected)
    except (OSError, ValueError, KeyError, re.error) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    stale = []
    for path in outputs:
        if args.root not in path.parents or any(
            ancestor.is_symlink() for ancestor in path.parents if ancestor != args.root
        ):
            print(f"Refusing linked or escaping generated path: {path}", file=sys.stderr)
            return 1
    for path, content in outputs.items():
        data = content.encode("utf-8") if isinstance(content, str) else content
        mode = package_mode(args.root, path)
        mode_drift = path.is_file() and mode is not None and (
            bool(path.stat().st_mode & 0o111) != bool(mode & 0o111))
        if path.is_symlink() or not path.is_file() or path.read_bytes() != data or mode_drift:
            stale.append(path)
            if not args.check:
                path.parent.mkdir(parents=True, exist_ok=True)
                if path.is_symlink():
                    path.unlink()
                path.write_bytes(data)
                if mode is not None:
                    path.chmod(mode)
    # packages/ is entirely generated. Stale files can expose the wrong host or
    # retain removed executable hooks, so freshness includes unexpected files.
    for host in ("claude", "codex"):
        package_root = args.root / "packages" / host
        if not package_root.exists():
            continue
        for path in sorted(package_root.rglob("*"), key=lambda p: len(p.parts), reverse=True):
            relative = path.relative_to(package_root)
            if selected is not None and relative.parts[0] not in selected:
                continue
            if path.is_symlink() or (path.is_file() and path not in outputs):
                stale.append(path)
                if not args.check:
                    path.unlink()
            elif path.is_dir() and not any(path.iterdir()) and not args.check:
                path.rmdir()
    # Prune only reserved generated paths; preserve arbitrary operator/source files.
    for plugin in (args.root / "plugins").iterdir():
        if not (plugin / ".claude-plugin/plugin.json").is_file():
            continue
        if selected is not None and plugin.name not in selected:
            continue
        for name in OPTIONAL_ARTIFACTS:
            path = plugin / ".codex-plugin" / name
            if path not in outputs and (path.is_file() or path.is_symlink()):
                stale.append(path)
                if not args.check:
                    path.unlink()
        for tree in ("skills", "project-template"):
            generated_root = plugin / ".codex-plugin" / tree
            for path in generated_root.rglob("*"):
                if path.is_file() and path not in outputs:
                    stale.append(path)
                    if not args.check:
                        path.unlink()
            for path in sorted(generated_root.rglob("*"), key=lambda p: len(p.parts), reverse=True):
                if path.is_dir() and not any(path.iterdir()):
                    stale.append(path)
                    if not args.check:
                        path.rmdir()
    if args.check and stale:
        for path in stale:
            print(f"stale Codex artifact: {path.relative_to(args.root)}")
        return 1
    scope = ", ".join(sorted(selected)) if selected is not None else "all plugins"
    print(f"Codex artifacts {'checked' if args.check else 'generated'}: {len(outputs)} files ({scope})")
    desc_paths = [p for p in outputs if p.name == "SKILL.md"
                  and (args.root / "plugins") in p.parents
                  and p.parent.parent.name == "skills"]
    desc_bytes = sum(len(json.loads(re.search(r'^description:\s*(.+)$', outputs[p], re.M)[1]))
                      for p in desc_paths)
    print(f"Codex session-start description weight: {len(desc_paths)} skills, "
          f"{desc_bytes:,} bytes (~{desc_bytes // 4:,} tokens) sent every session")
    return 0


if __name__ == "__main__":
    sys.exit(main())
