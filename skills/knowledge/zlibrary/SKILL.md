---
name: zlibrary
description: Search and download books from Z-Library using the zlibrary-mcp server.
license: Apache-2.0
metadata:
  type: tool
  python_package: skills.knowledge.zlibrary
---

# Z-Library Skill

Search and download books from Z-Library using the zlibrary-mcp server.

## Prerequisites

1. Z-Library account credentials in `.env`:
   ```
   ZLIBRARY_EMAIL=your-email@example.com
   ZLIBRARY_PASSWORD=your-password
   ```

2. MCP root path configured:
   ```
   MCP_ROOT=/path/to/mcp
   ```

3. zlibrary-mcp cloned and built:
   ```bash
   cd $MCP_ROOT/zlibrary-mcp
   bash setup-uv.sh
   npm install
   npm run build
   ```

## Functions

### search_books(query, limit=10)
Search for books on Z-Library.
- Returns list of book metadata (title, authors, year, format, etc.)

### download_book(book_id, save_to_db=True)
Download a book by its Z-Library ID.
- Saves to `downloads/` folder
- Optionally adds to database

### search_and_download(query, download_first=True)
Search and optionally download the first result.

### list_downloaded_books()
List all downloaded books from the database.

### get_book_info(book_id)
Get detailed info about a specific book.

## Usage

```python
from skills.knowledge.zlibrary.client import search_books, download_book

# Search for books
books = search_books("Python programming", limit=5)

# Download a specific book
result = download_book(books[0]["id"])
print(f"Downloaded to: {result['local_path']}")
```

### CLI Usage

```bash
# Search for books
python -m skills.knowledge.zlibrary search "Python"

# Download a book
python -m skills.knowledge.zlibrary download <book_id>

# List downloaded books
python -m skills.knowledge.zlibrary list
```

## Downloads Location

Books are downloaded to: `downloads/` in the project root.
