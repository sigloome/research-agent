from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from backend.app import app, _extract_arxiv_ids


@pytest.fixture
def client():
    return TestClient(app)


def test_extract_arxiv_ids_normalizes_versions():
    ids = _extract_arxiv_ids("check 2602.04879v1 and 2602.04879 and 2602.04880v2")
    assert ids == ["2602.04879", "2602.04880"]


def test_get_paper_details_accepts_versioned_id(client):
    with patch("backend.app.manager.get_paper") as mock_get, patch(
        "backend.app.manager.get_paper_full_text"
    ) as mock_full:
        mock_get.return_value = {"id": "2602.04879", "title": "t"}
        mock_full.return_value = None

        response = client.get("/api/paper/2602.04879v1")

    assert response.status_code == 200
    mock_get.assert_called_once_with("2602.04879")
    mock_full.assert_called_once_with("2602.04879")


def test_fetch_paper_uses_canonical_id(client, monkeypatch):
    from skills.knowledge.paper import core as paper_core

    captured = {}

    def _fake_ingest(source, force_update=False):
        captured["source"] = source
        return {"ok": True, "paper_id": source}

    monkeypatch.setattr(paper_core, "paper_ingest", _fake_ingest)
    response = client.post("/api/paper/2602.04879v2/fetch")
    assert response.status_code == 200
    assert captured["source"] == "2602.04879"


def test_read_paper_accepts_versioned_id(client):
    with patch("backend.app.manager.get_paper") as mock_get:
        mock_get.return_value = {"id": "2602.04879", "title": "x"}
        response = client.get("/api/papers/2602.04879v3")
    assert response.status_code == 200
    mock_get.assert_called_once_with("2602.04879")
