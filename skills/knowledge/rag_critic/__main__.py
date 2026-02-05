
import argparse
import sys
import json
import logging
import asyncio
from skills.knowledge.rag_critic.critic import RagCritic

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

def main():
    parser = argparse.ArgumentParser(description="RAG Critic CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Command: evaluate
    eval_parser = subparsers.add_parser("evaluate", help="Evaluate a chunk against a query")
    eval_parser.add_argument("query", help="User query")
    eval_parser.add_argument("chunk", help="Text chunk to evaluate")
    eval_parser.add_argument("--model", default="claude-sonnet-4-5-20250929", help="Model to use")

    args = parser.parse_args()

    if args.command == "evaluate":
        print(f"Evaluating chunk relevance...")
        critic = RagCritic(model=args.model)
        
        async def run_eval():
             return await critic.evaluate_chunk(args.query, args.chunk)

        try:
            result = asyncio.run(run_eval())
            print(json.dumps(result, indent=2))
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)

    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
