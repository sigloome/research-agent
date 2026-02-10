"""Minimal eval runner guardrails for deterministic and weekly-audit profiles."""

from __future__ import annotations

import argparse
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Run eval suite guardrails")
    parser.add_argument("--suite", required=True, choices=["pr", "nightly", "weekly_audit"])
    parser.add_argument("--dataset", default=str(DATASET_PATH))
    parser.add_argument("--judge-rate", type=float, default=MAX_WEEKLY_JUDGE_RATE)
    parser.add_argument("--k", type=int, default=1)
    args = parser.parse_args()

    summary = run_suite(
        suite=args.suite,
        dataset_path=Path(args.dataset),
        judge_rate=args.judge_rate,
        k=args.k,
    )
    print(summary)


if __name__ == "__main__":
    main()
