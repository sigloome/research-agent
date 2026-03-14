"""Deterministic metrics for paper retrieval benchmark governance and quality."""

from __future__ import annotations

import json
import re
from urllib.parse import urlparse
from typing import Dict, Iterable, List, Mapping, Sequence

REQUIRED_SIGNATURE_FIELDS = (
    "dataset_version",
    "dataset_hash",
    "snapshot_id",
    "seed",
    "params_signature",
    "git_commit",
)


def evaluate_benchmark_signature(signature: Mapping[str, object]) -> Dict[str, object]:
    missing = [field for field in REQUIRED_SIGNATURE_FIELDS if field not in signature]
    completeness = (len(REQUIRED_SIGNATURE_FIELDS) - len(missing)) / len(REQUIRED_SIGNATURE_FIELDS)
    return {
        "signature_completeness": completeness,
        "missing_fields": missing,
        "comparable": not missing,
    }


def evaluate_benchmark_budget(
    *,
    profile: str,
    observed: Mapping[str, float],
    budgets: Mapping[str, Mapping[str, float]],
) -> Dict[str, object]:
    budget = dict(budgets.get(profile, {}))
    violations: List[str] = []

    thresholds = {
        "sample_count": "sample_count_max",
        "mean_total_tokens": "mean_total_tokens_max",
        "p95_latency_ms": "p95_latency_ms_max",
        "timeout_rate": "timeout_rate_max",
    }
    for metric_name, threshold_name in thresholds.items():
        if threshold_name not in budget:
            continue
        if float(observed.get(metric_name, 0.0)) > float(budget[threshold_name]):
            violations.append(metric_name)

    over_budget = bool(violations)
    blocking = bool(budget.get("blocking", True))
    return {
        "profile": profile,
        "violations": violations,
        "over_budget": over_budget,
        "should_fail": over_budget and blocking,
    }


def evaluate_cluster_coverage(
    *,
    observed_paper_ids: Sequence[str],
    required_clusters: Mapping[str, Sequence[str]],
) -> Dict[str, object]:
    observed = set(observed_paper_ids)
    matched_clusters = [
        cluster_name
        for cluster_name, cluster_ids in required_clusters.items()
        if any(paper_id in observed for paper_id in cluster_ids)
    ]
    total = max(len(required_clusters), 1)
    return {
        "matched_clusters": matched_clusters,
        "cluster_coverage": len(matched_clusters) / total,
    }


def evaluate_comparison_facet_coverage(
    *,
    observed_facets: Iterable[str],
    required_facets: Sequence[str],
) -> Dict[str, object]:
    observed = {facet.strip().lower() for facet in observed_facets}
    required = [facet.strip().lower() for facet in required_facets]
    covered = [facet for facet in required if facet in observed]
    total = max(len(required), 1)
    return {
        "covered_facets": covered,
        "facet_coverage": len(covered) / total,
    }


def extract_observed_facets_from_evidence(evidence_items: Iterable[Mapping[str, object]]) -> List[str]:
    facets = set()
    for item in evidence_items:
        for key in ("method", "dataset", "metric", "value", "limitation"):
            value = item.get(key)
            if isinstance(value, str) and value.strip():
                facets.add("result" if key == "value" else key)
        polarity = str(item.get("polarity") or "").strip().lower()
        if polarity in {"support", "contradict"}:
            facets.add(polarity)
        if item.get("source_ref"):
            facets.add("citation")
        if item.get("comparability_warning"):
            facets.add("comparability_warning")
    return sorted(facets)


def evaluate_evidence_item_coverage(
    *,
    evidence_items: Iterable[Mapping[str, object]],
    required_facets: Sequence[str],
) -> Dict[str, object]:
    observed = extract_observed_facets_from_evidence(evidence_items)
    return evaluate_comparison_facet_coverage(
        observed_facets=observed,
        required_facets=required_facets,
    )


def evaluate_support_contradict_recall(
    *,
    observed_paper_ids: Sequence[str],
    support_paper_ids: Sequence[str],
    contradict_paper_ids: Sequence[str],
) -> Dict[str, object]:
    observed = set(observed_paper_ids)
    support = set(support_paper_ids)
    contradict = set(contradict_paper_ids)
    support_recall = len(observed & support) / max(len(support), 1)
    contradict_recall = len(observed & contradict) / max(len(contradict), 1)
    return {
        "support_recall": support_recall,
        "contradict_recall": contradict_recall,
        "balanced_evidence": bool(observed & support) and bool(observed & contradict),
    }


def evaluate_repeat_run_stability(
    *,
    baseline: Mapping[str, float],
    repeated: Mapping[str, float],
    tolerance: float,
) -> Dict[str, object]:
    metric_names = sorted(set(baseline) & set(repeated))
    drifts: Dict[str, float] = {}
    out_of_tolerance: List[str] = []
    for metric_name in metric_names:
        drift = abs(float(baseline[metric_name]) - float(repeated[metric_name]))
        drifts[metric_name] = drift
        if drift > tolerance:
            out_of_tolerance.append(metric_name)
    return {
        "metric_drifts": drifts,
        "out_of_tolerance_metrics": out_of_tolerance,
        "within_tolerance": not out_of_tolerance,
    }


def evaluate_span_grounding(
    *,
    evidence_items: Iterable[Mapping[str, object]],
    required_source_refs: Sequence[str],
    required_evidence_items: Sequence[Mapping[str, object]] | None = None,
) -> Dict[str, object]:
    observed_items = [item for item in evidence_items if isinstance(item, Mapping)]
    required = [ref.strip() for ref in required_source_refs if isinstance(ref, str) and ref.strip()]
    required_item_map: Dict[str, Mapping[str, object]] = {}
    for item in required_evidence_items or []:
        if not isinstance(item, Mapping):
            continue
        ref = item.get("source_ref")
        if isinstance(ref, str) and ref.strip():
            required_item_map[ref.strip()] = item

    matched = [
        ref
        for ref in required
        if any(
            _source_ref_matches(
                required_ref=ref,
                observed_item=item,
                required_item=required_item_map.get(ref),
            )
            for item in observed_items
        )
    ]
    total = max(len(required), 1)
    return {
        "matched_source_refs": matched,
        "span_grounding_recall": len(matched) / total,
    }


def _normalize_source_ref(ref: str) -> tuple[str, str]:
    raw = ref.strip().lower()
    if "://" in raw:
        parsed = urlparse(raw)
        base = (parsed.netloc + parsed.path).rstrip("/")
        fragment = parsed.fragment
    else:
        base, _, fragment = raw.partition("#")
        base = base.rstrip("/")
    return base, fragment


def _extract_ref_identifier(ref: str) -> str:
    base, _fragment = _normalize_source_ref(ref)
    tail = base.split("/")[-1]
    return tail.strip()


def _normalize_anchor(anchor: str) -> str:
    return re.sub(r"\d+$", "", anchor or "").strip()


def _signature_overlap(required_item: Mapping[str, object], observed_item: Mapping[str, object]) -> int:
    overlap = 0
    for key in ("paper_id", "dataset", "metric", "value", "polarity", "method"):
        required_value = str(required_item.get(key) or "").strip().lower()
        observed_value = str(observed_item.get(key) or "").strip().lower()
        if required_value and observed_value and required_value == observed_value:
            overlap += 1
    return overlap


def _source_ref_matches(
    *,
    required_ref: str,
    observed_item: Mapping[str, object],
    required_item: Mapping[str, object] | None = None,
) -> bool:
    observed_ref = observed_item.get("source_ref")
    if not isinstance(observed_ref, str) or not observed_ref.strip():
        return False
    observed_ref = observed_ref.strip()
    if observed_ref == required_ref:
        return True

    req_base, req_fragment = _normalize_source_ref(required_ref)
    obs_base, obs_fragment = _normalize_source_ref(observed_ref)
    if req_base != obs_base:
        return False
    if not req_fragment or not obs_fragment:
        return True
    if req_fragment == obs_fragment:
        return True
    if _normalize_anchor(req_fragment) and _normalize_anchor(req_fragment) == _normalize_anchor(obs_fragment):
        return True

    inferred_required = dict(required_item or {})
    if "paper_id" not in inferred_required:
        paper_id = _extract_ref_identifier(required_ref)
        if paper_id:
            inferred_required["paper_id"] = paper_id
    return _signature_overlap(inferred_required, observed_item) >= 2


def extract_candidate_paper_ids(retrieval_context: Mapping[str, object]) -> List[str]:
    candidate_papers = retrieval_context.get("candidate_papers", [])
    ids: List[str] = []
    if isinstance(candidate_papers, list):
        for item in candidate_papers:
            if isinstance(item, Mapping):
                paper_id = item.get("paper_id")
                if isinstance(paper_id, str) and paper_id:
                    ids.append(paper_id)
    return ids


def evaluate_case_against_retrieval_context(
    *,
    case: Mapping[str, object],
    retrieval_context: Mapping[str, object],
) -> Dict[str, object]:
    expect = case.get("expect", {})
    if not isinstance(expect, Mapping):
        expect = {}
    candidate_ids = extract_candidate_paper_ids(retrieval_context)
    evidence_items = retrieval_context.get("evidence_items", [])
    if not isinstance(evidence_items, list):
        evidence_items = []

    result: Dict[str, object] = {
        "candidate_paper_ids": candidate_ids,
        "paper_recall": 0.0,
    }

    required_paper_ids = expect.get("required_paper_ids", [])
    if isinstance(required_paper_ids, list) and required_paper_ids:
        matched_required = len(set(candidate_ids) & set(str(x) for x in required_paper_ids))
        result["paper_recall"] = matched_required / len(required_paper_ids)

    required_clusters = expect.get("required_clusters")
    if isinstance(required_clusters, Mapping):
        result.update(
            evaluate_cluster_coverage(
                observed_paper_ids=candidate_ids,
                required_clusters={
                    str(k): [str(v) for v in values]
                    for k, values in required_clusters.items()
                    if isinstance(values, list)
                },
            )
        )

    required_facets = expect.get("required_facets", [])
    if isinstance(required_facets, list) and required_facets:
        result.update(
            {
                f"evidence_{k}": v
                for k, v in evaluate_evidence_item_coverage(
                    evidence_items=evidence_items,
                    required_facets=[str(x) for x in required_facets],
                ).items()
            }
        )

    required_source_refs = expect.get("required_evidence_refs", [])
    if isinstance(required_source_refs, list) and required_source_refs:
        result.update(
            evaluate_span_grounding(
                evidence_items=evidence_items,
                required_source_refs=[str(x) for x in required_source_refs],
                required_evidence_items=[
                    item for item in expect.get("required_evidence_items", []) if isinstance(item, Mapping)
                ],
            )
        )

    support_ids = expect.get("support_paper_ids", [])
    contradict_ids = expect.get("contradict_paper_ids", [])
    if isinstance(support_ids, list) and isinstance(contradict_ids, list) and (
        support_ids or contradict_ids
    ):
        result.update(
            evaluate_support_contradict_recall(
                observed_paper_ids=candidate_ids,
                support_paper_ids=[str(x) for x in support_ids],
                contradict_paper_ids=[str(x) for x in contradict_ids],
            )
        )

    return result


def load_paper_benchmark_cases(path: str) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows
