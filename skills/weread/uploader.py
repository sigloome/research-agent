"""
WeRead (微信读书) Book Upload Skill

This skill helps upload local books to WeRead.
Note: WeRead requires WeChat login for upload functionality.
"""

import json
import os
import webbrowser
from pathlib import Path
from typing import Any, Dict, List, Optional

# Supported formats
SUPPORTED_FORMATS = ['.epub', '.pdf', '.txt', '.mobi']

# Project paths
# skills/weread/uploader.py -> parent.parent.parent = project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DOWNLOADS_DIR = PROJECT_ROOT / "downloads"
LOCAL_ARTICLES_DIR = PROJECT_ROOT / "data" / "local_articles"

# WeRead URLs
WEREAD_UPLOAD_URL = "https://weread.qq.com/web/upload"
WEREAD_API_BASE = "https://weread.qq.com"


def list_uploadable_books(
    directories: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    List all books that can be uploaded to WeRead.
    
    Args:
        directories: Optional list of directories to scan. 
                    Defaults to downloads/ and local_articles/
    
    Returns:
        List of book info dicts with name, path, format, size
    """
    if directories is None:
        directories = [str(DOWNLOADS_DIR), str(LOCAL_ARTICLES_DIR)]
    
    books = []
    
    for dir_path in directories:
        dir_path = Path(dir_path)
        if not dir_path.exists():
            continue
            
        for file_path in dir_path.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_FORMATS:
                size_bytes = file_path.stat().st_size
                books.append({
                    'name': file_path.name,
                    'path': str(file_path),
                    'format': file_path.suffix.lower().lstrip('.'),
                    'size_bytes': size_bytes,
                    'size_mb': size_bytes / (1024 * 1024)
                })
    
    return books


def open_upload_page() -> str:
    """
    Open the WeRead upload page in the default browser.
    
    Returns:
        Message indicating the action taken
    """
    webbrowser.open(WEREAD_UPLOAD_URL)
    return """
WeRead Upload Page Opened!

Please follow these steps:
1. Scan the QR code with WeChat on your phone
2. Confirm the login on your phone
3. Click "传书到手机" (Transfer book to phone)
4. Select your book file to upload

Note: You can upload EPUB, PDF, TXT, or MOBI files (max 50MB each).
"""


def get_weread_cookies() -> Optional[Dict[str, str]]:
    """
    Get WeRead cookies from environment or secrets file.
    
    Returns:
        Dictionary of cookies or None if not configured
    """
    # Try environment variable first
    cookies_str = os.environ.get('WEREAD_COOKIES')
    if cookies_str:
        try:
            return json.loads(cookies_str)
        except json.JSONDecodeError:
            pass
    
    # Try secrets file
    secrets_file = PROJECT_ROOT / "secrets" / "weread_cookies.json"
    if secrets_file.exists():
        try:
            with open(secrets_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    
    return None


def save_weread_cookies(cookies: Dict[str, str]) -> bool:
    """
    Save WeRead cookies to secrets file.
    
    Args:
        cookies: Dictionary of cookie name-value pairs
        
    Returns:
        True if saved successfully
    """
    secrets_dir = PROJECT_ROOT / "secrets"
    secrets_dir.mkdir(exist_ok=True)
    
    secrets_file = secrets_dir / "weread_cookies.json"
    try:
        with open(secrets_file, 'w') as f:
            json.dump(cookies, f, indent=2)
        return True
    except IOError:
        return False


def check_cookies_valid(cookies: Dict[str, str]) -> bool:
    """
    Check if WeRead cookies are valid by making a test API call.
    
    Args:
        cookies: Dictionary of cookie name-value pairs
        
    Returns:
        True if cookies are valid
    """
    try:
        import requests
    except ImportError:
        print("Warning: requests library not installed")
        return False
    
    # Required cookies
    required = ['wr_vid', 'wr_skey']
    if not all(k in cookies for k in required):
        return False
    
    # Test API endpoint
    test_url = f"{WEREAD_API_BASE}/web/shelf/sync"
    
    try:
        response = requests.get(
            test_url,
            cookies=cookies,
            headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            },
            timeout=10
        )
        # If we get a valid response, cookies are good
        return response.status_code == 200
    except Exception:
        return False


def upload_book(
    file_path: str,
    cookies: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Upload a book to WeRead.
    
    Note: This requires valid WeRead cookies. See SKILL.md for how to get cookies.
    
    Args:
        file_path: Path to the book file
        cookies: Optional cookies dict. If not provided, will try to load from config.
        
    Returns:
        Result dict with success status and message
    """
    try:
        import requests
    except ImportError:
        return {
            'success': False,
            'error': 'requests library not installed. Run: pip install requests'
        }
    
    file_path = Path(file_path)
    
    # Validate file
    if not file_path.exists():
        return {
            'success': False,
            'error': f'File not found: {file_path}'
        }
    
    if file_path.suffix.lower() not in SUPPORTED_FORMATS:
        return {
            'success': False,
            'error': f'Unsupported format: {file_path.suffix}. Supported: {SUPPORTED_FORMATS}'
        }
    
    # Check file size (50MB limit)
    size_mb = file_path.stat().st_size / (1024 * 1024)
    if size_mb > 50:
        return {
            'success': False,
            'error': f'File too large: {size_mb:.2f} MB (max 50 MB)'
        }
    
    # Get cookies
    if cookies is None:
        cookies = get_weread_cookies()
    
    if not cookies:
        return {
            'success': False,
            'error': 'No WeRead cookies configured. Please login first and save cookies.',
            'instructions': '''
To save cookies:
1. Open https://weread.qq.com in your browser
2. Login with WeChat QR code
3. Open Developer Tools (F12) > Application > Cookies
4. Copy cookies to secrets/weread_cookies.json:
   {"wr_vid": "xxx", "wr_skey": "xxx", "wr_rt": "xxx", ...}
'''
        }
    
    # Validate cookies
    if not check_cookies_valid(cookies):
        return {
            'success': False,
            'error': 'WeRead cookies are invalid or expired. Please login again.'
        }
    
    # Upload endpoint (discovered from web interface)
    upload_url = f"{WEREAD_API_BASE}/web/book/upload"
    
    try:
        with open(file_path, 'rb') as f:
            files = {
                'file': (file_path.name, f, 'application/octet-stream')
            }
            
            response = requests.post(
                upload_url,
                files=files,
                cookies=cookies,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                    'Origin': 'https://weread.qq.com',
                    'Referer': 'https://weread.qq.com/web/upload'
                },
                timeout=120  # Large files may take time
            )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('succ') or result.get('errCode') == 0:
                return {
                    'success': True,
                    'message': f'Successfully uploaded: {file_path.name}',
                    'book_id': result.get('bookId'),
                    'response': result
                }
            else:
                return {
                    'success': False,
                    'error': result.get('errMsg', 'Upload failed'),
                    'response': result
                }
        else:
            return {
                'success': False,
                'error': f'HTTP error: {response.status_code}',
                'response': response.text
            }
            
    except requests.exceptions.Timeout:
        return {
            'success': False,
            'error': 'Upload timed out. The file may be too large.'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Upload failed: {str(e)}'
        }


def upload_all_books(
    directories: Optional[List[str]] = None,
    cookies: Optional[Dict[str, str]] = None
) -> List[Dict[str, Any]]:
    """
    Upload all books from specified directories.
    
    Args:
        directories: Directories to scan for books
        cookies: WeRead cookies
        
    Returns:
        List of results for each book
    """
    books = list_uploadable_books(directories)
    results = []
    
    for book in books:
        result = upload_book(book['path'], cookies)
        result['file'] = book['name']
        results.append(result)
    
    return results


# Browser automation approach (requires selenium)
def upload_via_browser(file_path: str) -> Dict[str, Any]:
    """
    Upload a book using browser automation.
    This approach works without pre-saved cookies but requires manual QR code scan.
    
    Args:
        file_path: Path to the book file
        
    Returns:
        Result dict
    """
    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.support.ui import WebDriverWait
    except ImportError:
        return {
            'success': False,
            'error': 'Selenium not installed. Run: pip install selenium'
        }
    
    file_path = Path(file_path).resolve()
    
    if not file_path.exists():
        return {
            'success': False,
            'error': f'File not found: {file_path}'
        }
    
    try:
        # Initialize browser
        options = webdriver.ChromeOptions()
        options.add_argument('--start-maximized')
        driver = webdriver.Chrome(options=options)
        
        # Navigate to upload page
        driver.get(WEREAD_UPLOAD_URL)
        
        print("\n" + "="*50)
        print("Please scan the QR code with WeChat to login")
        print("Waiting for login... (timeout: 120 seconds)")
        print("="*50 + "\n")
        
        # Wait for login (look for upload button to become active)
        wait = WebDriverWait(driver, 120)
        
        # After login, find the file input and upload
        # Note: WeRead may use hidden file input, this is a general approach
        try:
            file_input = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="file"]'))
            )
            file_input.send_keys(str(file_path))
            
            # Wait for upload to complete
            import time
            time.sleep(5)  # Give time for upload
            
            return {
                'success': True,
                'message': f'Upload initiated for: {file_path.name}',
                'note': 'Check WeRead app to confirm the book was received'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Could not find upload input: {str(e)}',
                'note': 'WeRead interface may have changed'
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
    finally:
        # Don't close browser immediately so user can see result
        print("\nBrowser will close in 30 seconds...")
        import time
        time.sleep(30)
        try:
            driver.quit()
        except Exception:
            pass
