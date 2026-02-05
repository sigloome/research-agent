"""
Z-Library Client
Interacts with zlibrary-mcp server for searching and downloading books.
"""
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from skills.knowledge.db import manager

# Get paths from environment
MCP_ROOT = os.environ.get("MCP_ROOT", os.path.expanduser("~/code/mcp"))
ZLIBRARY_MCP_PATH = Path(MCP_ROOT) / "zlibrary-mcp"
DOWNLOADS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "downloads"

# Ensure downloads directory exists
DOWNLOADS_DIR.mkdir(exist_ok=True)


def get_zlibrary_env() -> Dict[str, str]:
    """Get environment variables for Z-Library MCP."""
    return {
        "ZLIBRARY_EMAIL": os.environ.get("ZLIBRARY_EMAIL", ""),
        "ZLIBRARY_PASSWORD": os.environ.get("ZLIBRARY_PASSWORD", ""),
        "PATH": os.environ.get("PATH", ""),
        "HOME": os.environ.get("HOME", ""),
    }


def run_mcp_command(tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run a command through the zlibrary-mcp server.
    This is a simplified client that calls the MCP tools directly via node.
    """
    mcp_script = ZLIBRARY_MCP_PATH / "dist" / "index.js"
    
    if not mcp_script.exists():
        return {"error": f"MCP script not found at {mcp_script}. Run 'npm run build' in zlibrary-mcp directory."}
    
    # For now, we'll use Python's zlibrary library directly since it's vendored
    # The MCP server is primarily for AI assistant integration
    # We can call the Python functions directly for better control
    
    try:
        # Import the vendored zlibrary module
        import sys
        zlibrary_path = ZLIBRARY_MCP_PATH / "zlibrary"
        if str(zlibrary_path.parent) not in sys.path:
            sys.path.insert(0, str(zlibrary_path.parent))
        
        import asyncio

        from zlibrary import AsyncZlib
        
        # Run async function
        return asyncio.get_event_loop().run_until_complete(
            _run_zlibrary_tool(tool_name, args)
        )
    except ImportError as e:
        return {"error": f"Failed to import zlibrary: {e}. Make sure dependencies are installed."}
    except Exception as e:
        return {"error": f"Error running MCP command: {e}"}


async def _run_zlibrary_tool(tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """Run a zlibrary tool asynchronously."""
    import sys
    zlibrary_path = ZLIBRARY_MCP_PATH / "zlibrary"
    if str(zlibrary_path.parent) not in sys.path:
        sys.path.insert(0, str(zlibrary_path.parent))
    
    from zlibrary import AsyncZlib
    
    email = os.environ.get("ZLIBRARY_EMAIL", "")
    password = os.environ.get("ZLIBRARY_PASSWORD", "")
    
    if not email or not password:
        return {"error": "Z-Library credentials not configured. Set ZLIBRARY_EMAIL and ZLIBRARY_PASSWORD in .env"}
    
    lib = AsyncZlib()
    await lib.login(email, password)
    
    if tool_name == "search":
        query = args.get("query", "")
        limit = args.get("limit", 10)
        
        paginator = await lib.search(q=query, count=limit)
        results = []
        
        async for book in paginator:
            results.append({
                "id": str(book.id),
                "title": book.name,
                "authors": book.authors if hasattr(book, 'authors') else [],
                "year": str(book.year) if hasattr(book, 'year') else "",
                "language": book.language if hasattr(book, 'language') else "",
                "format": book.extension if hasattr(book, 'extension') else "",
                "file_size": book.size if hasattr(book, 'size') else "",
                "cover_url": book.cover if hasattr(book, 'cover') else "",
            })
            if len(results) >= limit:
                break
        
        return {"books": results}
    
    elif tool_name == "download":
        book_id = args.get("book_id", "")
        
        # Get book details first
        book = await lib.getById(book_id)
        if not book:
            return {"error": f"Book not found: {book_id}"}
        
        # Download the book
        filename = f"{book.name[:50]}_{book_id}.{book.extension}"
        filename = "".join(c for c in filename if c.isalnum() or c in "._- ")
        
        download_path = DOWNLOADS_DIR / filename
        
        try:
            await book.download(str(download_path))
            
            return {
                "success": True,
                "local_path": str(download_path),
                "book": {
                    "id": str(book.id),
                    "title": book.name,
                    "authors": book.authors if hasattr(book, 'authors') else [],
                    "format": book.extension,
                }
            }
        except Exception as e:
            return {"error": f"Download failed: {e}"}
    
    return {"error": f"Unknown tool: {tool_name}"}


def search_books(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Search for books on Z-Library.
    
    Args:
        query: Search query (title, author, ISBN, etc.)
        limit: Maximum number of results
    
    Returns:
        List of book metadata dictionaries
    """
    print(f"[zlibrary] Searching for: {query}")
    result = run_mcp_command("search", {"query": query, "limit": limit})
    
    if "error" in result:
        print(f"[zlibrary] Error: {result['error']}")
        return []
    
    return result.get("books", [])


def download_book(book_id: str, save_to_db: bool = True) -> Dict[str, Any]:
    """
    Download a book from Z-Library.
    
    Args:
        book_id: Z-Library book ID
        save_to_db: Whether to save book info to database
    
    Returns:
        Dictionary with download result and local path
    """
    print(f"[zlibrary] Downloading book: {book_id}")
    result = run_mcp_command("download", {"book_id": book_id})
    
    if "error" in result:
        print(f"[zlibrary] Error: {result['error']}")
        return result
    
    if save_to_db and result.get("success"):
        book_data = result.get("book", {})
        
        # Get Z-Library source ID
        source_id = manager.get_zlibrary_source_id()
        
        # Generate unique ID
        unique_id = f"zlib-{book_id}"
        
        # Save to database
        manager.add_book({
            "id": unique_id,
            "title": book_data.get("title"),
            "authors": book_data.get("authors", []),
            "format": book_data.get("format"),
            "local_path": result.get("local_path"),
            "zlibrary_id": book_id,
            "source_id": source_id,
            "tags": ["zlibrary", "downloaded"],
        })
        
        print(f"[zlibrary] Book saved to database: {book_data.get('title')}")
    
    return result


def search_and_download(query: str, download_first: bool = True) -> Dict[str, Any]:
    """
    Search for a book and optionally download the first result.
    
    Args:
        query: Search query
        download_first: Whether to download the first matching book
    
    Returns:
        Dictionary with search results and download info
    """
    books = search_books(query, limit=5)
    
    if not books:
        return {"error": "No books found", "query": query}
    
    result = {"books": books}
    
    if download_first and books:
        first_book = books[0]
        download_result = download_book(first_book["id"])
        result["downloaded"] = download_result
    
    return result


def list_downloaded_books() -> List[Dict[str, Any]]:
    """List all downloaded books from the database."""
    return manager.list_books()


def get_book_info(book_id: str) -> Optional[Dict[str, Any]]:
    """Get book information from the database."""
    return manager.get_book(book_id)
