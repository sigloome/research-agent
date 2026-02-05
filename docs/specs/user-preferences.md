# User Preferences Specification

## Overview

Track user queries and learn preferences to personalize recommendations.
Uses a dual-storage approach:
1. **SQL Database (`papers.db`)**: Stores structured preference weights for Agent decision making.
2. **Markdown Profile (`user_profile.md`)**: Stores a human-readable history/biography (synced to Knowledge Graph).

## Requirements

### Functional Requirements

1. **Query Tracking**
   - Record every user query
   - Store query context
   - Timestamp queries

2. **Preference Learning**
   - Extract topics from queries
   - Weight by frequency
   - Identify patterns

3. **Recommendation Personalization**
   - Include preferences in agent prompt
   - Suggest relevant questions
   - Prioritize preferred topics

4. **Preference Display**
   - Show learned preferences
   - Allow preference editing (future)

### Non-Functional Requirements

1. **Privacy**
   - Preferences stored locally
   - No external transmission
   - User can clear data

2. **Performance**
   - Preference lookup < 50ms
   - Minimal storage overhead

## Data Model

```sql
-- User queries for preference learning
CREATE TABLE user_queries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query TEXT NOT NULL,
    context TEXT,  -- JSON with paper_id, etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Learned preferences
CREATE TABLE user_preferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    preference_type TEXT NOT NULL,  -- 'topic', 'format', 'depth'
    value TEXT NOT NULL,
    weight REAL DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_queries_date ON user_queries(created_at);
CREATE INDEX idx_preferences_type ON user_preferences(preference_type);
```

## API Specification

### Record Query
Called internally when user sends message. Extracts topics and updates SQL preference weights.

### Feedback Processing
Called when user interacts with UI elements (clicks, ratings).
- **Click**: Boosts topics associated with the clicked paper in SQL.
- **Rating**: Updates preferences based on positive/negative signal.
- **Log**: Appends event description to Markdown profile.

### Get Preferences
```
GET /api/preferences

Response: {
  "preferences": {
    "topics": [
      {"value": "LLM", "weight": 5.0},
      {"value": "transformers", "weight": 3.0}
    ],
    "recent_queries": [
      "How do transformers work?",
      "Find papers on LLM alignment"
    ]
  },
  "suggestions": [
    "What are the latest advances in LLM?",
    "Compare transformer architectures"
  ]
}
```

## Preference Types

### Topics
- Extracted from queries
- Keywords and phrases
- Weighted by frequency

### Format Preferences
- Detail level (summary vs deep dive)
- Response length
- Technical depth

### Interest Areas
- Paper categories (cs.AI, cs.LG, etc.)
- Specific research areas
- Authors of interest

## Skill Implementation

### preference/analyzer.py

```python
def record_query(query: str, context: dict = None) -> None:
    """Record a user query for preference learning."""
    
def get_preference_summary() -> dict:
    """Get summary of learned preferences."""
    
def extract_topics(query: str) -> list:
    """Extract topic keywords from query."""
    
def update_preference(ptype: str, value: str, weight_delta: float = 1.0):
    """Update or create a preference."""
    
def get_recent_queries(limit: int = 10) -> list:
    """Get recent user queries."""
```

## Agent Integration

### System Prompt Addition
```
## User Preferences

Based on the user's history, they are interested in:
- Topics: LLM (5.0), transformers (3.0), alignment (2.0)
- Recent focus: reasoning capabilities in large models

Consider these preferences when:
- Recommending papers
- Answering questions
- Suggesting follow-up topics
```

## Test Cases

1. **Record Query**
   - Query saved to database
   - Timestamp recorded
   - Context stored if provided

2. **Topic Extraction**
   - Keywords extracted correctly
   - Stopwords filtered
   - Technical terms preserved

3. **Preference Weighting**
   - Repeated topics increase weight
   - Recent queries weighted higher
   - Weights decay over time (future)

4. **Suggestion Generation**
   - Suggestions based on preferences
   - Diverse topic coverage
   - Relevant to recent queries

5. **Agent Integration**
   - Preferences in system prompt
   - Agent acknowledges preferences
   - Recommendations reflect interests
