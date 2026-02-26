---
name: animated-diagram
description: "Create dynamic animated SVG diagrams with SMIL animations for AWS architecture traffic flow, service interactions, and deployment pipelines. Use when creating animated or dynamic diagrams."
---

# Animated Diagram Skill

Create dynamic animated diagrams using SVG with SMIL animations. Produces self-contained HTML files with traffic flow visualizations, pulsing effects, interactive legends, and responsive scaling.

## When to Use

- Traffic flow visualization (request paths through AWS services)
- Service interaction diagrams with animated connections
- Deployment pipelines with step-by-step animation
- Real-time monitoring dashboards with animated status indicators

## Architecture

Each animated diagram is a self-contained HTML file with three layers:

1. **Background Layer** — Static architecture (Draw.io PNG export or inline SVG)
2. **Animation Layer** — SVG overlay with SMIL `<animateMotion>` and `<animate>` elements
3. **Interactive Layer** — JavaScript legend toggles for animation groups

## Color Standards

| Traffic Type | Color | Hex |
|-------------|-------|-----|
| Outbound | Red | `#DD344C` |
| Inbound | Blue | `#147EBA` |
| AWS Internal | Orange | `#FF9900` |
| Success/Active | Green | `#1B660F` |
| Warning | Yellow | `#F2C94C` |
| Background | Squid Ink | `#232F3E` |

## Quick Start

1. Create static architecture with architecture-diagram-agent (or inline SVG)
2. Define traffic paths as orthogonal SVG `<path>` elements
3. Add animated dots using `<animateMotion>` following the paths
4. Add pulsing effects on key nodes using `<animate>`
5. Wrap in responsive HTML with interactive legend

## Templates

- `templates/traffic-flow.html` — Complete traffic flow template with all patterns

## References

- `references/smil-animation-guide.md` — SMIL animation syntax and patterns
- `references/aws-diagram-patterns.md` — AWS architecture color coding and layout conventions
