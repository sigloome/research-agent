"""
Tests for paper API endpoints.
"""
from unittest.mock import patch

import pytest


class TestPapersAPI:
    """Test paper-related API endpoints."""
    
    @pytest.fixture
    def client(self, project_root):
        """Create test client."""
        import sys
        sys.path.insert(0, str(project_root))
        
        from fastapi.testclient import TestClient

        from backend.app import app
        
        return TestClient(app)
    
    def test_list_papers(self, client):
        """Test GET /api/papers."""
        with patch('skills.db.manager.list_papers') as mock_list:
            mock_list.return_value = [
                {
                    'id': '2401.12345',
                    'title': 'Test Paper',
                    'authors': '["Author A"]',
                    'abstract': 'Test abstract',
                    'published_date': '2024-01-01',
                    'source_id': 1
                }
            ]
            
            response = client.get("/api/papers")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_list_papers_with_source_filter(self, client):
        """Test GET /api/papers with source_id filter."""
        with patch('skills.db.manager.list_papers') as mock_list:
            mock_list.return_value = []
            
            response = client.get("/api/papers?source_id=1")
        
        assert response.status_code == 200
        mock_list.assert_called()
    
    def test_get_paper(self, client):
        """Test GET /api/papers/{id}."""
        with patch('skills.db.manager.get_paper') as mock_get:
            mock_get.return_value = {
                'id': '2401.12345',
                'title': 'Test Paper',
                'authors': '["Author A"]'
            }
            
            response = client.get("/api/papers/2401.12345")
        
        assert response.status_code == 200
        data = response.json()
        assert data['id'] == '2401.12345'
    
    def test_get_paper_not_found(self, client):
        """Test GET /api/papers/{id} for non-existent paper."""
        with patch('skills.db.manager.get_paper') as mock_get:
            mock_get.return_value = None
            
            response = client.get("/api/papers/nonexistent")
        
        assert response.status_code == 404


class TestSourcesAPI:
    """Test source-related API endpoints."""
    
    @pytest.fixture
    def client(self, project_root):
        """Create test client."""
        import sys
        sys.path.insert(0, str(project_root))
        
        from fastapi.testclient import TestClient

        from backend.app import app
        
        return TestClient(app)
    
    def test_list_sources(self, client):
        """Test GET /api/sources."""
        with patch('skills.db.manager.list_sources') as mock_list:
            mock_list.return_value = [
                {'id': 1, 'name': 'ArXiv', 'source_type': 'arxiv'}
            ]
            
            response = client.get("/api/sources")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_create_source(self, client):
        """Test POST /api/sources."""
        with patch('skills.db.manager.add_source') as mock_add:
            mock_add.return_value = 5
            
            response = client.post("/api/sources", json={
                'name': 'New Source',
                'source_type': 'custom',
                'icon': '🆕'
            })
        
        assert response.status_code == 200
        data = response.json()
        assert data['id'] == 5


class TestBooksAPI:
    """Test book-related API endpoints."""
    
    @pytest.fixture
    def client(self, project_root):
        """Create test client."""
        import sys
        sys.path.insert(0, str(project_root))
        
        from fastapi.testclient import TestClient

        from backend.app import app
        
        return TestClient(app)
    
    def test_list_books(self, client):
        """Test GET /api/books."""
        with patch('skills.db.manager.list_books') as mock_list:
            mock_list.return_value = []
            
            response = client.get("/api/books")
        
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_search_books(self, client):
        """Test GET /api/books/search/{query}."""
        with patch('skills.db.manager.search_books') as mock_search:
            mock_search.return_value = []
            
            response = client.get("/api/books/search/machine%20learning")
        
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestChatAPI:
    """Test chat API endpoint."""
    
    @pytest.fixture
    def client(self, project_root):
        """Create test client."""
        import sys
        sys.path.insert(0, str(project_root))
        
        from fastapi.testclient import TestClient

        from backend.app import app
        
        return TestClient(app)
    
    def test_chat_endpoint_exists(self, client):
        """Test POST /api/chat endpoint exists."""
        # We just verify the endpoint exists, actual chat requires agent setup
        response = client.post("/api/chat", json={"message": "test"})
        
        # Should not be 404 (method not allowed or validation error is OK)
        assert response.status_code != 404


class TestPreferencesAPI:
    """Test preferences API endpoint."""
    
    @pytest.fixture
    def client(self, project_root):
        """Create test client."""
        import sys
        sys.path.insert(0, str(project_root))
        
        from fastapi.testclient import TestClient

        from backend.app import app
        
        return TestClient(app)
    
    def test_get_preferences(self, client):
        """Test GET /api/preferences."""
        with patch('skills.db.manager.get_user_preferences') as mock_prefs:
            mock_prefs.return_value = []
            with patch('skills.db.manager.get_recent_queries') as mock_queries:
                mock_queries.return_value = []
                with patch('skills.db.manager.get_preference_summary') as mock_summary:
                    mock_summary.return_value = ""
                    
                    response = client.get("/api/preferences")
        
        assert response.status_code == 200
        data = response.json()
        assert 'preferences' in data or 'suggestions' in data
