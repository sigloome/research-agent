---
name: paper-search
description: Search and fetch AI research papers from ArXiv and other sources. Use this skill when users want to find papers on specific topics, fetch paper details, or search the local paper database.
license: Apache-2.0
metadata:
  short-description: Search and fetch AI research papers
  python_package: skills.knowledge.paper_search
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

To fetch papers on a topic, run the script:

```bash
cd /Users/bytedance/code/anti-demo
python -c "from skills.paper.operations import fetch_papers; import json; print(json.dumps(fetch_papers('YOUR_QUERY', max_results=5), default=str, indent=2))"
```

Replace `YOUR_QUERY` with the search term (e.g., "LLM alignment", "attention mechanisms", "cat:cs.AI").

### Search Local Database

```bash
cd /Users/bytedance/code/anti-demo
python -c "from skills.paper.operations import search_local_papers; import json; print(json.dumps(search_local_papers('YOUR_QUERY'), default=str, indent=2))"
```

### Read Paper Details

```bash
cd /Users/bytedance/code/anti-demo
python -c "from skills.paper.operations import read_paper; print(read_paper('PAPER_ID'))"
```

## Implementation Files

The skill implementation is in `skills/paper/operations.py` and can be modified for custom behavior.

### CLI Usage

```bash
# Search ArXiv
python -m skills.knowledge.paper_search search "LLM agents" --max 5

# Get paper metadata by ID
python -m skills.knowledge.paper_search get "2310.xxxxx"
```

## Functions:
- `fetch_papers(query, sort_by, max_results)` - Fetch from ArXiv
- `search_local_papers(query)` - Search local DB
- `add_paper_by_url(url)` - Add by ArXiv URL
- `read_paper(id)` - Get paper details
