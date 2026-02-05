"""
Paper-related tool implementations.
This file can be modified via update_skill_code and hot reloaded.
"""

import json
from typing import Any, Dict, List, Optional

from backend.logging_config import get_skill_logger
from skills.knowledge.db import manager
from skills.knowledge.paper_search import fetcher
from skills.knowledge.summarizer import summarize
from skills.knowledge.paper_search import fetcher
from skills.knowledge.summarizer import summarize
from backend.event_bus import emit, EventType

logger = get_skill_logger("paper")


def get_source_id_for_type(source_type: str = "arxiv") -> Optional[int]:
    """Get the source ID for a given source type."""
    source = manager.get_source_by_name(source_type.capitalize())
    if source:
        return source["id"]
    # Try to find by type
    sources = manager.list_sources()
    for s in sources:
        if s["source_type"] == source_type:
            return s["id"]
    return None


def extract_tags_from_abstract(abstract: str) -> list:
    """Extract simple tags from abstract using keyword matching."""
    keywords = [
        "LLM",
        "transformer",
        "attention",
        "RLHF",
        "GPT",
        "BERT",
        "diffusion",
        "vision",
        "language model",
        "neural network",
        "deep learning",
        "reinforcement",
        "fine-tuning",
        "prompt",
        "reasoning",
        "agent",
        "multimodal",
    ]
    tags = []
    abstract_lower = abstract.lower()
    for kw in keywords:
        if kw.lower() in abstract_lower:
            tags.append(kw)
    return tags[:5] if tags else ["AI"]


def fetch_papers(
    query: str, sort_by: str = "recent", max_results: int = 5, source_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    """Fetches papers from ArXiv/S2, summarizes them, and adds to DB."""
    logger.info("fetch_papers", query=query, sort_by=sort_by, max_results=max_results)
    arxiv_sort = "submittedDate"
    if sort_by == "relevance":
        arxiv_sort = "relevance"

    # Limit max results for faster response
    max_results = min(max_results, 5)

    # Get ArXiv source ID if not provided
    if source_id is None:
        source_id = get_source_id_for_type("arxiv")

    # fetcher.fetch_and_process returns enriched papers
    papers = fetcher.fetch_and_process(query, sort_by=arxiv_sort, max_results=max_results)
    results = []

    for p in papers:
        existing = manager.get_paper(p["id"])
        if existing and existing.get("summary_main_ideas"):
            results.append(existing)
            continue

        # Generate quick summary from abstract only (skip full summarization for speed)
        try:
            # Use a simpler summary generation - just extract key info without LLM call
            p["tags"] = extract_tags_from_abstract(p.get("abstract", ""))
            p["summary_main_ideas"] = p.get("abstract", "")[:500]
            p["source_id"] = source_id  # Associate with source
            p["source_id"] = source_id  # Associate with source
            manager.add_paper(p)

            # TRIGGER RAG SYNC
            # TRIGGER RAG SYNC (Decoupled)
            # Index abstract + title for global understanding
            content_to_index = f"Paper Title: {p.get('title')}\nAbstract: {p.get('abstract')}"
            logger.debug("emitting_paper_added", paper_id=p.get("id"))
            emit(
                EventType.PAPER_ADDED, payload={"content": content_to_index}, source="fetch_papers"
            )

        except Exception as e:
            logger.error("paper_processing_failed", paper_id=p.get("id"), error=str(e))
        results.append(p)

    return results


def search_local_papers(query: str) -> List[Dict[str, Any]]:
    """Search for papers already stored in the local database."""
    logger.info("search_local_papers", query=query)
    papers = manager.search_local_papers(query)
    return papers


def add_paper_by_url(url: str, source_id: Optional[int] = None) -> str:
    """Add a specific paper by its ArXiv URL."""
    logger.info("add_paper_by_url", url=url)
    p = fetcher.fetch_from_url(url)
    if not p:
        return "Failed to fetch paper from URL."

    # Get ArXiv source ID if not provided
    if source_id is None:
        source_id = get_source_id_for_type("arxiv")

    summary = summarize.generate_summary(p["abstract"], p["title"])
    p.update(summary)
    p["source_id"] = source_id  # Associate with source
    p["source_id"] = source_id  # Associate with source
    manager.add_paper(p)

    # TRIGGER RAG SYNC
    # TRIGGER RAG SYNC (Decoupled)
    content_to_index = f"Paper Title: {p.get('title')}\nAbstract: {p.get('abstract')}\nSummary: {p.get('summary_main_ideas')}"
    logger.debug("emitting_paper_added", paper_title=p.get("title"))
    emit(EventType.PAPER_ADDED, payload={"content": content_to_index}, source="add_paper_by_url")

    return f"Added paper: {p['title']} to database."


from skills.knowledge.paper import downloader
from skills.knowledge.paper.downloader import PaperWithdrawnError
from skills.knowledge.summarizer import summarize

def analyze_paper(paper_id: str, force_update: bool = False) -> Dict[str, Any]:
    """
    Downloads full text (HTML/PDF) and generates AI summary for a paper.
    """
    logger.info("analyze_paper", paper_id=paper_id)
    paper = manager.get_paper(paper_id)
    if not paper:
        raise ValueError(f"Paper {paper_id} not found")

    # 1. Download Content if missing
    # 1. Download Content if missing or forced
    full_text = manager.get_paper_full_text(paper_id)
    if not full_text or force_update:
        # Construct URLs
        html_url = f"https://arxiv.org/html/{paper_id}"
        pdf_url = f"https://arxiv.org/pdf/{paper_id}.pdf"
        
        save_dir = manager.DATA_DIR / "papers"
        try:
            saved_path = downloader.download_paper_content(paper_id, html_url, pdf_url, save_dir)
        except PaperWithdrawnError:
            print(f"Paper {paper_id} is withdrawn.")
            paper['content_source'] = 'withdrawn'
            paper['summary_main_ideas'] = "This paper has been withdrawn by the authors."
            paper['full_text'] = ""
            manager.add_paper(paper)
            return paper

        if saved_path:
            paper['full_text_local_path'] = saved_path
            
            # Read back text
            with open(saved_path, 'r', encoding='utf-8') as f:
                full_text = f.read()

            # Heuristic to detect if it was likely PDF extraction (PDFs won't have <html> usually)
            if "References" in full_text[-5000:] and "<html>" not in full_text[:1000]:
                 paper['content_source'] = 'pdf'
            else:
                 paper['content_source'] = 'html' 
            
            manager.add_paper(paper)
    
    # 2. Generate Summary
    if full_text:
        # Check if summary already exists? User said "generate ... for all", potentially re-generate or fill missing.
        summary_ctx = f"{paper.get('abstract', '')}\n\nFull Text:\n{full_text[:50000]}"
        summary = summarize.generate_summary(summary_ctx, paper.get('title', ''))
        
        paper.update(summary)
        manager.add_paper(paper)
        paper['full_text'] = full_text
        
        # 3. RAG Indexing
        # Construct rich context for citation support
        rag_content = (
            f"Paper Analysis: {paper.get('title')}\n"
            f"Authors: {paper.get('authors')}\n"
            f"ArXiv ID: {paper.get('id')}\n"
            f"URL: {paper.get('url')}\n\n"
            f"Abstract:\n{paper.get('abstract')}\n\n"
            f"Full Content:\n{full_text}"
        )
        logger.info("emitting_paper_updated_for_rag", paper_id=paper_id)
        emit(EventType.PAPER_ADDED, payload={"content": rag_content}, source="analyze_paper")
        
    return paper


# -----------------------------------------------------------------------------
# Unified Research Interface (merged from skills/research)
# -----------------------------------------------------------------------------
from skills.knowledge.zlibrary import client as zlib_client
from skills.knowledge.local_files import importer as local_files_ops


class ResearchAssistant:
    """
    Unified research assistant for managing papers and books.
    
    Capabilities:
    1. Search for papers/books (ArXiv, ZLibrary, Local DB)
    2. Add papers by URL
    3. Get details of specific items
    4. List managed items
    """
    
    def search(self, query: str, source: str = "all", limit: int = 5) -> Dict[str, List[Dict[str, Any]]]:
        """
        Search for research materials.
        
        Args:
            query: Search term
            source: Source to search ('all', 'arxiv', 'zlib', 'local')
            limit: Max results per source
            
        Returns:
            Dict containing results keyed by source.
        """
        results = {}
        
        if source in ["all", "local"]:
            results["local"] = search_local_papers(query)
            
        if source in ["all", "arxiv"]:
            results["arxiv"] = fetch_papers(query, sort_by="relevance", max_results=limit)
            
        if source in ["all", "zlib"]:
            try:
                results["zlib"] = zlib_client.search_books(query, limit=limit)
            except Exception as e:
                results["zlib"] = [{"error": str(e)}]
                
        return results

    def add(self, target: str) -> str:
        """
        Add a research item to the library.
        
        Args:
            target: Can be an ArXiv URL, a local file path, or a Z-Library ID.
        """
        import os
        
        if "arxiv.org" in target:
            return add_paper_by_url(target)
            
        if target.endswith(".pdf"):
            if os.path.exists(target):
                return local_files_ops.import_pdf(target)
            return "File not found."

        if target.isdigit() or (len(target) < 20 and "." not in target and "/" not in target):
            res = zlib_client.download_book(target)
            if "error" in res:
                return f"Failed to download book {target}: {res['error']}"
            return f"Downloaded book: {res.get('local_path')}"
             
        return "Unknown target format. Please provide a valid ArXiv URL, file path, or Book ID."

    def details(self, item_id: str) -> Dict[str, Any]:
        """Get detailed information about an item."""
        if item_id.startswith("zlib-") or item_id.isdigit():
            return zlib_client.get_book_info(item_id) or {"error": "Book not found"}
        return analyze_paper(item_id)
        
    def list_items(self) -> List[Dict[str, Any]]:
        """List all locally available items (papers and books)."""
        papers = search_local_papers("")
        books = zlib_client.list_downloaded_books()
        return papers + books
