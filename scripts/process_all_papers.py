
import sys
import os
import time
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from skills.knowledge.db import manager
from skills.knowledge.paper import core as paper_core
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
            # Contract ingest path guarantees local persistence + key fields when possible.
            paper_core.paper_ingest(paper_id)
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
