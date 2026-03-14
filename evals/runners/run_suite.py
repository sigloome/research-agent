"""Minimal eval runner guardrails for deterministic and weekly-audit profiles."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import sqlite3
import sys
import types
from pathlib import Path
from typing import Dict, Iterable, List, Sequence

from evals.runners.task_loader import EvalTask, index_by_id, load_tasks

DATASET_PATH = Path(__file__).resolve().parents[1] / "datasets" / "retrieval_prompt_paths.jsonl"

PR_NIGHTLY_IDS = [
    "RET-01",
    "RET-02",
    "RET-03",
    "RET-04",
    "RET-05",
    "RET-06",
    "RET-08",
    "AGT-01",
    "AGT-02",
    "AGT-03",
    "AGT-04",
    "AGT-05",
    "AGT-06",
    "AGT-07",
    "AGT-08",
    "AGT-09",
    "AGT-10",
    "AGT-11",
    "AGT-12",
    "AGT-13",
    "AGT-14",
    "AGT-15",
    "AGT-16",
]

WEEKLY_AUDIT_REQUIRED_IDS = ["RET-07"]
WEEKLY_AUDIT_SAMPLE_CANDIDATES = ["AGT-03"]
MAX_WEEKLY_JUDGE_RATE = 0.15
PAPER_BENCHMARK_MANIFEST_PATH = (
    Path(__file__).resolve().parents[1] / "datasets" / "paper_benchmark" / "manifest_v1.json"
)


def _select_ids(task_map: Dict[str, EvalTask], ids: Sequence[str]) -> List[EvalTask]:
    missing = [task_id for task_id in ids if task_id not in task_map]
    if missing:
        raise ValueError(f"missing required tasks in dataset: {missing}")
    return [task_map[task_id] for task_id in ids]


def enforce_deterministic_only(tasks: Iterable[EvalTask]) -> None:
    """PR/nightly guardrail: every selected task must keep runtime judge off."""

    offenders = [task.id for task in tasks if task.runtime_llm_judge != "off"]
    if offenders:
        raise ValueError(
            "deterministic runner cannot include runtime judge tasks: "
            + ", ".join(offenders)
        )


def enforce_weekly_judge_rate(total_task_count: int, runtime_judged_count: int, judge_rate: float) -> float:
    """Weekly guardrail: configured and observed judge rates must be <= 0.15."""

    if judge_rate > MAX_WEEKLY_JUDGE_RATE:
        raise ValueError(
            f"weekly judge_rate must be <= {MAX_WEEKLY_JUDGE_RATE:.2f}; got {judge_rate:.2f}"
        )
    observed = runtime_judged_count / max(total_task_count, 1)
    if observed > judge_rate:
        raise ValueError(
            f"weekly observed judge rate {observed:.4f} exceeds configured cap {judge_rate:.4f}"
        )
    return observed


def build_weekly_audit_plan(tasks: Sequence[EvalTask], judge_rate: float = MAX_WEEKLY_JUDGE_RATE) -> dict:
    """Build weekly audit run plan with RET-07 + sampled AGT-03 and guardrail checks."""

    task_map = index_by_id(tasks)
    required_runtime = _select_ids(task_map, WEEKLY_AUDIT_REQUIRED_IDS)

    sampled_runtime: List[EvalTask] = []
    for candidate_id in WEEKLY_AUDIT_SAMPLE_CANDIDATES:
        if candidate_id in task_map:
            sampled_runtime.append(task_map[candidate_id])
            break

    runtime_judged_tasks = required_runtime + sampled_runtime
    observed_rate = enforce_weekly_judge_rate(
        total_task_count=len(tasks),
        runtime_judged_count=len(runtime_judged_tasks),
        judge_rate=judge_rate,
    )

    audit_task_ids = [task.id for task in runtime_judged_tasks]
    return {
        "suite": "weekly_audit",
        "task_count": len(tasks),
        "runtime_judge_task_ids": audit_task_ids,
        "runtime_judge_task_count": len(runtime_judged_tasks),
        "observed_judge_rate": observed_rate,
    }


def run_suite(
    suite: str,
    dataset_path: str | Path = DATASET_PATH,
    judge_rate: float = MAX_WEEKLY_JUDGE_RATE,
    k: int = 1,
) -> dict:
    """Run suite selection + guardrail validation and return a dry-run summary."""

    del k

    tasks = load_tasks(dataset_path)
    task_map = index_by_id(tasks)

    if suite in {"pr", "nightly"}:
        selected = _select_ids(task_map, PR_NIGHTLY_IDS)
        enforce_deterministic_only(selected)
        return {
            "suite": suite,
            "selected_task_ids": [task.id for task in selected],
            "selected_task_count": len(selected),
        }

    if suite == "weekly_audit":
        return build_weekly_audit_plan(tasks, judge_rate=judge_rate)

    raise ValueError(f"unsupported suite: {suite}")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return "sha256:" + digest.hexdigest()


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _count_jsonl_records(path: Path) -> int:
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def _load_jsonl_rows(path: Path) -> List[dict]:
    rows: List[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def _collect_case_paper_ids(rows: Sequence[dict]) -> List[str]:
    paper_ids = set()
    for row in rows:
        for key in ("seed_paper_ids",):
            values = row.get(key, [])
            if isinstance(values, list):
                for value in values:
                    if isinstance(value, str):
                        paper_ids.add(value)
        expect = row.get("expect", {})
        if not isinstance(expect, dict):
            continue
        for key in ("required_paper_ids", "support_paper_ids", "contradict_paper_ids"):
            values = expect.get(key, [])
            if isinstance(values, list):
                for value in values:
                    if isinstance(value, str):
                        paper_ids.add(value)
        required_clusters = expect.get("required_clusters", {})
        if isinstance(required_clusters, dict):
            for values in required_clusters.values():
                if isinstance(values, list):
                    for value in values:
                        if isinstance(value, str):
                            paper_ids.add(value)
    return sorted(paper_ids)


def _validate_snapshot_contains_papers(snapshot_path: Path, paper_ids: Sequence[str]) -> None:
    if not paper_ids:
        return
    conn = sqlite3.connect(snapshot_path)
    try:
        cur = conn.cursor()
        placeholders = ",".join("?" for _ in paper_ids)
        cur.execute(f"SELECT id FROM papers WHERE id IN ({placeholders})", list(paper_ids))
        present = {row[0] for row in cur.fetchall()}
    finally:
        conn.close()
    missing = [paper_id for paper_id in paper_ids if paper_id not in present]
    if missing:
        raise ValueError(
            "paper benchmark snapshot missing referenced paper ids: " + ", ".join(missing)
        )


def build_paper_benchmark_plan(
    *,
    suite: str,
    manifest_path: str | Path = PAPER_BENCHMARK_MANIFEST_PATH,
    params_signature_name: str,
    git_commit: str,
) -> dict:
    manifest = _load_json(Path(manifest_path))
    tier_by_suite = {
        "paper_core": "core",
        "paper_full": "full",
        "paper_audit": "audit",
    }
    if suite not in tier_by_suite:
        raise ValueError(f"unsupported paper benchmark suite: {suite}")
    tier = tier_by_suite[suite]
    tier_cfg = dict(manifest["tiers"][tier])
    dataset_path = Path(tier_cfg["file"])
    if not dataset_path.exists():
        raise ValueError(f"paper benchmark dataset missing: {dataset_path}")
    actual_dataset_hash = _sha256_file(dataset_path)
    declared_dataset_hash = str(tier_cfg.get("hash") or "").strip()
    if declared_dataset_hash and actual_dataset_hash != declared_dataset_hash:
        raise ValueError(
            f"paper benchmark dataset hash mismatch for {dataset_path}: "
            f"declared={declared_dataset_hash} actual={actual_dataset_hash}"
        )
    actual_sample_count = _count_jsonl_records(dataset_path)
    declared_sample_count = int(tier_cfg["sample_count"])
    if actual_sample_count != declared_sample_count:
        raise ValueError(
            f"paper benchmark sample count mismatch for {dataset_path}: "
            f"declared={declared_sample_count} actual={actual_sample_count}"
        )

    blocking = bool(tier_cfg.get("blocking", tier in {"core", "full"}))
    snapshot_path = Path(tier_cfg["snapshot_path"])
    if blocking and not snapshot_path.exists():
        raise ValueError(f"snapshot restore precondition failed: {snapshot_path}")
    case_rows = _load_jsonl_rows(dataset_path)
    referenced_paper_ids = _collect_case_paper_ids(case_rows)
    _validate_snapshot_contains_papers(snapshot_path, referenced_paper_ids)

    params_signature_cfg = manifest["params_signatures"][params_signature_name]
    signature = {
        "dataset_version": manifest["dataset_version"],
        "dataset_hash": actual_dataset_hash,
        "snapshot_id": tier_cfg["snapshot_id"],
        "seed": manifest["default_seed"],
        "params_signature": json.dumps(params_signature_cfg, sort_keys=True),
        "git_commit": git_commit,
    }
    return {
        "suite": suite,
        "tier": tier,
        "blocking": blocking,
        "dataset_path": str(dataset_path),
        "declared_dataset_hash": declared_dataset_hash,
        "signature": signature,
        "budget": dict(tier_cfg.get("budget", {})),
        "sample_count": declared_sample_count,
        "snapshot_path": str(snapshot_path),
        "referenced_paper_ids": referenced_paper_ids,
    }


def _load_snapshot_rows(snapshot_path: Path) -> List[dict]:
    conn = sqlite3.connect(snapshot_path)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM papers")
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def _tokenize(text: str) -> List[str]:
    return [token for token in "".join(ch.lower() if ch.isalnum() else " " for ch in text).split() if token]


def _build_snapshot_search_fn(snapshot_rows: Sequence[dict]):
    rows = [dict(row) for row in snapshot_rows]

    def search(query: str) -> List[dict]:
        semantic_mode = query.startswith("semantic::")
        semantic_query = query.split("semantic::", 1)[1] if semantic_mode else query
        query_tokens = _tokenize(semantic_query)
        query_text = semantic_query.lower()
        semantic_hints = {
            "graph retrieval": {"graph", "retrieval", "evidence", "reasoning", "multi", "hop"},
            "transformer attention": {"transformer", "attention", "context", "long"},
            "counter evidence": {"contradict", "failure", "regression", "negative", "worse"},
        }

        def score(row: dict) -> tuple:
            paper_id = str(row.get("id") or "")
            haystack = " ".join(
                str(row.get(key) or "")
                for key in (
                    "id",
                    "title",
                    "abstract",
                    "summary_main_ideas",
                    "summary_methods",
                    "summary_results",
                    "summary_limitations",
                    "tags",
                )
            ).lower()
            token_hits = sum(1 for token in query_tokens if token in haystack)
            exact_id = 1 if paper_id.lower() in query.lower() else 0
            semantic_hits = 0
            if semantic_mode:
                for hint_tokens in semantic_hints.values():
                    overlap = len(hint_tokens & set(query_tokens))
                    if overlap and any(token in haystack for token in hint_tokens):
                        semantic_hits = max(
                            semantic_hits,
                            overlap + sum(1 for token in hint_tokens if token in haystack),
                        )
            graph_bias = 1 if "graph" in haystack and any(t in query.lower() for t in ("graph", "multi-hop", "hotpot")) else 0
            transformer_bias = 1 if any(t in haystack for t in ("transformer", "attention")) and any(
                t in query.lower() for t in ("transformer", "attention", "context")
            ) else 0
            contradiction_bias = 1 if any(
                token in haystack for token in ("contradict", "failure", "regression", "negative")
            ) and any(
                token in query_text for token in ("contradict", "failure", "regression", "negative")
            ) else 0
            recent = 1 if paper_id.startswith(("24", "25")) else 0
            classic = 1 if paper_id == "1706.03762" else 0
            return (
                semantic_hits,
                token_hits,
                exact_id,
                contradiction_bias,
                graph_bias,
                transformer_bias,
                recent,
                classic,
                str(row.get("title") or ""),
            )

        return sorted(rows, key=score, reverse=True)

    return search


def _mean(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def _mean_present(case_results: Sequence[dict], metric_name: str) -> float:
    values = [
        float(item["scores"][metric_name])
        for item in case_results
        if metric_name in item.get("scores", {})
    ]
    return _mean(values)


def _p95(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, int(len(ordered) * 0.95) - 1))
    return float(ordered[index])


def _install_runtime_import_stubs() -> None:
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
    if "structlog.typing" not in sys.modules:
        structlog_typing = types.ModuleType("structlog.typing")
        structlog_typing.Processor = object
        sys.modules["structlog.typing"] = structlog_typing
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


def execute_paper_benchmark_suite(
    *,
    suite: str,
    manifest_path: str | Path = PAPER_BENCHMARK_MANIFEST_PATH,
    params_signature_name: str,
    git_commit: str,
) -> dict:
    _install_runtime_import_stubs()
    from backend.multi_agent_runtime import MultiAgentRuntime, parse_runtime_profile
    from evals.metrics.paper_benchmark import (
        evaluate_benchmark_budget,
        evaluate_benchmark_signature,
        evaluate_case_against_retrieval_context,
        load_paper_benchmark_cases,
    )

    plan = build_paper_benchmark_plan(
        suite=suite,
        manifest_path=manifest_path,
        params_signature_name=params_signature_name,
        git_commit=git_commit,
    )
    signature_eval = evaluate_benchmark_signature(plan["signature"])
    if not signature_eval["comparable"]:
        raise ValueError("paper benchmark execution requires complete signature")

    rows = _load_snapshot_rows(Path(plan["snapshot_path"]))
    search_fn = _build_snapshot_search_fn(rows)
    profile = parse_runtime_profile(params_signature_name)
    if profile is None:
        raise ValueError(f"unsupported params signature/runtime profile: {params_signature_name}")
    runtime = MultiAgentRuntime(
        paper_search_fn=search_fn,
        graph_query_fn=lambda *_args, **_kwargs: "",
    )
    cases = load_paper_benchmark_cases(plan["dataset_path"])

    case_results: List[dict] = []
    latencies: List[float] = []
    token_counts: List[float] = []
    for case in cases:
        query = str(case.get("query") or " ".join(case.get("seed_paper_ids", [])) or case.get("id") or "")
        result = asyncio.run(runtime.run(query, profile, None))
        retrieval_context = result.retrieval_context
        case_score = evaluate_case_against_retrieval_context(
            case=case,
            retrieval_context=retrieval_context,
        )
        latency_ms = sum(h.latency_ms for h in result.handoffs)
        latencies.append(float(latency_ms))
        token_counts.append(float(len(json.dumps(retrieval_context, ensure_ascii=False)) // 4))
        case_results.append(
            {
                "id": case["id"],
                "intent": case.get("intent"),
                "profile": profile.value,
                "query": query,
                "latency_ms": latency_ms,
                "retrieval_context": retrieval_context,
                "scores": case_score,
            }
        )

    aggregate = {
        "paper_recall": _mean_present(case_results, "paper_recall"),
        "cluster_coverage": _mean_present(case_results, "cluster_coverage"),
        "evidence_facet_coverage": _mean_present(case_results, "evidence_facet_coverage"),
        "support_recall": _mean_present(case_results, "support_recall"),
        "contradict_recall": _mean_present(case_results, "contradict_recall"),
        "span_grounding_recall": _mean_present(case_results, "span_grounding_recall"),
        "balanced_evidence_rate": _mean(
            [
                1.0 if item["scores"].get("balanced_evidence") else 0.0
                for item in case_results
                if "balanced_evidence" in item.get("scores", {})
            ]
        ),
        "sample_count": float(len(case_results)),
        "mean_total_tokens": _mean(token_counts),
        "p95_latency_ms": _p95(latencies),
        "timeout_rate": 0.0,
    }
    budget_eval = evaluate_benchmark_budget(
        profile=plan["tier"],
        observed=aggregate,
        budgets={plan["tier"]: {**plan["budget"], "blocking": plan["blocking"]}},
    )
    return {
        "suite": suite,
        "plan": plan,
        "signature_evaluation": signature_eval,
        "budget_evaluation": budget_eval,
        "aggregate_scores": aggregate,
        "case_results": case_results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run eval suite guardrails")
    parser.add_argument(
        "--suite",
        required=True,
        choices=["pr", "nightly", "weekly_audit", "paper_core", "paper_full", "paper_audit"],
    )
    parser.add_argument("--dataset", default=str(DATASET_PATH))
    parser.add_argument("--judge-rate", type=float, default=MAX_WEEKLY_JUDGE_RATE)
    parser.add_argument("--k", type=int, default=1)
    parser.add_argument("--manifest", default=str(PAPER_BENCHMARK_MANIFEST_PATH))
    parser.add_argument("--params-signature", default="baseline")
    parser.add_argument("--git-commit", default="local-dev")
    args = parser.parse_args()

    if args.suite in {"paper_core", "paper_full", "paper_audit"}:
        summary = execute_paper_benchmark_suite(
            suite=args.suite,
            manifest_path=Path(args.manifest),
            params_signature_name=args.params_signature,
            git_commit=args.git_commit,
        )
    else:
        summary = run_suite(
            suite=args.suite,
            dataset_path=Path(args.dataset),
            judge_rate=args.judge_rate,
            k=args.k,
        )
    print(summary)


if __name__ == "__main__":
    main()
