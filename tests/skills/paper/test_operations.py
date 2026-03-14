"""Tests for paper fetching and local indexing behavior."""

from skills.knowledge.paper import core


def test_fetch_papers_invokes_ingest_for_new_paper(monkeypatch):
    fetched = [
        {
            "id": "2401.12345",
            "title": "Test Paper",
            "abstract": "About LLM transformers",
            "authors": ["Author A"],
            "published_date": "2024-01-01",
            "url": "https://arxiv.org/abs/2401.12345",
        }
    ]
    captured = {"ingest_calls": 0, "added": 0}

    monkeypatch.setattr(core.fetcher, "fetch_and_process", lambda *_args, **_kwargs: fetched)
    monkeypatch.setattr(core, "get_source_id_for_type", lambda *_args, **_kwargs: 1)
    monkeypatch.setattr(core.manager, "get_paper", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(core.manager, "add_paper", lambda *_args, **_kwargs: captured.__setitem__("added", captured["added"] + 1))
    monkeypatch.setattr(core, "emit", lambda *_args, **_kwargs: None)

    def _fake_ingest(source, force_update=False, source_id=None):
        captured["ingest_calls"] += 1
        assert source == "2401.12345"
        return {"ok": False, "status": "failed", "missing_fields": ["full_text_local_path"]}

    monkeypatch.setattr(core, "paper_ingest", _fake_ingest)
    results = core.fetch_papers("LLM", max_results=1)

    assert isinstance(results, list)
    assert captured["added"] == 1
    assert captured["ingest_calls"] == 1


def test_fetch_papers_skips_ingest_when_existing_is_complete(monkeypatch):
    fetched = [{"id": "2402.12345", "title": "Existing", "abstract": "x"}]
    existing = {
        "id": "2402.12345",
        "summary_main_ideas": "main",
        "summary_methods": "methods",
        "summary_results": "results",
        "summary_limitations": "limitations",
        "full_text_local_path": "/tmp/2402.12345.txt",
    }
    captured = {"ingest_calls": 0}

    monkeypatch.setattr(core.fetcher, "fetch_and_process", lambda *_args, **_kwargs: fetched)
    monkeypatch.setattr(core, "get_source_id_for_type", lambda *_args, **_kwargs: 1)
    monkeypatch.setattr(core.manager, "get_paper", lambda *_args, **_kwargs: existing)
    monkeypatch.setattr(core.manager, "add_paper", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(core, "emit", lambda *_args, **_kwargs: None)

    def _fake_ingest(*_args, **_kwargs):
        captured["ingest_calls"] += 1
        return {"ok": True}

    monkeypatch.setattr(core, "paper_ingest", _fake_ingest)
    results = core.fetch_papers("LLM", max_results=1)

    assert len(results) == 1
    assert results[0]["id"] == "2402.12345"
    assert captured["ingest_calls"] == 0


def test_extract_tags_from_abstract():
    abstract = "This paper presents a novel LLM approach using transformer attention."
    tags = core.extract_tags_from_abstract(abstract)
    assert "LLM" in tags
    assert "transformer" in tags
    assert "attention" in tags


def test_extract_tags_empty_abstract():
    tags = core.extract_tags_from_abstract("")
    assert tags == ["AI"]


def test_search_returns_list(monkeypatch):
    monkeypatch.setattr(core.manager, "search_local_papers", lambda query: [{"id": "1", "q": query}])
    results = core.search_local_papers("test query")
    assert isinstance(results, list)
    assert results[0]["q"] == "test query"
