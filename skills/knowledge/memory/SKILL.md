---
name: memory
description: "[DEPRECATED] Manual graph memory for storing knowledge nodes. Use graph-rag instead."
license: Apache-2.0
metadata:
  short-description: Deprecated graph memory storage
  deprecated: true
  replacement: knowledge/graph-rag
  python_package: skills.knowledge.memory
---

# Memory Skill (Deprecated)

> **Warning**: This skill is deprecated. Use `skills.knowledge.graph_rag` for new code.

A manual knowledge graph implementation for storing nodes (papers, concepts) and edges (relationships like 'refutes', 'supports'). This has been superseded by the LightRAG-based `graph_rag` skill.

## Capabilities

1. **Add nodes** - Store facts, papers, or concepts with metadata
2. **Add edges** - Create relationships between nodes with confidence scores
3. **Query relationships** - Find related nodes by relationship type
4. **Multi-hop traversal** - Navigate the graph to find indirect connections
5. **Reasoning queries** - Answer relationship questions using graph traversal
6. **Persistence** - Save/load graph to JSON file

## CLI Usage

> **Deprecated**: This skill does not support CLI operations. Please use `skills.knowledge.graph_rag` instead.

```bash
python -m skills.knowledge.memory
# Output: WARNING: This skill is DEPRECATED.
```

## Usage

### Initialize Graph Memory

```python
from skills.knowledge.memory.graph_store import GraphMemory

# Create with persistence
graph = GraphMemory(persist_path="data/knowledge_graph.json")
```

### Add Nodes

```python
# Add a paper node
graph.add_node(
    id="paper_001",
    type="paper",
    content="Attention Is All You Need - Introduces the Transformer architecture",
    metadata={"authors": ["Vaswani et al."], "year": 2017}
)

# Add a concept node
graph.add_node(
    id="concept_attention",
    type="concept",
    content="Self-attention mechanism for sequence modeling"
)
```

### Add Edges (Relationships)

```python
# Create a relationship with confidence and evidence
graph.add_edge(
    source_id="paper_001",
    target_id="concept_attention",
    relation_type="introduces",
    confidence=1.0,
    evidence="The paper proposes the self-attention mechanism"
)

# Create a refutation relationship
graph.add_edge(
    source_id="paper_002",
    target_id="paper_001",
    relation_type="refutes",
    confidence=0.8,
    evidence="Claims transformers have efficiency issues"
)
```

### Query Related Nodes

```python
# Get all related nodes
related = graph.get_related_nodes("paper_001")

# Get only nodes with a specific relationship
supporters = graph.get_related_nodes("paper_001", relation_type="supports")
```

### Multi-Hop Queries

```python
# Find nodes up to 2 hops away
result = graph.multi_hop_query("paper_001", max_depth=2)
# Returns: {0: [start_node], 1: [direct_connections], 2: [indirect_connections]}
```

### Reasoning Queries

```python
# Ask about relationships to a concept
summary = graph.reasoning_query("Transformer")
# Returns: "Regarding Transformer:\n- It is SUPPORTED by: ...\n- It is REFUTED by: ..."
```

### Get Statistics

```python
stats = graph.get_stats()
# Returns: {'total_nodes': 10, 'total_edges': 15, 'node_types': [...], 'relation_types': [...]}
```

## Migration to graph_rag

Replace:
```python
from skills.knowledge.memory.graph_store import GraphMemory
```

With:
```python
from skills.knowledge.graph_rag import initialize_rag, index_text, query_rag
```

## Implementation Files

- `skills/knowledge/memory/graph_store.py` - GraphMemory class implementation

## Relationship Types

Common relationship types used:
- `supports` - Evidence supporting a claim
- `refutes` - Evidence contradicting a claim
- `introduces` - Paper/work that introduces a concept
- `extends` - Work that builds upon another
- `cites` - Citation relationship
