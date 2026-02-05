# Book Management Specification

## Overview

Book search, download, and upload functionality via Z-Library and WeRead.

## Requirements

### Functional Requirements

1. **Z-Library Search**
   - Search books by title/author
   - Display search results
   - Show book metadata

2. **Book Download**
   - Download books to local storage
   - Track download in database
   - Support multiple formats (PDF, EPUB)

3. **Book Storage**
   - Store in `downloads/` directory
   - Track metadata in database
   - Associate with Z-Library source

4. **WeRead Upload**
   - List uploadable books
   - Upload to WeRead (requires auth)
   - Track upload status

### Non-Functional Requirements

1. **File Size**
   - Max 50MB for WeRead upload
   - Handle large downloads gracefully

2. **Formats**
   - Support: PDF, EPUB, TXT, MOBI
   - Format detection by extension

## API Specification

### List Books
```
GET /api/books
Response: [
  {
    "id": 1,
    "title": "Book Title",
    "authors": "Author Name",
    "format": "pdf",
    "local_path": "/path/to/book.pdf"
  }
]
```

### Get Book
```
GET /api/books/{id}
Response: {book object}
```

### Search Books
```
GET /api/books/search/{query}
Response: [matching books]
```

## Data Model

```sql
CREATE TABLE books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    authors TEXT,
    publisher TEXT,
    year INTEGER,
    language TEXT,
    format TEXT,
    file_size TEXT,
    pages INTEGER,
    isbn TEXT,
    description TEXT,
    cover_url TEXT,
    download_url TEXT,
    local_path TEXT,
    processed_text_path TEXT,
    zlibrary_id TEXT,
    source_id INTEGER REFERENCES library_sources(id),
    tags TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_books_zlibrary ON books(zlibrary_id);
CREATE INDEX idx_books_source ON books(source_id);
```

## Skills

### zlibrary

```python
# Search books
books = search_books("machine learning", limit=10)

# Download book
result = download_book(book_id)

# List downloaded
downloaded = list_downloaded_books()
```

### weread

```python
# List uploadable
books = list_uploadable_books()

# Upload book
result = upload_book("/path/to/book.pdf")

# Open upload page
open_upload_page()
```

## Test Cases

1. **Z-Library Search**
   - Returns book list
   - Books have required metadata
   - Handles no results

2. **Book Download**
   - Saves file to downloads/
   - Records in database
   - Handles download errors

3. **WeRead List**
   - Finds books in downloads/ and local_articles/
   - Filters by supported formats
   - Checks file size limits

4. **WeRead Upload**
   - Requires cookies/auth
   - Shows clear error without auth
   - Handles successful upload

## Environment Variables

```
# Z-Library credentials
ZLIBRARY_EMAIL=your-email
ZLIBRARY_PASSWORD=your-password

# MCP root for zlibrary-mcp
MCP_ROOT=/path/to/mcp

# WeRead cookies (optional)
WEREAD_COOKIES={"wr_vid": "...", ...}
```
