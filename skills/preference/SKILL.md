---
name: preference
description: Analyze user queries, learn preferences via feedback (bandit), and manage user profiles.
license: Apache-2.0
metadata:
  short-description: User preference analysis and learning
  python_package: skills.preference
---

# Preference Skill

Analyzes user queries to extract topics, query types, and interests for personalized recommendations. Maintains a user profile that syncs with the knowledge graph.

## Capabilities

1. **Extract topics** - Detect AI/ML research topics from user queries
2. **Detect query type** - Classify queries (find papers, explain, summarize, compare, recommend)
3. **Extract interests** - Identify specific models, techniques, and entities mentioned
4. **Analyze queries** - Full analysis combining topics, type, and interests
5. **Update preferences** - Record queries and update preference weights in the database
6. **Manage user profile** - Read/write user profile with auto-sync to RAG

## Usage

### Analyze a Query

```python
from skills.preference.analyzer import analyze_query

result = analyze_query("Find recent papers on LLM alignment using RLHF")
# Returns: {
#   'topics': ['large language models', 'alignment', 'reinforcement learning'],
#   'query_type': 'find_papers',
#   'interests': ['rlhf']
# }
```

### Extract Topics Only

```python
from skills.preference.analyzer import extract_topics

topics = extract_topics("How does chain of thought prompting improve reasoning?")
# Returns: ['prompt engineering', 'reasoning']
```

### Detect Query Type

```python
from skills.preference.analyzer import detect_query_type

query_type = detect_query_type("Explain how transformers work")
# Returns: 'explain_concept'
```

### Update Preferences from Query

```python
from skills.preference.analyzer import update_preferences_from_query

# Records the query and updates preference weights in the database
analysis = update_preferences_from_query("Find papers on multimodal LLMs")
```

```python
from skills.preference.implementation import get_user_profile, update_user_profile, append_to_profile

# Read current profile
profile = get_user_profile()

# Update entire profile
update_user_profile("# User Profile\n\n## Research Interests\n- LLM alignment\n- AI safety")

# Append a new section
append_to_profile("Recent Searches", "- Chain of thought prompting\n- RLHF techniques")
```

### CLI Usage

```bash
# Analyze a query
python -m skills.preference analyze "Find papers on LLM agents"

# Extract topics only
python -m skills.preference extract-topics "How does RLHF work?"

# Update preferences from a query
python -m skills.preference update "Find papers on multimodal models"

# Show user profile
python -m skills.preference show-profile

# Append to profile
python -m skills.preference append-profile --section "Notes" --content "User likes succinct summaries"
```

## Supported Topics

The analyzer recognizes these AI/ML research categories:

- **Core ML**: machine learning, deep learning, reinforcement learning
- **NLP & Language**: large language models, NLP, transformers, prompt engineering
- **Vision**: computer vision, image generation, multimodal
- **AI Safety**: alignment, safety, interpretability
- **Agents & Systems**: agents, reasoning, retrieval (RAG)
- **Training**: fine-tuning, training, efficiency
- **Applications**: code generation, summarization, question answering

## Query Types

- `find_papers` - Searching for research papers
- `explain_concept` - Asking for explanations
- `summarize` - Requesting summaries
- `compare` - Comparing approaches/models
- `recommend` - Asking for recommendations
- `paper_lookup` - Looking up specific papers
- `general` - Other queries

## Implementation Files

- `skills/preference/analyzer.py` - Query analysis and topic extraction
- `skills/preference/implementation.py` - User profile management with RAG sync
- `skills/preference/feedback.py` - Feedback collection utilities

## Auto-Sync Feature

The user profile (`data/preferences/user_profile.md`) automatically syncs to the Preference Knowledge Graph when:
- The profile is updated programmatically
- Manual changes are detected on read
