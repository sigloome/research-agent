import asyncio
import os
from typing import List, Optional
import threading

from claude_agent_sdk import ClaudeAgentOptions, query
from skills.knowledge.db import manager
from skills.preference.implementation import append_to_history, get_user_history

async def _generate_summary() -> Optional[str]:
    """
    Internal async function to generate summary using Claude SDK.
    """
    queries = manager.get_recent_queries(limit=10)
    if not queries:
        return None

    # Format for LLM
    query_texts = [q['query_text'] for q in queries]
    query_block = "\n".join([f"- {t}" for t in query_texts])
    
    prompt = f"""
    The following are the user's recent queries in an AI research assistant:
    
    {query_block}
    
    Generate a SINGLE concise sentence summarizing the user's primary recent interest. 
    Start with "User has recently been exploring..." or "User is focused on...".
    Do not mention specific query counts. If the queries are too diverse, summarize the main theme.
    """
    
    model = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929")
    options = ClaudeAgentOptions(cwd=".", model=model, allowed_tools=[])
    
    response_text = ""
    try:
        async for message in query(prompt=prompt, options=options):
            if hasattr(message, "content") and message.content:
                for block in message.content:
                    if hasattr(block, "text"):
                        response_text += block.text
        return response_text.strip()
    except Exception as e:
        print(f"Error generating summary: {e}")
        return None

def sync_recent_activity_to_profile():
    """
    Fetch recent SQL queries, summarize with LLM, and append to Markdown history.
    This function handles the async event loop complexity.
    """
    def _run():
        try:
            # check if loop exists
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            summary = loop.run_until_complete(_generate_summary())
            
            if summary:
                # Check for duplication (simple string check)
                current = get_user_history()
                if summary in current:
                    return

                # Append to HISTORY
                append_to_history("Auto-Summary (Recent Activity)", summary)
                print(f"[Sync] Updated history: {summary}")
        except Exception as e:
            print(f"[Sync] Failed: {e}")

    # Fire and forget in a separate thread to avoid blocking main response
    threading.Thread(target=_run, daemon=True).start()
