from __future__ import annotations

import json
import hashlib
import sqlite3
import sys
import types
from pathlib import Path

import pytest

from evals.runners.run_suite import build_paper_benchmark_plan, execute_paper_benchmark_suite


def _install_runtime_stubs() -> None:
    class _Logger:
        def info(self, *_args, **_kwargs):
            return None

        def warning(self, *_args, **_kwargs):
            return None

        def error(self, *_args, **_kwargs):
            return None

        def debug(self, *_args, **_kwargs):
            return None

    if "backend.logging_config" not in sys.modules:
        logging_mod = types.ModuleType("backend.logging_config")
        logging_mod.get_logger = lambda *_args, **_kwargs: _Logger()
        logging_mod.get_rag_logger = lambda *_args, **_kwargs: _Logger()
        sys.modules["backend.logging_config"] = logging_mod
    if "structlog" not in sys.modules:
        structlog = types.ModuleType("structlog")
        structlog.get_logger = lambda *_args, **_kwargs: _Logger()
        sys.modules["structlog"] = structlog
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
    if "claude_agent_sdk" not in sys.modules:
        sdk_mod = types.ModuleType("claude_agent_sdk")

        class ClaudeAgentOptions:
            def __init__(self, **_kwargs):
                pass

        async def query(*_args, **_kwargs):
            if False:
                yield None

        sdk_mod.ClaudeAgentOptions = ClaudeAgentOptions
        sdk_mod.query = query
        sys.modules["claude_agent_sdk"] = sdk_mod


def _write_manifest(tmp_path: Path, *, with_snapshot: bool = True) -> Path:
    dataset_dir = tmp_path / "datasets"
    dataset_dir.mkdir(parents=True, exist_ok=True)
    core_file = dataset_dir / "core_v1.jsonl"
    core_file.write_text(
        '{"id":"PBR-001","seed_paper_ids":["PBR-001"],"expect":{"required_paper_ids":["PBR-001"]}}\n',
        encoding="utf-8",
    )
    full_file = dataset_dir / "full_v1.jsonl"
    full_file.write_text(
        '{"id":"PBR-002","seed_paper_ids":["PBR-002"],"expect":{"required_paper_ids":["PBR-002"]}}\n',
        encoding="utf-8",
    )
    audit_file = dataset_dir / "audit_v1.jsonl"
    audit_file.write_text(
        '{"id":"PBR-003","seed_paper_ids":["PBR-003"],"expect":{"required_paper_ids":["PBR-003"]}}\n',
        encoding="utf-8",
    )

    def _sha(path: Path) -> str:
        return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()

    snapshot_path = tmp_path / "fixtures" / "snapshots" / "papers_snapshot_v1.sqlite"
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    if with_snapshot:
        conn = sqlite3.connect(snapshot_path)
        c = conn.cursor()
        c.execute("CREATE TABLE papers (id TEXT PRIMARY KEY)")
        for paper_id in ("PBR-001", "PBR-002", "PBR-003"):
            c.execute("INSERT INTO papers (id) VALUES (?)", (paper_id,))
        conn.commit()
        conn.close()

    manifest = {
        "dataset_version": "paper_bench_v1",
        "default_seed": 42,
        "tiers": {
            "core": {
                "file": str(core_file),
                "sample_count": 1,
                "snapshot_id": "papers_snapshot_v1",
                "snapshot_path": str(snapshot_path),
                "hash": _sha(core_file),
                "blocking": True,
                "budget": {
                    "sample_count_max": 24,
                    "mean_total_tokens_max": 5000,
                    "p95_latency_ms_max": 8000,
                    "timeout_rate_max": 0.0,
                },
            },
            "full": {
                "file": str(full_file),
                "sample_count": 1,
                "snapshot_id": "papers_snapshot_v1",
                "snapshot_path": str(snapshot_path),
                "hash": _sha(full_file),
                "blocking": True,
                "budget": {
                    "sample_count_max": 72,
                    "mean_total_tokens_max": 7000,
                    "p95_latency_ms_max": 12000,
                    "timeout_rate_max": 0.02,
                },
            },
            "audit": {
                "file": str(audit_file),
                "sample_count": 1,
                "snapshot_id": "papers_snapshot_v1",
                "snapshot_path": str(snapshot_path),
                "hash": _sha(audit_file),
                "blocking": False,
                "budget": {
                    "sample_count_max": 24,
                    "mean_total_tokens_max": 7000,
                    "p95_latency_ms_max": 12000,
                    "timeout_rate_max": 0.02,
                },
            },
        },
        "params_signatures": {
            "baseline": {"topk": 20, "graph_hop": 0, "max_evidence_per_paper": 2},
            "hybrid": {"topk": 24, "graph_hop": 0, "max_evidence_per_paper": 3},
        },
    }
    manifest_path = tmp_path / "paper_benchmark_manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return manifest_path


def test_build_paper_benchmark_plan_core_requires_snapshot_and_signature(tmp_path: Path):
    manifest_path = _write_manifest(tmp_path)
    plan = build_paper_benchmark_plan(
        suite="paper_core",
        manifest_path=manifest_path,
        params_signature_name="baseline",
        git_commit="deadbeef",
    )
    assert plan["suite"] == "paper_core"
    assert plan["tier"] == "core"
    assert plan["blocking"] is True
    assert plan["signature"]["dataset_version"] == "paper_bench_v1"
    assert plan["signature"]["snapshot_id"] == "papers_snapshot_v1"
    assert plan["budget"]["sample_count_max"] == 24
    assert "PBR-001" in plan["referenced_paper_ids"]



def test_build_paper_benchmark_plan_fails_when_blocking_snapshot_missing(tmp_path: Path):
    manifest_path = _write_manifest(tmp_path, with_snapshot=False)
    with pytest.raises(ValueError, match="snapshot restore precondition failed"):
        build_paper_benchmark_plan(
            suite="paper_core",
            manifest_path=manifest_path,
            params_signature_name="baseline",
            git_commit="deadbeef",
        )



def test_build_paper_benchmark_plan_marks_audit_non_blocking(tmp_path: Path):
    manifest_path = _write_manifest(tmp_path)
    plan = build_paper_benchmark_plan(
        suite="paper_audit",
        manifest_path=manifest_path,
        params_signature_name="baseline",
        git_commit="deadbeef",
    )
    assert plan["tier"] == "audit"
    assert plan["blocking"] is False


def test_build_paper_benchmark_plan_fails_when_snapshot_missing_referenced_ids(tmp_path: Path):
    manifest_path = _write_manifest(tmp_path)
    snapshot_path = tmp_path / "fixtures" / "snapshots" / "papers_snapshot_v1.sqlite"
    conn = sqlite3.connect(snapshot_path)
    c = conn.cursor()
    c.execute("DELETE FROM papers WHERE id = ?", ("PBR-001",))
    conn.commit()
    conn.close()
    with pytest.raises(ValueError, match="snapshot missing referenced paper ids"):
        build_paper_benchmark_plan(
            suite="paper_core",
            manifest_path=manifest_path,
            params_signature_name="baseline",
            git_commit="deadbeef",
        )


def test_execute_paper_benchmark_suite_runs_runtime_and_scores_cases(tmp_path: Path):
    _install_runtime_stubs()
    manifest_path = _write_manifest(tmp_path)
    summary = execute_paper_benchmark_suite(
        suite="paper_core",
        manifest_path=manifest_path,
        params_signature_name="baseline",
        git_commit="deadbeef",
    )
    assert summary["suite"] == "paper_core"
    assert summary["signature_evaluation"]["comparable"] is True
    assert summary["aggregate_scores"]["paper_recall"] == 1.0
    assert summary["aggregate_scores"]["sample_count"] == 1.0
    assert summary["budget_evaluation"]["should_fail"] is False
    assert summary["case_results"][0]["scores"]["paper_recall"] == 1.0


def test_build_paper_benchmark_plan_supports_hybrid_signature(tmp_path: Path):
    manifest_path = _write_manifest(tmp_path)
    plan = build_paper_benchmark_plan(
        suite="paper_core",
        manifest_path=manifest_path,
        params_signature_name="hybrid",
        git_commit="deadbeef",
    )
    assert plan["signature"]["params_signature"] == '{"graph_hop": 0, "max_evidence_per_paper": 3, "topk": 24}'


def test_execute_paper_benchmark_suite_supports_hybrid_profile(tmp_path: Path):
    _install_runtime_stubs()
    manifest_path = _write_manifest(tmp_path)
    summary = execute_paper_benchmark_suite(
        suite="paper_core",
        manifest_path=manifest_path,
        params_signature_name="hybrid",
        git_commit="deadbeef",
    )
    assert summary["suite"] == "paper_core"
    assert summary["plan"]["signature"]["params_signature"] == '{"graph_hop": 0, "max_evidence_per_paper": 3, "topk": 24}'


def test_execute_paper_benchmark_suite_aggregates_only_applicable_metrics(tmp_path: Path):
    _install_runtime_stubs()
    dataset_dir = tmp_path / "datasets"
    dataset_dir.mkdir(parents=True, exist_ok=True)
    core_file = dataset_dir / "core_v1.jsonl"
    core_file.write_text(
        '\n'.join(
            [
                '{"id":"REL-1","query":"related","seed_paper_ids":["P1"],"expect":{"required_clusters":{"classic":["P1"]}}}',
                '{"id":"XVAL-1","query":"xval","seed_paper_ids":["P2"],"expect":{"support_paper_ids":["P2"],"contradict_paper_ids":["P3"]}}',
            ]
        )
        + '\n',
        encoding="utf-8",
    )
    audit_file = dataset_dir / "audit_v1.jsonl"
    audit_file.write_text('{"id":"AUD-1","seed_paper_ids":["P1"]}\n', encoding="utf-8")
    full_file = dataset_dir / "full_v1.jsonl"
    full_file.write_text('{"id":"FULL-1","seed_paper_ids":["P1"]}\n', encoding="utf-8")
    snapshot_path = tmp_path / "fixtures" / "snapshots" / "papers_snapshot_v1.sqlite"
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(snapshot_path)
    c = conn.cursor()
    c.execute(
        "CREATE TABLE papers (id TEXT PRIMARY KEY, title TEXT, url TEXT, abstract TEXT, tags TEXT, summary_main_ideas TEXT, summary_methods TEXT, summary_results TEXT, summary_limitations TEXT)"
    )
    c.execute("INSERT INTO papers VALUES (?,?,?,?,?,?,?,?,?)", ("P1", "Classic", "https://arxiv.org/abs/P1", "", "", "classic", "", "", ""))
    c.execute("INSERT INTO papers VALUES (?,?,?,?,?,?,?,?,?)", ("P2", "Support", "https://arxiv.org/abs/P2", "", "", "support", "", "better support", ""))
    c.execute("INSERT INTO papers VALUES (?,?,?,?,?,?,?,?,?)", ("P3", "Contradict", "https://arxiv.org/abs/P3", "", "", "contradict", "", "negative regression", "failure"))
    conn.commit()
    conn.close()

    def _sha(path: Path) -> str:
        return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()

    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "dataset_version": "paper_bench_v1",
                "default_seed": 42,
                "tiers": {
                    "core": {
                        "file": str(core_file),
                        "sample_count": 2,
                        "snapshot_id": "papers_snapshot_v1",
                        "snapshot_path": str(snapshot_path),
                        "hash": _sha(core_file),
                        "blocking": True,
                        "budget": {
                            "sample_count_max": 2,
                            "mean_total_tokens_max": 5000,
                            "p95_latency_ms_max": 8000,
                            "timeout_rate_max": 0.0,
                        },
                    },
                    "full": {
                        "file": str(full_file),
                        "sample_count": 1,
                        "snapshot_id": "papers_snapshot_v1",
                        "snapshot_path": str(snapshot_path),
                        "hash": _sha(full_file),
                        "blocking": True,
                        "budget": {},
                    },
                    "audit": {
                        "file": str(audit_file),
                        "sample_count": 1,
                        "snapshot_id": "papers_snapshot_v1",
                        "snapshot_path": str(snapshot_path),
                        "hash": _sha(audit_file),
                        "blocking": False,
                        "budget": {},
                    },
                },
                "params_signatures": {
                    "graph_expand": {"topk": 30, "graph_hop": 1, "max_evidence_per_paper": 3}
                },
            }
        ),
        encoding="utf-8",
    )

    summary = execute_paper_benchmark_suite(
        suite="paper_core",
        manifest_path=manifest_path,
        params_signature_name="graph_expand",
        git_commit="deadbeef",
    )
    assert summary["aggregate_scores"]["cluster_coverage"] == 1.0
    assert summary["aggregate_scores"]["support_recall"] == 1.0
    assert summary["aggregate_scores"]["contradict_recall"] == 1.0
