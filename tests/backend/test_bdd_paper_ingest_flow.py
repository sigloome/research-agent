"""Executable BDD coverage for paper ingest durability contract."""

from __future__ import annotations

from skills.knowledge.db import manager


def test_bdd_paper_ingest_success_contract(monkeypatch, temp_db, tmp_path):
    """Given/When/Then: ingest succeeds only with local path + key fields."""
    from skills.knowledge.paper import core

    original_db = manager.DB_PATH
    manager.DB_PATH = temp_db
    manager.init_db()

    saved = tmp_path / "ingest.txt"
    saved.write_text("paper body", encoding="utf-8")

    monkeypatch.setattr(
        core.fetcher,
        "get_arxiv_paper_by_id",
        lambda _paper_id: {
            "id": "2402.11111",
            "title": "BDD ingest paper",
            "authors": ["A"],
            "published_date": "2024-02-01",
            "url": "https://arxiv.org/abs/2402.11111",
            "abstract": "bdd abstract",
        },
    )
    monkeypatch.setattr(core.downloader, "download_paper_content", lambda *_a, **_k: str(saved))
    monkeypatch.setattr(
        core.summarize,
        "generate_summary",
        lambda *_a, **_k: {
            "summary_main_ideas": "main",
            "summary_methods": "methods",
            "summary_results": "results",
            "summary_limitations": "limitations",
        },
    )

    # Given a valid source and available storage
    # When paper_ingest is executed
    result = core.paper_ingest("2402.11111", force_update=True)

    # Then contract returns success with durable fields
    assert result["ok"] is True
    assert result["local_path"] == str(saved)
    assert result["missing_fields"] == []

    manager.DB_PATH = original_db


def test_bdd_paper_ingest_failure_contract(monkeypatch, temp_db):
    """Given/When/Then: missing local persistence yields failure envelope."""
    from skills.knowledge.paper import core

    original_db = manager.DB_PATH
    manager.DB_PATH = temp_db
    manager.init_db()

    monkeypatch.setattr(
        core.fetcher,
        "get_arxiv_paper_by_id",
        lambda _paper_id: {
            "id": "2402.22222",
            "title": "BDD ingest fail paper",
            "authors": ["A"],
            "published_date": "2024-02-01",
            "url": "https://arxiv.org/abs/2402.22222",
            "abstract": "bdd abstract",
        },
    )
    monkeypatch.setattr(core.downloader, "download_paper_content", lambda *_a, **_k: None)

    # Given downloader cannot persist content
    # When ingest is executed
    result = core.paper_ingest("2402.22222", force_update=True)

    # Then operation must fail and not report success
    assert result["ok"] is False
    assert result["status"] == "failed"

    manager.DB_PATH = original_db
