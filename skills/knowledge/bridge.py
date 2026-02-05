import os
import numpy as np
import json
from typing import List, Dict, Any, Optional

# Import structured logging
try:
    from backend.logging_config import get_rag_logger

    logger = get_rag_logger()
except ImportError:
    import structlog

    logger = structlog.get_logger("bridge")

try:
    from anthropic import AsyncAnthropic
except ImportError:
    AsyncAnthropic = object

try:
    from sentence_transformers import SentenceTransformer

    # Initialize global model on import to avoid reloading
    # use a small, fast model
    _LOCAL_EMBED_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
    HAS_LOCAL_EMBED = True
except ImportError:
    _LOCAL_EMBED_MODEL = None
    HAS_LOCAL_EMBED = False
    logger.warning(
        "sentence_transformers_missing", hint="Embeddings will fail. Install sentence-transformers."
    )

# Constants for Anthropic
ANTHROPIC_BASE_URL = os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
ANTHROPIC_AUTH_TOKEN = os.environ.get("ANTHROPIC_AUTH_TOKEN")
# Default model for knowledge operations - fast but capable
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-3-haiku-20240307")


def get_anthropic_async_client():
    if not ANTHROPIC_AUTH_TOKEN:
        raise ValueError("ANTHROPIC_AUTH_TOKEN not found in environment")

    return AsyncAnthropic(api_key=ANTHROPIC_AUTH_TOKEN, base_url=ANTHROPIC_BASE_URL)


async def anthropic_complete_if_cache(
    prompt: str, system_prompt: str = None, history_messages: list = [], **kwargs
) -> str:
    """
    Custom completion function for LightRAG using Anthropic.
    """
    client = get_anthropic_async_client()

    messages = []
    if history_messages:
        messages.extend(history_messages)
    messages.append({"role": "user", "content": prompt})

    model_to_use = kwargs.get("model") or ANTHROPIC_MODEL

    try:
        # Remove incompatible args that might come from other integrations
        excluded_keys = ["model", "hashing_kv", "keyword_extraction", "json_model", "enable_cot"]
        client_kwargs = {k: v for k, v in kwargs.items() if k not in excluded_keys}

        response = await client.messages.create(
            model=model_to_use,
            system=system_prompt if system_prompt else "",
            messages=messages,
            max_tokens=kwargs.get("max_tokens", 4096),
            **client_kwargs
        )
        return response.content[0].text
    except Exception as e:
        logger.error("completion_failed", error=str(e))
        raise e


async def local_embedding(texts: list[str]) -> np.ndarray:
    """
    Local embedding using sentence-transformers.
    Robust, free, offline-capable.
    """
    if not HAS_LOCAL_EMBED:
        logger.warning(
            "local_embedding_unavailable", hint="Using random mock embeddings for system continuity"
        )
        # Return random vectors of dimension 384 (all-MiniLM-L6-v2 size)
        return np.random.rand(len(texts), 384)

    try:
        # SentenceTransformer encode returns ndarray by default
        embeddings = _LOCAL_EMBED_MODEL.encode(texts)
        return embeddings
    except Exception as e:
        logger.error("embedding_failed", error=str(e))
        logger.warning("embedding_fallback", hint="Using random embeddings due to error")
        return np.random.rand(len(texts), 384)
