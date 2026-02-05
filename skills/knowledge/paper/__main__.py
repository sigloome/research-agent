
import argparse
import sys
import json
import logging
from skills.knowledge.paper.core import (
    fetch_papers,
    add_paper_by_url,
    analyze_paper,
    search_local_papers
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

def main():
    parser = argparse.ArgumentParser(description="Library Paper CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Command: fetch (ArXiv search)
    fetch_parser = subparsers.add_parser("fetch", help="Fetch papers from ArXiv")
    fetch_parser.add_argument("query", help="Search query")
    fetch_parser.add_argument("--max", type=int, default=5, help="Max results")

    # Command: add (by URL)
    add_parser = subparsers.add_parser("add", help="Add paper by ArXiv URL")
    add_parser.add_argument("url", help="ArXiv URL")

    # Command: analyze (Download + Summarize)
    analyze_parser = subparsers.add_parser("analyze", help="Analyze paper (Download + Summarize)")
    analyze_parser.add_argument("id", help="Paper ID (e.g. 2310.xxxxx)")

    # Command: search (Local)
    search_parser = subparsers.add_parser("search", help="Search local papers")
    search_parser.add_argument("query", help="Search query")

    args = parser.parse_args()

    if args.command == "fetch":
        print(f"Fetching papers for '{args.query}'...")
        papers = fetch_papers(args.query, max_results=args.max)
        print(f"Found {len(papers)} papers:")
        for p in papers:
            print(f"  - [{p['id']}] {p['title']} ({p.get('published', 'N/A')})")

    elif args.command == "add":
        print(f"Adding paper from {args.url}...")
        result = add_paper_by_url(args.url)
        print(result)

    elif args.command == "analyze":
        print(f"Analyzing paper {args.id}...")
        try:
            paper = analyze_paper(args.id)
            print("Analysis complete.")
            print(f"Title: {paper.get('title')}")
            print(f"Summary: {paper.get('summary_main_ideas')[:200]}...")
            print(f"Full text stored at: {paper.get('full_text_local_path')}")
        except Exception as e:
            print(f"Error analyzing paper: {e}")

    elif args.command == "search":
        papers = search_local_papers(args.query)
        print(f"Found {len(papers)} matches:")
        for p in papers:
            print(f"  - {p.get('title', 'No Title')}")

    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
