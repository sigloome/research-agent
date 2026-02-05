
import os
import requests
from pathlib import Path
from bs4 import BeautifulSoup

class PaperWithdrawnError(Exception):
    pass

class PaperDownloadError(Exception):
    pass

def download_paper_content(paper_id: str, html_url: str, pdf_url: str, save_dir: Path) -> str:
    """
    Downloads paper content, preferring HTML, falling back to PDF (text extraction).
    Returns the absolute path to the saved text file.
    """
    save_dir.mkdir(parents=True, exist_ok=True)
    # Fix: ensure we don't treat .NNNN as extension to be replaced
    # Explicitly construct filename
    out_path = save_dir / f"{paper_id}.txt"
    
    # FIRST: Check Abstract page for withdrawn status
    # content_url passed here is usually HTML url, but we can infer ABS url
    # Actually, let's just use the paper_id to construct abs url
    abs_url = f"https://arxiv.org/abs/{paper_id}"
    try:
        resp_abs = requests.get(abs_url, timeout=10)
        if resp_abs.status_code == 200:
             if "This paper has been withdrawn" in resp_abs.text or "<em>(withdrawn)</em>" in resp_abs.text:
                 raise PaperWithdrawnError("Paper marked as withdrawn on ArXiv")
    except PaperWithdrawnError:
        raise
    except Exception:
        # Ignore other errors, proceed to download attempts
        pass

    # Try HTML first (ArXiv HTML)
    try:
        if html_url:
            print(f"Attempting HTML download from {html_url}")
            resp = requests.get(html_url, timeout=15)
            if resp.status_code == 200:
                text = resp.text
                
                # Basic HTML clean up to extract text? 
                # Or keep HTML structure? User said "html is preferrable than the pdf" likely for reading.
                # But for LLM, text is better. 
                # "please download full context of arxiv papers, html is preferrable than the pdf"
                # This implies saving the FULL content for the user to READ? Or for the LLM?
                # "papers should have summary... of their contents" -> LLM needs text.
                # "download full context... html preferrable" -> User might want to read it?
                # Given current PaperDetail uses ReactMarkdown, Markdown is best.
                # Let's convert HTML to Markdown if possible, or just save text.
                # Validating: ArXiv HTML is actually responsive HTML5.
                
                # Extract content using BeautifulSoup
                soup = BeautifulSoup(text, 'html.parser')
                # Remove header/footer if possible (ArXiv specific?)
                # ArXiv HTML usually has class="ltx_page_content" or similar.
                
                # For now, let's just extract text with structure
                text_content = soup.get_text(separator='\n\n')
                
                # Save as .txt
                # out_path is already defined above
                out_path.write_text(text_content, encoding='utf-8')
                return str(out_path.absolute())
                
    except Exception as e:
        print(f"HTML download failed: {e}")

    # Fallback to PDF
    if pdf_url:
        print(f"HTML failed. Attempting PDF download from {pdf_url}")
        try:
            resp = requests.get(pdf_url, timeout=30)
            if resp.status_code == 200:
                import io
                import pypdf
                
                pdf_file = io.BytesIO(resp.content)
                reader = pypdf.PdfReader(pdf_file)
                
                text_content = []
                for page in reader.pages:
                    text_content.append(page.extract_text())
                
                full_text = "\n\n".join(text_content)
                
                # Save as .txt
                # out_path is already defined above
                out_path.write_text(full_text, encoding='utf-8')
                return str(out_path.absolute())
        except Exception as e:
            print(f"PDF download/extraction failed: {e}")
            
    return None
