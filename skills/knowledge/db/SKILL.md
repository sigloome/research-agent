---
name: db
description: Manage the local research database (SQLite). Initialize DB, list papers/books, and view statistics.
license: Apache-2.0
metadata:
  type: utility
  python_package: skills.knowledge.db
---

# Db Skill

Description needed.

## Usage

```python
from skills.db import ...
```

### CLI Usage

```bash
# Initialize DB
python -m skills.knowledge.db init

# Show status
python -m skills.knowledge.db status

# List papers
python -m skills.knowledge.db list-papers --limit 5

# Search papers
python -m skills.knowledge.db search-papers "LLM agents"

# List books
python -m skills.knowledge.db list-books

# List sources
python -m skills.knowledge.db list-sources
```

## Functions

### `get_db_connection()`

Description needed.

### `init_db()`

Description needed.

### `add_paper()`

Description needed.

### `add_source()`

Description needed.

### `list_sources()`

Description needed.

### `get_source()`

Description needed.

### `get_source_by_name()`

Description needed.

### `update_source()`

Description needed.

### `delete_source()`

Description needed.

### `list_papers()`

Description needed.

### `get_paper()`

Description needed.

### `search_local_papers()`

Description needed.

### `add_book()`

Description needed.

### `list_books()`

Description needed.

### `get_book()`

Description needed.

### `search_books()`

Description needed.

### `get_zlibrary_source_id()`

Description needed.

### `record_user_query()`

Description needed.

### `get_recent_queries()`

Description needed.

### `update_user_preference()`

Description needed.

### `get_user_preferences()`

Description needed.

### `get_preference_summary()`

Description needed.

## Examples

TODO: Add examples.
