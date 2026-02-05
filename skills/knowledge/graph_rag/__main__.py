
import argparse
import sys
import logging
from skills.knowledge.graph_rag.implementation import initialize_rag, index_text, query_rag, reset_rag

# Configure logging to stdout
logging.basicConfig(level=logging.INFO, format='%(message)s')

def main():
    parser = argparse.ArgumentParser(description="GraphRAG CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Command: init
    init_parser = subparsers.add_parser("init", help="Initialize the RAG system")
    init_parser.add_argument("--name", default="knowledge", help="Name of the RAG instance")
    init_parser.add_argument("--dir", default="./data/graph_rag", help="Working directory")

    # Command: index
    index_parser = subparsers.add_parser("index", help="Index text content")
    index_parser.add_argument("text", help="Text to index (or use --file)")
    index_parser.add_argument("--name", default="knowledge", help="Name of the RAG instance")

    # Command: query
    query_parser = subparsers.add_parser("query", help="Query the RAG system")
    query_parser.add_argument("query", help="Query string")
    query_parser.add_argument("--mode", default="global", choices=["naive", "local", "global", "hybrid"], help="Query mode")
    query_parser.add_argument("--name", default="knowledge", help="Name of the RAG instance")

    args = parser.parse_args()

    if args.command == "init":
        print(f"Initializing RAG '{args.name}' at '{args.dir}'...")
        initialize_rag(name=args.name, working_dir=args.dir)
        print("Done.")

    elif args.command == "index":
        print(f"Indexing text into '{args.name}'...")
        index_text(args.text, rag_name=args.name)
        print("Done.")

    elif args.command == "query":
        print(f"Querying '{args.name}' (mode: {args.mode})...")
        response = query_rag(args.query, mode=args.mode, rag_name=args.name)
        print("\n--- Response ---\n")
        print(response)
        print("\n----------------\n")

    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
