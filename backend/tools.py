"""
Tools module - orchestrates tool definitions and delegates to skills.
Skill implementations are in skills/ directories.
"""
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List

# Base paths - PROJECT_ROOT is parent of backend/
PROJECT_ROOT = Path(__file__).parent.parent

# Add project root to path for imports
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))  # noqa: E402

# Import skill modules
from skills.knowledge.paper import core as paper_ops
from skills.knowledge.note import tool as note_ops

# Import using importlib to handle hyphenated directory name
import importlib
skill_management = importlib.import_module("skills.skill-management.core")


def get_tool_function(name: str) -> Callable:
    """
    Get a tool function by name.
    Always gets the latest version from the (potentially reloaded) module.
    """
    # Skill management tools
    if hasattr(skill_management, name):
        return getattr(skill_management, name)
    
    # Paper tools
    if hasattr(paper_ops, name):
        return getattr(paper_ops, name)
        

        
    raise ValueError(f"Unknown tool: {name}")


def execute_tool(name: str, **kwargs) -> Any:
    """Execute a tool by name with the given arguments.
    Note: Returns JSON string for dict/list results to ensure SDK compatibility.
    """
    fn = get_tool_function(name)
    result = fn(**kwargs)
    # SDK expects string results - serialize complex types
    if isinstance(result, (dict, list)):
        return json.dumps(result, indent=2, default=str)
    return result



# Tool Definitions - schema for the agent
TOOLS_DEF = [
    # Skill management tools
    {
        "name": "list_skills",
        "description": "List all available skills with their names, descriptions, and paths.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "search_skills",
        "description": "Search for skills by name or description.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query to match against skill names and descriptions"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "read_skill",
        "description": "Read the content of a skill file (SKILL.md or Python module).",
        "input_schema": {
            "type": "object",
            "properties": {
                "skill_path": {"type": "string", "description": "Path to the skill file (e.g., 'skills/paper/core.py' or 'paper-search')"}
            },
            "required": ["skill_path"]
        }
    },
    {
        "name": "update_skill_code",
        "description": "Update the code of a skill file and hot-reload it. Use with CAUTION.",
        "input_schema": {
            "type": "object",
            "properties": {
                "skill_path": {"type": "string", "description": "Path to file within skills/ (e.g., 'skills/paper/core.py')"},
                "code": {"type": "string", "description": "Full new code content for the file"}
            },
            "required": ["skill_path", "code"]
        }
    },
    # Note: Paper operations (fetch_papers, analyze_paper, search_local_papers, add_paper_by_url)
    # are available as skills in skills/knowledge/paper/core.py, not as SDK tools.
    {
        "name": "create_note",
        "description": "Create a new note, annotation, or summary.",
        "input_schema": {
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "The content of the note (Markdown supported)"},
                "title": {"type": "string", "description": "Title of the note"},
                "note_type": {"type": "string", "enum": ["note", "annotation", "summary"], "default": "note"},
                "tags": {"type": "array", "items": {"type": "string"}, "description": "List of tags"}
            },
            "required": ["content"]
        }
    },
    {
        "name": "update_note",
        "description": "Update an existing note. Only provide fields you want to change.",
        "input_schema": {
            "type": "object",
            "properties": {
                "note_id": {"type": "integer", "description": "ID of the note to update"},
                "content": {"type": "string", "description": "New content"},
                "title": {"type": "string", "description": "New title"},
                "note_type": {"type": "string", "enum": ["note", "annotation", "summary"]},
                "tags": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["note_id"]
        }
    },
    {
        "name": "delete_note",
        "description": "Delete a note by ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "note_id": {"type": "integer", "description": "ID of the note to delete"}
            },
            "required": ["note_id"]
        }
    },
    {
        "name": "list_notes",
        "description": "List or search notes.",
        "input_schema": {
            "type": "object",
            "properties": {
                "search": {"type": "string", "description": "Search query for title/content"},
                "note_type": {"type": "string", "enum": ["note", "annotation", "summary"]},
                "limit": {"type": "integer", "default": 20}
            }
        }
    },
    {
        "name": "get_note",
        "description": "Get details of a specific note.",
        "input_schema": {
            "type": "object",
            "properties": {
                "note_id": {"type": "integer", "description": "ID of the note to get"}
            },
            "required": ["note_id"]
        }
    },
]


def _serialize_result(result: Any) -> Any:
    """Serialize dict/list results to JSON strings for SDK compatibility."""
    if isinstance(result, (dict, list)):
        return json.dumps(result, indent=2, default=str)
    return result

# Dynamic tool map that supports hot reload
def get_tool_map() -> Dict[str, Callable]:
    """Get the current tool map with latest function references.
    All results are serialized to ensure SDK compatibility.
    """
    def wrap(fn):
        """Wrapper that serializes complex return types."""
        def wrapped(**kw):
            return _serialize_result(fn(**kw))
        return wrapped
    
    return {
        # Skill management
        "list_skills": wrap(lambda **kw: getattr(skill_management, 'list_skills')(**kw)),
        "search_skills": wrap(lambda **kw: getattr(skill_management, 'search_skills')(**kw)),
        "read_skill": wrap(lambda **kw: getattr(skill_management, 'read_skill')(**kw)),
        "update_skill_code": wrap(lambda **kw: getattr(skill_management, 'update_skill_code')(**kw)),
        # Note: Paper operations are skills, not tools (see skills/knowledge/paper/core.py)
        # Note tools
        "create_note": wrap(lambda **kw: getattr(note_ops, 'create_note')(**kw)),
        "update_note": wrap(lambda **kw: getattr(note_ops, 'update_note')(**kw)),
        "delete_note": wrap(lambda **kw: getattr(note_ops, 'delete_note')(**kw)),
        "list_notes": wrap(lambda **kw: getattr(note_ops, 'list_notes')(**kw)),
        "get_note": wrap(lambda **kw: getattr(note_ops, 'get_note')(**kw)),
    }

# For backward compatibility
TOOL_MAP = get_tool_map()
