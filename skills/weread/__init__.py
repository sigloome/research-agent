"""
WeRead (微信读书) Upload Skill

Upload local books to WeRead for reading on mobile devices.
"""

from .uploader import (
    SUPPORTED_FORMATS,
    WEREAD_UPLOAD_URL,
    check_cookies_valid,
    get_weread_cookies,
    list_uploadable_books,
    open_upload_page,
    save_weread_cookies,
    upload_all_books,
    upload_book,
    upload_via_browser,
)

__all__ = [
    'list_uploadable_books',
    'open_upload_page',
    'upload_book',
    'upload_all_books',
    'upload_via_browser',
    'get_weread_cookies',
    'save_weread_cookies',
    'check_cookies_valid',
    'SUPPORTED_FORMATS',
    'WEREAD_UPLOAD_URL',
]
