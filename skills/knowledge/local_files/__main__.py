
import argparse
import sys
import json
import logging
from skills.knowledge.local_files.importer import import_pdf, list_local_files, import_all_from_directory

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

def main():
    parser = argparse.ArgumentParser(description="Local Files CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Command: import
    import_parser = subparsers.add_parser("import", help="Import a PDF file")
    import_parser.add_argument("path", help="Path to PDF file")
    import_parser.add_argument("--title", help="Optional title override")

    # Command: list
    list_parser = subparsers.add_parser("list", help="List PDF files in local articles directory")
    list_parser.add_argument("--dir", help="Optional directory override")

    # Command: import-dir
    import_dir_parser = subparsers.add_parser("import-dir", help="Import all PDFs from a directory")
    import_dir_parser.add_argument("path", help="Directory path to import from")

    args = parser.parse_args()

    if args.command == "import":
        print(f"Importing {args.path}...")
        result = import_pdf(args.path, title=args.title)
        if "error" in result:
             print(f"Error: {result['error']}")
        else:
             print(f"Imported: {result['title']} (ID: {result['id']})")

    elif args.command == "list":
        files = list_local_files(directory=args.dir)
        print(f"Found {len(files)} files:")
        for f in files:
            print(f"  - {f['name']} ({f['size']} bytes) - {f['path']}")

    elif args.command == "import-dir":
        print(f"Importing all PDFs from {args.path}...")
        results = import_all_from_directory(args.path)
        print(f"Processed {len(results)} files.")
        for res in results:
             if "error" in res:
                 print(f"  - Error: {res['error']}")
             else:
                 print(f"  - Imported: {res['title']}")

    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
