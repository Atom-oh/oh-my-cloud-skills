#!/usr/bin/env python3
"""Validate Codex plugin manifests and the repo marketplace."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$"
)

ALLOWED_MANIFEST_FIELDS = {
    "id",
    "name",
    "version",
    "description",
    "skills",
    "apps",
    "mcpServers",
    "interface",
    "author",
    "homepage",
    "repository",
    "license",
    "keywords",
}
# Plugins deliberately absent from the Codex surface — an upstream mirror whose manifest
# set is kept verbatim (docs/reference/project-init-upstream-sync.md). Everything else
# missing a .codex-plugin manifest is an error, not a warning. Keep in sync with
# MIRRORED_PLUGINS in test-plugins.py (same plugin, other surface).
CLAUDE_ONLY = {"project-init"}

ALLOWED_INSTALL_POLICIES = {"NOT_AVAILABLE", "AVAILABLE", "INSTALLED_BY_DEFAULT"}
ALLOWED_AUTH_POLICIES = {"ON_INSTALL", "ON_USE"}


class CodexPluginValidator:
    def __init__(self, project_root: Path, verbose: bool = False):
        self.project_root = project_root
        self.plugins_dir = project_root / "plugins"
        self.verbose = verbose
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)
        if self.verbose:
            print(f"  [ERROR] {message}")

    def warn(self, message: str) -> None:
        self.warnings.append(message)
        if self.verbose:
            print(f"  [WARN] {message}")

    def load_json(self, path: Path, label: str) -> dict[str, Any] | None:
        if not path.is_file():
            self.error(f"{label} missing at {path}")
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            self.error(f"{label} contains invalid JSON: {exc}")
            return None
        if not isinstance(payload, dict):
            self.error(f"{label} must contain a JSON object")
            return None
        return payload

    def discover_plugins(self) -> list[str]:
        """Plugins exposed on the Codex surface — those carrying a `.codex-plugin` manifest.

        A missing Codex manifest is an ERROR for every plugin except those in
        `CLAUDE_ONLY`: `project-init` is mirrored verbatim from its upstream fork source,
        which ships no Codex manifest, so it is deliberately absent from the Codex
        marketplace and skipped silently (a standing warning on a known-correct state is
        noise that buries a real one). Anywhere else, a `.codex-plugin/plugin.json` that
        goes missing means the plugin silently dropped off the Codex marketplace — the
        suite has to fail, not warn, since warnings don't reach the exit code.
        """
        names = {
            path.parent.parent.name
            for path in self.plugins_dir.glob("*/.codex-plugin/plugin.json")
        }
        for path in self.plugins_dir.glob("*/.claude-plugin/plugin.json"):
            name = path.parent.parent.name
            if name in names or name in CLAUDE_ONLY:
                continue
            self.error(f"{name}: no .codex-plugin manifest — not exposed to Codex "
                       f"(add one, or list it in CLAUDE_ONLY if that's deliberate)")
        return sorted(names)

    def validate_manifest(self, plugin_name: str) -> None:
        plugin_dir = self.plugins_dir / plugin_name
        manifest_path = plugin_dir / ".codex-plugin" / "plugin.json"
        manifest = self.load_json(manifest_path, f"{plugin_name} Codex plugin.json")
        if manifest is None:
            return

        unknown = sorted(set(manifest) - ALLOWED_MANIFEST_FIELDS)
        if unknown:
            self.error(f"{plugin_name}: unsupported Codex manifest fields: {', '.join(unknown)}")

        self.require_string(manifest, "name", plugin_name)
        if manifest.get("name") != plugin_name:
            self.error(f"{plugin_name}: manifest name must match plugin directory")

        version = self.require_string(manifest, "version", plugin_name)
        if version and SEMVER_RE.fullmatch(version) is None:
            self.error(f"{plugin_name}: version must be strict semver")

        self.require_string(manifest, "description", plugin_name)
        author = manifest.get("author")
        if not isinstance(author, dict) or not author.get("name"):
            self.error(f"{plugin_name}: author.name is required")

        claude_manifest_path = plugin_dir / ".claude-plugin" / "plugin.json"
        if claude_manifest_path.exists():
            claude_manifest = self.load_json(claude_manifest_path, f"{plugin_name} Claude plugin.json")
            if claude_manifest and version != claude_manifest.get("version"):
                self.error(
                    f"{plugin_name}: Codex version {version} does not match "
                    f"Claude version {claude_manifest.get('version')}"
                )

        if manifest.get("skills") != "./skills/":
            self.error(f"{plugin_name}: skills must be './skills/'")
        self.validate_skills(plugin_name, plugin_dir / "skills")

        mcp_servers = manifest.get("mcpServers")
        if mcp_servers is not None:
            if mcp_servers != "./.mcp.json":
                self.error(f"{plugin_name}: mcpServers must be './.mcp.json'")
            self.validate_mcp(plugin_name, plugin_dir / ".mcp.json")

        interface = manifest.get("interface")
        if not isinstance(interface, dict):
            self.error(f"{plugin_name}: interface object is required")
            return

        for field in (
            "displayName",
            "shortDescription",
            "longDescription",
            "developerName",
            "category",
        ):
            self.require_string(interface, field, plugin_name, prefix="interface")

        capabilities = interface.get("capabilities")
        if not isinstance(capabilities, list) or not all(
            isinstance(item, str) and item.strip() for item in capabilities
        ):
            self.error(f"{plugin_name}: interface.capabilities must be a non-empty string list")

        default_prompt = interface.get("defaultPrompt", interface.get("default_prompt"))
        if not self.is_prompt_value(default_prompt):
            self.error(f"{plugin_name}: interface.defaultPrompt must be a string or string list")

    def validate_skills(self, plugin_name: str, skills_dir: Path) -> None:
        if not skills_dir.is_dir():
            self.error(f"{plugin_name}: skills directory missing")
            return
        skill_dirs = [
            path
            for path in skills_dir.iterdir()
            if path.is_dir()
            and not path.name.startswith(".")
            and not path.name.endswith("-workspace")
        ]
        if not skill_dirs:
            self.error(f"{plugin_name}: no skill directories found")
            return
        for skill_dir in sorted(skill_dirs):
            skill_md = skill_dir / "SKILL.md"
            if not skill_md.is_file():
                self.error(f"{plugin_name}: skill {skill_dir.name} missing SKILL.md")
                continue
            try:
                content = skill_md.read_text(encoding="utf-8")
            except OSError as exc:
                self.error(f"{plugin_name}: cannot read {skill_md}: {exc}")
                continue
            if not content.startswith("---\n"):
                self.error(f"{plugin_name}: skill {skill_dir.name} missing YAML frontmatter")
                continue
            end = content.find("\n---", 4)
            if end == -1:
                self.error(f"{plugin_name}: skill {skill_dir.name} frontmatter is not closed")
                continue
            frontmatter = content[4:end]
            if not re.search(r"^name:\s*\S+", frontmatter, re.MULTILINE):
                self.error(f"{plugin_name}: skill {skill_dir.name} missing frontmatter name")
            if not re.search(r"^description:\s*\S+", frontmatter, re.MULTILINE):
                self.error(f"{plugin_name}: skill {skill_dir.name} missing frontmatter description")

    def validate_mcp(self, plugin_name: str, mcp_path: Path) -> None:
        payload = self.load_json(mcp_path, f"{plugin_name} .mcp.json")
        if payload is None:
            return
        servers = payload.get("mcpServers")
        if not isinstance(servers, dict) or not servers:
            self.error(f"{plugin_name}: .mcp.json mcpServers must be a non-empty object")
            return
        for server_name, config in servers.items():
            if not isinstance(server_name, str) or not server_name:
                self.error(f"{plugin_name}: MCP server names must be non-empty strings")
            if not isinstance(config, dict):
                self.error(f"{plugin_name}: MCP server {server_name} config must be an object")
                continue
            if not config.get("command"):
                self.error(f"{plugin_name}: MCP server {server_name} missing command")

    def validate_marketplace(self, plugin_names: list[str]) -> None:
        marketplace_path = self.project_root / ".agents" / "plugins" / "marketplace.json"
        marketplace = self.load_json(marketplace_path, "Codex marketplace.json")
        if marketplace is None:
            return

        self.require_string(marketplace, "name", "marketplace")
        interface = marketplace.get("interface")
        if not isinstance(interface, dict) or not interface.get("displayName"):
            self.error("marketplace: interface.displayName is required")

        entries = marketplace.get("plugins")
        if not isinstance(entries, list):
            self.error("marketplace: plugins must be an array")
            return

        expected = set(plugin_names)
        seen: set[str] = set()
        for entry in entries:
            if not isinstance(entry, dict):
                self.error("marketplace: plugin entries must be objects")
                continue
            name = entry.get("name")
            if not isinstance(name, str) or not name:
                self.error("marketplace: plugin entry name is required")
                continue
            seen.add(name)
            if name in CLAUDE_ONLY:
                # A CLAUDE_ONLY plugin is deliberately off the Codex surface, so a
                # marketplace entry for it is either stale or premature. Neither of the
                # other checks catches it: `expected` never contains it (so "missing
                # entry" can't fire) and its plugins/ directory does exist (so the
                # source-path check passes). Error only once the manifest is actually
                # gone — while it still ships one, the entry is merely early, and the
                # pairing is meant to land in a single commit.
                if (self.plugins_dir / name / ".codex-plugin" / "plugin.json").is_file():
                    self.warn(f"marketplace: entry {name} is listed as Claude-only "
                              f"(CLAUDE_ONLY) but still ships a .codex-plugin manifest — "
                              f"remove both together")
                else:
                    self.error(f"marketplace: entry {name} is deliberately Claude-only "
                               f"(CLAUDE_ONLY) and ships no .codex-plugin manifest — "
                               f"remove it from the Codex marketplace")
            elif name not in expected:
                # `expected` is the Codex surface (plugins with a .codex-plugin manifest),
                # not "directories that exist" — so say which one is actually absent. The
                # directory usually IS there; the manifest is what's missing, and
                # discover_plugins() has already errored about it.
                self.warn(f"marketplace: entry {name} has no .codex-plugin manifest")

            source = entry.get("source")
            expected_path = f"./plugins/{name}"
            if not isinstance(source, dict):
                self.error(f"marketplace {name}: source object is required")
            else:
                if source.get("source") != "local":
                    self.error(f"marketplace {name}: source.source must be local")
                if source.get("path") != expected_path:
                    self.error(f"marketplace {name}: source.path must be {expected_path}")
                if not (self.project_root / "plugins" / name).is_dir():
                    self.error(f"marketplace {name}: source path does not exist")

            policy = entry.get("policy")
            if not isinstance(policy, dict):
                self.error(f"marketplace {name}: policy object is required")
            else:
                if policy.get("installation") not in ALLOWED_INSTALL_POLICIES:
                    self.error(f"marketplace {name}: invalid policy.installation")
                if policy.get("authentication") not in ALLOWED_AUTH_POLICIES:
                    self.error(f"marketplace {name}: invalid policy.authentication")
            if not isinstance(entry.get("category"), str) or not entry["category"].strip():
                self.error(f"marketplace {name}: category is required")

        missing = sorted(expected - seen)
        if missing:
            self.error(f"marketplace missing plugin entries: {', '.join(missing)}")

    @staticmethod
    def is_prompt_value(value: Any) -> bool:
        if isinstance(value, str):
            return bool(value.strip())
        if isinstance(value, list):
            return bool(value) and all(isinstance(item, str) and item.strip() for item in value)
        return False

    def require_string(
        self,
        payload: dict[str, Any],
        field: str,
        plugin_name: str,
        *,
        prefix: str | None = None,
    ) -> str | None:
        value = payload.get(field)
        label = f"{prefix}.{field}" if prefix else field
        if not isinstance(value, str) or not value.strip():
            self.error(f"{plugin_name}: {label} must be a non-empty string")
            return None
        return value

    def run(self, only_plugin: str | None = None) -> bool:
        plugin_names = self.discover_plugins()
        if only_plugin:
            if only_plugin not in plugin_names:
                self.error(f"Unknown plugin: {only_plugin}")
                plugin_names = []
            else:
                plugin_names = [only_plugin]

        print("=" * 50)
        print("  Codex Plugin Validation Suite")
        print("=" * 50)

        for plugin_name in plugin_names:
            print(f"  Checking {plugin_name}")
            self.validate_manifest(plugin_name)

        if not only_plugin:
            self.validate_marketplace(plugin_names)

        print("=" * 50)
        print(f"  Plugins checked: {len(plugin_names)}")
        print(f"  Errors:          {len(self.errors)}")
        print(f"  Warnings:        {len(self.warnings)}")
        print("=" * 50)

        if self.errors:
            print("\nERRORS:")
            for error in self.errors:
                print(f"  - {error}")
        if self.warnings:
            print("\nWARNINGS:")
            for warning in self.warnings:
                print(f"  - {warning}")

        if not self.errors:
            print("\nRESULT: ALL CODEX PLUGIN CHECKS PASSED")
        else:
            print("\nRESULT: CODEX PLUGIN CHECKS FAILED")

        return not self.errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate Codex plugin support")
    parser.add_argument("--plugin", "-p", help="Validate one plugin by name")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--root", help="Validate a different repo root instead of this script's "
                         "own checkout (e.g. a PR-head tree fetched as data by pr-review's L1 gate)")
    args = parser.parse_args()

    project_root = Path(args.root).resolve() if args.root else Path(__file__).parent.parent.resolve()
    validator = CodexPluginValidator(project_root, verbose=args.verbose)
    ok = validator.run(only_plugin=args.plugin)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
