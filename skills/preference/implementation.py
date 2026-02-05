import os
from pathlib import Path
import hashlib

# Import structured logging
try:
    from backend.logging_config import get_skill_logger

    logger = get_skill_logger("preference")
except ImportError:
    import structlog

    logger = structlog.get_logger("preference")

# Global state for sync
_LAST_PROFILE_HASH = None

# Path to the profile
PROFILE_PATH = Path("data/preferences/user_profile.md")
HISTORY_PATH = Path("data/preferences/user_history.md")
PROFILE_PATH.parent.mkdir(parents=True, exist_ok=True)

if not PROFILE_PATH.exists():
    PROFILE_PATH.write_text("# User Profile\n\nNo preferences set yet.", encoding="utf-8")

if not HISTORY_PATH.exists():
    HISTORY_PATH.write_text("# User Interaction History\n\nNo history yet.", encoding="utf-8")


def get_user_profile() -> str:
    """
    Read the user's profile from markdown.
    """
    content = PROFILE_PATH.read_text(encoding="utf-8")
    check_and_sync_profile(content)
    return content


def get_user_history() -> str:
    """
    Read the user's history from markdown.
    """
    if not HISTORY_PATH.exists():
        return ""
    return HISTORY_PATH.read_text(encoding="utf-8")


def check_and_sync_profile(content: str):
    """
    Check if the profile content has changed since last known hash.
    If so, re-index it into the Preference RAG.
    """
    global _LAST_PROFILE_HASH

    current_hash = hashlib.md5(content.encode("utf-8")).hexdigest()

    if _LAST_PROFILE_HASH is None:
        # First load, just set the hash without re-indexing to avoid startup churn
        # UNLESS it's empty/new? No, let's assume if it exists, it might need indexing.
        # But we don't want to re-index on every restart if it hasn't changed.
        # For now, let's just set the hash. To support true persistence we'd need to store the hash on disk.
        # User requirement: "if preference files are updated manually...".
        # We'll optimistically index on startup to be safe? Or maybe just set hash.
        # Let's index on first load to ensure RAG is populated.
        logger.debug("profile_first_load_indexing")
        _LAST_PROFILE_HASH = current_hash
        _index_to_rag(content)
        return

    if current_hash != _LAST_PROFILE_HASH:
        logger.info("profile_changed_reindexing")
        _LAST_PROFILE_HASH = current_hash
        _index_to_rag(content)


def _index_to_rag(content: str):
    """Helper to index content to Preference RAG."""
    try:
        from skills.knowledge.graph_rag import index_text, initialize_rag

        # Ensure preference RAG is initialized
        initialize_rag(name="preference", working_dir="./data/graph_rag_preference")

        logger.info("profile_syncing_to_rag")
        index_text(f"User Profile / Preferences:\n{content}", rag_name="preference")
    except Exception as e:
        logger.error("profile_sync_failed", error=str(e))


def update_user_profile(new_content: str):
    """
    Overwrite the user's profile.
    """
    PROFILE_PATH.write_text(new_content, encoding="utf-8")

    # Auto-Sync: Index this into RAG so the agent "knows" it conceptually
    _index_to_rag(new_content)

    # Update hash to prevent double-sync on next read
    global _LAST_PROFILE_HASH
    _LAST_PROFILE_HASH = hashlib.md5(new_content.encode("utf-8")).hexdigest()


def append_to_profile(section: str, content: str):
    """
    Append a new section to the profile.
    """
    current = get_user_profile()
    new_data = f"\n\n## {section}\n{content}"
    update_user_profile(current + new_data)


def update_user_history(new_content: str):
    """
    Overwrite the user's history.
    """
    HISTORY_PATH.write_text(new_content, encoding="utf-8")
    # We could index this too if needed, but for now let's just keep it as a log.
    # If we want the agent to 'remember' it via RAG, we should index it using a separate key or same key.
    # For now, let's index it with a distinct prefix to the same RAG.
    _index_to_rag(f"User History:\n{new_content}")


def append_to_history(section: str, content: str):
    """
    Append a new section to the history.
    """
    current = get_user_history()
    # Remove placeholder if present
    if "No history yet" in current:
        current = current.replace("No history yet", "").strip()
        
    new_data = f"\n\n## {section}\n{content}"
    update_user_history(current + new_data)
