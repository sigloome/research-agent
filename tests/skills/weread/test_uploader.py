"""
Tests for WeRead upload skill.
"""
from unittest.mock import MagicMock, patch


class TestWeReadUploader:
    """Test WeRead upload functionality."""
    
    def test_list_uploadable_books(self, project_root, tmp_path):
        """Test listing uploadable books."""
        import sys
        sys.path.insert(0, str(project_root))
        
        from skills.weread.uploader import list_uploadable_books
        
        # Create test files
        (tmp_path / "test.pdf").write_text("dummy pdf")
        (tmp_path / "test.epub").write_text("dummy epub")
        (tmp_path / "test.txt").write_text("dummy txt")
        (tmp_path / "test.doc").write_text("dummy doc")  # Unsupported
        
        books = list_uploadable_books(directories=[str(tmp_path)])
        
        assert isinstance(books, list)
        assert len(books) == 3  # pdf, epub, txt (not doc)
        
        formats = [b['format'] for b in books]
        assert 'pdf' in formats
        assert 'epub' in formats
        assert 'txt' in formats
    
    def test_list_uploadable_books_empty(self, project_root, tmp_path):
        """Test listing with no uploadable books."""
        import sys
        sys.path.insert(0, str(project_root))
        
        from skills.weread.uploader import list_uploadable_books
        
        books = list_uploadable_books(directories=[str(tmp_path)])
        
        assert isinstance(books, list)
        assert len(books) == 0
    
    def test_upload_book_no_cookies(self, project_root, tmp_path):
        """Test upload fails without cookies."""
        import sys
        sys.path.insert(0, str(project_root))
        
        from skills.weread.uploader import upload_book
        
        # Create test file
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"dummy pdf content")
        
        result = upload_book(str(test_file))
        
        assert isinstance(result, dict)
        assert result['success'] is False
        assert 'cookies' in result['error'].lower() or 'instructions' in result
    
    def test_upload_book_file_not_found(self, project_root):
        """Test upload with non-existent file."""
        import sys
        sys.path.insert(0, str(project_root))
        
        from skills.weread.uploader import upload_book
        
        result = upload_book("/nonexistent/path/book.pdf")
        
        assert isinstance(result, dict)
        assert result['success'] is False
        assert 'not found' in result['error'].lower()
    
    def test_upload_book_unsupported_format(self, project_root, tmp_path):
        """Test upload with unsupported format."""
        import sys
        sys.path.insert(0, str(project_root))
        
        from skills.weread.uploader import upload_book
        
        test_file = tmp_path / "test.doc"
        test_file.write_bytes(b"dummy content")
        
        result = upload_book(str(test_file))
        
        assert isinstance(result, dict)
        assert result['success'] is False
        assert 'unsupported' in result['error'].lower()
    
    def test_upload_book_too_large(self, project_root, tmp_path):
        """Test upload fails for files over 50MB."""
        import sys
        sys.path.insert(0, str(project_root))
        
        from skills.weread.uploader import upload_book
        
        # Create a file that reports as >50MB via mock
        test_file = tmp_path / "large.pdf"
        test_file.write_bytes(b"x")  # Small file, but we'll mock the size check
        
        with patch('pathlib.Path.stat') as mock_stat:
            mock_stat.return_value = MagicMock(st_size=60 * 1024 * 1024)  # 60MB
            
            result = upload_book(str(test_file))
        
        assert isinstance(result, dict)
        assert result['success'] is False
        assert 'large' in result['error'].lower() or '50' in result['error']
    
    def test_supported_formats_constant(self, project_root):
        """Test SUPPORTED_FORMATS constant."""
        import sys
        sys.path.insert(0, str(project_root))
        
        from skills.weread.uploader import SUPPORTED_FORMATS
        
        assert isinstance(SUPPORTED_FORMATS, list)
        assert '.pdf' in SUPPORTED_FORMATS
        assert '.epub' in SUPPORTED_FORMATS
        assert '.txt' in SUPPORTED_FORMATS
        assert '.mobi' in SUPPORTED_FORMATS
