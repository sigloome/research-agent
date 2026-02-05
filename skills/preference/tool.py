
from typing import Any, Dict
from skills.preference.core import FeedbackEvent, analyze_event
from skills.preference.feedback import process_feedback as api_process_feedback 

# Agent Adapter
# In a real scenario, the Agent might want to "Simulate" feedback or "Analyze" it without triggering side effects,
# or it might want to trigger the exact same side effects as the API.
# For this pilot, let's expose a tool that allows the Agent to "Log User Feedback" manually if it detects it in conversation.

def log_user_feedback(event_type: str, target_content: str, value: float = 1.0) -> str:
    """
    Log user feedback directly from the Agent.
    
    Args:
        event_type: "rating" or "click" or "copy"
        target_content: The content the user reacted to
        value: 1.0 for positive, -1.0 for negative
    """
    # Create the event model using Core
    event = FeedbackEvent(
        event_type=event_type,
        target_id="agent_generated",
        target_content=target_content,
        value=value
    )
    
    # Analyze (Core)
    update_text, _, _ = analyze_event(event)
    
    # Execute Side Effects (Reuse API Adapter Logic for now to ensure consistency)
    # Ideally, side effects should be in a separate Service, but for this step 1 refactor, 
    # re-using the process_feedback function ensures we hit the DB/RAG the same way.
    success = api_process_feedback(event)
    
    return f"Feedback logged: {success}. Analysis: {update_text}"
