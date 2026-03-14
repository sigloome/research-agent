from __future__ import annotations

import json
from pathlib import Path

from skills.knowledge.db import manager


def _mock_summary() -> dict:
    return {
        "tags": ["LLM"],
        "summary_main_ideas": "main",
        "summary_methods": "methods",
        "summary_results": "results",
        "summary_limitations": "limitations",
    }


def test_paper_ingest_success_and_retrieval(monkeypatch, temp_db, tmp_path):
    from skills.knowledge.paper import core

    original_db = manager.DB_PATH
    manager.DB_PATH = temp_db
    manager.init_db()

    text_path = tmp_path / "2401.12345.txt"
    text_path.write_text("Full Text Content", encoding="utf-8")

    monkeypatch.setattr(
        core.fetcher,
        "get_arxiv_paper_by_id",
        lambda _paper_id: {
            "id": "2401.12345",
            "title": "Contract Test Paper",
            "authors": ["A"],
            "published_date": "2024-01-01",
            "url": "https://arxiv.org/abs/2401.12345",
            "abstract": "A paper about contract tests",
        },
    )
    monkeypatch.setattr(
        core.downloader,
        "download_paper_content",
        lambda *_args, **_kwargs: str(text_path),
    )
    monkeypatch.setattr(core.summarize, "generate_summary", lambda *_args, **_kwargs: _mock_summary())

    result = core.paper_ingest("2401.12345", force_update=True)
    assert result["ok"] is True
    assert result["paper_id"] == "2401.12345"
    assert result["local_path"] == str(text_path)

    hits = manager.search_local_papers("Contract Test Paper")
    assert any(p.get("id") == "2401.12345" for p in hits)

    manager.DB_PATH = original_db


def test_paper_ingest_failure_on_missing_local_persistence(monkeypatch, temp_db):
    from skills.knowledge.paper import core

    original_db = manager.DB_PATH
    manager.DB_PATH = temp_db
    manager.init_db()

    monkeypatch.setattr(
        core.fetcher,
        "get_arxiv_paper_by_id",
        lambda _paper_id: {
            "id": "2401.54321",
            "title": "Fail Test Paper",
            "authors": ["A"],
            "published_date": "2024-01-01",
            "url": "https://arxiv.org/abs/2401.54321",
            "abstract": "A paper expected to fail ingest",
        },
    )
    monkeypatch.setattr(core.downloader, "download_paper_content", lambda *_args, **_kwargs: None)

    result = core.paper_ingest("2401.54321", force_update=True)
    assert result["ok"] is False
    assert result["status"] == "failed"

    manager.DB_PATH = original_db


def test_paper_ingest_accepts_versioned_id(monkeypatch, temp_db, tmp_path):
    from skills.knowledge.paper import core

    original_db = manager.DB_PATH
    manager.DB_PATH = temp_db
    manager.init_db()

    text_path = tmp_path / "2602.04879.txt"
    text_path.write_text("Full Text Content", encoding="utf-8")

    def _fake_get_by_id(arxiv_id):
        assert arxiv_id == "2602.04879"
        return {
            "id": "2602.04879",
            "title": "Versioned Test Paper",
            "authors": ["A"],
            "published_date": "2024-01-01",
            "url": "https://arxiv.org/abs/2602.04879",
            "abstract": "A paper about versioned IDs",
        }

    monkeypatch.setattr(core.fetcher, "get_arxiv_paper_by_id", _fake_get_by_id)
    monkeypatch.setattr(
        core.downloader,
        "download_paper_content",
        lambda *_args, **_kwargs: str(text_path),
    )
    monkeypatch.setattr(core.summarize, "generate_summary", lambda *_args, **_kwargs: _mock_summary())

    result = core.paper_ingest("2602.04879v1", force_update=True)
    assert result["ok"] is True
    assert result["paper_id"] == "2602.04879"

    manager.DB_PATH = original_db
