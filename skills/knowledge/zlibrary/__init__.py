"""Z-Library skill - search and download books."""
from .client import (
    DOWNLOADS_DIR as DOWNLOADS_DIR,
    download_book as download_book,
    get_book_info as get_book_info,
    list_downloaded_books as list_downloaded_books,
    search_and_download as search_and_download,
    search_books as search_books,
)
