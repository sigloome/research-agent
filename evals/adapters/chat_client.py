"""Chat client adapters for fixture replay and optional API streaming."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Iterator, List, Protocol

import httpx


class ChatClient(Protocol):
    """Protocol for chat stream producers used by eval runners."""

    def stream(self, task_id: str, message: str, session_id: str = "default") -> Iterable[str]:
        """Yield raw stream chunks for a task input."""


@dataclass
class FixtureChatClient:
    """Deterministic fixture-backed client for PR/nightly tests."""

    fixture_streams: Dict[str, List[str]]

    def stream(self, task_id: str, message: str, session_id: str = "default") -> Iterator[str]:
        del message
        del session_id
        chunks = self.fixture_streams.get(task_id, [])
        for chunk in chunks:
            yield chunk


@dataclass
class HttpChatClient:
    """Thin adapter around `/api/chat` for optional integration runs."""

    base_url: str
    timeout_seconds: float = 20.0

    def stream(self, task_id: str, message: str, session_id: str = "default") -> Iterator[str]:
        del task_id
        with httpx.Client(base_url=self.base_url, timeout=self.timeout_seconds) as client:
            with client.stream(
                "POST",
                "/api/chat",
                json={"message": message, "session_id": session_id},
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line:
                        yield line
