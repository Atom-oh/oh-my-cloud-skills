# Plugin runtime readiness

Successful installation establishes package discovery. To run a requested feature,
also check its local dependencies, host capabilities, trust state and provider
readiness. Record which check actually ran; a missing dependency or reviewer is not
a passing result.

## Readiness by plugin

| Plugin | Local prerequisites | Trust / external prerequisites | Evidence required |
|---|---|---|---|
| aws-content-plugin | Dependencies of the selected format: Node/PptxGenJS and python-pptx for native PPTX; Python Playwright plus its browser for local web checks; PyMuPDF for PDF image extraction | Browser MCP startup when used; content-review PASS before completion/publication | Produce and validate the requested artifact; distinguish an optional preview from its mandatory quality gate |
| aws-ops-plugin | AWS CLI or the configured API tools; kubectl for cluster diagnostics | Required tools, credentials and explicitly authorized target/scope; bundled awsdocs/awsapi do not supply credentials | Actual diagnostic evidence; separately supplied knowledge/pricing/IaC tools are not assumed installed |
| co-agent | Host CLI and configured supported peer CLIs | READY raw-CLI peers for consensus/harness; advisory modes may disclose solo operation | Record participants, scope and verified findings; when no eligible external implementer exists, Codex-host harness uses explicitly selected host implementation with READY external review |
| agentcore-creator | Standard-library Python for local conversion; generated framework dependencies for execution | Deployment additionally requires the appropriate toolkit/MCP, AWS credentials and authorization | Test generated code with its documented context/region contract; unconverted hooks remain gaps, not protections |
| project-init | Python, project templates and valid skill metadata; Git for the default hook launcher | Consumer hook installation, project trust, then definition-specific hook trust | Native project discovery and execution; Claude-only migrate-hooks is not a Codex migration |
| kiro | Usable kiro-cli; verified consumer agents and POSIX no-follow/locking operations for delegation preparation | Authentication and separate process/tool trust; opt-in commit/push hooks require their own settings/trust | Structured manual-review evidence or guarded task results; an applied-diff scope guard is not process isolation |
| kiro-power-converter | Standard-library Python; POSIX no-follow directory descriptors and /proc/self/fd or /dev/fd; Git for GitHub inputs | Target write permissions; Kiro activation is separate | Valid metadata/MCP output and an explicit per-hook report; conversion does not prove activation |
| token-saver | Python | SessionStart hook trust for automatic loading | Exact shared policy supplied once per session; manual skill use does not prove a hook ran |
| pr-dash | Claude Code 2.1.287+ for the mod; authenticated `gh` for both mod and skill | Mod hooks load with the plugin (no settings-hook trust prompt); `--safe-mode` or `disableAllHooks` stop them | A pane or status line in the terminal/Desktop app, or command text where nothing draws; Codex gets only the text skill |

The marketplace's source agents become specialist procedures in Codex. Source
model/effort, tool restrictions and persistent memory are not automatically supplied
by entry skills. Use supported agent tools with actual boundaries or execute inline.
Power conversion's [safe-publication prerequisites](../../plugins/kiro-power-converter/skills/kiro-convert/references/conversion-rules.md)
are required before output mutation. Unsupported platforms refuse the operation;
this does not claim a verified OS matrix.

## Check the installed dependency location

Resolve `<plugin-root>` from the loaded skill path. Do not test a different checkout
or guess a cached version. A consumer's Node script may find its own dependencies
while a bundled module loaded by absolute path cannot; test the bundled module
using the same resolution environment as the build:

```bash
NODE_PATH="$(npm root -g)" node -e 'require(process.argv[1])' \
  "<plugin-root>/skills/aws-light-fcd/scripts/deck_kit.js"
python3 -c 'import pptx'
```

The [native PPTX dependency instructions](../../plugins/aws-content-plugin/skills/aws-light-fcd/SKILL.md#dependencies)
own installation and the required QA/font-embedding workflow. Use the dependency
path selected by that workflow; this readiness check does not install globally.

For local web testing, verify both the Python package and its installed executable:

```bash
python3 -c 'from playwright.sync_api import sync_playwright; p = sync_playwright().start(); b = p.chromium.launch(headless=True); b.close(); p.stop()'
```

An MCP browser may select a different browser/channel. Check its actual startup
error and installed executable rather than treating the Python probe as proof of
MCP readiness. For PDF image extraction, `python3 -c 'import fitz'` checks PyMuPDF;
its [conversion script](../../plugins/aws-content-plugin/skills/reactive-presentation/scripts/convert_to_remarp.py)
owns the supported conversion and dependency instructions.
Browser and PDF dependencies are required only for features that use them.
Canonical [web presentation instructions](../../plugins/aws-content-plugin/skills/reactive-presentation/SKILL.md)
describe local setup and validation.

Do not dump environment values or credential files to diagnose authentication.
Use the relevant provider's existing setup procedure and report only safe status.

## Hook trust and execution

Review configured definitions with Codex `/hooks`. Installation does not grant
trust. Project-init consumers first install/merge native project templates and
establish project trust, then review/trust each current hook definition. Preserve
existing definitions and user settings; definition changes require renewed review.

Local opt-in review hooks keep their own documented failure policies. They do not
replace mandatory latest-HEAD CI review. PostToolUse feedback cannot undo an action,
and hook coverage is not a complete security boundary.

The [runtime verification guide](codex-runtime-verification.md) owns disposable
installation and native hook reproduction. Its loopback fixtures make no external
model calls, use their own capability profile and trust only disposable definitions.
Passing them does not establish provider login, inference quality or deployment.

## Reporting a feature result

Name the requested feature, installed package/version, local checks, participant
or provider readiness, trust evidence and actual workflow result. Keep unverified
external capabilities explicit. Package discovery, a direct handler smoke test and
a native trusted event are different evidence and should be reported separately.
