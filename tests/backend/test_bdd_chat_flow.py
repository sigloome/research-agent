"""Executable BDD coverage for chat stream, tool trace, and persistence."""

from __future__ import annotations

import json
import sys
import types
from typing import AsyncGenerator

import pytest
from fastapi.testclient import TestClient

from skills.knowledge.db import manager


@pytest.fixture
def client(temp_db):
    if "sentence_transformers" not in sys.modules:
        stub_mod = types.ModuleType("sentence_transformers")

        class _StubSentenceTransformer:
            def __init__(self, *_args, **_kwargs):
                pass

            def encode(self, texts):
                size = len(texts) if texts is not None else 0
                return [[0.0] * 384 for _ in range(size)]

        stub_mod.SentenceTransformer = _StubSentenceTransformer
        sys.modules["sentence_transformers"] = stub_mod

    original_path = manager.DB_PATH
    manager.DB_PATH = temp_db
    manager.init_db()

    from backend import app as backend_app
    from unittest.mock import AsyncMock

    backend_app.agent.initialize = AsyncMock()

    with TestClient(backend_app.app) as test_client:
        yield test_client

    manager.DB_PATH = original_path


def _make_stream_chunk(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def test_bdd_stream_contract_and_done_marker(client):
    """Given/When/Then: stream returns finish and [DONE] contract markers."""
    from backend import app as backend_app

    async def fake_generator(*_args, **_kwargs) -> AsyncGenerator[str, None]:
        yield _make_stream_chunk({"type": "start"})
        yield _make_stream_chunk({"type": "text-delta", "delta": "hello"})
        yield _make_stream_chunk({"type": "finish", "finishReason": "stop"})

    backend_app.agent.chat_generator = fake_generator

    chat = client.post("/api/chats", json={"title": "BDD stream"})
    chat_id = chat.json()["id"]

    # Given an existing chat and a user message
    payload = {"message": "test stream contract", "session_id": chat_id}
    # When /api/chat is called
    response = client.post("/api/chat", json=payload)
    body = response.text

    # Then stream includes finish and [DONE]
    assert response.status_code == 200
    assert '"type": "finish"' in body
    assert "data: [DONE]" in body


def test_bdd_tool_trace_events_visible_in_stream(client):
    """Given/When/Then: tool-input/tool-output events are preserved in stream."""
    from backend import app as backend_app

    async def fake_generator(*_args, **_kwargs) -> AsyncGenerator[str, None]:
        yield _make_stream_chunk(
            {"type": "tool-input-start", "toolCallId": "call-1", "toolName": "Skill"}
        )
        yield _make_stream_chunk(
            {
                "type": "tool-input-available",
                "toolCallId": "call-1",
                "toolName": "Skill",
                "input": {"action": "run", "skill": "knowledge"},
            }
        )
        yield _make_stream_chunk(
            {"type": "tool-output-available", "toolCallId": "call-1", "output": {"ok": True}}
        )
        yield _make_stream_chunk({"type": "finish", "finishReason": "stop"})

    backend_app.agent.chat_generator = fake_generator

    chat = client.post("/api/chats", json={"title": "BDD tool trace"})
    chat_id = chat.json()["id"]

    # Given a request expected to use tools
    payload = {"message": "use knowledge skill", "session_id": chat_id}
    # When /api/chat is called
    response = client.post("/api/chat", json=payload)
    body = response.text

    # Then tool trace events are present
    assert response.status_code == 200
    assert '"type": "tool-input-start"' in body
    assert '"type": "tool-input-available"' in body
    assert '"type": "tool-output-available"' in body


def test_bdd_chat_history_persists_user_and_assistant(client):
    """Given/When/Then: assistant response is persisted after stream completion."""
    from backend import app as backend_app

    async def fake_generator(*_args, **_kwargs) -> AsyncGenerator[str, None]:
        yield _make_stream_chunk({"type": "text-delta", "delta": "Persisted answer"})
        yield _make_stream_chunk({"type": "finish", "finishReason": "stop"})

    backend_app.agent.chat_generator = fake_generator

    chat = client.post("/api/chats", json={"title": "BDD persistence"})
    chat_id = chat.json()["id"]

    # Given a new chat session
    payload = {"message": "save this conversation", "session_id": chat_id}
    # When user sends a message and stream completes
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200

    # Then user+assistant messages are persisted in chat history
    history_resp = client.get(f"/api/chats/{chat_id}")
    history = history_resp.json()
    assert history_resp.status_code == 200
    assert len(history) >= 2
    assert history[0]["role"] == "user"
    assert history[-1]["role"] == "assistant"
    assert history[-1]["content"] == "Persisted answer"


def test_bdd_skill_triggered_paper_ingest_runs_without_text_fallback(client, monkeypatch):
    """Given/When/Then: ingest runs from skill event, not from text mention fallback."""
    from backend import app as backend_app

    called = {"skill_sources": None, "fallback_text": None}

    async def fake_generator(*_args, **_kwargs) -> AsyncGenerator[str, None]:
        yield _make_stream_chunk(
            {
                "type": "tool-input-available",
                "toolCallId": "call-ingest",
                "toolName": "skills.knowledge.paper_ingest",
                "input": {"source": "2401.12345"},
            }
        )
        yield _make_stream_chunk({"type": "text-delta", "delta": "Mention 2401.12345 in answer."})
        yield _make_stream_chunk({"type": "finish", "finishReason": "stop"})

    async def fake_run_skill_ingest(sources):
        called["skill_sources"] = list(sources)

    async def fake_text_fallback(_text):
        called["fallback_text"] = "called"

    backend_app.agent.chat_generator = fake_generator
    monkeypatch.setattr(backend_app, "_run_skill_triggered_ingest", fake_run_skill_ingest)
    monkeypatch.setattr(backend_app, "_auto_ingest_papers_from_response", fake_text_fallback)
    monkeypatch.delenv("ENABLE_PAPER_TEXT_MENTION_FALLBACK", raising=False)

    chat = client.post("/api/chats", json={"title": "BDD skill ingest"})
    chat_id = chat.json()["id"]
    response = client.post("/api/chat", json={"message": "ingest it", "session_id": chat_id})
    assert response.status_code == 200

    assert called["skill_sources"] == ["2401.12345"]
    assert called["fallback_text"] is None


def test_bdd_no_skill_event_does_not_auto_ingest_from_text_when_fallback_disabled(client, monkeypatch):
    """Given/When/Then: text mention alone does not trigger ingest when fallback is off."""
    from backend import app as backend_app

    called = {"skill_sources": None, "fallback_text": None}

    async def fake_generator(*_args, **_kwargs) -> AsyncGenerator[str, None]:
        yield _make_stream_chunk({"type": "text-delta", "delta": "See 2401.54321."})
        yield _make_stream_chunk({"type": "finish", "finishReason": "stop"})

    async def fake_run_skill_ingest(sources):
        called["skill_sources"] = list(sources)

    async def fake_text_fallback(_text):
        called["fallback_text"] = "called"

    backend_app.agent.chat_generator = fake_generator
    monkeypatch.setattr(backend_app, "_run_skill_triggered_ingest", fake_run_skill_ingest)
    monkeypatch.setattr(backend_app, "_auto_ingest_papers_from_response", fake_text_fallback)
    monkeypatch.delenv("ENABLE_PAPER_TEXT_MENTION_FALLBACK", raising=False)

    chat = client.post("/api/chats", json={"title": "BDD no fallback"})
    chat_id = chat.json()["id"]
    response = client.post("/api/chat", json={"message": "just mention", "session_id": chat_id})
    assert response.status_code == 200

    assert called["skill_sources"] is None
    assert called["fallback_text"] is None
