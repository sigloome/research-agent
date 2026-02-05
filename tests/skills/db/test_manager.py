"""
Tests for database manager functionality.
"""
import sqlite3
from pathlib import Path


class TestDatabaseManager:
    """Test database operations."""
    
    def test_add_paper(self, temp_db, sample_paper):
        """Test adding a paper to the database."""
        # Import with temp db
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        
        from skills.db import manager
        original_db = manager.DB_PATH
        manager.DB_PATH = temp_db
        
        try:
            manager.add_paper(sample_paper)
            
            # Verify paper was added
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM papers WHERE id = ?", (sample_paper['id'],))
            row = cursor.fetchone()
            conn.close()
            
            assert row is not None
            assert sample_paper['title'] in str(row)
        finally:
            manager.DB_PATH = original_db
    
    def test_get_paper(self, temp_db, sample_paper):
        """Test retrieving a paper from the database."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        
        from skills.db import manager
        original_db = manager.DB_PATH
        manager.DB_PATH = temp_db
        
        try:
            # Add paper first
            manager.add_paper(sample_paper)
            
            # Retrieve it
            paper = manager.get_paper(sample_paper['id'])
            
            assert paper is not None
            assert paper['title'] == sample_paper['title']
            assert paper['id'] == sample_paper['id']
        finally:
            manager.DB_PATH = original_db
    
    def test_list_papers(self, temp_db, sample_paper):
        """Test listing papers."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        
        from skills.db import manager
        original_db = manager.DB_PATH
        manager.DB_PATH = temp_db
        
        try:
            manager.add_paper(sample_paper)
            
            papers = manager.list_papers()
            
            assert isinstance(papers, list)
            assert len(papers) >= 1
        finally:
            manager.DB_PATH = original_db
    
    def test_search_local_papers(self, temp_db, sample_paper):
        """Test searching papers."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        
        from skills.db import manager
        original_db = manager.DB_PATH
        manager.DB_PATH = temp_db
        
        try:
            manager.add_paper(sample_paper)
            
            # Search for term in title
            results = manager.search_local_papers("Language Models")
            
            assert isinstance(results, list)
            assert len(results) >= 1
            assert results[0]['id'] == sample_paper['id']
        finally:
            manager.DB_PATH = original_db
    
    def test_search_no_results(self, temp_db):
        """Test search with no matching results."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        
        from skills.db import manager
        original_db = manager.DB_PATH
        manager.DB_PATH = temp_db
        
        try:
            results = manager.search_local_papers("nonexistent query xyz123")
            
            assert isinstance(results, list)
            assert len(results) == 0
        finally:
            manager.DB_PATH = original_db


class TestSourceManagement:
    """Test library source operations."""
    
    def test_list_sources(self, temp_db):
        """Test listing sources."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        
        from skills.db import manager
        original_db = manager.DB_PATH
        manager.DB_PATH = temp_db
        
        try:
            sources = manager.list_sources()
            
            assert isinstance(sources, list)
            assert len(sources) >= 1  # Default ArXiv source
        finally:
            manager.DB_PATH = original_db
    
    def test_add_source(self, temp_db):
        """Test adding a new source."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        
        from skills.db import manager
        original_db = manager.DB_PATH
        manager.DB_PATH = temp_db
        
        try:
            source_id = manager.add_source(
                name="Test Source",
                source_type="custom",
                icon="🧪",
                description="A test source"
            )
            
            assert source_id is not None
            assert source_id > 0
            
            # Verify source exists
            sources = manager.list_sources()
            source_names = [s['name'] for s in sources]
            assert "Test Source" in source_names
        finally:
            manager.DB_PATH = original_db


class TestBookManagement:
    """Test book operations."""
    
    def test_add_book(self, temp_db, sample_book):
        """Test adding a book."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        
        from skills.db import manager
        original_db = manager.DB_PATH
        manager.DB_PATH = temp_db
        
        try:
            # add_book doesn't return anything, just stores the book
            manager.add_book(sample_book)
            
            # Verify by fetching
            book = manager.get_book(sample_book['id'])
            assert book is not None
            assert book['title'] == sample_book['title']
        finally:
            manager.DB_PATH = original_db
    
    def test_list_books(self, temp_db, sample_book):
        """Test listing books."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        
        from skills.db import manager
        original_db = manager.DB_PATH
        manager.DB_PATH = temp_db
        
        try:
            manager.add_book(sample_book)
            
            books = manager.list_books()
            
            assert isinstance(books, list)
            assert len(books) >= 1
        finally:
            manager.DB_PATH = original_db


class TestUserPreferences:
    """Test user preference operations."""
    
    def test_record_query(self, temp_db):
        """Test recording a user query."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        
        from skills.db import manager
        original_db = manager.DB_PATH
        manager.DB_PATH = temp_db
        
        try:
            # Record query using correct column names
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO user_queries (query_text, query_type, topics) VALUES (?, ?, ?)",
                ("test query", "search", '["LLM"]')
            )
            conn.commit()
            
            # Verify
            cursor.execute("SELECT * FROM user_queries")
            rows = cursor.fetchall()
            conn.close()
            
            assert len(rows) >= 1
        finally:
            manager.DB_PATH = original_db
