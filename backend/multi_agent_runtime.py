"""Explicit multi-agent runtime skeleton with typed handoff contracts.

The runtime is opt-in and compatible with the existing orchestrator path:
- default chat path keeps legacy behavior
- benchmark/profile mode can enable explicit multi-agent routing
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from backend.logging_config import get_logger
from skills.knowledge.db import manager
from skills.knowledge.graph_rag import query_rag
from skills.knowledge.rag_critic.retriever import HierarchicalRetriever
from skills.preference.implementation import get_user_history, get_user_profile

logger = get_logger()


class RuntimeProfile(str, Enum):
    BASELINE = "baseline"
    GRAPH = "graph"
    GRAPH_CRITIC = "graph_critic"


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
    answer_context: str
    verifier_summary: str


class MultiAgentRuntime:
    """Orchestrates retrieval/preference/verifier sub-agents before answer step."""

    def __init__(self) -> None:
        self._critic = HierarchicalRetriever()

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

        context = self._build_answer_context(query=query, handoffs=handoffs)
        return RuntimeResult(
            profile=profile,
            route=route,
            handoffs=handoffs,
            answer_context=context,
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

            if profile == RuntimeProfile.GRAPH:
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
        papers = manager.search_local_papers(query) or []
        compact = []
        for row in papers[:5]:
            if not isinstance(row, dict):
                continue
            compact.append(
                {
                    "id": row.get("id"),
                    "title": row.get("title"),
                    "summary": row.get("summary_main_ideas"),
                    "source": "local_vector",
                }
            )
        return {"mode": "baseline_local_vector", "items": compact}

    def _retrieve_graph(self, query: str) -> Dict[str, Any]:
        answer = query_rag(query, mode="global")
        return {"mode": "graph_retrieval", "graph_answer": str(answer)}

    async def _retrieve_graph_with_critic(self, query: str) -> Dict[str, Any]:
        graph_answer = str(query_rag(query, mode="hybrid"))
        chunks = [line.strip() for line in graph_answer.splitlines() if line.strip()]
        if not chunks:
            chunks = [graph_answer]
        filtered = await self._critic.retrieve_and_filter(query, chunks[:8])
        return {
            "mode": "graph_retrieval_with_critic",
            "graph_answer": graph_answer,
            "filtered_chunks": filtered,
        }

    def _fallback_web_retrieval(self, query: str) -> Dict[str, Any]:
        return {
            "mode": "fallback_web_retrieval",
            "web_query": query,
            "reason": "local retrieval path unavailable",
        }

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
        serializable = [item.to_dict() for item in handoffs]
        return (
            "[Multi-Agent Runtime Context]\n"
            "Use the following validated handoff envelopes for answer synthesis.\n\n"
            f"Original query:\n{query}\n\n"
            "Handoffs(JSON):\n"
            f"{serializable}"
        )


def parse_runtime_profile(raw: Optional[str]) -> Optional[RuntimeProfile]:
    if raw is None:
        return None
    normalized = raw.strip().lower()
    if not normalized:
        return None
    if normalized in {"baseline", "local", "vector"}:
        return RuntimeProfile.BASELINE
    if normalized in {"graph", "graph_retrieval"}:
        return RuntimeProfile.GRAPH
    if normalized in {"graph_critic", "graph+critic", "graph_retrieval_critic"}:
        return RuntimeProfile.GRAPH_CRITIC
    return None

