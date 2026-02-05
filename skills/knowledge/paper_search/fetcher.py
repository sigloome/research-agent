import re
import time
from typing import Any, Dict, List, Optional

import feedparser
import requests

# Semantic Scholar API base
S2_API_URL = "https://api.semanticscholar.org/graph/v1/paper"

def get_arxiv_papers(query: str = "cat:cs.AI", max_results: int = 10, sort_by: str = "submittedDate") -> List[Dict[str, Any]]:
    """
    Fetches papers from ArXiv API.
    query: ArXiv search query (default: Computer Science AI)
    sort_by: submittedDate, relevance, lastUpdatedDate
    """
    base_url = "http://export.arxiv.org/api/query"
    params = {
        "search_query": query,
        "start": 0,
        "max_results": max_results,
        "sortBy": sort_by,
        "sortOrder": "descending"
    }
    
    try:
        response = requests.get(base_url, params=params, timeout=10)
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to ArXiv: {e}")
        return []
    if response.status_code != 200:
        print(f"Error fetching from ArXiv: {response.status_code}")
        return []
        
    feed = feedparser.parse(response.content)
    papers = []
    
    for entry in feed.entries:
        # Extract ArXiv ID
        # id looks like http://arxiv.org/abs/2301.12345v1
        try:
            arxiv_id = entry.id.split('/abs/')[-1].split('v')[0]
        except Exception:
            arxiv_id = entry.id
            
        # Check if HTML version might exist (arxiv.org/html/ID)
        html_url = f"https://arxiv.org/html/{arxiv_id}"
        
        paper = {
            "id": arxiv_id,
            "title": entry.title.replace('\n', ' '),
            "authors": [a.name for a in entry.authors],
            "published_date": entry.published,
            "url": entry.link,
            "abstract": entry.summary.replace('\n', ' '),
            "content_source": "pdf", # default
            "html_url": html_url,
        "pdf_url": next((link.href for link in entry.links if link.type == 'application/pdf'), None)
        }
        papers.append(paper)
        
    return papers

def enrich_with_s2(papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Enrich papers with Semantic Scholar data (citations).
    """
    enriched = []
    for paper in papers:
        arxiv_id = paper['id']
        try:
            # S2 usually accepts ARXIV:ID format
            s2_id = f"ARXIV:{arxiv_id}"
            url = f"{S2_API_URL}/{s2_id}"
            params = {"fields": "citationCount,influentialCitationCount,title"}
            
            # Rate limiting handling (simple sleep)
            time.sleep(0.1) 
            
            resp = requests.get(url, params=params, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                paper['citation_count'] = data.get('citationCount', 0)
            else:
                paper['citation_count'] = 0
                
        except Exception as e:
            print(f"Error fetching S2 for {arxiv_id}: {e}")
            paper['citation_count'] = 0
            
        enriched.append(paper)
    return enriched

def fetch_and_process(query="cat:cs.AI", sort_by="submittedDate", max_results: int = 5) -> List[Dict[str, Any]]:
    # Limit max results for faster response
    max_results = min(max_results, 10)
    
    # 1. Fetch from ArXiv
    print(f"Fetching from ArXiv: {query} (max {max_results})...")
    raw_papers = get_arxiv_papers(query, max_results, sort_by)
    
    # 2. Enrich with S2 (skip for faster response)
    # enriched_papers = enrich_with_s2(raw_papers)
    # Just return without S2 enrichment for speed
    for p in raw_papers:
        p['citation_count'] = 0
    
    return raw_papers

def get_arxiv_paper_by_id(arxiv_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetches a single paper by ArXiv ID.
    """
    base_url = "http://export.arxiv.org/api/query"
    params = {
        "id_list": arxiv_id
    }
    
    try:
        response = requests.get(base_url, params=params, timeout=10)
    except requests.exceptions.RequestException:
        return None
    if response.status_code != 200:
        return None
        
    feed = feedparser.parse(response.content)
    if not feed.entries:
        return None
        
    entry = feed.entries[0]
    # ID cleaning
    try:
        clean_id = entry.id.split('/abs/')[-1].split('v')[0]
    except Exception:
        clean_id = entry.id
    
    paper = {
        "id": clean_id,
        "title": entry.title.replace('\n', ' '),
        "authors": [a.name for a in entry.authors],
        "published_date": entry.published,
        "url": entry.link,
        "abstract": entry.summary.replace('\n', ' '),
        "content_source": "pdf",
        "html_url": f"https://arxiv.org/html/{clean_id}",
        "pdf_url": next((l.href for l in entry.links if l.type == 'application/pdf'), None)
    }
    return paper

def fetch_from_url(url: str) -> Optional[Dict[str, Any]]:
    """
    Parses ArXiv URL and fetches paper data.
    """
    match = re.search(r'arxiv\.org/(?:abs|pdf|html)/(\d+\.\d+)', url)
    if not match:
        print(f"Could not parse ArXiv ID from {url}")
        return None
        
    arxiv_id = match.group(1)
    print(f"Detected ArXiv ID: {arxiv_id}")
    
    paper = get_arxiv_paper_by_id(arxiv_id)
    if paper:
        # Enrich
        enriched = enrich_with_s2([paper])
        return enriched[0]
    return None
