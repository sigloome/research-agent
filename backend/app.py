import json
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))  # noqa: E402

# Load environment variables
load_dotenv(PROJECT_ROOT / ".env")

from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.logging_config import get_api_logger
from backend.agent import MainAgent
from skills.knowledge.paper.downloader import download_paper_content
from skills.knowledge.summarizer.summarize import generate_summary
from skills.knowledge.db import manager
from skills.preference.analyzer import update_preferences_from_query
from skills.knowledge.graph_rag import initialize_rag
from skills.preference.feedback import FeedbackEvent, process_feedback

logger = get_api_logger()

app = FastAPI(title="AI Paper Agent")

@app.post("/api/feedback")
async def submit_feedback(event: FeedbackEvent):
    success = process_feedback(event)
    return {"success": success, "message": "Feedback processed" if success else "Ignored"}

class NoteCreate(BaseModel):
    content: str
    title: Optional[str] = None
    note_type: str = "note"  # 'note', 'annotation', 'summary'
    paper_id: Optional[str] = None  # Backward compatibility
    tags: Optional[List[str]] = None
    linked_items: Optional[List[dict]] = None  # [{"type": "paper", "id": "..."}]


class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    note_type: Optional[str] = None
    tags: Optional[List[str]] = None


class NoteLinkCreate(BaseModel):
    linked_type: str  # 'paper' or 'note'
    linked_id: str
    link_type: str = "reference"

@app.get("/api/paper/{paper_id}")
async def get_paper_details(paper_id: str):
    paper = manager.get_paper(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    full_text = manager.get_paper_full_text(paper_id)
    if full_text:
        paper['full_text'] = full_text
        
    return paper

@app.post("/api/paper/{paper_id}/analyze")
async def analyze_paper(paper_id: str, force_update: bool = False):
    logger.info(f"API analyze_paper called for {paper_id} with force_update={force_update}")
    try:
        from skills.knowledge.paper import core
        return core.analyze_paper(paper_id, force_update=force_update)
    except ValueError as e:
        logger.error(f"ValueError in analyze_paper: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/notes")
async def list_notes(
    paper_id: Optional[str] = None,
    note_type: Optional[str] = None,
    search: Optional[str] = None
):
    """List notes with optional filters."""
    return manager.get_notes(
        paper_id=paper_id,
        note_type=note_type,
        search_query=search
    )


@app.get("/api/notes/{note_id}")
async def get_note(note_id: int):
    """Get a single note by ID."""
    note = manager.get_note(note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@app.post("/api/notes")
async def create_note(note: NoteCreate):
    # 1. Save to DB
    note_id = manager.add_note(
        content=note.content,
        title=note.title,
        note_type=note.note_type,
        tags=note.tags,
        linked_items=note.linked_items,
        paper_id=note.paper_id  # Backward compatibility
    )
    
    # 2. Index to RAG (Async)
    try:
        rag = initialize_rag()
        # Create a document string that gives context
        doc_content = f"[{note.note_type.upper()}]"
        if note.title:
            doc_content += f" {note.title}"
        
        # Get linked paper titles for context
        linked_papers = []
        if note.paper_id:
            paper = manager.get_paper(note.paper_id)
            if paper:
                linked_papers.append(paper['title'])
        if note.linked_items:
            for item in note.linked_items:
                if item.get('type') == 'paper':
                    paper = manager.get_paper(item['id'])
                    if paper:
                        linked_papers.append(paper['title'])
        
        if linked_papers:
            doc_content += f"\nRelated to: {', '.join(linked_papers)}"
        doc_content += f"\n\n{note.content}"
        
        await rag.ainsert(doc_content)
    except Exception as e:
        logger.error(f"Failed to index note to RAG: {e}")
        
    return {"id": note_id, "status": "saved_and_indexing"}


@app.put("/api/notes/{note_id}")
async def update_note(note_id: int, update: NoteUpdate):
    """Update an existing note."""
    success = manager.update_note(
        note_id=note_id,
        title=update.title,
        content=update.content,
        note_type=update.note_type,
        tags=update.tags
    )
    if not success:
        raise HTTPException(status_code=404, detail="Note not found")
    return {"status": "updated"}


@app.delete("/api/notes/{note_id}")
async def delete_note(note_id: int):
    """Delete a note."""
    success = manager.delete_note(note_id)
    if not success:
        raise HTTPException(status_code=404, detail="Note not found")
    return {"status": "deleted"}


@app.post("/api/notes/{note_id}/links")
async def add_note_link(note_id: int, link: NoteLinkCreate):
    """Add a link from a note to a paper or another note."""
    link_id = manager.add_note_link(
        note_id=note_id,
        linked_type=link.linked_type,
        linked_id=link.linked_id,
        link_type=link.link_type
    )
    return {"id": link_id, "status": "linked"}


@app.delete("/api/notes/{note_id}/links/{link_id}")
async def remove_note_link(note_id: int, link_id: int):
    """Remove a link from a note."""
    success = manager.remove_note_link(link_id)
    if not success:
        raise HTTPException(status_code=404, detail="Link not found")
    return {"status": "unlinked"}


@app.get("/api/papers/{paper_id}/notes")
async def get_paper_notes(paper_id: str):
    """Get all notes linked to a specific paper."""
    return manager.get_paper_notes(paper_id)


# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/feedback")
async def submit_feedback(event: FeedbackEvent):
    success = process_feedback(event)
    return {"success": success, "message": "Feedback processed" if success else "Ignored"}


# Initialize Agent
# We use a single global instance for this single-user demo
agent = MainAgent()


@app.on_event("startup")
async def startup_db():
    manager.init_db()
    # Initialize Event Bus Handlers
    from skills.knowledge.handlers import register_handlers

    register_handlers()
    
    # Initialize Persistent Agent
    await agent.initialize()


# ============ Chat Management API ============

class Message(BaseModel):
    id: int
    chat_id: str
    role: str
    content: str
    created_at: str

class Chat(BaseModel):
    id: str
    title: Optional[str] = None
    created_at: str

class ChatCreate(BaseModel):
    title: Optional[str] = None

class ChatRequest(BaseModel):
    messages: Optional[List[Dict[str, Any]]] = None
    message: Optional[str] = None
    session_id: str = "default"  # Add session_id support


@app.get("/api/chats", response_model=List[Chat])
async def list_chats():
    """List all chat sessions."""
    return manager.list_chats()


@app.post("/api/chats", response_model=Chat)
async def create_chat(chat_data: ChatCreate):
    """Create a new chat session."""
    chat_id = manager.create_chat(chat_data.title)
    chat = manager.get_chat(chat_id)
    if not chat:
        raise HTTPException(status_code=500, detail="Failed to create chat")
    return chat


@app.get("/api/chats/{chat_id}", response_model=List[Message])
async def get_chat_history(chat_id: str):
    """Get full message history for a chat."""
    chat = manager.get_chat(chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return manager.get_chat_history(chat_id)


@app.delete("/api/chats/{chat_id}")
async def delete_chat(chat_id: str):
    """Delete a chat session."""
    success = manager.delete_chat(chat_id)
    if not success:
        raise HTTPException(status_code=404, detail="Chat not found")
    return {"status": "deleted"}





@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    logger.error(f"DEBUG: Entered chat_endpoint with message: {request.message} session: {request.session_id}")
    # Prefer single message with stateful backend
    latest_query = ""
    
    if request.message:
        latest_query = request.message
    elif request.messages:
        # Extract the latest user query from history
        for msg in reversed(request.messages):
            if msg.get("role") == "user":
                latest_query = msg.get("content", "")
                break
    
    logger.error(f"DEBUG: Latest query determined: {latest_query}")
    if not latest_query:
        raise HTTPException(status_code=400, detail="No message provided")

    # Ensure valid session/chat exists
    chat_id = request.session_id
    existing_chat = manager.get_chat(chat_id)
    if not existing_chat:
        # If default, create it
        if chat_id == "default":
            # Check if we have a default chat or create one?
            # Actually, "default" is a magic string in SDK.
            # Map "default" to a real DB chat?
            # For simplicity, if chat_id doesn't exist, we create it
            manager.create_chat("Default Chat") # ID will be generated, wait.
            # We need to preserve the ID provided if possible, or mapping.
            # But the request has session_id. The frontend should create chat first then send ID.
            # If "default" is passed, we might fail or treat as ephemeral?
            # Users must create chat first via sidebar logic.
            # BUT: legacy behavior used "default".
            # Let's create a chat entry with ID "default" to bridge the gap.
            try:
                # Manually insert to force ID="default"
                conn = manager.get_db_connection()
                conn.execute(
                    'INSERT INTO chats (id, title, created_at) VALUES (?, ?, ?)',
                    ("default", "General Chat", manager.datetime.now().isoformat())
                )
                conn.commit()
                conn.close()
            except:
                pass # Already exists
        else:
            # If specific ID passed but not found, 404
            raise HTTPException(status_code=404, detail="Chat session not found")

    # Load existing conversation history for context
    # This ensures the agent can continue historical conversations properly
    conversation_history = []
    try:
        existing_messages = manager.get_chat_history(chat_id)
        if existing_messages:
            conversation_history = [
                {"role": msg["role"], "content": msg["content"]}
                for msg in existing_messages
            ]
            logger.info(f"Loaded {len(conversation_history)} messages from history for chat {chat_id}")
    except Exception as e:
        logger.warning(f"Failed to load chat history: {e}")

    # Save User Message
    manager.save_message(chat_id, "user", latest_query)

    # Record the query and update preferences
    try:
        analysis = update_preferences_from_query(latest_query)
        logger.info(
            "preference_recorded", topics=analysis["topics"], query_type=analysis["query_type"]
        )
    except Exception as e:
        logger.warning("preference_update_failed", error=str(e))

    # Get user preference summary
    try:
        user_preferences = manager.get_preference_summary()
        logger.debug(
            "preference_context_loaded",
            preview=user_preferences[:100] if user_preferences else None,
        )
    except Exception as e:
        logger.warning("preference_fetch_failed", error=str(e))
        user_preferences = None

    # Use async generator for claude_agent_sdk streaming
    # WRAPPER: Accumulate specific response
    async def async_stream_generator():
        full_response = ""
        try:
            async for chunk in agent.chat_generator(
                latest_query, 
                session_id=request.session_id, 
                user_preferences=user_preferences,
                conversation_history=conversation_history
            ):
                # The SDK `chat_generator` yields SSE formatted strings "data: ...\n\n" or "0:...\n"
                
                try:
                    # Specific parsing for Vercel Protocol yielded by agent.py
                    # Format: 0:"json_quoted_string"\n
                    if chunk.startswith("0:"):
                        # Strip 0: and trailing \n
                        raw_val = chunk[2:].strip()
                        if raw_val:
                            text_val = json.loads(raw_val)
                            if isinstance(text_val, str):
                                full_response += text_val
                                logger.error(f"DEBUG: Appended from 0: {text_val[:20]}... Total: {len(full_response)}")
                    
                    # Case 2: Standard SSE format (data: {"type": "content", "content": "..."}\n\n)
                    elif chunk.startswith("data: "):
                        json_str = chunk[6:].strip()
                        if json_str and json_str != "[DONE]":
                            data = json.loads(json_str)
                            if isinstance(data, dict):
                                if data.get("type") == "content" and "content" in data:
                                    full_response += data["content"]
                                    logger.error(f"DEBUG: Appended from data content: {data['content'][:20]}...")
                                elif "text" in data: # Fallback for other potential formats
                                    full_response += data["text"]
                    # Case 3: Vercel Data format (d:{"type":...}\n)
                    elif chunk.startswith("d:"):
                        # Usually for tools/meta, not part of full_response text
                        pass
                except Exception as e:
                    logger.error(f"DEBUG: Error parsing chunk {repr(chunk)}: {e}")
                    
                yield chunk
        finally:
            # After stream ends, save response
            logger.error(f"DEBUG: Stream finished. full_response len: {len(full_response)}")
            if full_response:
                logger.error(f"DEBUG: Saving assistant message for chat {chat_id}")
                manager.save_message(chat_id, "assistant", full_response)
            else:
                logger.error(f"DEBUG: No assistant response accumulated to save!")

    return StreamingResponse(
        async_stream_generator(),
        media_type="text/plain; charset=utf-8",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/api/papers")
def list_papers(sort: str = "created_at_desc", source_id: int = None, source_type: str = None):
    return manager.list_papers(sort_by=sort, source_id=source_id, source_type=source_type)


@app.get("/api/papers/{paper_id}")
def read_paper(paper_id: str):
    p = manager.get_paper(paper_id)
    if not p:
        raise HTTPException(status_code=404, detail="Paper not found")
    return p


# ============ Books API (Z-Library) ============


@app.get("/api/books")
def list_books(source_id: int = None):
    """List all books in the library."""
    return manager.list_books(source_id=source_id)


@app.get("/api/books/{book_id}")
def read_book(book_id: str):
    """Get a specific book by ID."""
    b = manager.get_book(book_id)
    if not b:
        raise HTTPException(status_code=404, detail="Book not found")
    return b


@app.get("/api/books/search/{query}")
def search_books(query: str):
    """Search books by title, author, or description."""
    return manager.search_books(query)


# ============ Library Sources API ============


class SourceCreate(BaseModel):
    name: str
    source_type: str  # 'arxiv', 'url', 'local_file', 'bibtex', 'custom'
    config: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    icon: Optional[str] = "📁"


class SourceUpdate(BaseModel):
    name: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    enabled: Optional[bool] = None


@app.get("/api/sources")
def list_sources():
    """List all library sources with paper counts."""
    return manager.list_sources()


@app.post("/api/sources")
def create_source(source: SourceCreate):
    """Create a new library source."""
    source_id = manager.add_source(
        name=source.name,
        source_type=source.source_type,
        config=source.config,
        description=source.description,
        icon=source.icon or "📁",
    )
    if source_id:
        return {"id": source_id, "message": f"Source '{source.name}' created successfully"}
    raise HTTPException(status_code=400, detail="Failed to create source")


@app.get("/api/sources/{source_id}")
def get_source(source_id: int):
    """Get a specific library source."""
    source = manager.get_source(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    return source


@app.put("/api/sources/{source_id}")
def update_source(source_id: int, source: SourceUpdate):
    """Update a library source."""
    existing = manager.get_source(source_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Source not found")

    manager.update_source(
        source_id=source_id,
        name=source.name,
        config=source.config,
        description=source.description,
        icon=source.icon,
        enabled=source.enabled,
    )
    return {"message": "Source updated successfully"}


@app.delete("/api/sources/{source_id}")
def delete_source(source_id: int):
    """Delete a library source."""
    if manager.delete_source(source_id):
        return {"message": "Source deleted successfully"}
    raise HTTPException(status_code=404, detail="Source not found")


@app.get("/api/preferences")
def get_preferences():
    """
    Get user preferences and suggested questions based on history.
    """
    preferences = manager.get_user_preferences(limit=20)
    recent_queries = manager.get_recent_queries(limit=10)
    summary = manager.get_preference_summary()

    # Generate personalized suggestions based on preferences
    suggestions = generate_suggestions(preferences)

    return {
        "preferences": preferences,
        "recent_queries": [q["query_text"] for q in recent_queries[:5]],
        "summary": summary,
        "suggestions": suggestions,
    }


def generate_suggestions(preferences: Dict) -> List[str]:
    """
    Generate personalized question suggestions based on user preferences.
    """
    suggestions = []

    # Default suggestions
    default_suggestions = [
        "Find papers on LLM alignment",
        "Summarize recent NeurIPS papers",
        "Explain attention mechanisms",
        "Search for chain of thought",
    ]

    if not preferences:
        return default_suggestions

    # Generate topic-based suggestions
    topics = preferences.get("topic", [])
    if topics:
        top_topics = [t["value"] for t in topics[:3]]
        for topic in top_topics:
            suggestions.append(f"Find recent papers on {topic}")

        if len(top_topics) >= 2:
            suggestions.append(f"Compare {top_topics[0]} and {top_topics[1]} approaches")

    # Generate interest-based suggestions
    interests = preferences.get("interest", [])
    if interests:
        top_interest = interests[0]["value"]
        suggestions.append(f"Explain how {top_interest} works")
        suggestions.append(f"Latest research on {top_interest}")

    # Add query-type based suggestions
    query_types = preferences.get("query_type", [])
    if query_types and topics:
        qt = query_types[0]["value"]
        topic = topics[0]["value"]
        if qt == "summarize":
            suggestions.append(f"Summarize key findings in {topic}")
        elif qt == "explain_concept":
            suggestions.append(f"Deep dive into {topic} concepts")

    # Limit to 4 suggestions, fill with defaults if needed
    if len(suggestions) < 4:
        for default in default_suggestions:
            if default not in suggestions and len(suggestions) < 4:
                suggestions.append(default)

    return suggestions[:4]


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=18000)
