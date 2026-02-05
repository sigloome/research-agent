"""
Agent Adapter for Note Skill.
Wraps core logic for use by the AI Agent to manage notes.
"""
from typing import Any, Dict, List, Optional
from skills.knowledge.db import manager

def create_note(
    content: str,
    title: Optional[str] = None,
    note_type: str = "note",
    tags: Optional[List[str]] = None
) -> int:
    """
    Create a new note.
    
    Args:
        content: The text content of the note (Markdown supported)
        title: Optional title for the note
        note_type: Type of note ('note', 'annotation', 'summary')
        tags: List of string tags
        
    Returns:
        The new note ID.
    """
    return manager.add_note(
        content=content,
        title=title,
        note_type=note_type,
        tags=tags
    )

def update_note(
    note_id: int,
    title: Optional[str] = None,
    content: Optional[str] = None,
    note_type: Optional[str] = None,
    tags: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Update an existing note. Only provided fields are updated.
    
    Args:
        note_id: The ID of the note to update
        title: New title (optional)
        content: New content (optional)
        note_type: New type (optional)
        tags: New list of tags (optional)
        
    Returns:
        Status dictionary {"status": "updated"} or error
    """
    success = manager.update_note(
        note_id=note_id,
        title=title,
        content=content,
        note_type=note_type,
        tags=tags
    )
    
    if not success:
        raise ValueError(f"Note with ID {note_id} not found")
        
    return {"status": "updated", "id": note_id}

def delete_note(note_id: int) -> Dict[str, Any]:
    """
    Delete a note by ID.
    
    Args:
        note_id: The ID of the note to delete
        
    Returns:
        Status dictionary {"status": "deleted"}
    """
    success = manager.delete_note(note_id)
    if not success:
        raise ValueError(f"Note with ID {note_id} not found")
        
    return {"status": "deleted", "id": note_id}

def get_note(note_id: int) -> Dict[str, Any]:
    """
    Get a single note's details.
    
    Args:
        note_id: The ID of the note
        
    Returns:
        Note dictionary
    """
    note = manager.get_note(note_id)
    if not note:
        raise ValueError(f"Note with ID {note_id} not found")
    return note

def list_notes(
    search: Optional[str] = None,
    note_type: Optional[str] = None,
    limit: int = 20
) -> List[Dict[str, Any]]:
    """
    List and filter notes.
    
    Args:
        search: Search term for title/content
        note_type: Filter by 'note', 'annotation', or 'summary'
        limit: Max results to return
        
    Returns:
        List of notes
    """
    return manager.get_notes(
        search_query=search,
        note_type=note_type,
        limit=limit
    )
