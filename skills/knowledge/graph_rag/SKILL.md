---
name: graph-rag
description: Graph-based Retrieval Augmented Generation (GraphRAG) using lightrag-hku. Enables global understanding and complex reasoning over document collections.
license: Apache-2.0
metadata:
  type: library-wrapper
  python_package: skills.knowledge.graph_rag
---

# GraphRAG Skill

This skill provides **Graph-based Retrieval Augmented Generation (GraphRAG)** capabilities using the `lightrag-hku` library.

Unlike simple vector search, GraphRAG builds a knowledge graph from your documents, allowing for:
1.  **Global Understanding**: Answering questions like "What are the main themes?" across all documents.
2.  **Complex Reasoning**: Connecting concepts via graph traversal.

## Prerequisite

- `pip install lightrag-hku`
- working directory for storage (default: `./data/graph_rag`)
- OpenAI API Key (or compatible)

## Usage

```python
from skills.knowledge.graph_rag import initialize_rag, index_text, query_rag

# 1. Initialize
# rag = initialize_rag(working_dir="./data/graph_rag")
```

### CLI Usage

You can also run this skill directly from the terminal:

```bash
# Initialize
python -m skills.knowledge.graph_rag init --dir ./data/graph_rag

# Index text
python -m skills.knowledge.graph_rag index "Recent advances in LLMs..."

# Query
python -m skills.knowledge.graph_rag query "What are the main themes?" --mode global
```

## Modes

- **Global**: Uses the graph structure to answer high-level questions. Best for summaries.
- **Local**: Uses the graph to find specific neighbors of an entity. Best for specific details.
- **Naive**: Standard vector search (baseline).
- **Hybrid**: Combines Local + Global + Vector.
