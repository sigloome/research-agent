
import sys
import os
import time
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from skills.knowledge.db import manager
from skills.knowledge.paper import operations
from backend.logging_config import get_skill_logger

logger = get_skill_logger("batch_process")

def process_all_papers():
    print("Initializing Database...")
    manager.init_db()
    
    print("Fetching all papers...")
    # manager.list_papers returns list of dicts. We need ID.
    # list_papers supports sort, but gets everything?
    # Actually manager.list_papers uses a limit if not specified? 
    # Checking manager.py source would be good, but assuming it gets enough or we can use SQL directly.
    # Or simplified: use sqlite3 directly to get all IDs.
    
    conn = manager.get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id, title FROM papers")
    papers = c.fetchall()
    conn.close()
    
    total = len(papers)
    print(f"Found {total} papers. Starting processing...")
    
    for i, (paper_id, title) in enumerate(papers):
        print(f"[{i+1}/{total}] Processing: {title} ({paper_id})...")
        try:
            # Check if full text already exists locally to skip download?
            # User said "generate summary for all existed papers".
            # operations.analyze_paper checks if text exists. If it does, strictly speaking it skips download.
            # But the user might want to re-try download if previous attempt failed?
            # For now, rely on analyze_paper logic: "if not full_text: download".
            # If text exists, it proceeds to Summary.
            
            operations.analyze_paper(paper_id)
            print(f"  > Success.")
            
            # Rate limiting sleep
            time.sleep(2) 
            
        except Exception as e:
            print(f"  > Failed: {e}")
            logger.error(f"Failed to process {paper_id}", error=str(e))
            # Continue to next
            continue

if __name__ == "__main__":
    process_all_papers()
