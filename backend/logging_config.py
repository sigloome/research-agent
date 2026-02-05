"""
Structured Logging Configuration for Velvet Research.

This module provides a centralized logging configuration using structlog.
It supports both human-readable console output (development) and JSON output (production).

Interview Talking Points:
- "I implemented structured logging with context-rich events for production observability"
- "The logger automatically includes timestamps, log levels, and caller information"
- "In production mode, logs are JSON-formatted for easy parsing by log aggregators (ELK, Datadog)"
- "Context binding allows tracking request IDs, user sessions, and research operations across calls"

Usage:
    from backend.logging_config import get_logger

    logger = get_logger(__name__)
    logger.info("research_started", query="LLM alignment", user_id="abc123")

    # With context binding (preserved across calls)
    bound_logger = logger.bind(session_id="sess-123")
    bound_logger.info("step_started", step="search")
    bound_logger.info("step_completed", step="search", papers_found=5)
"""

import logging
import os
import sys
from typing import Optional

import structlog
from structlog.typing import Processor


def configure_logging(
    level: str = "INFO",
    json_output: bool = False,
    log_file: Optional[str] = None,
) -> None:
    """
    Configure structured logging for the application.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_output: If True, output logs as JSON (for production/log aggregators)
        log_file: Optional file path to write logs to
    """
    # Determine if we're in production mode
    is_production = os.getenv("ENVIRONMENT", "development").lower() == "production"
    json_output = json_output or is_production

    # Base processors that are always applied
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if json_output:
        # Production: JSON output for log aggregators
        shared_processors.extend(
            [
                structlog.processors.format_exc_info,
                structlog.processors.JSONRenderer(),
            ]
        )
    else:
        # Development: Human-readable colored output
        shared_processors.extend(
            [
                structlog.dev.ConsoleRenderer(
                    colors=True,
                    exception_formatter=structlog.dev.plain_traceback,
                ),
            ]
        )

    # Configure structlog
    structlog.configure(
        processors=shared_processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure the standard library logging
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Create handlers
    handlers = [logging.StreamHandler(sys.stdout)]

    if log_file:
        file_handler = logging.FileHandler(log_file)
        handlers.append(file_handler)

    # Configure root logger
    logging.basicConfig(
        format="%(message)s",
        level=log_level,
        handlers=handlers,
        force=True,
    )

    # Reduce noise from third-party libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_logger(name: str = None) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger instance.

    Args:
        name: Logger name (typically __name__ from the calling module)

    Returns:
        A bound logger instance that supports context binding

    Example:
        logger = get_logger(__name__)
        logger.info("operation_started", operation="research", query="LLM")

        # Bind context for all subsequent calls
        logger = logger.bind(session_id="abc123")
        logger.info("paper_found", title="Attention Is All You Need")  # includes session_id
    """
    return structlog.get_logger(name)


# Convenience loggers for common subsystems
def get_research_logger() -> structlog.stdlib.BoundLogger:
    """Get a logger pre-configured for research operations."""
    return get_logger("research").bind(subsystem="research")


def get_rag_logger() -> structlog.stdlib.BoundLogger:
    """Get a logger pre-configured for RAG/knowledge graph operations."""
    return get_logger("rag").bind(subsystem="knowledge")


def get_api_logger() -> structlog.stdlib.BoundLogger:
    """Get a logger pre-configured for API operations."""
    return get_logger("api").bind(subsystem="api")


def get_skill_logger(skill_name: str) -> structlog.stdlib.BoundLogger:
    """Get a logger pre-configured for a specific skill."""
    return get_logger(f"skill.{skill_name}").bind(subsystem="skill", skill=skill_name)


# Initialize logging on module import with sensible defaults
# Can be reconfigured by calling configure_logging() explicitly
_initialized = False


def ensure_initialized():
    """Ensure logging is initialized (called automatically on first use)."""
    global _initialized
    if not _initialized:
        log_level = os.getenv("LOG_LEVEL", "INFO")
        json_mode = os.getenv("LOG_FORMAT", "text").lower() == "json"
        configure_logging(level=log_level, json_output=json_mode)
        _initialized = True


# Auto-initialize on import
ensure_initialized()
