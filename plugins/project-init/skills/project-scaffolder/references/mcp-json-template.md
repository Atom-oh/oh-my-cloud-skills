# MCP Configuration Template

Template for `.mcp.json`, the project-scoped Model Context Protocol server list. The file is committed and shared with the team, so it never holds secret values: reference each secret as `${VAR}` and let every developer keep the value in their own environment.

---

## Base Template

Path: `.mcp.json`

`/init-project` writes exactly this unless the user asked for specific servers in its question round. An empty server map is valid JSON, loads no tools, and costs no context.

```json
{
  "mcpServers": {}
}
```

JSON has no comments, so do not add commented-out example servers; an invalid `.mcp.json` fails to load. When detection suggests an integration (a GitHub remote, a database config), put a suggested `claude mcp add --scope project ...` line in the init summary instead of editing the file.

## Adding a Server

Add servers with `claude mcp add --scope project <name> ...`, which writes the entry to `.mcp.json` in the right shape; `claude mcp add --help` lists the transports and options. Take the package name or URL from the server's own documentation rather than from memory, because MCP server packages get renamed and archived.

An entry has this shape. `${VAR}` and `${VAR:-default}` expand in `command`, `args`, `env`, `url`, and `headers`:

```json
{
  "mcpServers": {
    "<local-server>": {
      "command": "<executable>",
      "args": ["<arg>"],
      "env": {
        "SERVICE_TOKEN": "${SERVICE_TOKEN}"
      }
    },
    "<remote-server>": {
      "type": "http",
      "url": "https://<host>/mcp",
      "headers": {
        "Authorization": "Bearer ${REMOTE_API_TOKEN}"
      }
    }
  }
}
```

## Rules

- Reference secrets as `${VAR}`, because the file is committed and shared; document each variable in `.env.example` without a value.
- Add the servers the project uses, not ones it might use, because every server's tools are offered to Claude in each session of every developer.
- Claude Code asks each developer to approve a project server before connecting to it, so a server added here is not trusted silently.
