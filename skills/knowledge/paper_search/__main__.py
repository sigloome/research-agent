
import argparse
import sys
import json
import logging
from skills.knowledge.paper_search.fetcher import fetch_and_process, get_arxiv_paper_by_id, enrich_with_s2

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

def main():
    parser = argparse.ArgumentParser(description="Paper Search CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Command: search
    search_parser = subparsers.add_parser("search", help="Search ArXiv")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--max", type=int, default=5, help="Max results")

    # Command: get
    get_parser = subparsers.add_parser("get", help="Get paper by ID")
    get_parser.add_argument("id", help="ArXiv ID")

    args = parser.parse_args()

    if args.command == "search":
        print(f"Searching for '{args.query}'...")
        papers = fetch_and_process(args.query, max_results=args.max)
        print(f"Found {len(papers)} papers:")
        for p in papers:
            print(f"  - [{p['id']}] {p.get('title')}")

    elif args.command == "get":
        print(f"Fetching paper {args.id}...")
        paper = get_arxiv_paper_by_id(args.id)
        if paper:
            print(json.dumps(paper, indent=2))
        else:
            print("Paper not found.")

    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
