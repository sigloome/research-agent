# Core Features Specification

## Overview

Core features that define the Velvet Research platform.

## Requirements

### Functional Requirements

1. **Paper Search and Management**
   - Search ArXiv for papers by topic
   - Store papers in local database
   - Display papers with pagination
   - Filter by source

2. **Book Management**
   - Search Z-Library for books
   - Download books to local storage
   - Track downloaded books in database
   - Upload books to WeRead

3. **AI Chat Interface**
   - Streaming chat responses
   - Tool execution with visual feedback
   - Paper-specific questions
   - Preference-aware recommendations

4. **User Preferences**
   - Track user queries
   - Learn topic preferences
   - Personalize recommendations

### Non-Functional Requirements

1. **Performance**
   - API response < 500ms for list operations
   - Chat streaming with < 100ms latency per chunk
   - Paper fetch < 5s for 5 papers

2. **Reliability**
   - Graceful degradation when ArXiv is slow
   - Database connection pooling
   - Error handling with user feedback

3. **Security**
   - API keys in environment variables
   - No credentials in git
   - Input validation on all endpoints

## API Specification

### Base URL
- Development: `http://localhost:18000`
- Frontend: `http://localhost:15173`

### Endpoints

See individual spec files for detailed endpoint documentation.

## Data Model

### Core Tables

```sql
-- Papers from various sources
papers (
    id TEXT PRIMARY KEY,
    title TEXT,
    authors TEXT,
    abstract TEXT,
    summary_main_ideas TEXT,
    tags TEXT,
    published_date TEXT,
    url TEXT,
    pdf_url TEXT,
    html_url TEXT,
    citation_count INTEGER,
    source_id INTEGER,
    created_at TIMESTAMP
)

-- Library sources
library_sources (
    id INTEGER PRIMARY KEY,
    name TEXT,
    source_type TEXT,
    url TEXT,
    icon TEXT,
    description TEXT,
    config TEXT,
    created_at TIMESTAMP
)

-- Downloaded books
books (
    id INTEGER PRIMARY KEY,
    title TEXT,
    authors TEXT,
    publisher TEXT,
    year INTEGER,
    format TEXT,
    local_path TEXT,
    source_id INTEGER,
    created_at TIMESTAMP
)

-- User query history
user_queries (
    id INTEGER PRIMARY KEY,
    query TEXT,
    context TEXT,
    created_at TIMESTAMP
)

-- Learned preferences
user_preferences (
    id INTEGER PRIMARY KEY,
    preference_type TEXT,
    value TEXT,
    weight REAL,
    created_at TIMESTAMP
)
```

## Test Cases

### Critical Paths

1. **Paper Search Flow**
   - User enters search query
   - Papers fetched from ArXiv
   - Papers displayed in table
   - User can filter by source

2. **Chat Flow**
   - User sends message
   - Agent processes with tools
   - Response streams to UI
   - Tool executions shown

3. **Book Download Flow**
   - User searches Z-Library
   - Results displayed
   - User triggers download
   - Book saved locally

## Dependencies

- ArXiv API
- Semantic Scholar API (optional)
- Z-Library (via MCP)
- Claude API
