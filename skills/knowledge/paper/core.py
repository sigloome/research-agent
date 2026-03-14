"""
Paper-related tool implementations.
This file can be modified via update_skill_code and hot reloaded.
"""

import json
from typing import Any, Dict, List, Optional

from backend.event_bus import EventType, emit
from backend.logging_config import get_skill_logger
from skills.knowledge.db import manager
from skills.knowledge.paper.id_utils import canonicalize_arxiv_id, resolve_paper_id
from skills.knowledge.paper_search import fetcher
from skills.knowledge.summarizer import summarize

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


def _is_ingest_complete(paper: Dict[str, Any]) -> bool:
    required = (
        "summary_main_ideas",
        "summary_methods",
        "summary_results",
        "summary_limitations",
        "full_text_local_path",
    )
    return all(str(paper.get(field, "")).strip() for field in required)


def _emit_fetch_rag_index(paper: Dict[str, Any]) -> None:
    content_to_index = f"Paper Title: {paper.get('title')}\nAbstract: {paper.get('abstract')}"
    logger.debug("emitting_paper_added", paper_id=paper.get("id"))
    emit(EventType.PAPER_ADDED, payload={"content": content_to_index}, source="fetch_papers")


def fetch_papers(
    query: str, sort_by: str = "recent", max_results: int = 5, source_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    """Fetch from ArXiv, persist metadata, then run ingest for durable local retrieval."""
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
        paper_id = str(p.get("id", "")).strip()
        if not paper_id:
            continue
        existing = manager.get_paper(paper_id)
        if existing and _is_ingest_complete(existing):
            results.append(existing)
            continue

        try:
            if existing is None:
                p["tags"] = extract_tags_from_abstract(p.get("abstract", ""))
                p["summary_main_ideas"] = p.get("abstract", "")[:500]
                p["source_id"] = source_id
                manager.add_paper(p)
                _emit_fetch_rag_index(p)
            ingest_result = paper_ingest(paper_id, force_update=False, source_id=source_id)
            ingested = manager.get_paper(paper_id)
            if ingested:
                results.append(ingested)
            elif existing:
                results.append(existing)
            else:
                results.append(p)
            if not ingest_result.get("ok"):
                logger.warning(
                    "paper_ingest_incomplete_after_fetch",
                    paper_id=paper_id,
                    missing_fields=ingest_result.get("missing_fields", []),
                    error=ingest_result.get("error"),
                )
        except Exception as e:
            logger.error("paper_processing_failed", paper_id=p.get("id"), error=str(e))
            if existing:
                results.append(existing)
            else:
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
    p["source_id"] = source_id
    manager.add_paper(p)

    # TRIGGER RAG SYNC
    # TRIGGER RAG SYNC (Decoupled)
    content_to_index = f"Paper Title: {p.get('title')}\nAbstract: {p.get('abstract')}\nSummary: {p.get('summary_main_ideas')}"
    logger.debug("emitting_paper_added", paper_title=p.get("title"))
    emit(EventType.PAPER_ADDED, payload={"content": content_to_index}, source="add_paper_by_url")

    return f"Added paper: {p['title']} to database."


from skills.knowledge.paper import downloader
from skills.knowledge.paper.downloader import PaperWithdrawnError


def _extract_arxiv_id(source: str) -> Optional[str]:
    return canonicalize_arxiv_id(source or "")


def paper_ingest(
    source: str,
    *,
    force_update: bool = False,
    source_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Codex-native ingest contract:
    1) persist local content (full_text_local_path)
    2) persist key summary fields for retrieval
    Returns a structured success/failure envelope.
    """
    if not source or not str(source).strip():
        return {"ok": False, "status": "failed", "error": "source is required"}

    # Local PDF path ingest path
    source_text = str(source).strip()
    if source_text.lower().endswith(".pdf"):
        imported = local_files_ops.import_pdf(source_text)
        if isinstance(imported, dict) and imported.get("error"):
            return {
                "ok": False,
                "status": "failed",
                "error": imported["error"],
                "source": source_text,
            }
        paper_id = imported.get("id") if isinstance(imported, dict) else None
        if not paper_id:
            return {
                "ok": False,
                "status": "failed",
                "error": "local import did not return paper id",
                "source": source_text,
            }
    else:
        # ArXiv URL / ID ingest path
        arxiv_id = _extract_arxiv_id(source_text)
        if not arxiv_id:
            return {
                "ok": False,
                "status": "failed",
                "error": "unsupported source format; provide arxiv id/url or local pdf path",
                "source": source_text,
            }

        existing = manager.get_paper(arxiv_id)
        if existing is None:
            paper = fetcher.get_arxiv_paper_by_id(arxiv_id)
            if not paper:
                return {
                    "ok": False,
                    "status": "failed",
                    "error": f"failed to fetch metadata for arxiv id {arxiv_id}",
                    "source": source_text,
                }
            if source_id is None:
                source_id = get_source_id_for_type("arxiv")
            paper["source_id"] = source_id
            manager.add_paper(paper)
        paper_id = arxiv_id

    analyzed = analyze_paper(resolve_paper_id(str(paper_id)), force_update=force_update)
    local_path = analyzed.get("full_text_local_path")
    key_fields = [
        "summary_main_ideas",
        "summary_methods",
        "summary_results",
        "summary_limitations",
    ]
    missing = [f for f in key_fields if not str(analyzed.get(f, "")).strip()]
    if missing:
        fallback_text = (
            str(analyzed.get("summary_main_ideas", "")).strip()
            or str(analyzed.get("abstract", "")).strip()
            or "Summary not available from parser; please review full text."
        )
        for field in missing:
            analyzed[field] = fallback_text
        manager.add_paper(analyzed)
        missing = [f for f in key_fields if not str(analyzed.get(f, "")).strip()]
    local_ok = bool(local_path and str(local_path).strip())
    ok = local_ok and not missing

    return {
        "ok": ok,
        "status": "success" if ok else "failed",
        "paper_id": analyzed.get("id"),
        "title": analyzed.get("title"),
        "local_path": local_path,
        "missing_fields": missing,
        "content_source": analyzed.get("content_source"),
    }

def analyze_paper(paper_id: str, force_update: bool = False) -> Dict[str, Any]:
    """
    Downloads full text (HTML/PDF) and generates AI summary for a paper.
    """
    resolved_paper_id = resolve_paper_id(paper_id)
    logger.info("analyze_paper", paper_id=resolved_paper_id)
    paper = manager.get_paper(resolved_paper_id)
    if not paper:
        raise ValueError(f"Paper {resolved_paper_id} not found")

    # 1. Download Content if missing
    # 1. Download Content if missing or forced
    full_text = manager.get_paper_full_text(resolved_paper_id)
    if not full_text or force_update:
        # Construct URLs
        html_url = f"https://arxiv.org/html/{resolved_paper_id}"
        pdf_url = f"https://arxiv.org/pdf/{resolved_paper_id}.pdf"
        
        save_dir = manager.DATA_DIR / "papers"
        try:
            saved_path = downloader.download_paper_content(
                resolved_paper_id, html_url, pdf_url, save_dir
            )
        except PaperWithdrawnError:
            print(f"Paper {resolved_paper_id} is withdrawn.")
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
        logger.info("emitting_paper_updated_for_rag", paper_id=resolved_paper_id)
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
            result = paper_ingest(target)
            if result.get("ok"):
                return f"Ingested paper: {result.get('paper_id')}"
            return f"Failed to ingest paper: {result.get('error', 'unknown error')}"
            
        if target.endswith(".pdf"):
            if os.path.exists(target):
                result = paper_ingest(target)
                if result.get("ok"):
                    return f"Ingested paper: {result.get('paper_id')}"
                return f"Failed to ingest paper: {result.get('error', 'unknown error')}"
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
