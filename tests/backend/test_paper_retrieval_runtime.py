from __future__ import annotations

import asyncio
import sys
import types


def _install_test_stubs() -> None:
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
        logging_mod.get_skill_logger = lambda *_args, **_kwargs: _Logger()
        sys.modules["backend.logging_config"] = logging_mod

    if "structlog" not in sys.modules:
        structlog = types.ModuleType("structlog")

        structlog.get_logger = lambda *_args, **_kwargs: _Logger()
        structlog.configure = lambda *_args, **_kwargs: None
        structlog.make_filtering_bound_logger = lambda *_args, **_kwargs: _Logger
        structlog.processors = types.SimpleNamespace(
            TimeStamper=lambda **_kwargs: None,
            add_log_level=None,
            StackInfoRenderer=None,
            format_exc_info=None,
            UnicodeDecoder=None,
            JSONRenderer=lambda **_kwargs: None,
        )
        structlog.dev = types.SimpleNamespace(ConsoleRenderer=lambda **_kwargs: None)
        structlog.stdlib = types.SimpleNamespace(
            add_logger_name=None,
            add_log_level=None,
            PositionalArgumentsFormatter=None,
            ProcessorFormatter=types.SimpleNamespace(
                wrap_for_formatter=lambda *_args, **_kwargs: None
            ),
            LoggerFactory=lambda *_args, **_kwargs: None,
            BoundLogger=_Logger,
        )
        sys.modules["structlog"] = structlog
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


def test_run_codex_sdk_injects_structured_retrieval_context_when_runtime_profile_present(monkeypatch):
    _install_test_stubs()
    from backend.agent import MainAgent
    from backend.multi_agent_runtime import RuntimeProfile

    agent = MainAgent()
    captured = {}

    async def fake_stream_codex_sdk(**kwargs):
        captured["query"] = kwargs["query"]
        yield agent._format_chunk({"type": "finish", "finishReason": "stop"})

    async def fake_runtime_run(query, profile, user_preferences=None):
        class _Result:
            answer_context = (
                "[RetrievalContext]\n"
                '{"profile":"baseline","intent":"lookup",'
                '"candidate_papers":[{"paper_id":"1706.03762"}],'
                '"evidence_items":[],"coverage_audit":{"has_classic_baseline":true}}'
            )
            verifier_summary = "ready_for_answer"

        assert query == "transformer paper"
        assert profile == RuntimeProfile.BASELINE
        assert user_preferences == "pref-summary"
        return _Result()

    monkeypatch.setattr("backend.agent.stream_codex_sdk", fake_stream_codex_sdk)
    monkeypatch.setattr(agent.multi_agent_runtime, "run", fake_runtime_run)

    async def _collect():
        return [
            chunk
            async for chunk in agent.run(
                query="transformer paper",
                chat_id="default",
                user_preferences="pref-summary",
                conversation_history=None,
                runtime_profile=RuntimeProfile.BASELINE,
            )
        ]

    chunks = asyncio.run(_collect())

    assert any('"type": "finish"' in c for c in chunks)
    assert "[RetrievalContext]" in captured["query"]
    assert '"candidate_papers"' in captured["query"]
    assert '"coverage_audit"' in captured["query"]


def test_run_codex_sdk_does_not_inject_retrieval_context_without_runtime_profile(monkeypatch):
    _install_test_stubs()
    from backend.agent import MainAgent

    agent = MainAgent()
    captured = {}

    async def fake_stream_codex_sdk(**kwargs):
        captured["query"] = kwargs["query"]
        yield agent._format_chunk({"type": "finish", "finishReason": "stop"})

    async def fail_runtime_run(*_args, **_kwargs):
        raise AssertionError("runtime should not run when runtime_profile is None")

    monkeypatch.setattr("backend.agent.stream_codex_sdk", fake_stream_codex_sdk)
    monkeypatch.setattr(agent.multi_agent_runtime, "run", fail_runtime_run)

    async def _collect():
        return [
            chunk
            async for chunk in agent.run(
                query="transformer paper",
                chat_id="default",
                user_preferences=None,
                conversation_history=None,
                runtime_profile=None,
            )
        ]

    chunks = asyncio.run(_collect())

    assert any('"type": "finish"' in c for c in chunks)
    assert "[RetrievalContext]" not in captured["query"]
