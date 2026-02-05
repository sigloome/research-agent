from backend.event_bus import subscribe, EventType, Event
from skills.knowledge.graph_rag import index_text

# Import structured logging
try:
    from backend.logging_config import get_skill_logger

    logger = get_skill_logger("knowledge")
except ImportError:
    import structlog

    logger = structlog.get_logger("knowledge")


def on_paper_added(event: Event):
    """
    Handler for PAPER_ADDED event.
    Extracts content from payload and indexes it into the Knowledge Graph.
    """
    logger.info("paper_added_event_received", source=event.source)
    payload = event.payload

    if isinstance(payload, dict) and "content" in payload:
        content = payload["content"]
        logger.debug("indexing_content", preview=content[:50])
        try:
            index_text(content)
            logger.info("paper_indexed_successfully")
        except Exception as e:
            logger.error("paper_indexing_failed", error=str(e))
    else:
        logger.warning("invalid_payload_format")


def register_handlers():
    """Register all knowledge-related handlers."""
    subscribe(EventType.PAPER_ADDED, on_paper_added)
    logger.info("event_handlers_registered")
