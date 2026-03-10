import asyncio

from backend.multi_agent_runtime import (
    AgentRole,
    MultiAgentRuntime,
    RuntimeProfile,
    parse_runtime_profile,
)


def test_parse_runtime_profile_aliases():
    assert parse_runtime_profile("baseline") == RuntimeProfile.BASELINE
    assert parse_runtime_profile("vector") == RuntimeProfile.BASELINE
    assert parse_runtime_profile("graph") == RuntimeProfile.GRAPH
    assert parse_runtime_profile("graph+critic") == RuntimeProfile.GRAPH_CRITIC
    assert parse_runtime_profile("unknown") is None


def test_runtime_baseline_handoffs(monkeypatch):
    runtime = MultiAgentRuntime()

    monkeypatch.setattr(
        "backend.multi_agent_runtime.manager.search_local_papers",
        lambda q: [{"id": "1706.03762", "title": "Attention", "summary_main_ideas": "Transformer"}],
    )
    monkeypatch.setattr("backend.multi_agent_runtime.get_user_profile", lambda: "profile-ok")
    monkeypatch.setattr("backend.multi_agent_runtime.get_user_history", lambda: "history-ok")

    result = asyncio.run(runtime.run("test query", RuntimeProfile.BASELINE, "pref"))
    assert result.profile == RuntimeProfile.BASELINE
    assert result.route == "local-worker-first"
    assert [h.role for h in result.handoffs] == [
        AgentRole.ORCHESTRATOR,
        AgentRole.RETRIEVAL,
        AgentRole.PREFERENCE,
        AgentRole.VERIFIER,
        AgentRole.ANSWER,
    ]
    retrieval = result.handoffs[1]
    assert retrieval.ok is True
    assert retrieval.payload["mode"] == "baseline_local_vector"
    assert retrieval.fallback_used is False
    assert result.answer_envelope.role == AgentRole.ANSWER
    assert result.answer_envelope.ok is True


def test_runtime_retrieval_fallback(monkeypatch):
    runtime = MultiAgentRuntime()

    def raise_graph(_q: str) -> str:
        raise RuntimeError("graph unavailable")

    monkeypatch.setattr("backend.multi_agent_runtime.query_rag", raise_graph)
    monkeypatch.setattr("backend.multi_agent_runtime.get_user_profile", lambda: "")
    monkeypatch.setattr("backend.multi_agent_runtime.get_user_history", lambda: "")

    result = asyncio.run(runtime.run("query", RuntimeProfile.GRAPH, None))
    retrieval = result.handoffs[1]
    assert retrieval.ok is True
    assert retrieval.fallback_used is True
    assert retrieval.payload["mode"] == "fallback_web_retrieval"
