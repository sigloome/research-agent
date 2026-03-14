from __future__ import annotations

from backend.app import _extract_skill_ingest_source, _is_text_fallback_ingest_enabled


def test_extract_skill_ingest_source_from_tool_input_event():
    event = {
        "type": "tool-input-available",
        "toolName": "skills.knowledge.paper_ingest",
        "input": {"source": "2401.12345"},
    }
    assert _extract_skill_ingest_source(event) == "2401.12345"


def test_extract_skill_ingest_source_from_arguments_field():
    event = {
        "type": "tool-input-available",
        "toolName": "skills.knowledge.paper_ingest",
        "input": {"arguments": {"source": "https://arxiv.org/abs/2402.11111"}},
    }
    assert _extract_skill_ingest_source(event) == "https://arxiv.org/abs/2402.11111"


def test_extract_skill_ingest_source_ignores_non_ingest_tools():
    event = {
        "type": "tool-input-available",
        "toolName": "skills.knowledge.search",
        "input": {"source": "2401.12345"},
    }
    assert _extract_skill_ingest_source(event) is None


def test_text_fallback_ingest_disabled_by_default(monkeypatch):
    monkeypatch.delenv("ENABLE_PAPER_TEXT_MENTION_FALLBACK", raising=False)
    assert _is_text_fallback_ingest_enabled() is False


def test_text_fallback_ingest_enabled_by_env(monkeypatch):
    monkeypatch.setenv("ENABLE_PAPER_TEXT_MENTION_FALLBACK", "true")
    assert _is_text_fallback_ingest_enabled() is True
