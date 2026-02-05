"""
Local File Importer
Handles importing papers from local PDF files.
"""
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Try to import PDF parsing library
try:
    import PyPDF2
    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False

try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

from skills.knowledge.db import manager

# Default local articles folder
# Path: .claude/skills/local_files/importer.py -> project root
# Use resolve() to handle symlinks correctly
# skills/local_files/importer.py -> parent.parent.parent = project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
LOCAL_ARTICLES_DIR = PROJECT_ROOT / "data" / "local_articles"


def get_local_source_id() -> Optional[int]:
    """Get or create the local files source."""
    source = manager.get_source_by_name("Local Files")
    if source:
        return source['id']
    
    # Try to find existing local_file source
    sources = manager.list_sources()
    for s in sources:
        if s['source_type'] == 'local_file':
            return s['id']
    
    # Create new local files source
    source_id = manager.add_source(
        name="Local Files",
        source_type="local_file",
        config={"path": str(LOCAL_ARTICLES_DIR)},
        description="Papers imported from local PDF files",
        icon="📁"
    )
    return source_id


def extract_text_from_pdf(pdf_path: str, max_pages: int = 10) -> str:
    """Extract text content from a PDF file."""
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        return ""
    
    text_content = []
    
    # Try PyMuPDF first (better quality)
    if HAS_PYMUPDF:
        try:
            doc = fitz.open(str(pdf_path))
            for i, page in enumerate(doc):
                if i >= max_pages:
                    break
                text_content.append(page.get_text())
            doc.close()
            return "\n".join(text_content)
        except Exception as e:
            print(f"PyMuPDF error: {e}")
    
    # Fallback to PyPDF2
    if HAS_PYPDF2:
        try:
            with open(pdf_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for i, page in enumerate(reader.pages):
                    if i >= max_pages:
                        break
                    text_content.append(page.extract_text() or "")
            return "\n".join(text_content)
        except Exception as e:
            print(f"PyPDF2 error: {e}")
    
    return ""


def extract_metadata_from_pdf(pdf_path: str) -> Dict[str, Any]:
    """Extract metadata from a PDF file."""
    pdf_path = Path(pdf_path)
    metadata = {
        "title": pdf_path.stem,  # Default to filename without extension
        "authors": [],
        "created_date": None,
    }
    
    if HAS_PYMUPDF:
        try:
            doc = fitz.open(str(pdf_path))
            pdf_meta = doc.metadata
            if pdf_meta:
                if pdf_meta.get("title"):
                    metadata["title"] = pdf_meta["title"]
                if pdf_meta.get("author"):
                    # Split authors by common delimiters
                    authors = pdf_meta["author"].replace(";", ",").split(",")
                    metadata["authors"] = [a.strip() for a in authors if a.strip()]
                if pdf_meta.get("creationDate"):
                    metadata["created_date"] = pdf_meta["creationDate"]
            doc.close()
        except Exception as e:
            print(f"Error extracting PDF metadata: {e}")
    elif HAS_PYPDF2:
        try:
            with open(pdf_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                pdf_meta = reader.metadata
                if pdf_meta:
                    if pdf_meta.get("/Title"):
                        metadata["title"] = pdf_meta["/Title"]
                    if pdf_meta.get("/Author"):
                        authors = pdf_meta["/Author"].replace(";", ",").split(",")
                        metadata["authors"] = [a.strip() for a in authors if a.strip()]
                    if pdf_meta.get("/CreationDate"):
                        metadata["created_date"] = pdf_meta["/CreationDate"]
        except Exception as e:
            print(f"Error extracting PDF metadata: {e}")
    
    return metadata


def generate_paper_id(file_path: str) -> str:
    """Generate a unique ID for a local paper based on file path."""
    path_hash = hashlib.md5(file_path.encode()).hexdigest()[:12]
    return f"local-{path_hash}"


def import_pdf(file_path: str, title: str = None, authors: List[str] = None) -> Dict[str, Any]:
    """
    Import a PDF file into the library.
    
    Args:
        file_path: Path to the PDF file
        title: Optional title override
        authors: Optional authors override
    
    Returns:
        The imported paper data or error message
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        return {"error": f"File not found: {file_path}"}
    
    if not file_path.suffix.lower() == '.pdf':
        return {"error": f"Not a PDF file: {file_path}"}
    
    print(f"[local_files] Importing PDF: {file_path}")
    
    # Extract metadata from PDF
    metadata = extract_metadata_from_pdf(str(file_path))
    
    # Use provided overrides or extracted metadata
    paper_title = title or metadata.get("title", file_path.stem)
    paper_authors = authors or metadata.get("authors", [])
    
    # Extract text for abstract/summary
    text_content = extract_text_from_pdf(str(file_path), max_pages=5)
    
    # Use first ~1000 chars as abstract if available
    abstract = text_content[:1000].strip() if text_content else f"Imported from local file: {file_path.name}"
    
    # Generate unique ID
    paper_id = generate_paper_id(str(file_path))
    
    # Get or create local files source
    source_id = get_local_source_id()
    
    # Create paper data
    paper_data = {
        "id": paper_id,
        "title": paper_title,
        "authors": paper_authors,
        "abstract": abstract,
        "url": f"file://{file_path.absolute()}",
        "published_date": metadata.get("created_date") or datetime.now().isoformat(),
        "content_source": "local_pdf",
        "full_text_local_path": str(file_path.absolute()),
        "source_id": source_id,
        "tags": ["local", "imported"],
        "summary_main_ideas": abstract[:500] if abstract else None,
    }
    
    # Add to database
    manager.add_paper(paper_data)
    
    print(f"[local_files] Imported paper: {paper_title}")
    
    return paper_data


def list_local_files(directory: str = None) -> List[Dict[str, Any]]:
    """List all PDF files in the local articles directory."""
    dir_path = Path(directory) if directory else LOCAL_ARTICLES_DIR
    
    if not dir_path.exists():
        return []
    
    files = []
    for pdf_file in dir_path.glob("**/*.pdf"):
        files.append({
            "path": str(pdf_file),
            "name": pdf_file.name,
            "size": pdf_file.stat().st_size,
            "modified": datetime.fromtimestamp(pdf_file.stat().st_mtime).isoformat()
        })
    
    return files


def import_all_from_directory(directory: str = None) -> List[Dict[str, Any]]:
    """Import all PDF files from a directory."""
    files = list_local_files(directory)
    results = []
    
    for file_info in files:
        result = import_pdf(file_info["path"])
        results.append(result)
    
    return results
