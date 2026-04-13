# MCP Configuration Template

Template for `.mcp.json` - Model Context Protocol server configuration.

---

## Base Template

Path: `.mcp.json`

```json
{
  "mcpServers": {}
}
```

## Example Configurations

### GitHub Integration

Connect Claude to GitHub for PR, issue, and repo management:

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "<token>"
      }
    }
  }
}
```

### PostgreSQL / Database

Connect Claude to a database for direct queries:

```json
{
  "mcpServers": {
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres"],
      "env": {
        "DATABASE_URL": "postgresql://user:pass@localhost:5432/mydb"
      }
    }
  }
}
```

### Slack Integration

Connect Claude to Slack for notifications and search:

```json
{
  "mcpServers": {
    "slack": {
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-server-slack"],
      "env": {
        "SLACK_BOT_TOKEN": "<xoxb-token>"
      }
    }
  }
}
```

### Playwright (Browser Automation)

Connect Claude to a browser for testing and automation:

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-server-playwright"]
    }
  }
}
```

## Security Rules

- NEVER put real tokens or secrets directly in `.mcp.json`
- Use environment variable references where possible
- Add `.mcp.json` to `.gitignore` if it contains project-specific secrets
- Keep a `.mcp.json.example` with placeholder values in the repository
- Follow the principle of minimum permissions for MCP server scopes
