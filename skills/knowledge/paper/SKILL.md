---
name: paper
description: Unified interface for searching, managing, and reading research papers and books. Supports ArXiv, Z-Library, and local PDF import.
license: Apache-2.0
metadata:
  type: tool
  python_package: skills.knowledge.paper
---

# Paper Skill

The **Paper Skill** is the unified entry point for all research-related operations. It provides both low-level functions and a high-level `ResearchAssistant` class.

## Features

- **Unified Search**: Search across ArXiv, Z-Library, and your local database.
- **Smart Add**: Add content by URL (ArXiv), ID (Z-Library), or local file path.
- **Analyze**: Download full text and generate AI summaries.
- **Library Management**: List and manage your collection of papers and books.

## Usage

### High-Level API (ResearchAssistant)

```python
from skills.knowledge.paper.core import ResearchAssistant

assistant = ResearchAssistant()

# Search for papers and books
results = assistant.search("Agentic patterns", source="all", limit=5)

# Add a paper by URL
assistant.add("https://arxiv.org/abs/2310.xxxxx")

# Download a book by ID
assistant.add("123456")

# Get details/analyze
details = assistant.details("2310.xxxxx")

# List library
items = assistant.list_items()
```

### Low-Level Functions

```python
from skills.knowledge.paper.core import fetch_papers, search_local_papers, add_paper_by_url, analyze_paper

# Fetch from ArXiv (saves to DB)
papers = fetch_papers("LLM agents", max_results=5)

# Search local DB
local = search_local_papers("transformer")

# Add by URL
add_paper_by_url("https://arxiv.org/abs/2310.xxxxx")

# Analyze (download + summarize)
paper = analyze_paper("2310.xxxxx")
```

### CLI

```bash
# Fetch papers
python -m skills.knowledge.paper fetch "LLM agents" --max 5

# Add by URL
python -m skills.knowledge.paper add "https://arxiv.org/abs/2401.xxxxx"

# Analyze paper
python -m skills.knowledge.paper analyze "2401.xxxxx"

# Search local
python -m skills.knowledge.paper search "agents"
```

## Underlying Components

This skill coordinates:
- `skills.knowledge.paper_search` (ArXiv fetcher)
- `skills.knowledge.zlibrary` (Book search/download)
- `skills.knowledge.local_files` (PDF import)
- `skills.knowledge.db` (Storage)
