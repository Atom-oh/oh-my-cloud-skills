# Memory Strategy and Knowledge Loading

Strategy for converting Claude Code plugin reference documents into AgentCore Memory configurations, including STM/LTM strategy design and initial knowledge loading.

## AgentCore Memory Model

AgentCore Memory uses a dual-store architecture:

| Store | Purpose | Data Type | Lifecycle |
|-------|---------|-----------|-----------|
| **STM** (Short-Term Memory) | Raw event storage | Conversation history, session data, tool results | Per-session, auto-managed |
| **LTM** (Long-Term Memory) | Semantic knowledge | Extracted facts, procedures, preferences | Persistent, strategy-driven |

### STM (Short-Term Memory)

STM stores raw events from agent interactions. It is **automatically managed** by the AgentCore Runtime — no manual configuration needed beyond enabling it.

```json
{
  "stm": {
    "enabled": true,
    "maxEvents": 1000
  }
}
```

### LTM (Long-Term Memory)

LTM stores semantic knowledge extracted from interactions via **strategies**. Each strategy defines:
- What to extract (patterns, triggers)
- Where to store it (namespaces)
- How to organize it (categorization rules)

LTM is also used for **initial knowledge loading** — pre-populating domain knowledge from reference documents at deployment time.

## Namespace Design

### Namespace Hierarchy

AgentCore Memory namespaces use path-like patterns:

```
/skill/<skill-name>/knowledge/     ← Domain knowledge from references
/skill/<skill-name>/procedures/    ← Operational procedures from SKILL.md
/user/facts/                       ← Auto-extracted user information
/user/preferences/                 ← Auto-extracted user preferences
/project/context/                  ← Auto-extracted project context
```

### Mapping Claude Code References to Namespaces

Each skill's `references/` directory maps to LTM namespaces:

```
Plugin: aws-ops-plugin
  skills/ops-troubleshoot/references/ → /skill/ops-troubleshoot/knowledge/
  skills/ops-health-check/references/ → /skill/ops-health-check/knowledge/
  skills/ops-network-diagnosis/references/ → /skill/ops-network-diagnosis/knowledge/
```

### Namespace Naming Rules

| Rule | Example |
|------|---------|
| Path-like with leading/trailing slashes | `/skill/ops-troubleshoot/knowledge/` |
| Lowercase with hyphens for names | `/skill/ops-network-diagnosis/` |
| Max 128 characters total path | Truncate skill name if needed |
| Skill-scoped by default | `/skill/<skill-name>/` prefix |

### Shared References

If multiple skills reference the same document:
1. Place in the namespace of the primary skill (first one listed in plugin.json)
2. Add cross-reference tags for secondary skills in the strategy definition

## LTM Strategy Design

### Strategy-per-Skill Pattern

Each skill gets an extraction strategy that defines how knowledge is captured and organized:

```json
{
  "strategyName": "ops-troubleshoot-extraction",
  "description": "Extract troubleshooting knowledge from ops interactions",
  "extractionRules": [
    {
      "namespace": "/skill/ops-troubleshoot/knowledge/",
      "triggers": ["troubleshoot", "debug", "incident", "error"],
      "description": "Domain knowledge about troubleshooting procedures"
    },
    {
      "namespace": "/skill/ops-troubleshoot/procedures/",
      "triggers": ["run", "execute", "check", "verify"],
      "description": "Operational procedures and command sequences"
    }
  ]
}
```

### Tag Generation for Strategies

Tags are derived from multiple sources:

| Source | Tags Generated |
|--------|---------------|
| Skill `triggers` | Direct inclusion (e.g., `troubleshoot`, `debug`) |
| Document headings | Keyword extraction from `## ` headings |
| Code block languages | Language tags (e.g., `bash`, `python`, `yaml`) |
| AWS service names | Service tags (e.g., `eks`, `vpc`, `iam`) detected from content |

## Initial Knowledge Loading

Reference documents from Claude Code plugins are **pre-loaded into LTM** at deployment time. This provides the agent with domain knowledge from day one.

### Chunking Strategy for Initial Knowledge

Documents are chunked before loading into LTM to ensure optimal retrieval.

#### Heading-Based Chunking

Split documents by `## ` (level-2) headings. Each heading becomes a separate chunk.

```markdown
# Document Title          <- Document-level metadata only (not a chunk)

## Section A              <- Chunk 1
Content of section A...

## Section B              <- Chunk 2
Content of section B...

### Subsection B.1        <- Included in Chunk 2 (subsection stays with parent)
More content...

## Section C              <- Chunk 3
Content of section C...
```

#### Chunk Size Guidelines

| Metric | Target | Action if Exceeded |
|--------|--------|--------------------|
| Min tokens | 100 | Merge with next chunk |
| Max tokens | 2000 | Split at `### ` sub-headings |
| Optimal | 500-1500 | No action needed |

Token estimation: `len(text.split()) * 1.3` (rough approximation).

#### Code Block Handling

Code blocks are never split across chunks. If a chunk contains a code block:
1. Include the entire code block in the chunk
2. If the code block alone exceeds max tokens, keep as single oversized chunk (do not split code)

#### Table Handling

Tables follow the same rules as code blocks — never split a table across chunks. Include the table header with every chunk if a table must be split (rare, only for very large tables).

### Chunk Metadata

Each chunk includes metadata for LTM retrieval:

```yaml
---
title: "5-Minute Triage Procedure"
namespace: /skill/ops-troubleshoot/knowledge/
source: incident-commands.md
chunk: 2/5
headingPath: "Incident Response > 5-Minute Triage"
tags:
  - triage
  - incident
  - kubectl
---
```

### Chunking Algorithm

```python
def chunk_document(content: str, max_tokens: int = 2000, min_tokens: int = 100) -> list:
    """Split markdown document into chunks by ## headings."""
    lines = content.split("\n")
    chunks = []
    current_chunk = []
    current_heading = ""

    for line in lines:
        if line.startswith("## ") and current_chunk:
            chunk_text = "\n".join(current_chunk)
            token_est = len(chunk_text.split()) * 1.3

            if token_est < min_tokens and chunks:
                # Merge with previous chunk
                chunks[-1]["content"] += "\n\n" + chunk_text
            else:
                chunks.append({
                    "heading": current_heading,
                    "content": chunk_text,
                })

            current_chunk = [line]
            current_heading = line.lstrip("# ").strip()
        else:
            current_chunk.append(line)

    # Final chunk
    if current_chunk:
        chunk_text = "\n".join(current_chunk)
        chunks.append({
            "heading": current_heading or "Introduction",
            "content": chunk_text,
        })

    return chunks
```

## Output Structure

```
memory/
├── memory-config.json              # STM/LTM master configuration
├── strategies/
│   ├── ops-troubleshoot-extraction.json
│   ├── ops-health-check-extraction.json
│   └── ops-network-diagnosis-extraction.json
└── initial-knowledge/
    ├── ops-troubleshoot/
    │   ├── incident-commands-1.md  # Chunk 1
    │   ├── incident-commands-2.md  # Chunk 2
    │   └── common-errors-1.md     # Chunk 1 (single-chunk doc)
    ├── ops-health-check/
    │   └── health-checklist-1.md
    └── ops-network-diagnosis/
        ├── vpc-cni-troubleshoot-1.md
        └── vpc-cni-troubleshoot-2.md
```

## Special Cases

| Case | Handling |
|------|----------|
| Empty reference file | Skip (do not create empty chunk) |
| Binary files in references/ | Skip (log warning in conversion output) |
| Very short file (<100 tokens) | Single chunk, no splitting |
| File with only code blocks | Single chunk per code block |
| Korean-language content | Preserve as-is; adjust token estimation (Korean ~2x tokens per word) |
| Mixed language (Korean + English) | Single chunk; add both language tags |
| Mermaid diagrams | Preserve in chunk as code block; add `mermaid` tag |
| No references for a skill | Skip initial knowledge loading; strategy still created for runtime extraction |
