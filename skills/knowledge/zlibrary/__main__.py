
import argparse
import sys
import json
import logging
import asyncio
from skills.knowledge.zlibrary.client import (
    search_books,
    download_book,
    search_and_download,
    list_downloaded_books
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

def main():
    parser = argparse.ArgumentParser(description="Z-Library CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Command: search
    search_parser = subparsers.add_parser("search", help="Search Z-Library")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--limit", type=int, default=5, help="Limit results")

    # Command: download
    download_parser = subparsers.add_parser("download", help="Download book by ID")
    download_parser.add_argument("id", help="Z-Library Book ID")

    # Command: list
    subparsers.add_parser("list", help="List downloaded books")

    args = parser.parse_args()

    if args.command == "search":
        print(f"Searching for '{args.query}'...")
        # search_books is synchronous wrapper around async
        books = search_books(args.query, limit=args.limit)
        print(f"Found {len(books)} books:")
        for b in books:
            print(f"  - [{b['id']}] {b['title']} (Size: {b.get('file_size', '?')})")

    elif args.command == "download":
        print(f"Downloading book {args.id}...")
        result = download_book(args.id)
        if result.get("success"):
            print(f"Success! Saved to: {result['local_path']}")
        else:
            print(f"Failed: {result.get('error')}")

    elif args.command == "list":
        try:
            books = list_downloaded_books()
            print(f"Found {len(books)} downloaded books:")
            for b in books:
                print(f"  - [{b['id']}] {b.get('title', 'Unknown')}")
        except Exception as e:
            print(f"Error listing books: {e}")

    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
