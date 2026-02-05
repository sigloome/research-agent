# Skills System Specification

## Overview

The skills system provides modular, hot-reloadable capabilities for the AI agent. This standard aligns with the [AgentSkills.io Specification](https://agentskills.io/specification) while maintaining compatibility with Python module practices and establishing a **Core + Adapters** (Hexagonal) architecture for unified Agent/API access.

## Requirements

### Functional Requirements

1. **Skill Discovery**
   - List all available skills
   - Search skills by name/description
   - Read skill documentation

2. **Skill Execution**
   - Execute skill functions
   - Pass parameters to skills
   - Return results to agent

3. **Skill Management**
   - Update skill code at runtime
   - Hot-reload modified skills
   - Validate skill syntax

4. **Skill Documentation**
   - Each skill has SKILL.md
   - Docstrings for functions
   - Usage examples

### Non-Functional Requirements

1. **Hot Reload**
   - Code changes apply without restart
   - No state loss during reload
   - Syntax errors don't crash system

2. **Isolation**
   - Skills run in same process
   - Errors in one skill don't affect others
   - Dependencies managed per-skill

## Directory Structure & Conventions

Each skill resides in its own directory within `skills/`.

```text
skills/
└── <skill_name>/           # e.g., graph_rag (snake_case for Python)
    ├── SKILL.md            # REQUIRED: Spec definition
    ├── scripts/            # OPTIONAL: Executable entry points
    │   └── cli.py          # Standard CLI entry point
    ├── references/         # OPTIONAL: Documentation
    ├── assets/             # OPTIONAL: Static files
    ├── __init__.py         # Python module marker
    └── implementation.py   # Core logic
```

### Gap Resolution: Naming Convention
There is a necessary deviation to support Python imports while following the spec:
- **Spec**: Requires `kebab-case` directory names that match the `name` field.
- **Project**: Uses `snake_case` directory names for Python import compatibility.
- **Resolution**:
  - Directory: `snake_case` (e.g., `graph_rag`)
  - Frontmatter Name: `kebab-case` (e.g., `graph-rag`)

66: 
67: ## Architectural Standard: Core + Adapters
68:
69: To ensure skills are usable by both the AI Agent (via SDK) and the Backend API (via direct import) without high latency or code duplication, all skills MUST follow the **Hexagonal Architecture** pattern.
70:
71: ### Components
72:
73: 1. **Core Domain (`core.py`)**
74:    - **Constraint**: Pure Python. NO imports from `fastapi`, `claude_agent_sdk`, or framework-specific code.
75:    - **Responsibility**: Business logic, data transformation, database calls.
76:    - **Input/Output**: Typed Pydantic models or standard Python types.
77:
78: 2. **Agent Adapter (`tool.py`)** [Optional if using default exports]
79:    - **Constraint**: Must conform to `claude_agent_sdk` Tool interface.
80:    - **Responsibility**: Wraps `core.py` functions for the LLM. Handles descriptions, "thinking" steps, and simplified I/O suitable for tokens.
81:
82: 3. **API Adapter (`api.py` or `server.py`)** [Optional]
83:    - **Constraint**: Fast, synchronous (or async) Python calls.
84:    - **Responsibility**: Wraps `core.py` for REST endpoints.
85:
86: ### Directory Layout
87:
88: ```text
89: skills/
90: └── example_skill/
91:     ├── SKILL.md            # Spec
92:     ├── core.py             # Logic (Universal)
93:     ├── tool.py             # Agent Interface (SDK)
94:     ├── __init__.py         # Exports core functions
95:     └── ...
96: ```
97:
98: ## SKILL.md Format Specification


Every skill MUST have a `SKILL.md` file following this format:

### Required Sections

```markdown
---
name: skill-name        # kebab-case (e.g., graph-rag)
description: One-line description of what this skill does and when to use it.
license: MIT            # e.g., MIT, Proprietary
metadata:
  type: library-wrapper # Custom metadata
  short-description: Brief label (max 50 chars)
  deprecated: false     # Optional: true if deprecated
  replacement: path/to/new/skill  # Optional: if deprecated
---

# Skill Name

Brief overview paragraph explaining the skill's purpose.

## Capabilities

1. **Capability 1** - Description of what it does
2. **Capability 2** - Another capability
3. ...

## Usage

### Function/Feature Name

\`\`\`python
from skills.skill_name import function_name

# Example usage with comments
result = function_name(arg1, arg2)
\`\`\`

## Implementation Files

- `skills/skill_name/file.py` - Description of this file

## Additional Sections (Optional)

- Configuration
- Examples
- Notes/Caveats
- Migration guides (for deprecated skills)
```

### Frontmatter Fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Kebab-case skill identifier (e.g., `paper-search`) |
| `description` | Yes | Full description for AI agent context. Should explain **when** to use this skill. |
| `license` | No | License type (e.g., MIT) |
| `metadata.type` | No | Skill type (e.g., library-wrapper) |
| `metadata.short-description` | Yes | Brief label for listings (max 50 chars) |
| `metadata.deprecated` | No | Set to `true` if skill is deprecated |
| `metadata.replacement` | No | Path to replacement skill if deprecated |

### Content Guidelines

1. **Capabilities**: List 3-6 key features as numbered items
2. **Usage**: Provide runnable Python code examples
3. **Implementation Files**: List all Python files with brief descriptions
4. **Examples**: Show real-world usage scenarios
5. **Avoid**: Placeholder text like "TODO" or "Description needed"

### Example: Well-Formatted SKILL.md

```markdown
---
name: paper-search
description: Search and fetch AI research papers from ArXiv and other sources. Use this skill when users want to find papers on specific topics, fetch paper details, or search the local paper database.
metadata:
  short-description: Search and fetch AI research papers
---

# Paper Search Skill

This skill provides paper search and retrieval capabilities.

## Capabilities

1. **Fetch papers from ArXiv** - Search for recent papers by topic or query
2. **Search local database** - Find papers already stored locally
3. **Add paper by URL** - Import a specific paper from ArXiv URL
4. **Read paper details** - Get full details of a stored paper

## Usage

### Fetch Papers from ArXiv

\`\`\`python
from skills.knowledge.paper.core import fetch_papers

papers = fetch_papers("LLM alignment", max_results=5)
\`\`\`

## Implementation Files

- `skills/knowledge/paper/operations.py` - Main paper operations
- `skills/knowledge/paper_search/fetcher.py` - ArXiv fetching logic
```

## Scripts & Execution

- **CLI Entry Point**: `scripts/cli.py` (or `__main__.py` for module execution).
- **Format**: Scripts should be clearly documented in `SKILL.md`.

## Migration Guide

For existing skills:
1. **Add Frontmatter** to `SKILL.md`.
2. **Move/Symlink CLI**: Ensure `python -m skills.<name>` works (via `__main__.py`), and optionally expose it via `scripts/`.

## API Specification

### List Skills
```
GET /api/tools/skills
Response: [
  {
    "name": "paper-search",
    "description": "Search ArXiv papers",
    "path": ".claude/skills/paper_search/SKILL.md"
  }
]
```

### Search Skills
```
POST /api/tools/skills/search
Body: {"query": "paper"}
Response: [matching skills]
```

### Read Skill
```
GET /api/tools/skills/{path}
Response: {skill content}
```

### Update Skill
```
PUT /api/tools/skills/{path}
Body: {"code": "..."}
Response: {"success": true, "message": "Updated and reloaded"}
```

## Available Skills

### knowledge
- **Purpose**: Unified knowledge engine combining RAG, Research Library, and Import tools.
- **Capabilities**:
  - **RAG**: GraphRAG (`rag`), RAG Critic (`critic`)
  - **Research**: Paper Fetching (`paper`), Search (`search`), Z-Library (`zlib`)
  - **Management**: DB (`db`), PDF Import (`pdf`), Summarization (`summarize`)
- **CLI**: `python -m skills.knowledge [component] [command]`

### preference
- **Purpose**: User preference management and learning.
- **Capabilities**:
  - **Analysis**: Analyze queries for topics and intent.
  - **Learning**: Track and update user preferences via bandit feedback.
- **CLI**: `python -m skills.preference [analyze|learn-get|learn-update]`

### weread
- **Purpose**: Upload local books (EPUB, PDF) to WeRead (微信读书).
- **Functions**: `list_uploadable_books()`, `open_upload_page()`, `get_weread_cookies()`

### skill-management
- **Purpose**: Meta-skill to list, search, and read other skills.
- **CLI**: `python -m skills.skill-management [list|search|read]`


## Test Cases

1. **List Skills**
   - Returns all skills with metadata
   - Includes both SKILL.md and Python modules

2. **Search Skills**
   - Matches by name
   - Matches by description

3. **Read Skill**
   - Returns full content
   - Handles missing skills gracefully

4. **Update Skill**
   - Validates Python syntax
   - Hot-reloads module
   - Reports errors properly

5. **Skill Execution**
   - Functions callable via tools
   - Parameters passed correctly
   - Results returned to agent

## Adding New Skills

1. Create directory in `skills/` with appropriate category:
   - `skills/knowledge/` - Unified Knowledge Engine (RAG + Library)
   - `skills/preference/` - User Context & Learning
   - `skills/` - Other standalone skills (e.g. `weread`)
   - **Convention**: Directory name MUST be `snake_case` (e.g. `my_skill`), while `SKILL.md` name MUST be `kebab-case` (e.g. `my-skill`).
2. Add `__init__.py` with exports
3. Implement functionality in Python files
4. Add `SKILL.md` documentation following the format specification above
5. Add tests in `tests/skills/`
6. Update system prompt if skill needs special invocation

### Skill Checklist

Before submitting a new skill, verify:

- [ ] `SKILL.md` exists with proper frontmatter (`name`, `description`, `metadata`)
- [ ] Directory name is `snake_case`, `name` field is `kebab-case`
- [ ] All capabilities are listed and described
- [ ] Usage examples are runnable Python code
- [ ] Implementation files are listed
- [ ] No placeholder text (TODO, "Description needed")
- [ ] `__init__.py` exports key functions
- [ ] Tests exist in `tests/skills/skill_name/`
