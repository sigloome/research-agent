from __future__ import annotations

import asyncio
import sys
import types


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


def test_runtime_result_contains_structured_retrieval_context(monkeypatch):
    _install_runtime_stubs()
    from backend.multi_agent_runtime import MultiAgentRuntime, RuntimeProfile

    runtime = MultiAgentRuntime()
    monkeypatch.setattr(
        "backend.multi_agent_runtime.manager.search_local_papers",
        lambda q: [
            {
                "id": "1706.03762",
                "title": "Attention Is All You Need",
                "summary_main_ideas": "Transformer baseline",
                "url": "https://arxiv.org/abs/1706.03762",
            }
        ],
    )
    monkeypatch.setattr("backend.multi_agent_runtime.get_user_profile", lambda: "profile-ok")
    monkeypatch.setattr("backend.multi_agent_runtime.get_user_history", lambda: "history-ok")

    result = asyncio.run(runtime.run("transformer", RuntimeProfile.BASELINE, "pref"))
    retrieval = result.handoffs[1]
    payload = retrieval.payload

    assert payload["intent"] == "lookup"
    assert payload["candidate_papers"][0]["paper_id"] == "1706.03762"
    assert "coverage_audit" in payload
    assert payload["coverage_audit"]["has_classic_baseline"] is True
    assert result.answer_context.startswith("[RetrievalContext]")
    assert '"candidate_papers"' in result.answer_context


def test_graph_expand_related_work_adds_classic_and_recent_coverage(monkeypatch):
    _install_runtime_stubs()
    from backend.multi_agent_runtime import MultiAgentRuntime, RuntimeProfile

    rows = [
        {
            "id": "1706.03762",
            "title": "Attention Is All You Need",
            "summary_main_ideas": "Transformer architecture for sequence transduction.",
            "summary_methods": "Self-attention transformer baseline.",
            "summary_results": "Improves accuracy on MT.",
            "summary_limitations": "Different setup than graph retrieval papers.",
            "url": "https://arxiv.org/abs/1706.03762",
        },
        {
            "id": "2401.00003",
            "title": "Long Context Attention Extension",
            "summary_main_ideas": "Extends attention for longer contexts.",
            "summary_methods": "Long-context transformer attention extension.",
            "summary_results": "Improves accuracy on longer-context benchmark.",
            "summary_limitations": "Higher latency and different setup.",
            "url": "https://arxiv.org/abs/2401.00003",
        },
        {
            "id": "2301.00001",
            "title": "Sparse Transformer Retrieval",
            "summary_main_ideas": "Sparse attention for retrieval.",
            "summary_methods": "Sparse transformer retrieval method.",
            "summary_results": "Improves retrieval accuracy on benchmark.",
            "summary_limitations": "Limited evidence on multi-hop QA.",
            "url": "https://arxiv.org/abs/2301.00001",
        },
    ]

    monkeypatch.setattr("backend.multi_agent_runtime.get_user_profile", lambda: "profile-ok")
    monkeypatch.setattr("backend.multi_agent_runtime.get_user_history", lambda: "history-ok")

    runtime = MultiAgentRuntime(
        paper_search_fn=lambda _query: rows,
        graph_query_fn=lambda *_args, **_kwargs: "",
    )
    result = asyncio.run(
        runtime.run(
            "Which papers extend transformer attention for longer context windows?",
            RuntimeProfile.GRAPH_EXPAND,
            None,
        )
    )
    retrieval = result.retrieval_context
    candidate_ids = [item["paper_id"] for item in retrieval["candidate_papers"]]

    assert "1706.03762" in candidate_ids
    assert "2401.00003" in candidate_ids
    assert retrieval["coverage_audit"]["has_classic_baseline"] is True
    assert retrieval["coverage_audit"]["has_recent_followup"] is True


def test_hybrid_adds_semantic_only_candidate_over_baseline(monkeypatch):
    _install_runtime_stubs()
    from backend.multi_agent_runtime import MultiAgentRuntime, RuntimeProfile

    rows = [
        {
            "id": "lex-1",
            "title": "GraphRAG for Multi-Hop QA",
            "summary_main_ideas": "Graph retrieval on HotpotQA.",
            "summary_methods": "Graph retrieval.",
            "summary_results": "Improves F1 on HotpotQA.",
            "summary_limitations": "",
            "url": "https://arxiv.org/abs/lex-1",
        },
        {
            "id": "sem-1",
            "title": "Evidence Routing for Linked Reasoning",
            "summary_main_ideas": "Linked reasoning with evidence routing on HotpotQA multi-hop tasks.",
            "summary_methods": "Evidence routing with linked reasoning.",
            "summary_results": "Better EM on HotpotQA.",
            "summary_limitations": "",
            "url": "https://arxiv.org/abs/sem-1",
        },
    ]

    def search(query: str):
        if "semantic::" in query:
            return [rows[1]]
        return [rows[0]]

    monkeypatch.setattr("backend.multi_agent_runtime.get_user_profile", lambda: "profile-ok")
    monkeypatch.setattr("backend.multi_agent_runtime.get_user_history", lambda: "history-ok")

    runtime = MultiAgentRuntime(paper_search_fn=search)
    baseline = asyncio.run(runtime.run("graph retrieval hotpot", RuntimeProfile.BASELINE, None))
    hybrid = asyncio.run(runtime.run("graph retrieval hotpot", RuntimeProfile.HYBRID, None))

    baseline_ids = [item["paper_id"] for item in baseline.retrieval_context["candidate_papers"]]
    hybrid_ids = [item["paper_id"] for item in hybrid.retrieval_context["candidate_papers"]]

    assert baseline_ids == ["lex-1"]
    assert "sem-1" in hybrid_ids
    assert len(hybrid_ids) > len(baseline_ids)


def test_graph_expand_marks_two_or_more_cluster_reasons(monkeypatch):
    _install_runtime_stubs()
    from backend.multi_agent_runtime import MultiAgentRuntime, RuntimeProfile

    rows = [
        {
            "id": "1706.03762",
            "title": "Attention Is All You Need",
            "summary_main_ideas": "Transformer architecture.",
            "summary_methods": "Self-attention transformer baseline.",
            "summary_results": "Improves accuracy.",
            "summary_limitations": "Different setup.",
            "url": "https://arxiv.org/abs/1706.03762",
        },
        {
            "id": "2401.00003",
            "title": "Long Context Attention Extension",
            "summary_main_ideas": "Extends attention for longer contexts.",
            "summary_methods": "Long-context transformer attention extension.",
            "summary_results": "Improves accuracy on longer-context benchmark.",
            "summary_limitations": "Higher latency and different setup.",
            "url": "https://arxiv.org/abs/2401.00003",
        },
        {
            "id": "2301.00001",
            "title": "Sparse Transformer Retrieval",
            "summary_main_ideas": "Sparse attention for retrieval.",
            "summary_methods": "Sparse transformer retrieval method.",
            "summary_results": "Improves retrieval accuracy.",
            "summary_limitations": "Limited evidence on multi-hop QA.",
            "url": "https://arxiv.org/abs/2301.00001",
        },
    ]

    monkeypatch.setattr("backend.multi_agent_runtime.get_user_profile", lambda: "profile-ok")
    monkeypatch.setattr("backend.multi_agent_runtime.get_user_history", lambda: "history-ok")
    runtime = MultiAgentRuntime(paper_search_fn=lambda _query: rows, graph_query_fn=lambda *_a, **_k: "")

    result = asyncio.run(
        runtime.run(
            "Which papers extend transformer attention for longer context windows?",
            RuntimeProfile.GRAPH_EXPAND,
            None,
        )
    )
    reasons = {
        reason
        for item in result.retrieval_context["candidate_papers"]
        for reason in item.get("match_reasons", [])
    }
    assert "classic_baseline" in reasons
    assert "recent_followup" in reasons


def test_graph_verify_reranks_structured_evidence_and_checks_counter_evidence(monkeypatch):
    _install_runtime_stubs()
    from backend.multi_agent_runtime import MultiAgentRuntime, RuntimeProfile

    rows = [
        {
            "id": "2402.54321",
            "title": "GraphRAG Validation Study",
            "summary_main_ideas": "Follow-up validation on HotpotQA showing support evidence.",
            "summary_methods": "Graph retrieval validated on HotpotQA.",
            "summary_results": "Improves EM on HotpotQA and supports prior graph retrieval claims.",
            "summary_limitations": "Still uses different setup.",
            "url": "https://arxiv.org/abs/2402.54321",
        },
        {
            "id": "2402.09999",
            "title": "GraphRAG Failure Modes",
            "summary_main_ideas": "Analysis finds regression on some reasoning settings.",
            "summary_methods": "Failure analysis for graph retrieval on reasoning tasks.",
            "summary_results": "Negative regression on some MMLU settings.",
            "summary_limitations": "Non-comparable on some datasets and shows failure cases.",
            "url": "https://arxiv.org/abs/2402.09999",
        },
    ]

    class _Critic:
        async def retrieve_and_filter(self, query, chunks):
            assert "contradict" in " ".join(chunks).lower()
            return list(reversed(chunks))

    monkeypatch.setattr("backend.multi_agent_runtime.get_user_profile", lambda: "profile-ok")
    monkeypatch.setattr("backend.multi_agent_runtime.get_user_history", lambda: "history-ok")
    runtime = MultiAgentRuntime(
        paper_search_fn=lambda _query: rows,
        graph_query_fn=lambda *_a, **_k: "",
        critic=_Critic(),
    )

    result = asyncio.run(
        runtime.run(
            "Has the claim about graph retrieval improving multi-hop QA been supported or contradicted?",
            RuntimeProfile.GRAPH_VERIFY,
            None,
        )
    )
    retrieval = result.retrieval_context
    assert retrieval["coverage_audit"]["counter_evidence_checked"] is True
    assert retrieval["coverage_audit"]["has_counter_evidence"] is True
    assert any(item.get("evidence_type") == "critic_filtered" for item in retrieval["evidence_items"])
