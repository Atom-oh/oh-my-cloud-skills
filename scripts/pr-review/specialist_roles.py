#!/usr/bin/env python3
"""Specialize configured peers without replacing context, budgets or result gates."""
import argparse
import json
import re
from pathlib import Path
import shlex
import sys

ROLES = {
    "codex": ("correctness", "Trace changed code, data flow, edge cases, tests and regressions."),
    "kiro-opus": ("aws", "Check AWS infrastructure, IAM, network, secrets and applicable security/privacy boundaries."),
    "kiro-gpt": ("operations", "Check deployment, recovery, observability, resource lifecycle, budgets and operational documentation."),
    "kiro-glm": ("contracts", "Check API/schema/configuration compatibility, documentation promises and integration boundaries."),
}


def role_prompt(tag, context):
    role, focus = ROLES[tag]
    return (
        f"SPECIALIST ROLE: {role}\n{focus}\n"
        "Review the entire supplied diff or chunk through this specialization. "
        "The trusted common policy still applies; do not invent missing context. "
        "Other configured roles have different responsibilities. "
        "Report concrete findings, not an approval based on another role's output.\n\n"
        "COMMON TRUSTED CONTEXT AND OUTPUT CONTRACT:\n" + context
    )


def high_risk(diff):
    """Documentation paths do not make sensitive operational guidance low risk."""
    paths = []
    for line in diff.splitlines():
        if not line.startswith("diff --git "):
            continue
        try:
            pair = shlex.split(line[len("diff --git "):])
        except ValueError:
            return True
        if len(pair) != 2:
            return True
        paths.extend(p[2:] if p.startswith(("a/", "b/")) else p for p in pair)
    if not paths:
        return True
    sensitive_path = re.compile(
        r"(?:^|[/._-])(?:auth|security|secrets?|credentials?|polic(?:y|ies)|"
        r"runbooks?|operations?|deploy(?:ment)?|infra(?:structure)?|onboarding|"
        r"review)(?:$|[/._-])", re.I)
    for path in paths:
        ordinary_doc = (
            path in {"README.md", "CHANGELOG.md", "LICENSE", "LICENSE.md"}
            or (path.startswith("docs/") and path.endswith((".md", ".rst", ".txt"))
                and not path.startswith(("docs/decisions/", "docs/security/")))
        )
        if not ordinary_doc or sensitive_path.search(path):
            return True
    # Include removed text and hunk context: deleting a guard is sensitive too.
    sensitive_content = re.compile(
        r"\b(?:aws|amazon\s+web\s+services|iam|sts|assume.?role|cognito|bedrock|"
        r"cloudfront|alb|nlb|eks|ecs|ecr|s3|kms|vpc|security|"
        r"auth(?:entication|orization|n|z)?|oauth|oidc|jwt|mfa|"
        r"credentials?|secrets?|passwords?|tokens?|permissions?|privileges?|"
        r"tls|ssl|https|ingress|egress|firewall|encryption|"
        r"deploy(?:ment|ments|ing|ed)?|terraform|kubectl|helm|argocd|atlantis|"
        r"rollback|restore|migration|sudo|chmod|ci|workflow|"
        r"access[ -]control|public[ -]access)\b", re.I)
    return bool(sensitive_content.search(diff))


def model_family(tag, model):
    if tag == "codex" or model.startswith(("gpt-", "openai.", "global.openai.")):
        return "openai"
    if "claude" in model:
        return "anthropic"
    if model.startswith("glm-"):
        return "zhipu"
    return "unknown"


def assignments(codex_enabled, kiro_cells):
    cells = [("codex", "global.openai.gpt-6-astra")] if codex_enabled else []
    for line in kiro_cells.splitlines():
        if line.strip():
            model, tag = line.rsplit(":", 1)
            cells.append((tag, model))
    result = [{"tag": tag, "role": ROLES[tag][0], "model": model,
               "family": model_family(tag, model)} for tag, model in cells]
    if not result or len({r["role"] for r in result}) != len(result):
        raise ValueError("Expected a nonempty set of unique configured specialist roles")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    prompt = sub.add_parser("prompt")
    prompt.add_argument("tag", choices=ROLES)
    prompt.add_argument("context", type=Path)
    manifest = sub.add_parser("manifest")
    manifest.add_argument("codex_enabled", choices=["0", "1"])
    gate = sub.add_parser("gate")
    gate.add_argument("diff", type=Path)
    gate.add_argument("manifest", type=Path)
    args = parser.parse_args()
    if args.command == "prompt":
        print(role_prompt(args.tag, args.context.read_text()), end="")
    elif args.command == "manifest":
        print(json.dumps(assignments(args.codex_enabled == "1", sys.stdin.read()), indent=2))
    else:
        roles = json.loads(args.manifest.read_text())
        families = {r["family"] for r in roles} - {"unknown"}
        if high_risk(args.diff.read_text()) and len(families) < 2:
            print("High-risk review requires at least two configured model families.", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
