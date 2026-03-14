from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from scripts.build_paper_benchmark_snapshot import build_snapshot


def _write_source_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    c = conn.cursor()
    c.execute(
        "CREATE TABLE library_sources (id INTEGER PRIMARY KEY, name TEXT, source_type TEXT, config TEXT, description TEXT, icon TEXT, enabled INTEGER, created_at TEXT)"
    )
    c.execute(
        "CREATE TABLE papers (id TEXT PRIMARY KEY, title TEXT, authors TEXT, published_date TEXT, url TEXT, abstract TEXT, citation_count INTEGER, last_metadata_update TEXT, tags TEXT, summary_main_ideas TEXT, summary_methods TEXT, summary_results TEXT, summary_limitations TEXT, content_source TEXT, full_text_local_path TEXT, source_id INTEGER, created_at TEXT)"
    )
    c.execute(
        "INSERT INTO library_sources VALUES (1, 'ArXiv', 'arxiv', '{}', 'ArXiv', '📄', 1, '2026-03-14')"
    )
    for paper_id in ("p1", "p2", "p3"):
        c.execute(
            "INSERT INTO papers VALUES (?, ?, '[]', '2026-03-14', ?, '', 0, '2026-03-14', '[]', '', '', '', '', 'full_text', ?, 1, '2026-03-14')",
            (paper_id, f"Title {paper_id}", f"https://example.com/{paper_id}", f"/paper/{paper_id}.txt"),
        )
    conn.commit()
    conn.close()


def test_build_snapshot_copies_only_referenced_papers(tmp_path: Path):
    source_db = tmp_path / "source.sqlite"
    _write_source_db(source_db)

    dataset_dir = tmp_path / "datasets"
    dataset_dir.mkdir(parents=True)
    core = dataset_dir / "core.jsonl"
    core.write_text(
        '{"id":"c1","seed_paper_ids":["p1"],"expect":{"required_paper_ids":["p2"]}}\n',
        encoding="utf-8",
    )
    full = dataset_dir / "full.jsonl"
    full.write_text('{"id":"f1","seed_paper_ids":["p3"]}\n', encoding="utf-8")
    audit = dataset_dir / "audit.jsonl"
    audit.write_text('', encoding="utf-8")

    output = tmp_path / "snapshot.sqlite"
    manifest = {
        "tiers": {
            "core": {"file": str(core), "snapshot_path": str(output)},
            "full": {"file": str(full), "snapshot_path": str(output)},
            "audit": {"file": str(audit), "snapshot_path": str(output)},
        }
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    result = build_snapshot(source_db=source_db, manifest_path=manifest_path, output_path=output)
    assert result["paper_count"] == 3
    conn = sqlite3.connect(output)
    rows = conn.execute("SELECT id FROM papers ORDER BY id").fetchall()
    conn.close()
    assert [row[0] for row in rows] == ["p1", "p2", "p3"]
