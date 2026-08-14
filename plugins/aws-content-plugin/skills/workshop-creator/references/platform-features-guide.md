# Platform Features Guide

Additional features the Workshop Studio platform provides that aren't directly related to
`contentspec.yaml`/content authoring — the MCP Server, Atlas Agent, and the Content Quality Program (CQP).

---

## Workshop Studio MCP Server

The official **read-only** server (`workshop-studio-mcp`) that exposes Workshop Studio's Content
Catalog/Events API via MCP (Model Context Protocol). MCP-compatible clients such as Kiro IDE/CLI, Claude
Code, and Cline can directly query workshop/event/build/participant information.

- Provides 17 tools total, including identity lookup (`whoami`), content catalog (workshops/builds/
  permissions/linked event lists, repository credentials), and events (event/team/participant/output
  lookups, issuing team AWS credentials, generating console login links, viewing facilitator guides).
- The server itself only calls read-only APIs, but some tools (e.g. `get_event_team_credentials`) return
  temporary credentials/links for team-account access, and those credentials can be used for write
  operations (e.g. AWS API calls within a team account).
- Installed via internal Amazon authentication sessions and internal deployment tooling — currently a
  feature for Amazon-internal users only.
- Useful when an existing workshop author wants to query/debug their workshop's status directly from an IDE.

## Workshop Studio Atlas Agent

A **preview-stage** AI conversational assistant built into the Workshop Studio console. It answers with
awareness of the workshop/event context currently being viewed.

- Strength: Q&A grounded in official Workshop Studio documentation + community Q&A (deployment-failure
  troubleshooting, best practices, etc.)
- Catalog/status lookups for workshops/events you own or have permission for (cannot search/recommend from
  the public catalog)
- **No write operations possible** — cannot create/modify/delete workshops or events. Access to real-time
  participant capacity/permission data is also limited (checking directly in the console is recommended)
- Being a preview feature, it may not work perfectly in every scenario.

## Content Quality Program (CQP)

A program to maintain quality standards for published Workshop Studio content and promote excellent content
(consolidating the former ImmersionDay and Content Champion programs). The TFC (Tech Field Community)
reviews and curates content, with GenAI-based quality scanner integration planned for the future.

> This plugin's `content-review-agent` quality gate (Workshops are Visual-Testing-exempt → 90-point scale,
> PASS ≥77) aligns in direction with the "high quality bar" CQP requires — passing `content-review-agent`
> first, before registering content with CQP, gives you an advantage during their review process.

---

## When to reference which

- Want to check an existing workshop's build status/participant data directly from an IDE → MCP Server
- Want a quick documentation-based answer in the console → Atlas Agent
- Want to promote/register content as officially excellent content → CQP (coordinate with your TFC)

---

## Checklist

- [ ] If you need to repeatedly query workshop/event status from an IDE, consider installing the MCP Server (Amazon-internal users only)
- [ ] Remember the Atlas Agent cannot perform write operations — always create/modify via the console or API
- [ ] To register officially excellent content, first self-verify content quality with `content-review-agent`, then coordinate with your TFC
