
import argparse
import sys
import logging
from skills.weread.uploader import (
    list_uploadable_books,
    upload_book,
    upload_all_books,
    open_upload_page,
    upload_via_browser
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

def main():
    parser = argparse.ArgumentParser(description="WeRead Upload CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Command: list
    list_parser = subparsers.add_parser("list", help="List uploadable books")
    list_parser.add_argument("--dir", action="append", help="Directory to scan (can be used multiple times)")

    # Command: upload
    upload_parser = subparsers.add_parser("upload", help="Upload a book")
    upload_parser.add_argument("file", help="Path to book file")

    # Command: upload-all
    upload_all_parser = subparsers.add_parser("upload-all", help="Upload all books from directories")
    upload_all_parser.add_argument("--dir", action="append", help="Directory to scan")

    # Command: open
    open_parser = subparsers.add_parser("open", help="Open upload page in browser")

    # Command: browser-upload (selenium)
    browser_parser = subparsers.add_parser("browser-upload", help="Upload using Selenium automation")
    browser_parser.add_argument("file", help="Path to book file")

    args = parser.parse_args()

    if args.command == "list":
        books = list_uploadable_books(directories=args.dir)
        print(f"Found {len(books)} uploadable books:")
        for book in books:
            print(f"  - {book['name']} ({book['format']}, {book['size_mb']:.2f} MB)")
            print(f"    Path: {book['path']}")

    elif args.command == "upload":
        print(f"Uploading {args.file}...")
        result = upload_book(args.file)
        if result['success']:
            print(f"Success! {result['message']}")
        else:
            print(f"Error: {result['error']}")
            if 'instructions' in result:
                print(result['instructions'])

    elif args.command == "upload-all":
        print("Uploading all books...")
        results = upload_all_books(directories=args.dir)
        for res in results:
            status = "Success" if res['success'] else "Failed"
            msg = res.get('message', res.get('error'))
            print(f"[{status}] {res.get('file', 'Unknown')}: {msg}")

    elif args.command == "open":
        msg = open_upload_page()
        print(msg)

    elif args.command == "browser-upload":
        print(f"Starting browser automation for {args.file}...")
        result = upload_via_browser(args.file)
        print(result)

    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
