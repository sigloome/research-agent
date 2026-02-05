
from typing import Optional, Dict, Any
from datetime import datetime
from skills.preference import update_user_profile
# Import Core Logic
from skills.preference.core import FeedbackEvent, analyze_event

# Re-export FeedbackEvent for API compatibility
__all__ = ["FeedbackEvent", "process_feedback"]

def process_feedback(event: FeedbackEvent) -> bool:
    """
    API ADAPTER: Processes feedback via HTTP.
    1. Calls Core Logic to analyze.
    2. Handles Side Effects (DB, RAG).
    """
    # 1. Core Logic
    update_text, should_boost_sql, paper_id_to_boost = analyze_event(event)

    # 2. Side Effect: SQL Database Update
    sql_updated = False
    if should_boost_sql and paper_id_to_boost:
        try:
            from skills.knowledge.db import manager
            # Assume target_id might be a paper_id
            paper = manager.get_paper(paper_id_to_boost)
            if paper and paper.get('tags'):
                print(f"[Feedback] Boosting topics for paper {paper_id_to_boost}: {paper['tags']}")
                for tag in paper['tags']:
                    manager.update_user_preference("topic", tag, weight=0.5)
                manager.update_user_preference("interest", paper['title'], weight=0.5)
                sql_updated = True
        except ImportError:
            print("[Feedback] Warning: DB manager not available")
        except Exception as e:
            print(f"[Feedback] DB Error: {e}")

    # 3. Side Effect: Markdown Profile Update
    if update_text:
        print(f"[Feedback] Updating profile with: {update_text}")
        try:
            update_user_profile(update_text)
            return True
        except Exception as e:
            print(f"[Feedback] Error updating profile: {e}")
            return sql_updated
            
    return sql_updated
