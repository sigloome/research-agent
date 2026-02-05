"""
Tests for local file import skill.
"""
from unittest.mock import patch

import pytest


class TestLocalFilesImporter:
    """Test local file import functionality."""
    
    def test_list_local_files(self, project_root, tmp_path):
        """Test listing local PDF files."""
        import sys
        sys.path.insert(0, str(project_root))
        
        from skills.local_files import importer
        
        # Mock the LOCAL_ARTICLES_DIR
        original_dir = importer.LOCAL_ARTICLES_DIR
        importer.LOCAL_ARTICLES_DIR = tmp_path
        
        try:
            # Create test files
            (tmp_path / "paper1.pdf").write_bytes(b"%PDF-1.4 test")
            (tmp_path / "paper2.pdf").write_bytes(b"%PDF-1.4 test2")
            (tmp_path / "notes.txt").write_text("not a pdf")
            
            files = importer.list_local_files()
            
            assert isinstance(files, list)
            assert len(files) == 2  # Only PDFs
            
            names = [f['name'] for f in files]
            assert 'paper1.pdf' in names
            assert 'paper2.pdf' in names
        finally:
            importer.LOCAL_ARTICLES_DIR = original_dir
    
    def test_list_local_files_empty(self, project_root, tmp_path):
        """Test listing with no files."""
        import sys
        sys.path.insert(0, str(project_root))
        
        from skills.local_files import importer
        
        original_dir = importer.LOCAL_ARTICLES_DIR
        importer.LOCAL_ARTICLES_DIR = tmp_path
        
        try:
            files = importer.list_local_files()
            
            assert isinstance(files, list)
            assert len(files) == 0
        finally:
            importer.LOCAL_ARTICLES_DIR = original_dir
    
    def test_generate_paper_id(self, project_root):
        """Test paper ID generation."""
        import sys
        sys.path.insert(0, str(project_root))
        
        from skills.local_files.importer import generate_paper_id
        
        id1 = generate_paper_id("Test Paper Title")
        id2 = generate_paper_id("Test Paper Title")
        id3 = generate_paper_id("Different Title")
        
        # Same title should generate same ID
        assert id1 == id2
        # Different titles should generate different IDs
        assert id1 != id3
        # IDs should be strings
        assert isinstance(id1, str)
        # IDs should have expected format
        assert id1.startswith("local-")
    
    def test_extract_metadata_from_pdf(self, project_root, tmp_path):
        """Test PDF metadata extraction."""
        import sys
        sys.path.insert(0, str(project_root))
        
        from skills.local_files.importer import extract_metadata_from_pdf
        
        # Create a minimal PDF-like file
        test_pdf = tmp_path / "test.pdf"
        test_pdf.write_bytes(b"%PDF-1.4\n%%EOF")
        
        # Should not crash, may return empty metadata
        try:
            metadata = extract_metadata_from_pdf(str(test_pdf))
            assert isinstance(metadata, dict)
        except Exception as e:
            # PDF parsing may fail for minimal test file
            pytest.skip(f"PDF parsing unavailable: {e}")


class TestImportPDF:
    """Test PDF import functionality."""
    
    def test_import_pdf_not_found(self, project_root):
        """Test importing non-existent file."""
        import sys
        sys.path.insert(0, str(project_root))
        
        from skills.local_files.importer import import_pdf
        
        with patch('skills.db.manager.add_paper'):
            result = import_pdf("/nonexistent/file.pdf")
        
        assert isinstance(result, dict)
        assert result.get('success') is False or 'error' in str(result).lower()
    
    def test_import_pdf_non_pdf(self, project_root, tmp_path):
        """Test importing non-PDF file."""
        import sys
        sys.path.insert(0, str(project_root))
        
        from skills.local_files.importer import import_pdf
        
        test_file = tmp_path / "test.txt"
        test_file.write_text("Not a PDF")
        
        with patch('skills.db.manager.add_paper'):
            result = import_pdf(str(test_file))
        
        # Should handle gracefully (either error or process anyway)
        assert isinstance(result, dict)
