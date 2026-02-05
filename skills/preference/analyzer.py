"""
User Preference Analyzer (API Adapter)

Analyzes user queries to extract topics, query types, and interests
for personalized recommendations.
"""

from typing import Dict, Any
# Import pure logic from Core
from skills.preference.core import analyze_query

def update_preferences_from_query(query: str) -> Dict[str, Any]:
    """
    Analyze a query and update user preferences in the database.
    This acts as the Orchestrator/Adapter:
    1. Call Core Logic (analyze_query)
    2. Call Persistence Adapter (manager)
    """
    from skills.knowledge.db import manager
    
    # 1. Core Analysis
    analysis = analyze_query(query)
    
    # 2. Persistence (Side Effects)
    # Record the query
    manager.record_user_query(
        query_text=query,
        query_type=analysis['query_type'],
        topics=analysis['topics']
    )
    
    # Update topic preferences
    for topic in analysis['topics']:
        manager.update_user_preference('topic', topic, weight=1.0)
    
    # Update query type preferences
    if analysis['query_type']:
        manager.update_user_preference('query_type', analysis['query_type'], weight=0.5)
    
    # Update specific interest preferences
    for interest in analysis['interests']:
        manager.update_user_preference('interest', interest, weight=1.5)
    
    # Trigger Auto-Sync to Profile (Background)
    try:
        from skills.preference.sync import sync_recent_activity_to_profile
        # We only sync occasionally or if significant topics found?
        # For prototype, sync every time is fine (it's threaded).
        sync_recent_activity_to_profile()
    except Exception as e:
        print(f"Preference sync warning: {e}")

    return analysis
