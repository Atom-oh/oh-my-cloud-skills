# Draw.io MCP Setup Guide

Draw.io MCP enables real-time diagram editing via Claude Code. This is **optional** - XML direct writing works without MCP.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         사용자 시스템                                    │
│                                                                          │
│  ┌──────────────────┐                      ┌─────────────────────────┐  │
│  │ Draw.io          │   WebSocket (:3333)  │ drawio-mcp-server       │  │
│  │ (브라우저/앱)    │◄────────────────────►│ (Singleton 인스턴스)    │  │
│  │ + Browser        │                      │                         │  │
│  │   Extension      │                      │ HTTP :3000/mcp          │  │
│  └──────────────────┘                      └────────────┬────────────┘  │
│                                                         │               │
│                                                         ▼               │
│  ┌──────────────────┐     HTTP            ┌─────────────────────────┐  │
│  │ Claude Code      │◄───────────────────►│ /mcp endpoint           │  │
│  │ Session 1        │                     │ (다중 클라이언트 지원)   │  │
│  └──────────────────┘                     └─────────────────────────┘  │
│                                                         ▲               │
│  ┌──────────────────┐     HTTP                          │               │
│  │ Claude Code      │◄──────────────────────────────────┘               │
│  │ Session 2        │                                                   │
│  └──────────────────┘                                                   │
└─────────────────────────────────────────────────────────────────────────┘
```

**Key Points:**
- **HTTP mode** supports multiple Claude Code sessions
- Only **1 server instance** runs (prevents port conflicts)
- Browser Extension connects via WebSocket, Claude Code via HTTP

---

## Step 1: Install and Run drawio-mcp-server

### 1.1 Start Server (HTTP Mode)

```bash
# Foreground
npx -y drawio-mcp-server --transport http --http-port 3000

# Background
npx -y drawio-mcp-server --transport http --http-port 3000 &

# stdio + HTTP simultaneous (optional)
npx -y drawio-mcp-server --transport stdio,http --http-port 3000
```

### 1.2 Health Check

```bash
curl http://localhost:3000/health
# Response: {"status":"ok"}
```

### 1.3 Auto-Start Configuration (Optional)

**macOS - LaunchAgent:**

```bash
cat << 'EOF' > ~/Library/LaunchAgents/com.drawio.mcp.plist
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.drawio.mcp</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/npx</string>
        <string>-y</string>
        <string>drawio-mcp-server</string>
        <string>--transport</string>
        <string>http</string>
        <string>--http-port</string>
        <string>3000</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
EOF

launchctl load ~/Library/LaunchAgents/com.drawio.mcp.plist
```

**Linux - systemd:**

```bash
cat << 'EOF' > ~/.config/systemd/user/drawio-mcp.service
[Unit]
Description=Draw.io MCP Server
After=network.target

[Service]
ExecStart=/usr/bin/npx -y drawio-mcp-server --transport http --http-port 3000
Restart=always
RestartSec=10

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable drawio-mcp
systemctl --user start drawio-mcp
```

---

## Step 2: Browser Extension Installation

### 2.1 Chrome Extension

1. **Chrome Web Store**: [Draw.io MCP Extension](https://chrome.google.com/webstore/detail/drawio-mcp-extension/okdbbjbbccdhhfaefmcmekalmmdjjide)

2. **Manual Installation** (Developer Mode):
   ```bash
   git clone https://github.com/lgazo/drawio-mcp-extension.git
   # chrome://extensions → Developer mode → Load unpacked
   ```

### 2.2 Extension Settings

1. Click Extension icon
2. **WebSocket Port**: `3333` (default)
3. Click **Connect**

### 2.3 Open Draw.io App

- **Web**: https://app.diagrams.net/
- **Desktop**: draw.io Desktop

---

## Step 3: Connection Verification

### 3.1 Server Connection Test

```bash
# HTTP endpoint
curl http://localhost:3000/health
# {"status":"ok"}

# MCP endpoint
curl http://localhost:3000/mcp
```

### 3.2 Claude Code Verification

```bash
/mcp
# Check drawio server is connected
```

### 3.3 Draw.io Verification

1. Open Draw.io
2. Browser Extension icon → Check "Connected" status
3. Click "Test Connection" in Extension

---

## Step 4: MCP Tools Usage

```yaml
# Get categories
mcp__drawio__get-shape-categories

# List AWS icons
mcp__drawio__get-shapes-in-category:
  category: "AWS"

# Add icon
mcp__drawio__add-cell-of-shape:
  shape: "mxgraph.aws4.ec2"
  x: 200
  y: 200
  width: 60
  height: 60

# Add connection
mcp__drawio__add-edge:
  source: "cell-id-1"
  target: "cell-id-2"
```

---

## Claude Code MCP Configuration

### HTTP Mode (Recommended)

**Pre-requisite**: Run drawio-mcp-server in HTTP mode first.

**~/.claude/settings.json or .mcp.json:**
```json
{
  "mcpServers": {
    "drawio": {
      "type": "http",
      "url": "http://localhost:3000/mcp"
    }
  }
}
```

### stdio Mode (Single Session)

> Warning: Only one Claude Code session can use stdio mode at a time.

```json
{
  "mcpServers": {
    "drawio": {
      "command": "npx",
      "args": ["-y", "drawio-mcp-server"]
    }
  }
}
```

### Mode Comparison

| Item | HTTP Mode | stdio Mode |
|------|----------|-----------|
| Multi-session | Supported | Port conflict |
| Setup complexity | Requires separate server | Simple |
| Stability | High (Singleton) | Session-dependent |
| Recommended for | General use | Testing/development |

---

## MCP Tools Reference

### Query Tools

| Tool | Description |
|------|------|
| `get-selected-cell` | Get selected cell info |
| `get-shape-categories` | List available shape categories |
| `get-shapes-in-category` | List shapes in a category |
| `get-shape-by-name` | Search shape by name |
| `list-paged-model` | Paginated diagram cell info |

### Modification Tools

| Tool | Description |
|------|------|
| `add-rectangle` | Add rectangle |
| `add-edge` | Connect two cells (arrow) |
| `delete-cell-by-id` | Delete cell |
| `add-cell-of-shape` | Add shape from library |
| `set-cell-shape` | Change cell shape |
| `set-cell-data` | Store custom properties |
| `edit-cell` | Modify vertex properties |
| `edit-edge` | Modify edge connections |

---

## Troubleshooting

| Symptom | Cause | Solution |
|------|------|----------|
| `Connection refused` | Server not running | Run `npx -y drawio-mcp-server --transport http` |
| `Port already in use` | Port conflict | Kill existing process: `lsof -ti:3000 \| xargs kill` |
| Extension "Disconnected" | WebSocket connection failed | Check Extension port setting (default 3333) |
| MCP tools not available | HTTP connection failed | Check `curl http://localhost:3000/health` |
| Draw.io app unresponsive | Extension not installed | Install and activate Chrome Extension |

### Port Change

```bash
# Server - Change WebSocket port (for Extension)
npx -y drawio-mcp-server --transport http --extension-port 8080
# Must also change port in Extension settings!
```

---

## Fallback: Without MCP

If MCP setup is difficult or connection is unstable, use **XML direct writing**:

```
1. Create .drawio XML file with Write tool
2. Export PNG with /opt/homebrew/bin/drawio CLI
3. Insert image into PPT/document
```

This method **always works** and requires no setup.
