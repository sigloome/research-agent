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


_install_runtime_stubs()

from backend.multi_agent_runtime import (
    AgentRole,
    MultiAgentRuntime,
    RuntimeProfile,
    parse_runtime_profile,
)


def test_parse_runtime_profile_aliases():
    assert parse_runtime_profile("baseline") == RuntimeProfile.BASELINE
    assert parse_runtime_profile("vector") == RuntimeProfile.BASELINE
    assert parse_runtime_profile("hybrid") == RuntimeProfile.HYBRID
    assert parse_runtime_profile("graph") == RuntimeProfile.GRAPH_EXPAND
    assert parse_runtime_profile("graph+critic") == RuntimeProfile.GRAPH_VERIFY
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

    result = asyncio.run(runtime.run("query", RuntimeProfile.GRAPH_EXPAND, None))
    retrieval = result.handoffs[1]
    assert retrieval.ok is True
    assert retrieval.fallback_used is True
    assert retrieval.payload["mode"] == "fallback_web_retrieval"
