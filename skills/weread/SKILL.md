---
name: weread
description: Upload local books (EPUB, PDF, TXT) to WeRead (微信读书) for cloud reading. Includes CLI for listing and uploading books.
license: Apache-2.0
metadata:
  type: utility
  python_package: skills.weread
---

# WeRead Upload Skill

Upload local books (EPUB, PDF) to WeRead (微信读书).

## Important: Authentication Required

WeRead requires WeChat login to upload books. The upload process involves:
1. Scanning a QR code with WeChat app on your phone
2. Confirming login on your phone
3. Then uploading files through the web interface

## Usage

### List Books for Upload

```python
from skills.weread import list_uploadable_books

# List all books that can be uploaded
books = list_uploadable_books()
for book in books:
    print(f"  - {book['name']} ({book['format']}, {book['size_mb']:.2f} MB)")
```

### Open WeRead Upload Page

```python
from skills.weread import open_upload_page

# Opens WeRead upload page in browser
open_upload_page()
```

### Upload with Saved Cookies (Advanced)

If you have WeRead cookies saved, you can upload programmatically:

```python
from skills.weread import upload_book

# Upload a book (requires authentication cookies in .env or secrets)
result = upload_book("/path/to/book.epub")
```

### CLI Usage

```bash
# List uploadable books
python -m skills.weread list

# Upload a specific book
python -m skills.weread upload path/to/book.pdf

# Open upload page
python -m skills.weread open

# Upload using browser automation (Selenium)
python -m skills.weread browser-upload path/to/book.pdf
```

## Supported Formats

- EPUB (.epub)
- PDF (.pdf)
- TXT (.txt)
- MOBI (.mobi) - may have limited support

## File Size Limits

WeRead has upload limits:
- Maximum file size: 50MB per file
- Daily upload limit: varies by account type

## Storing Credentials

WeRead cookies can be stored in `.env`:

```
WEREAD_COOKIES={"wr_vid": "xxx", "wr_skey": "xxx", ...}
```

Note: Cookies expire and need to be refreshed periodically.

## Getting Cookies

1. Open https://weread.qq.com in your browser
2. Login with WeChat QR code
3. Open Developer Tools (F12) > Application > Cookies
4. Copy the cookie values (especially `wr_vid`, `wr_skey`, `wr_rt`, `wr_localvid`)
