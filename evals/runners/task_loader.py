"""Dataset loading helpers for eval runners."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List

REQUIRED_TASK_FIELDS = {
    "path_id",
    "mode",
    "required_invariants",
    "accepted_outcomes",
    "deterministic_metrics",
    "runtime_llm_judge",
}


@dataclass(frozen=True)
class EvalTask:
    """In-memory representation of one eval task from JSONL."""

    id: str
    path_id: str
    mode: str
    required_invariants: List[str]
    accepted_outcomes: List[Dict[str, Any]]
    deterministic_metrics: List[str]
    runtime_llm_judge: str
    raw: Dict[str, Any]


def load_tasks(dataset_path: str | Path) -> List[EvalTask]:
    """Load and validate task entries from JSONL."""

    path = Path(dataset_path)
    tasks: List[EvalTask] = []

    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        payload = json.loads(line)
        task_id = payload.get("id")
        if not task_id:
            raise ValueError(f"missing task id at line {line_number}")

        missing = sorted(field for field in REQUIRED_TASK_FIELDS if field not in payload)
        if missing:
            raise ValueError(f"task {task_id} missing required fields: {missing}")

        tasks.append(
            EvalTask(
                id=task_id,
                path_id=str(payload["path_id"]),
                mode=str(payload["mode"]),
                required_invariants=list(payload["required_invariants"]),
                accepted_outcomes=list(payload["accepted_outcomes"]),
                deterministic_metrics=list(payload["deterministic_metrics"]),
                runtime_llm_judge=str(payload["runtime_llm_judge"]),
                raw=payload,
            )
        )

    return tasks


def index_by_id(tasks: Iterable[EvalTask]) -> Dict[str, EvalTask]:
    """Map tasks by ID with uniqueness check."""

    mapping: Dict[str, EvalTask] = {}
    for task in tasks:
        if task.id in mapping:
            raise ValueError(f"duplicate task id: {task.id}")
        mapping[task.id] = task
    return mapping
