from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Iterable, List, Set


DEFAULT_MANIFEST = Path(__file__).resolve().parents[1] / "evals/datasets/paper_benchmark/manifest_v1.json"
DEFAULT_SOURCE_DB = Path(__file__).resolve().parents[1] / "data/papers.db"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl_rows(path: Path) -> List[dict]:
    rows: List[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def collect_referenced_paper_ids(rows: Iterable[dict]) -> List[str]:
    paper_ids: Set[str] = set()
    for row in rows:
        for paper_id in row.get("seed_paper_ids", []) or []:
            if isinstance(paper_id, str):
                paper_ids.add(paper_id)
        expect = row.get("expect", {})
        if not isinstance(expect, dict):
            continue
        for key in ("required_paper_ids", "support_paper_ids", "contradict_paper_ids"):
            for paper_id in expect.get(key, []) or []:
                if isinstance(paper_id, str):
                    paper_ids.add(paper_id)
        clusters = expect.get("required_clusters", {})
        if isinstance(clusters, dict):
            for ids in clusters.values():
                for paper_id in ids or []:
                    if isinstance(paper_id, str):
                        paper_ids.add(paper_id)
    return sorted(paper_ids)


def resolve_snapshot_path(manifest: dict) -> Path:
    core = manifest["tiers"]["core"]
    return Path(core["snapshot_path"])


def build_snapshot(source_db: Path, manifest_path: Path, output_path: Path | None = None) -> dict:
    manifest = load_json(manifest_path)
    dataset_paths = [Path(cfg["file"]) for cfg in manifest["tiers"].values()]
    rows: List[dict] = []
    for path in dataset_paths:
        rows.extend(load_jsonl_rows(path))
    paper_ids = collect_referenced_paper_ids(rows)
    output_path = output_path or resolve_snapshot_path(manifest)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        output_path.unlink()

    src = sqlite3.connect(source_db)
    src.row_factory = sqlite3.Row
    dst = sqlite3.connect(output_path)
    try:
        src_cursor = src.cursor()
        dst_cursor = dst.cursor()
        schema_rows = src_cursor.execute(
            "SELECT name, sql FROM sqlite_master WHERE type='table' AND name IN ('library_sources', 'papers')"
        ).fetchall()
        for row in schema_rows:
            dst_cursor.execute(row["sql"])

        source_rows = src_cursor.execute("SELECT * FROM library_sources").fetchall()
        if source_rows:
            columns = source_rows[0].keys()
            placeholders = ",".join("?" for _ in columns)
            dst_cursor.executemany(
                f"INSERT INTO library_sources ({','.join(columns)}) VALUES ({placeholders})",
                [tuple(r[c] for c in columns) for r in source_rows],
            )

        if paper_ids:
            placeholders = ",".join("?" for _ in paper_ids)
            paper_rows = src_cursor.execute(
                f"SELECT * FROM papers WHERE id IN ({placeholders})",
                paper_ids,
            ).fetchall()
        else:
            paper_rows = []

        if paper_rows:
            columns = paper_rows[0].keys()
            placeholders = ",".join("?" for _ in columns)
            dst_cursor.executemany(
                f"INSERT INTO papers ({','.join(columns)}) VALUES ({placeholders})",
                [tuple(r[c] for c in columns) for r in paper_rows],
            )
        dst.commit()
    finally:
        src.close()
        dst.close()

    return {
        "output_path": str(output_path),
        "paper_count": len(paper_ids),
        "paper_ids": paper_ids,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build frozen paper benchmark snapshot from source DB")
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--source-db", default=str(DEFAULT_SOURCE_DB))
    parser.add_argument("--output")
    args = parser.parse_args()

    result = build_snapshot(
        source_db=Path(args.source_db),
        manifest_path=Path(args.manifest),
        output_path=Path(args.output) if args.output else None,
    )
    print(result)


if __name__ == "__main__":
    main()
