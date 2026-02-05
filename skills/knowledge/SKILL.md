---
name: knowledge
description: Unified interface for constructing, managing, and querying the knowledge base (Papers, Books, RAG, Critic).
license: Apache-2.0
metadata:
  type: core-skill
  python_package: skills.knowledge
---

# Knowledge Skill

The central engine for all knowledge operations, consolidating RAG, Research Library, and Import tools.

## Components

### 1. RAG Engine (`rag`, `critic`)
- **GraphRAG**: Knowledge graph-based retrieval.
- **RAG Critic**: Quality filtering of retrieved chunks.

### 2. Research Library (`paper`, `search`, `zlib`)
- **Paper**: Fetch, analyze, and summarize ArXiv papers.
- **Search**: Search ArXiv and Semantic Scholar.
- **Z-Library**: Search and download books.

### 3. Management (`db`, `pdf`, `summarize`)
- **DB**: Manage local SQLite database.
- **PDF**: Import local PDF files.
- **Summarize**: General text summarization utility.

## CLI Usage

### RAG
```bash
python -m skills.knowledge rag init
python -m skills.knowledge rag query "Transformers"
```

### Research
```bash
# Search Papers
python -m skills.knowledge search search "Agents"

# Fetch & Analyze
python -m skills.knowledge paper fetch "LLM"
python -m skills.knowledge paper analyze "2310.xxxxx"

# Download Book
python -m skills.knowledge zlib search "Python"
```

### Import
```bash
# Import PDF directory
python -m skills.knowledge pdf import-dir ./papers/
```
