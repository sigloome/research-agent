
import argparse
import sys
import json
import logging
from skills.knowledge.db.manager import (
    init_db,
    list_papers,
    search_local_papers,
    list_books,
    search_books,
    list_sources,
    get_db_connection
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

def get_counts():
    conn = get_db_connection()
    c = conn.cursor()
    counts = {}
    c.execute("SELECT COUNT(*) FROM papers")
    counts['papers'] = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM books")
    counts['books'] = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM library_sources")
    counts['sources'] = c.fetchone()[0]
    conn.close()
    return counts

def main():
    parser = argparse.ArgumentParser(description="Library Database CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Command: init
    subparsers.add_parser("init", help="Initialize the database")

    # Command: status
    subparsers.add_parser("status", help="Show database statistics")

    # Command: list-papers
    papers_parser = subparsers.add_parser("list-papers", help="List papers")
    papers_parser.add_argument("--limit", type=int, default=10, help="Limit results")
    papers_parser.add_argument("--sort", default="created_at_desc", help="Sort order")

    # Command: search-papers
    search_papers_parser = subparsers.add_parser("search-papers", help="Search papers")
    search_papers_parser.add_argument("query", help="Search query")

    # Command: list-books
    books_parser = subparsers.add_parser("list-books", help="List books")
    books_parser.add_argument("--limit", type=int, default=10, help="Limit results")

    # Command: search-books
    search_books_parser = subparsers.add_parser("search-books", help="Search books")
    search_books_parser.add_argument("query", help="Search query")

    # Command: list-sources
    subparsers.add_parser("list-sources", help="List library sources")

    args = parser.parse_args()

    if args.command == "init":
        print("Initializing database...")
        init_db()
        print("Database initialized.")

    elif args.command == "status":
        try:
            counts = get_counts()
            print("Database Statistics:")
            print(f"  Papers:  {counts['papers']}")
            print(f"  Books:   {counts['books']}")
            print(f"  Sources: {counts['sources']}")
        except Exception as e:
            print(f"Error getting status: {e}")
            print("Try running 'init' first.")

    elif args.command == "list-papers":
        papers = list_papers(sort_by=args.sort)
        print(f"Found {len(papers)} papers (showing first {args.limit}):")
        for p in papers[:args.limit]:
            print(f"  - [{p['id']}] {p.get('title', 'No Title')} ({p.get('published_date', 'N/A')})")

    elif args.command == "search-papers":
        papers = search_local_papers(args.query)
        print(f"Found {len(papers)} matches:")
        for p in papers:
            print(f"  - {p.get('title', 'No Title')}")

    elif args.command == "list-books":
        books = list_books()
        print(f"Found {len(books)} books (showing first {args.limit}):")
        for b in books[:args.limit]:
            print(f"  - {b.get('title', 'No Title')} ({b.get('authors', 'N/A')})")

    elif args.command == "search-books":
        books = search_books(args.query)
        print(f"Found {len(books)} matches:")
        for b in books:
            print(f"  - {b.get('title', 'No Title')}")

    elif args.command == "list-sources":
        sources = list_sources()
        print(f"Found {len(sources)} sources:")
        for s in sources:
            status = "Enabled" if s['enabled'] else "Disabled"
            print(f"  - [{s['id']}] {s['name']} ({s['source_type']}) - {status}")

    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
