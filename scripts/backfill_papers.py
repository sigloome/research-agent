
import sqlite3
import requests
from bs4 import BeautifulSoup
import os
import sys
from pathlib import Path

# Fix relative imports
sys.path.append(os.getcwd())

from skills.knowledge.graph_rag import index_text, initialize_rag

DB_PATH = "data/papers.db"
ARTICLES_DIR = "data/local_articles"

def setup():
    if not os.path.exists(ARTICLES_DIR):
        os.makedirs(ARTICLES_DIR)
    
    # Initialize Knowledge RAG
    initialize_rag(name="knowledge", working_dir="./data/graph_rag")

def fetch_and_index():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Find papers with URL but no local path
    cursor.execute("SELECT id, title, url FROM papers WHERE (full_text_local_path IS NULL OR full_text_local_path = '') AND url IS NOT NULL AND url != ''")
    papers = cursor.fetchall()
    
    print(f"Found {len(papers)} papers to backfill.")
    
    success_count = 0
    fail_count = 0
    
    for pid, title, url in papers:
        print(f"Processing: {title} ({url})")
        try:
            # Download
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            # extract text
            soup = BeautifulSoup(response.content, 'html.parser')
            # remove scripts and styles
            for script in soup(["script", "style"]):
                script.decompose()
            
            text = soup.get_text()
            # clean whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            if len(text) < 100:
                print(f"  Skipping: Content too short ({len(text)} chars)")
                fail_count += 1
                continue
                
            # Save to file
            filename = f"{pid}.md"
            filepath = os.path.join(ARTICLES_DIR, filename)
            full_path = str(Path(filepath).absolute())
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"# {title}\n\nSource: {url}\n\n{text}")
                
            # Index
            print("  Indexing into RAG...")
            index_text(f"PAPER: {title}\nSOURCE: {url}\nCONTENT:\n{text}", rag_name="knowledge")
            
            # Update DB
            cursor.execute("UPDATE papers SET full_text_local_path = ? WHERE id = ?", (full_path, pid))
            conn.commit()
            
            print("  Success.")
            success_count += 1
            
        except Exception as e:
            print(f"  Failed: {e}")
            fail_count += 1
            # Continue to next paper
            
    print(f"\nBackfill Complete. Success: {success_count}, Failed: {fail_count}")
    conn.close()

if __name__ == "__main__":
    setup()
    fetch_and_index()
