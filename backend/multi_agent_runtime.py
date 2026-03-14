"""Explicit multi-agent runtime skeleton with typed handoff contracts.

The runtime is opt-in and compatible with the existing orchestrator path:
- default chat path keeps legacy behavior
- benchmark/profile mode can enable explicit multi-agent routing
"""

from __future__ import annotations

import asyncio
import json
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from backend.logging_config import get_logger
from skills.knowledge.db import manager
from skills.knowledge.graph_rag import query_rag
from skills.knowledge.rag_critic.retriever import HierarchicalRetriever
from skills.preference.implementation import get_user_history, get_user_profile

logger = get_logger()


class RuntimeProfile(str, Enum):
    BASELINE = "baseline"
    HYBRID = "hybrid"
    GRAPH_EXPAND = "graph_expand"
    GRAPH_VERIFY = "graph_verify"


class AgentRole(str, Enum):
    ORCHESTRATOR = "orchestrator"
    RETRIEVAL = "retrieval_agent"
    PREFERENCE = "preference_agent"
    ANSWER = "answer_agent"
    VERIFIER = "verifier_agent"


@dataclass
class HandoffError:
    code: str
    message: str
    retryable: bool = False
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HandoffEnvelope:
    role: AgentRole
    ok: bool
    payload: Dict[str, Any] = field(default_factory=dict)
    error: Optional[HandoffError] = None
    fallback_used: bool = False
    fallback_reason: Optional[str] = None
    latency_ms: int = 0

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        if self.error is not None:
            data["error"] = asdict(self.error)
        return data


@dataclass
class RuntimeResult:
    profile: RuntimeProfile
    route: str
    handoffs: List[HandoffEnvelope]
    retrieval_context: Dict[str, Any]
    answer_context: str
    answer_envelope: HandoffEnvelope
    verifier_summary: str


class MultiAgentRuntime:
    """Orchestrates retrieval/preference/verifier sub-agents before answer step."""

    def __init__(
        self,
        *,
        paper_search_fn: Optional[Callable[[str], List[Dict[str, Any]]]] = None,
        graph_query_fn: Optional[Callable[[str], Any]] = None,
        critic: Optional[HierarchicalRetriever] = None,
    ) -> None:
        self._critic = critic or HierarchicalRetriever()
        self._paper_search_fn = paper_search_fn or (lambda query: manager.search_local_papers(query))
        self._graph_query_fn = graph_query_fn or query_rag

    async def run(
        self,
        query: str,
        profile: RuntimeProfile,
        user_preferences: Optional[str] = None,
    ) -> RuntimeResult:
        route = "local-worker-first"
        handoffs: List[HandoffEnvelope] = []

        handoffs.append(self._orchestrator_handoff(query=query, profile=profile))
        retrieval = await self._retrieval_handoff(query=query, profile=profile)
        handoffs.append(retrieval)

        preference = self._preference_handoff(user_preferences=user_preferences)
        handoffs.append(preference)

        verifier = self._verifier_handoff(retrieval=retrieval, preference=preference)
        handoffs.append(verifier)

        retrieval_context = self._build_retrieval_context(
            query=query,
            profile=profile,
            retrieval=retrieval,
            preference=preference,
            verifier=verifier,
        )
        context = self._build_answer_context(retrieval_context=retrieval_context)
        answer = self._answer_handoff(query=query, handoffs=handoffs, context=context)
        handoffs.append(answer)
        return RuntimeResult(
            profile=profile,
            route=route,
            handoffs=handoffs,
            retrieval_context=retrieval_context,
            answer_context=context,
            answer_envelope=answer,
            verifier_summary=verifier.payload.get("summary", ""),
        )

    def _orchestrator_handoff(self, query: str, profile: RuntimeProfile) -> HandoffEnvelope:
        started = time.perf_counter()
        payload = {
            "query": query,
            "profile": profile.value,
            "routing_policy": "local-worker-first",
            "fallback_policy": "fallback-to-web-retrieval-if-local-miss",
        }
        latency_ms = int((time.perf_counter() - started) * 1000)
        return HandoffEnvelope(
            role=AgentRole.ORCHESTRATOR,
            ok=True,
            payload=payload,
            latency_ms=latency_ms,
        )

    async def _retrieval_handoff(self, query: str, profile: RuntimeProfile) -> HandoffEnvelope:
        started = time.perf_counter()
        try:
            if profile == RuntimeProfile.BASELINE:
                payload = self._retrieve_baseline(query)
                return HandoffEnvelope(
                    role=AgentRole.RETRIEVAL,
                    ok=True,
                    payload=payload,
                    latency_ms=int((time.perf_counter() - started) * 1000),
                )

            if profile == RuntimeProfile.HYBRID:
                payload = self._retrieve_hybrid(query)
                return HandoffEnvelope(
                    role=AgentRole.RETRIEVAL,
                    ok=True,
                    payload=payload,
                    latency_ms=int((time.perf_counter() - started) * 1000),
                )

            if profile == RuntimeProfile.GRAPH_EXPAND:
                payload = self._retrieve_graph(query)
                return HandoffEnvelope(
                    role=AgentRole.RETRIEVAL,
                    ok=True,
                    payload=payload,
                    latency_ms=int((time.perf_counter() - started) * 1000),
                )

            payload = await self._retrieve_graph_with_critic(query)
            return HandoffEnvelope(
                role=AgentRole.RETRIEVAL,
                ok=True,
                payload=payload,
                latency_ms=int((time.perf_counter() - started) * 1000),
            )
        except Exception as exc:
            logger.warning("multi_agent_retrieval_failed", error=str(exc), profile=profile.value)
            payload = self._fallback_web_retrieval(query)
            return HandoffEnvelope(
                role=AgentRole.RETRIEVAL,
                ok=True,
                payload=payload,
                fallback_used=True,
                fallback_reason=str(exc),
                latency_ms=int((time.perf_counter() - started) * 1000),
            )

    def _retrieve_baseline(self, query: str) -> Dict[str, Any]:
        intent = self._infer_intent(query)
        papers = self._paper_search(query) or []
        candidate_papers = []
        evidence_items = []
        for row in papers[:5]:
            if not isinstance(row, dict):
                continue
            paper_id = row.get("id")
            candidate_papers.append(
                {
                    "paper_id": paper_id,
                    "title": row.get("title"),
                    "summary": row.get("summary_main_ideas"),
                    "source": "local_lexical",
                    "url": row.get("url"),
                    "match_reasons": ["local_text_match"],
                }
            )
            evidence_items.extend(self._baseline_evidence_items(row, intent=intent))
        coverage_audit = {
            "has_classic_baseline": any(p.get("paper_id") == "1706.03762" for p in candidate_papers),
            "has_recent_followup": any(
                str(p.get("paper_id", "")).startswith("24") for p in candidate_papers
            ),
            "has_supporting_evidence": any(
                item.get("polarity") == "support" for item in evidence_items
            )
            or bool(candidate_papers),
            "has_counter_evidence": any(
                item.get("polarity") == "contradict" for item in evidence_items
            ),
            "counter_evidence_checked": intent == "cross_validation",
            "has_comparability_warning": any(
                item.get("comparability_warning") for item in evidence_items
            ),
        }
        return {
            "mode": "baseline_local_vector",
            "intent": intent,
            "candidate_papers": candidate_papers,
            "evidence_items": evidence_items,
            "coverage_audit": coverage_audit,
        }

    def _retrieve_graph(self, query: str) -> Dict[str, Any]:
        intent = self._infer_intent(query)
        baseline_payload = self._retrieve_hybrid(query)
        candidate_papers = list(baseline_payload.get("candidate_papers", []))
        answer = self._graph_query_fn(query, mode="global")
        graph_answer = str(answer)
        candidate_papers = self._merge_candidate_papers(
            candidate_papers,
            self._candidate_papers_from_graph_answer(graph_answer),
        )
        candidate_papers = self._merge_candidate_papers(
            candidate_papers,
            self._expand_related_candidates(query, candidate_papers),
        )
        if intent == "cross_validation":
            candidate_papers = self._merge_candidate_papers(
                candidate_papers,
                self._counter_evidence_candidates(query),
            )
        evidence_items = list(baseline_payload.get("evidence_items", []))
        evidence_items.extend(
            self._graph_evidence_items(candidate_papers, graph_answer or query, polarity="support")
        )
        return {
            "mode": "graph_expand_retrieval",
            "intent": intent,
            "graph_answer": graph_answer,
            "candidate_papers": candidate_papers,
            "evidence_items": evidence_items,
            "coverage_audit": {
                "has_classic_baseline": any(p.get("paper_id") == "1706.03762" for p in candidate_papers),
                "has_recent_followup": any(
                    str(p.get("paper_id", "")).startswith(("24", "25")) for p in candidate_papers
                ),
                "has_supporting_evidence": any(
                    item.get("polarity") == "support" for item in evidence_items
                )
                or bool(candidate_papers),
                "has_counter_evidence": any(
                    item.get("polarity") == "contradict" for item in evidence_items
                ),
                "counter_evidence_checked": intent == "cross_validation",
                "has_comparability_warning": any(
                    item.get("comparability_warning") for item in evidence_items
                ),
            },
        }

    async def _retrieve_graph_with_critic(self, query: str) -> Dict[str, Any]:
        graph_payload = self._retrieve_graph(query)
        graph_answer = str(graph_payload.get("graph_answer") or "")
        evidence_items = [
            item for item in graph_payload.get("evidence_items", []) if isinstance(item, dict)
        ]
        critic_inputs = [
            json.dumps(item, sort_keys=True)
            for item in evidence_items[:8]
        ]
        if not critic_inputs:
            critic_inputs = [line.strip() for line in graph_answer.splitlines() if line.strip()]
        if not critic_inputs:
            critic_inputs = [graph_answer or query]
        filtered = await self._critic.retrieve_and_filter(query, critic_inputs[:8])
        candidate_papers = list(graph_payload.get("candidate_papers", []))
        reranked_evidence = self._rerank_evidence_items(
            evidence_items=evidence_items,
            filtered_inputs=filtered,
        )
        return {
            "mode": "graph_verify_retrieval",
            "intent": graph_payload.get("intent", "cross_validation"),
            "graph_answer": graph_answer,
            "filtered_chunks": filtered,
            "candidate_papers": candidate_papers,
            "evidence_items": reranked_evidence,
            "coverage_audit": {
                "has_classic_baseline": any(p.get("paper_id") == "1706.03762" for p in candidate_papers),
                "has_recent_followup": any(
                    str(p.get("paper_id", "")).startswith(("24", "25")) for p in candidate_papers
                ),
                "has_supporting_evidence": any(
                    item.get("polarity") == "support" for item in reranked_evidence
                ),
                "has_counter_evidence": any(
                    item.get("polarity") == "contradict" for item in reranked_evidence
                ),
                "counter_evidence_checked": True,
                "has_comparability_warning": any(
                    item.get("comparability_warning") for item in reranked_evidence
                ),
            },
        }

    def _retrieve_hybrid(self, query: str) -> Dict[str, Any]:
        lexical_payload = self._retrieve_baseline(query)
        semantic_rows = self._paper_search(f"semantic::{query}")
        intent = lexical_payload.get("intent", self._infer_intent(query))
        semantic_rows = self._prioritize_semantic_rows(query, semantic_rows, intent=intent)
        semantic_candidates = []
        semantic_evidence = []
        for row in semantic_rows[:8]:
            paper_id = row.get("id")
            semantic_candidates.append(
                {
                    "paper_id": paper_id,
                    "title": row.get("title"),
                    "summary": row.get("summary_main_ideas"),
                    "source": "semantic_recall",
                    "url": row.get("url"),
                    "match_reasons": ["semantic_match"],
                }
            )
            semantic_evidence.extend(self._baseline_evidence_items(row, intent=intent))
        candidate_papers = self._merge_candidate_papers(
            list(lexical_payload.get("candidate_papers", [])),
            semantic_candidates,
        )
        evidence_items = self._merge_evidence_items(
            list(lexical_payload.get("evidence_items", [])),
            semantic_evidence,
        )
        for candidate in candidate_papers:
            reasons = set(candidate.get("match_reasons", []))
            source = str(candidate.get("source") or "")
            if "local_text_match" in reasons and "semantic_match" in reasons:
                candidate["source"] = "hybrid_mixed"
            elif "semantic_match" in reasons and source != "local_lexical":
                candidate["source"] = "semantic_recall"
        return {
            **lexical_payload,
            "mode": "hybrid_local_semantic",
            "candidate_papers": candidate_papers,
            "evidence_items": evidence_items,
        }

    def _fallback_web_retrieval(self, query: str) -> Dict[str, Any]:
        return {
            "mode": "fallback_web_retrieval",
            "intent": self._infer_intent(query),
            "web_query": query,
            "reason": "local retrieval path unavailable",
            "candidate_papers": [],
            "evidence_items": [],
            "coverage_audit": {
                "has_classic_baseline": False,
                "has_recent_followup": False,
                "has_supporting_evidence": False,
                "has_counter_evidence": False,
                "counter_evidence_checked": False,
                "has_comparability_warning": False,
            },
        }

    def _paper_search(self, query: str) -> List[Dict[str, Any]]:
        rows = self._paper_search_fn(query) or []
        return [row for row in rows if isinstance(row, dict)]

    def _preference_handoff(self, user_preferences: Optional[str]) -> HandoffEnvelope:
        started = time.perf_counter()
        try:
            profile_md = get_user_profile()
            history_md = get_user_history()
            payload = {
                "profile": profile_md,
                "history": history_md,
                "summary": user_preferences or "",
            }
            return HandoffEnvelope(
                role=AgentRole.PREFERENCE,
                ok=True,
                payload=payload,
                latency_ms=int((time.perf_counter() - started) * 1000),
            )
        except Exception as exc:
            return HandoffEnvelope(
                role=AgentRole.PREFERENCE,
                ok=False,
                payload={"summary": user_preferences or ""},
                error=HandoffError(
                    code="PREFERENCE_LOAD_FAILED",
                    message=str(exc),
                    retryable=False,
                ),
                latency_ms=int((time.perf_counter() - started) * 1000),
            )

    def _verifier_handoff(
        self, retrieval: HandoffEnvelope, preference: HandoffEnvelope
    ) -> HandoffEnvelope:
        started = time.perf_counter()
        issues: List[str] = []
        if not retrieval.ok:
            issues.append("retrieval_not_ok")
        if retrieval.fallback_used:
            issues.append("retrieval_fallback_used")
        if not preference.ok:
            issues.append("preference_not_ok")
        summary = "ready_for_answer" if not issues else ",".join(issues)
        return HandoffEnvelope(
            role=AgentRole.VERIFIER,
            ok=True,
            payload={"summary": summary, "issues": issues},
            latency_ms=int((time.perf_counter() - started) * 1000),
        )

    def _build_answer_context(self, query: str, handoffs: List[HandoffEnvelope]) -> str:
        raise NotImplementedError

    def _build_retrieval_context(
        self,
        *,
        query: str,
        profile: RuntimeProfile,
        retrieval: HandoffEnvelope,
        preference: HandoffEnvelope,
        verifier: HandoffEnvelope,
    ) -> Dict[str, Any]:
        retrieval_payload = dict(retrieval.payload)
        return {
            "profile": profile.value,
            "intent": retrieval_payload.get("intent", "lookup"),
            "query": query,
            "candidate_papers": list(retrieval_payload.get("candidate_papers", [])),
            "evidence_items": list(retrieval_payload.get("evidence_items", [])),
            "coverage_audit": dict(retrieval_payload.get("coverage_audit", {})),
            "verifier_summary": verifier.payload.get("summary", ""),
            "fallback_used": retrieval.fallback_used,
            "preference_summary": preference.payload.get("summary", ""),
        }

    def _build_answer_context(self, retrieval_context: Dict[str, Any]) -> str:
        return "[RetrievalContext]\n" + json.dumps(retrieval_context, ensure_ascii=False, sort_keys=True)

    def _candidate_papers_from_graph_answer(self, graph_answer: str) -> List[Dict[str, Any]]:
        lines = [line.strip("- ").strip() for line in graph_answer.splitlines() if line.strip()]
        if not lines:
            lines = [graph_answer.strip()] if graph_answer.strip() else []
        candidate_papers: List[Dict[str, Any]] = []
        for idx, line in enumerate(lines[:5], start=1):
            candidate_papers.append(
                {
                    "paper_id": f"graph-{idx}",
                    "title": line[:120],
                    "summary": line[:240],
                    "source": "graph_expand",
                    "match_reasons": ["graph_relation"],
                }
            )
        return candidate_papers

    def _merge_candidate_papers(
        self,
        current: List[Dict[str, Any]],
        additions: List[Dict[str, Any]],
        *,
        limit: int = 8,
    ) -> List[Dict[str, Any]]:
        merged: List[Dict[str, Any]] = []
        index_by_key: Dict[str, Dict[str, Any]] = {}
        for item in current + additions:
            paper_id = str(item.get("paper_id") or "").strip()
            title = str(item.get("title") or "").strip()
            dedupe_key = paper_id or title
            if not dedupe_key:
                continue
            if dedupe_key in index_by_key:
                existing = index_by_key[dedupe_key]
                existing_reasons = set(existing.get("match_reasons", []))
                existing_reasons.update(item.get("match_reasons", []))
                existing["match_reasons"] = sorted(existing_reasons)
                if existing.get("source") != item.get("source") and item.get("source"):
                    existing["source"] = "hybrid_mixed"
                for field in ("summary", "url", "title"):
                    if not existing.get(field) and item.get(field):
                        existing[field] = item.get(field)
                continue
            clone = dict(item)
            merged.append(clone)
            index_by_key[dedupe_key] = clone
            if len(merged) >= limit:
                break
        return merged

    def _merge_evidence_items(
        self,
        current: List[Dict[str, Any]],
        additions: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        merged: List[Dict[str, Any]] = []
        seen = set()
        for item in current + additions:
            dedupe_key = (
                str(item.get("paper_id") or ""),
                str(item.get("evidence_type") or ""),
                str(item.get("source_ref") or ""),
            )
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            merged.append(dict(item))
        return merged

    def _expand_related_candidates(
        self,
        query: str,
        candidate_papers: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        pool = self._paper_search(query)
        if not pool:
            pool = self._paper_search("")
        family = self._infer_family(query, candidate_papers, pool)
        related_rows = [row for row in pool if self._row_matches_family(row, family)]
        related_rows = self._prioritize_rows_for_graph_expand(query, related_rows)
        expanded: List[Dict[str, Any]] = []
        for row in related_rows[:6]:
            expanded.append(
                {
                    "paper_id": row.get("id"),
                    "title": row.get("title"),
                    "summary": row.get("summary_main_ideas"),
                    "source": "graph_expand",
                    "url": row.get("url"),
                    "match_reasons": self._graph_match_reasons(row, family),
                }
            )
        return expanded

    def _counter_evidence_candidates(self, query: str) -> List[Dict[str, Any]]:
        expanded: List[Dict[str, Any]] = []
        negative_probe = f"semantic::contradict regression failure negative results {query}"
        for row in self._paper_search(negative_probe)[:4]:
            expanded.append(
                {
                    "paper_id": row.get("id"),
                    "title": row.get("title"),
                    "summary": row.get("summary_main_ideas"),
                    "source": "counter_evidence_probe",
                    "url": row.get("url"),
                    "match_reasons": ["counter_evidence_probe"],
                }
            )
        return expanded

    def _graph_evidence_items(
        self,
        candidate_papers: List[Dict[str, Any]],
        text: str,
        *,
        polarity: str,
    ) -> List[Dict[str, Any]]:
        evidence: List[Dict[str, Any]] = []
        for item in candidate_papers[:3]:
            evidence.append(
                {
                    "paper_id": item.get("paper_id"),
                    "evidence_type": "graph_summary",
                    "polarity": item.get("polarity", polarity),
                    "source_ref": item.get("url") or text[:160],
                    "method": item.get("title"),
                }
            )
        return evidence

    def _prioritize_semantic_rows(
        self,
        query: str,
        rows: List[Dict[str, Any]],
        *,
        intent: str,
    ) -> List[Dict[str, Any]]:
        family = self._infer_family(query, [], rows)
        lowered_query = query.lower()

        def score(row: Dict[str, Any]) -> tuple:
            paper_id = str(row.get("id") or "")
            text = " ".join(
                str(row.get(key) or "")
                for key in ("title", "summary_main_ideas", "summary_methods", "summary_results", "summary_limitations")
            ).lower()
            family_match = 1 if self._row_matches_family(row, family) else 0
            recent = 1 if paper_id.startswith(("24", "25")) else 0
            comparability = 1 if "comparable" in text or "different setup" in text else 0
            support = 1 if any(token in text for token in ("support", "improve", "better")) else 0
            contradict = 1 if any(token in text for token in ("contradict", "regression", "negative")) else 0
            compare_intent = 1 if intent == "comparison" and (
                comparability or ("compare" in lowered_query and family_match)
            ) else 0
            xval_intent = 1 if intent == "cross_validation" and (support or contradict) else 0
            return (compare_intent, xval_intent, family_match, recent, comparability, support + contradict)

        return sorted(rows, key=score, reverse=True)

    def _rerank_evidence_items(
        self,
        *,
        evidence_items: List[Dict[str, Any]],
        filtered_inputs: List[str],
    ) -> List[Dict[str, Any]]:
        if not filtered_inputs:
            return evidence_items
        by_serialized = {
            json.dumps(item, sort_keys=True): item
            for item in evidence_items
            if isinstance(item, dict)
        }
        reranked: List[Dict[str, Any]] = []
        seen = set()
        for serialized in filtered_inputs:
            item = by_serialized.get(serialized)
            if not item:
                continue
            clone = dict(item)
            clone["evidence_type"] = "critic_filtered"
            clone["rerank_source"] = "evidence_item"
            dedupe_key = (
                str(clone.get("paper_id") or ""),
                str(clone.get("source_ref") or ""),
            )
            seen.add(dedupe_key)
            reranked.append(clone)
        for item in evidence_items:
            dedupe_key = (
                str(item.get("paper_id") or ""),
                str(item.get("source_ref") or ""),
            )
            if dedupe_key in seen:
                continue
            reranked.append(item)
        return reranked

    def _infer_family(
        self,
        query: str,
        candidate_papers: List[Dict[str, Any]],
        pool: List[Dict[str, Any]],
    ) -> str:
        text = " ".join(
            [query]
            + [str(item.get("title") or "") for item in candidate_papers]
            + [str(row.get("summary_main_ideas") or "") for row in pool[:5]]
        ).lower()
        if any(token in text for token in ("graph", "rag", "multi-hop", "hotpot", "2wiki")):
            return "graph"
        if any(token in text for token in ("transformer", "attention", "long context")):
            return "transformer"
        return "generic"

    def _row_matches_family(self, row: Dict[str, Any], family: str) -> bool:
        text = " ".join(
            str(row.get(key) or "")
            for key in ("title", "summary_main_ideas", "summary_methods", "summary_results")
        ).lower()
        if family == "graph":
            return any(token in text for token in ("graph", "hotpot", "2wiki", "multi-hop"))
        if family == "transformer":
            return any(token in text for token in ("transformer", "attention", "context"))
        return True

    def _prioritize_rows_for_graph_expand(
        self,
        query: str,
        rows: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        family = self._infer_family(query, [], rows)

        def score(row: Dict[str, Any]) -> tuple:
            paper_id = str(row.get("id") or "")
            text = " ".join(
                str(row.get(key) or "")
                for key in ("title", "summary_main_ideas", "summary_methods", "summary_results")
            ).lower()
            classic = 1 if paper_id == "1706.03762" else 0
            recent = 1 if paper_id.startswith(("24", "25")) else 0
            family_match = 1 if self._row_matches_family(row, family) else 0
            support = 1 if "improve" in text or "better" in text or "support" in text else 0
            contradict = 1 if "contradict" in text or "regression" in text or "negative" in text else 0
            return (family_match, classic, recent, support + contradict)

        return sorted(rows, key=score, reverse=True)

    def _graph_match_reasons(self, row: Dict[str, Any], family: str) -> List[str]:
        reasons = ["graph_relation"]
        paper_id = str(row.get("id") or "")
        if paper_id == "1706.03762":
            reasons.append("classic_baseline")
        if paper_id.startswith(("24", "25")):
            reasons.append("recent_followup")
        if family == "graph":
            reasons.append("same_method_family")
        if family == "transformer":
            reasons.append("attention_family")
        return reasons

    def _infer_intent(self, query: str) -> str:
        lowered = (query or "").lower()
        if any(token in lowered for token in ("compare", "comparison", "different", "difference")):
            return "comparison"
        if any(
            token in lowered
            for token in ("cross-validate", "cross validate", "support", "contradict", "validated")
        ):
            return "cross_validation"
        if any(token in lowered for token in ("related work", "related", "follow-up", "similar")):
            return "related_work"
        if any(token in lowered for token in ("summarize", "summary", "consensus", "evidence landscape")):
            return "synthesis"
        return "lookup"

    def _baseline_evidence_items(self, row: Dict[str, Any], *, intent: str) -> List[Dict[str, Any]]:
        paper_id = row.get("id")
        items: List[Dict[str, Any]] = []
        if intent == "comparison":
            items.append(
                {
                    "paper_id": paper_id,
                    "evidence_type": "result_tuple",
                    "method": row.get("summary_methods") or row.get("summary_main_ideas"),
                    "dataset": self._extract_dataset(row),
                    "metric": self._extract_metric(row),
                    "value": row.get("summary_results"),
                    "limitation": row.get("summary_limitations"),
                    "polarity": "neutral",
                    "comparability_warning": self._comparability_warning(row),
                    "source_ref": row.get("url") or row.get("title"),
                }
            )
            return items
        if intent == "cross_validation":
            items.append(
                {
                    "paper_id": paper_id,
                    "evidence_type": "claim",
                    "method": row.get("summary_methods") or row.get("summary_main_ideas"),
                    "dataset": self._extract_dataset(row),
                    "metric": self._extract_metric(row),
                    "value": row.get("summary_results"),
                    "limitation": row.get("summary_limitations"),
                    "polarity": self._infer_polarity(row),
                    "source_ref": row.get("url") or row.get("title"),
                }
            )
            return items
        items.append(
            {
                "paper_id": paper_id,
                "evidence_type": "summary",
                "method": row.get("summary_methods"),
                "dataset": self._extract_dataset(row),
                "metric": self._extract_metric(row),
                "value": row.get("summary_results"),
                "limitation": row.get("summary_limitations"),
                "polarity": "support" if row.get("summary_results") else "unknown",
                "source_ref": row.get("url") or row.get("title"),
            }
        )
        return items

    def _extract_dataset(self, row: Dict[str, Any]) -> Optional[str]:
        text = " ".join(
            str(row.get(key) or "")
            for key in ("summary_main_ideas", "summary_methods", "summary_results", "summary_limitations")
        ).lower()
        for dataset in ("hotpotqa", "2wiki", "mmlu", "gsm8k"):
            if dataset in text:
                return dataset.upper() if dataset == "mmlu" else dataset
        return None

    def _extract_metric(self, row: Dict[str, Any]) -> Optional[str]:
        text = " ".join(
            str(row.get(key) or "") for key in ("summary_results", "summary_limitations")
        ).lower()
        for metric in ("accuracy", "f1", "em"):
            if metric in text:
                return metric.upper() if metric in {"f1", "em"} else metric
        return None

    def _comparability_warning(self, row: Dict[str, Any]) -> Optional[str]:
        limitation = str(row.get("summary_limitations") or "").lower()
        if any(token in limitation for token in ("different setup", "non-comparable", "not directly comparable")):
            return "non-comparable"
        return None

    def _infer_polarity(self, row: Dict[str, Any]) -> str:
        results = str(row.get("summary_results") or "").lower()
        limitations = str(row.get("summary_limitations") or "").lower()
        if any(token in limitations for token in ("contradict", "fails", "negative", "regression")):
            return "contradict"
        if any(token in results for token in ("contradict", "fails", "negative", "regression", "worse")):
            return "contradict"
        if any(token in results for token in ("improve", "gain", "better", "support")):
            return "support"
        return "neutral"

    def _answer_handoff(
        self, query: str, handoffs: List[HandoffEnvelope], context: str
    ) -> HandoffEnvelope:
        started = time.perf_counter()
        payload = {
            "query": query,
            "context_preview": context[:400],
            "handoff_count": len(handoffs),
            "mode": "answer_synthesis_ready",
        }
        return HandoffEnvelope(
            role=AgentRole.ANSWER,
            ok=True,
            payload=payload,
            latency_ms=int((time.perf_counter() - started) * 1000),
        )


def parse_runtime_profile(raw: Optional[str]) -> Optional[RuntimeProfile]:
    if raw is None:
        return None
    normalized = raw.strip().lower()
    if not normalized:
        return None
    if normalized in {"baseline", "local", "vector"}:
        return RuntimeProfile.BASELINE
    if normalized in {"hybrid", "hybrid_local"}:
        return RuntimeProfile.HYBRID
    if normalized in {"graph_expand", "graph", "graph_retrieval"}:
        return RuntimeProfile.GRAPH_EXPAND
    if normalized in {"graph_verify", "graph_critic", "graph+critic", "graph_retrieval_critic"}:
        return RuntimeProfile.GRAPH_VERIFY
    return None
