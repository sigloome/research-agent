---
name: rag-critic
description: Evaluate and filter RAG retrieval results using an LLM critic. Improve retrieval quality by scoring chunks and filtering distractors.
license: Apache-2.0
metadata:
  short-description: LLM-based retrieval quality evaluation
  python_package: skills.knowledge.rag_critic
---

# RAG Critic Skill

Uses an LLM as a "critic" to evaluate the relevance of retrieved chunks to a query. Helps filter out irrelevant or misleading chunks (distractors) that match keywords but don't actually answer the question.

## CLI Usage

```bash
# Evaluate a chunk
python -m skills.knowledge.rag_critic evaluate "What is attention?" "The Transformer uses self-attention..."
```

## Capabilities

1. **Evaluate chunks** - Score individual chunks for relevance (0.0-1.0)
2. **Filter distractors** - Remove chunks that mention keywords but aren't relevant
3. **Hierarchical retrieval** - Retrieve and filter chunks in one pipeline
4. **Context-aware scoring** - Distinguish between "Related Work" mentions vs actual answers

## Problem Solved

Traditional RAG retrieval often returns chunks that contain query keywords but don't actually answer the question. For example:
- A chunk mentioning "Transformer" in a Related Work section
- Background descriptions of other people's work
- Tangentially related concepts

The RAG Critic scores each chunk and filters out these distractors.

## Usage

### Evaluate a Single Chunk

```python
import asyncio
from skills.knowledge.rag_critic.critic import RagCritic

critic = RagCritic(model="claude-sonnet-4-5-20250929")

async def evaluate():
    result = await critic.evaluate_chunk(
        query_text="What is the attention mechanism in Transformers?",
        chunk_text="The Transformer model relies entirely on self-attention..."
    )
    print(result)
    # Returns: {"score": 0.9, "reasoning": "Directly describes the attention mechanism"}

asyncio.run(evaluate())
```

### Filter Multiple Chunks

```python
import asyncio
from skills.knowledge.rag_critic.retriever import HierarchicalRetriever

retriever = HierarchicalRetriever(model="claude-sonnet-4-5-20250929")

async def filter_chunks():
    chunks = [
        "The Transformer uses self-attention to process sequences...",
        "In related work, Smith et al. also studied attention...",
        "Our experimental results show 95% accuracy...",
    ]
    
    filtered = await retriever.retrieve_and_filter(
        query="How does the Transformer's attention mechanism work?",
        chunks=chunks
    )
    # Returns only chunks with score >= 0.5
    return filtered

result = asyncio.run(filter_chunks())
```

## Scoring Guidelines

The critic uses these rules:
- **Low score (0.0-0.3)**: Keywords in Related Work/Background context
- **Medium score (0.4-0.6)**: Partially relevant, needs more context
- **High score (0.7-1.0)**: Directly answers the query or contains key evidence

## Configuration

```python
# Use a different model
critic = RagCritic(model="claude-haiku-3-5-20241022")

# Adjust the threshold in retriever (default: 0.5)
# Edit retriever.py line 36 to change threshold
```

## Implementation Files

- `skills/knowledge/rag_critic/critic.py` - RagCritic class with LLM evaluation
- `skills/knowledge/rag_critic/retriever.py` - HierarchicalRetriever for batch filtering

## Integration Example

```python
from skills.knowledge.graph_rag import query_rag
from skills.knowledge.rag_critic.retriever import HierarchicalRetriever

async def enhanced_rag_query(query: str):
    # 1. Get initial results from RAG
    raw_results = query_rag(query, mode="hybrid")
    
    # 2. Extract chunks
    chunks = [r['content'] for r in raw_results]
    
    # 3. Filter with critic
    retriever = HierarchicalRetriever()
    filtered_chunks = await retriever.retrieve_and_filter(query, chunks)
    
    return filtered_chunks
```

## Performance Notes

- Each chunk requires an LLM call, so batch evaluation can be slow
- Consider parallel evaluation for production use (modify retriever.py)
- Use a faster model (e.g., Haiku) for high-volume filtering
