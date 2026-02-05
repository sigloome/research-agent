
import argparse
import sys
import json
import logging
from skills.preference.analyzer import analyze_query, extract_topics, update_preferences_from_query
from skills.preference.implementation import get_user_profile, update_user_profile, append_to_profile
from skills.preference.learning.profile import UserProfile

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

def main():
    parser = argparse.ArgumentParser(description="User Preference CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Command: analyze
    analyze_parser = subparsers.add_parser("analyze", help="Analyze a user query")
    analyze_parser.add_argument("query", help="Query string")

    # Command: extract-topics
    topics_parser = subparsers.add_parser("extract-topics", help="Extract topics from query")
    topics_parser.add_argument("query", help="Query string")

    # Command: update
    update_parser = subparsers.add_parser("update", help="Update preferences from query")
    update_parser.add_argument("query", help="Query string")

    # Command: show-profile
    subparsers.add_parser("show-profile", help="Show current user profile")

    # Command: append-profile
    append_parser = subparsers.add_parser("append-profile", help="Append to user profile")
    append_parser.add_argument("--section", required=True, help="Section header")
    append_parser.add_argument("--content", required=True, help="Content to append")

    # Command: learning-get
    learn_get_parser = subparsers.add_parser("learn-get", help="Get learned preference")
    learn_get_parser.add_argument("category", help="Category (e.g., language)")

    # Command: learning-update
    learn_update_parser = subparsers.add_parser("learn-update", help="Update learned preference")
    learn_update_parser.add_argument("category", help="Category")
    learn_update_parser.add_argument("item", help="Item name")
    learn_update_parser.add_argument("reward", type=float, help="Reward value")

    args = parser.parse_args()

    if args.command == "analyze":
        result = analyze_query(args.query)
        print(json.dumps(result, indent=2))

    elif args.command == "extract-topics":
        topics = extract_topics(args.query)
        print("Detected Topics:")
        for t in topics:
            print(f"- {t}")

    elif args.command == "update":
        print(f"Updating preferences from query: '{args.query}'...")
        analysis = update_preferences_from_query(args.query)
        print("Update complete. Analysis result:")
        print(json.dumps(analysis, indent=2))

    elif args.command == "show-profile":
        profile = get_user_profile()
        print(profile)

    elif args.command == "append-profile":
        append_to_profile(args.section, args.content)
        print(f"Appended to section '{args.section}'.")

    elif args.command == "learn-get":
        profile = UserProfile()
        result = profile.get_preferred_option(args.category)
        if result:
            print(f"Preferred {args.category}: {result}")
        else:
            print(f"No preference found for category: {args.category}")

    elif args.command == "learn-update":
        profile = UserProfile()
        print(f"Updating {args.category}:{args.item} with reward {args.reward}...")
        profile.update_preference(args.category, args.item, args.reward)
        print("Done.")

    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
