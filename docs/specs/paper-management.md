# Paper Management Specification

## Overview

Paper search, storage, and display functionality.

## Requirements

### Functional Requirements

1. **Paper Search**
   - Search ArXiv by query
   - Sort by date or relevance
   - Limit results (1-10)

2. **Paper Storage**
   - Store papers in SQLite
   - Track source (ArXiv, local, etc.)
   - Store metadata and summaries

3. **Paper Display**
   - Paginated table view
   - Filter by source
   - Search within library
   - Quick actions (ask, view source)

4. **Local Import**
   - Import PDF files
   - Extract metadata
   - Generate paper ID

## API Specification

### List Papers
```
GET /api/papers?source_id={id}&page={n}&limit={n}
Response: {
  "papers": [...],
  "total": 100,
  "page": 1,
  "limit": 10
}
```

### Get Paper
```
GET /api/papers/{id}
Response: {paper object}
```

### Search Papers
```
POST /api/papers/search
Body: {"query": "LLM"}
Response: [matching papers]
```

### Fetch Papers
```
POST /api/papers/fetch
Body: {"query": "transformer", "max_results": 5}
Response: [fetched papers]
```

## Data Model

```sql
CREATE TABLE papers (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    authors TEXT,
    abstract TEXT,
    summary_main_ideas TEXT,
    tags TEXT,
    published_date TEXT,
    url TEXT,
    pdf_url TEXT,
    html_url TEXT,
    citation_count INTEGER DEFAULT 0,
    source_id INTEGER REFERENCES library_sources(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_papers_source ON papers(source_id);
CREATE INDEX idx_papers_date ON papers(published_date);
```

## User Interface

### Paper Table
- Columns: Title, Authors, Date, Source, Actions
- Sortable columns
- Expandable rows for abstract

### Filters
- Source dropdown
- Text search (debounced)
- Date range (future)

### Pagination
- Page size selector (10, 20, 50, 100)
- Page number input
- First/Last/Prev/Next buttons
- Total count display

### Actions
- "Ask about this paper" button
- "View source" link
- Copy citation (future)

## Test Cases

1. **Fetch Papers**
   - Returns list of papers
   - Papers have required fields
   - Respects max_results limit

2. **Search Local**
   - Matches title
   - Matches abstract
   - Returns empty for no match

3. **Pagination**
   - Correct page size
   - Correct total count
   - Handles edge cases (empty, single page)

4. **Source Filter**
   - Filters by source_id
   - Shows correct counts per source

5. **Local Import**
   - Extracts PDF metadata
   - Generates unique ID
   - Stores in database
