
import argparse
import sys
import logging

# Sub-components
from skills.knowledge.graph_rag.__main__ import main as rag_main
from skills.knowledge.rag_critic.__main__ import main as critic_main
from skills.knowledge.paper.__main__ import main as paper_main
from skills.knowledge.paper_search.__main__ import main as search_main
from skills.knowledge.db.__main__ import main as db_main
from skills.knowledge.local_files.__main__ import main as local_main
from skills.knowledge.zlibrary.__main__ import main as zlib_main
from skills.knowledge.summarizer.__main__ import main as sum_main

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

def main():
    parser = argparse.ArgumentParser(description="Knowledge Skill CLI")
    subparsers = parser.add_subparsers(dest="component", help="Component to use")

    # Component: rag
    rag_parser = subparsers.add_parser("rag", help="GraphRAG Engine", add_help=False)
    
    # Component: critic
    critic_parser = subparsers.add_parser("critic", help="RAG Critic", add_help=False)

    # Component: paper
    paper_parser = subparsers.add_parser("paper", help="Paper Operations", add_help=False)

    # Component: search
    search_parser = subparsers.add_parser("search", help="Paper Search", add_help=False)

    # Component: db
    db_parser = subparsers.add_parser("db", help="Database Management", add_help=False)

    # Component: pdf
    pdf_parser = subparsers.add_parser("pdf", help="Local PDF Importer", add_help=False)

    # Component: zlib
    zlib_parser = subparsers.add_parser("zlib", help="Z-Library", add_help=False)

    # Component: summarize
    sum_parser = subparsers.add_parser("summarize", help="Text Summarizer", add_help=False)

    args, remaining = parser.parse_known_args()

    # Forward to specific main functions with modified argv
    sys.argv = [sys.argv[0]] + remaining

    if args.component == "rag":
        rag_main()
    elif args.component == "critic":
        critic_main()
    elif args.component == "paper":
        paper_main()
    elif args.component == "search":
        search_main()
    elif args.component == "db":
        db_main()
    elif args.component == "pdf":
        local_main()
    elif args.component == "zlib":
        zlib_main()
    elif args.component == "summarize":
        sum_main()
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
