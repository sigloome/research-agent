
import argparse
import sys
import json
import logging
from skills.knowledge.summarizer.summarize import generate_summary

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

def main():
    parser = argparse.ArgumentParser(description="Summarizer CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Command: summarize
    sum_parser = subparsers.add_parser("summarize", help="Summarize text")
    sum_parser.add_argument("--file", help="Input file path")
    sum_parser.add_argument("--text", help="Input text string")
    sum_parser.add_argument("--title", default="", help="Title context")

    args = parser.parse_args()

    if args.command == "summarize":
        text = ""
        if args.file:
            try:
                with open(args.file, 'r', encoding='utf-8') as f:
                    text = f.read()
            except Exception as e:
                print(f"Error reading file: {e}")
                sys.exit(1)
        elif args.text:
            text = args.text
        else:
            # Try reading from stdin
            if not sys.stdin.isatty():
                text = sys.stdin.read()
            else:
                print("Error: Must provide --file, --text, or pipe input via stdin")
                sys.exit(1)

        print(f"Summarizing text ({len(text)} chars)...")
        result = generate_summary(text, title=args.title)
        print(json.dumps(result, indent=2))

    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
