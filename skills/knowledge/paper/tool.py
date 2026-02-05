"""
Agent Adapter for Paper Skill.
Wraps core logic for use by the AI Agent.
"""
from typing import Any, Dict, List, Optional
from skills.knowledge.paper import core

def fetch_papers(
    query: str, sort_by: str = "recent", max_results: int = 5, source_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Fetches papers from ArXiv or other sources.
    
    Args:
        query: Search query (topic or keywords)
        sort_by: "recent" or "relevance"
        max_results: Number of papers to return (default 5)
        source_id: Optional specific source ID
        
    Returns:
        List of paper dictionaries with title, abstract, etc.
    """
    return core.fetch_papers(query, sort_by, max_results, source_id)

def search_local_papers(query: str) -> List[Dict[str, Any]]:
    """
    Search for papers already stored in the local database.
    Useful for checking what is already known before fetching external papers.
    """
    return core.search_local_papers(query)

def add_paper_by_url(url: str, source_id: Optional[int] = None) -> str:
    """
    Add a specific paper by its ArXiv URL.
    """
    return core.add_paper_by_url(url, source_id)

def analyze_paper(paper_id: str) -> Dict[str, Any]:
    """
    Downloads full text and generates a detailed AI summary for a paper.
    Use this when you need deep understanding of a specific paper.
    """
    return core.analyze_paper(paper_id)
