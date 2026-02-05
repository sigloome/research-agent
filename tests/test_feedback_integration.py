
import unittest
import os
import shutil
import sys
sys.path.insert(0, os.getcwd())
print(f"DEBUG: CWD={os.getcwd()}")
print(f"DEBUG: sys.path={sys.path}")
try:
    import skills
    print(f"DEBUG: skills module found at {skills.__file__}")
except ImportError as e:
    print(f"DEBUG: skills module NOT found: {e}")

from pathlib import Path
import json
from datetime import datetime
from skills.preference.feedback import FeedbackEvent, process_feedback
from skills.knowledge.db import manager

# Setup test environment
TEST_DB_NAME = "test_feedback_papers.db"

class TestFeedbackIntegration(unittest.TestCase):
    def setUp(self):
        # Use a separate DB for testing
        os.environ["DB_NAME"] = TEST_DB_NAME
        # Re-initialize DB manager with new DB name
        # Note: manager module initializes DB_PATH at import time, so we might need to patch it 
        # or reload it. For checking logical flow, we can just point to the test DB if we mock manager.
        # But since manager is already imported in feedback.py, patching env var alone might be late.
        # Let's verify what manager uses. 
        # It uses os.getenv("DB_NAME", "papers.db"). If we set it before re-import/run, it might work?
        # Actually simplest is to just use the actual manager content since we can't easily reload module in this script structure.
        # We will manually override the DB_PATH in the manager object if possible or just accept main DB (bad practice).
        # Better: Let's patch manager.DB_PATH
        
        # Override manager's DB path for safety
        self.original_db_path = manager.DB_PATH
        self.test_db_path = str(Path(manager.PROJECT_ROOT) / "data" / TEST_DB_NAME)
        manager.DB_PATH = self.test_db_path
        
        # Initialize fresh DB
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
        manager.init_db()

    def tearDown(self):
        # Restore DB path
        manager.DB_PATH = self.original_db_path
        # Clean up test DB
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)

    def test_click_boosts_topics(self):
        # 1. Create a dummy paper with known tags
        paper_id = "test_paper_1"
        test_tags = ["Deep Learning", "Transformers"]
        manager.add_paper({
            "id": paper_id,
            "title": "Test Paper on Transformers",
            "tags": test_tags,
            "abstract": "Abstract...",
            "authors": ["Author A"]
        })
        
        # 2. Verify initial preferences are empty
        prefs = manager.get_user_preferences()
        self.assertEqual(len(prefs.get('topic', [])), 0)
        
        # 3. Simulate Click Feedback
        event = FeedbackEvent(
            event_type="click",
            target_id=paper_id,
            timestamp=datetime.now()
        )
        
        success = process_feedback(event)
        self.assertTrue(success, "Feedback processing should succeed")
        
        # 4. Verify SQL was updated
        prefs = manager.get_user_preferences()
        topics = prefs.get('topic', [])
        
        # Check that we have entries for our tags
        topic_values = [t['value'] for t in topics]
        self.assertIn("Deep Learning", topic_values)
        self.assertIn("Transformers", topic_values)
        
        # Check weight (should be > 0, exact increment depends on implementation (0.5))
        for t in topics:
            if t['value'] in test_tags:
                self.assertGreater(t['weight'], 0.0)
                
        # Check "interest" update (Paper Title)
        interests = prefs.get('interest', [])
        interest_values = [i['value'] for i in interests]
        self.assertIn("Test Paper on Transformers", interest_values)

if __name__ == "__main__":
    unittest.main()
