"""
Tests for paper fetching functionality.
"""
from unittest.mock import patch


class TestFetchPapers:
    """Test paper fetching from ArXiv."""
    
    def test_fetch_papers_returns_list(self, project_root):
        """Test that fetch_papers returns a list."""
        import sys
        sys.path.insert(0, str(project_root))
        
        from skills.knowledge.paper.core import fetch_papers
        
        # Mock the fetcher to avoid network calls
        with patch('skills.paper_search.fetcher.fetch_and_process') as mock_fetch:
            mock_fetch.return_value = [
                {
                    'id': '2401.12345',
                    'title': 'Test Paper',
                    'abstract': 'About LLM transformers',
                    'authors': ['Author A'],
                    'published_date': '2024-01-01',
                    'url': 'https://arxiv.org/abs/2401.12345',
                    'pdf_url': 'https://arxiv.org/pdf/2401.12345.pdf',
                    'html_url': 'https://arxiv.org/html/2401.12345',
                    'citation_count': 0
                }
            ]
            
            with patch('skills.db.manager.get_paper') as mock_get:
                mock_get.return_value = None
                with patch('skills.db.manager.add_paper') as mock_add:
                    with patch('skills.db.manager.get_source_by_name') as mock_source:
                        mock_source.return_value = {'id': 1}
                        
                        results = fetch_papers("LLM", max_results=1)
                        
                        assert isinstance(results, list)
                        assert len(results) >= 0
    
    def test_extract_tags_from_abstract(self, project_root):
        """Test tag extraction from abstract."""
        import sys
        sys.path.insert(0, str(project_root))
        
        from skills.knowledge.paper.core import extract_tags_from_abstract
        
        abstract = "This paper presents a novel LLM approach using transformer architecture with attention mechanisms."
        tags = extract_tags_from_abstract(abstract)
        
        assert isinstance(tags, list)
        assert 'LLM' in tags
        assert 'transformer' in tags
        assert 'attention' in tags
    
    def test_extract_tags_empty_abstract(self, project_root):
        """Test tag extraction with empty abstract."""
        import sys
        sys.path.insert(0, str(project_root))
        
        from skills.knowledge.paper.core import extract_tags_from_abstract
        
        tags = extract_tags_from_abstract("")
        
        assert isinstance(tags, list)
        assert 'AI' in tags  # Default tag


class TestSearchLocalPapers:
    """Test local paper search functionality."""
    
    def test_search_returns_list(self, project_root):
        """Test that search_local_papers returns a list."""
        import sys
        sys.path.insert(0, str(project_root))
        
        from skills.knowledge.paper.core import search_local_papers
        
        with patch('skills.db.manager.search_local_papers') as mock_search:
            mock_search.return_value = []
            
            results = search_local_papers("test query")
            
            assert isinstance(results, list)
            mock_search.assert_called_once_with("test query")
