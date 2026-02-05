import os
import logging
from pathlib import Path
from typing import Optional, List, Union

# Import structured logging
try:
    from backend.logging_config import get_rag_logger

    logger = get_rag_logger()
except ImportError:
    # Fallback to basic logging if backend not available
    import structlog

    logger = structlog.get_logger("rag")

# Import our custom bridge - independent of LightRAG
try:
    from skills.knowledge.bridge import anthropic_complete_if_cache, local_embedding
except ImportError as e:
    logger.error("bridge_import_failed", error=str(e))
    anthropic_complete_if_cache = None
    local_embedding = None

try:
    from lightrag import LightRAG, QueryParam
    from lightrag.utils import EmbeddingFunc
except ImportError:
    # Fallback or error handling if not installed
    logger.error("lightrag_not_installed", hint="Run 'pip install lightrag-hku'")
    LightRAG = object
    QueryParam = object

# Global instances storage
_RAG_INSTANCES = {}
_SYNC_LOOP = None


def _get_sync_loop():
    global _SYNC_LOOP
    import asyncio

    if _SYNC_LOOP is None or _SYNC_LOOP.is_closed():
        _SYNC_LOOP = asyncio.new_event_loop()
        asyncio.set_event_loop(_SYNC_LOOP)
    return _SYNC_LOOP


def initialize_rag(
    name: str = "knowledge",
    working_dir: str = "./data/graph_rag",
    llm_model: str = "gpt-4o-mini",
    embedding_model: str = "text-embedding-3-small",
) -> LightRAG:
    """
    Initialize the LightRAG instance.
    """
    global _RAG_INSTANCES

    # Ensure directory exists
    work_path = Path(working_dir)
    work_path.mkdir(parents=True, exist_ok=True)

    if name not in _RAG_INSTANCES:
        logger.info("rag_initializing", name=name, path=str(work_path.absolute()))

        # NOTE: LightRAG defaults to specific OpenAI functions.
        # For this prototype, we assume the user has OPENAI_API_KEY set or is using a compatible env.
        # Deep customization to use Anthropic would require defining custom binding functions here.

        rag_instance = LightRAG(
            working_dir=str(work_path),
            llm_model_func=anthropic_complete_if_cache,  # Use Anthropic Bridge
            embedding_func=EmbeddingFunc(
                embedding_dim=384,  # Updated for all-MiniLM-L6-v2
                max_token_size=8192,
                func=local_embedding,  # Use Local Bridge
            ),
        )

        # Initialize storage (async)
        # Handle running loop case
        import asyncio

        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                logger.debug("rag_init_async", name=name)
                loop.create_task(rag_instance.initialize_storages())
                _RAG_INSTANCES[name] = rag_instance
                return rag_instance
        except RuntimeError:
            pass

        # Sync case
        try:
            logger.debug("rag_init_sync", name=name)
            loop = _get_sync_loop()
            loop.run_until_complete(rag_instance.initialize_storages())
            _RAG_INSTANCES[name] = rag_instance
        except Exception as e:
            logger.error("rag_init_failed", name=name, error=str(e))

    return _RAG_INSTANCES.get(name)


def get_rag(name: str = "knowledge") -> Optional[LightRAG]:
    return _RAG_INSTANCES.get(name)


def index_text(text: str, rag_name: str = "knowledge"):
    """
    Index text into the graph.
    Auto-detects if running in async loop to avoid blocking errors.
    """
    import asyncio

    rag = _RAG_INSTANCES.get(rag_name)
    if not rag:
        if rag_name == "knowledge":
            # Auto-initialize default if missing
            rag = initialize_rag()
        else:
            raise ValueError(
                f"GraphRAG '{rag_name}' not initialized. Call initialize_rag(name='{rag_name}', ...) first."
            )

    try:
        # Check if there is a running loop
        loop = asyncio.get_running_loop()
        if loop.is_running():
            # If we are in an async loop, we cannot block.
            # We schedule the task to run in the background.
            logger.debug("indexing_scheduled_async", rag_name=rag_name)
            loop.create_task(rag.ainsert(text))
            return
    except RuntimeError:
        pass

    # If no loop is running, we can block uses our strict sync loop
    try:
        logger.debug("indexing_sync", rag_name=rag_name)
        loop = _get_sync_loop()
        loop.run_until_complete(rag.ainsert(text))
    except Exception as e:
        logger.error("indexing_failed", rag_name=rag_name, error=str(e))


def index_file(file_path: str, rag_name: str = "knowledge"):
    """
    Read a file and ingest it.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        content = path.read_text(encoding="utf-8")
        index_text(content, rag_name=rag_name)
    except Exception as e:
        logger.error("file_indexing_failed", file_path=file_path, error=str(e))
        # Simplistic PDF support could be added here
        raise


def query_rag(query: str, mode: str = "global", rag_name: str = "knowledge") -> str:
    """
    Query the GraphRAG system.
    Modes: 'naive', 'local', 'global', 'hybrid'
    """
    rag = _RAG_INSTANCES.get(rag_name)
    if not rag:
        # Try auto-init for default
        if rag_name == "knowledge":
            rag = initialize_rag()

        if not rag:
            raise RuntimeError(f"GraphRAG '{rag_name}' not initialized")

    logger.info("rag_query", rag_name=rag_name, mode=mode, query=query[:100])
    logger.debug("rag_query_debug", working_dir=rag.working_dir)

    import asyncio
    import inspect

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = _get_sync_loop()

    try:
        param = QueryParam(mode=mode)
        response = rag.query(query, param=param)

        if inspect.isawaitable(response):
            result = loop.run_until_complete(response)
        else:
            result = response

        return result
    except Exception as e:
        logger.error("rag_query_failed", rag_name=rag_name, error=str(e))
        return f"Error executing GraphRAG query: {e}"


def reset_rag(name: str = None):
    """Force re-initialization (useful for testing)"""
    global _RAG_INSTANCES
    if name:
        if name in _RAG_INSTANCES:
            del _RAG_INSTANCES[name]
    else:
        _RAG_INSTANCES = {}
