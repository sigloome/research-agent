
import argparse
import sys
import json
import logging
from . import core

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

def main():
    parser = argparse.ArgumentParser(description="Skill Management CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Command: list
    list_parser = subparsers.add_parser("list", help="List all skills")

    # Command: search
    search_parser = subparsers.add_parser("search", help="Search for skills")
    search_parser.add_argument("query", help="Search query")

    # Command: read
    read_parser = subparsers.add_parser("read", help="Read skill content")
    read_parser.add_argument("path", help="Path to skill file (e.g. skills/paper/operations.py)")

    args = parser.parse_args()

    if args.command == "list":
        skills = core.list_skills()
        print(json.dumps(skills, indent=2))

    elif args.command == "search":
        results = core.search_skills(args.query)
        print(json.dumps(results, indent=2))

    elif args.command == "read":
        content = core.read_skill(args.path)
        print(content)

    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
