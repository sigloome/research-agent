from __future__ import annotations

import asyncio
import os
import sys
import types

import pytest


def test_agent_uses_single_codex_sdk_provider(monkeypatch):
    if "backend.logging_config" not in sys.modules:
        logging_mod = types.ModuleType("backend.logging_config")

        class _Logger:
            def info(self, *_args, **_kwargs):
                return None

            def warning(self, *_args, **_kwargs):
                return None

            def error(self, *_args, **_kwargs):
                return None

            def debug(self, *_args, **_kwargs):
                return None

        logging_mod.get_logger = lambda *_args, **_kwargs: _Logger()
        logging_mod.get_rag_logger = lambda *_args, **_kwargs: _Logger()
        sys.modules["backend.logging_config"] = logging_mod
    if "structlog" not in sys.modules:
        structlog = types.ModuleType("structlog")
        structlog.get_logger = lambda *_args, **_kwargs: types.SimpleNamespace(
            info=lambda *_a, **_k: None,
            warning=lambda *_a, **_k: None,
            error=lambda *_a, **_k: None,
            debug=lambda *_a, **_k: None,
        )
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

    from backend.agent import MainAgent

    agent = MainAgent()
    assert agent.provider == "codex_sdk"

    async def fake_exec(**_kwargs):
        yield agent._format_chunk({"type": "start"})
        yield agent._format_chunk({"type": "finish", "finishReason": "stop"})

    monkeypatch.setattr(agent, "_run_codex_sdk", fake_exec, raising=False)

    async def _collect():
        return [
            chunk
            async for chunk in agent.run(
                query="hello",
                chat_id="default",
                user_preferences=None,
                conversation_history=None,
                runtime_profile=None,
            )
        ]

    chunks = asyncio.run(_collect())

    assert any('"type": "finish"' in c for c in chunks)


def test_codex_sdk_parser_success_and_failure_contracts():
    from backend.codex_sdk_runtime import codex_jsonl_to_ui_events

    success_lines = [
        '{"type":"thread.started","thread_id":"t1"}',
        '{"type":"turn.started"}',
        '{"type":"item.completed","item":{"id":"i1","type":"agent_message","text":"demo-ok"}}',
        '{"type":"turn.completed","usage":{"input_tokens":10,"output_tokens":3}}',
    ]
    events = codex_jsonl_to_ui_events(success_lines, return_code=0)
    assert events[0]["type"] == "start"
    assert any(e.get("type") == "text-delta" and e.get("delta") == "demo-ok" for e in events)
    assert events[-1] == {"type": "finish", "finishReason": "stop"}

    fail_lines = [
        "Error: config profile `missing` not found",
    ]
    fail_events = codex_jsonl_to_ui_events(fail_lines, return_code=1)
    assert any(e.get("type") == "error" for e in fail_events)
    assert fail_events[-1] == {"type": "finish", "finishReason": "error"}


def test_codex_sdk_parser_maps_mcp_tool_events():
    from backend.codex_sdk_runtime import codex_jsonl_to_ui_events

    lines = [
        '{"type":"thread.started","thread_id":"t1"}',
        '{"type":"turn.started"}',
        '{"type":"item.started","item":{"id":"m1","type":"mcp_tool_call","server":"skills","tool":"knowledge.paper_ingest","arguments":{"source":"2401.12345"},"status":"in_progress"}}',
        '{"type":"item.completed","item":{"id":"m1","type":"mcp_tool_call","server":"skills","tool":"knowledge.paper_ingest","arguments":{"source":"2401.12345"},"status":"completed","result":{"ok":true}}}',
        '{"type":"item.completed","item":{"id":"a1","type":"agent_message","text":"done"}}',
        '{"type":"turn.completed","usage":{"input_tokens":8,"output_tokens":2}}',
    ]
    events = codex_jsonl_to_ui_events(lines, return_code=0)
    types = [e.get("type") for e in events]
    assert "tool-input-start" in types
    assert "tool-input-available" in types
    assert "tool-output-available" in types
    assert any(e.get("type") == "data-native-tooling" for e in events)


def test_codex_sdk_parser_maps_output_text_delta_events():
    from backend.codex_sdk_runtime import codex_jsonl_to_ui_events

    lines = [
        '{"type":"thread.started","thread_id":"t1"}',
        '{"type":"response.output_text.delta","delta":"hello "}',
        '{"type":"response.output_text.delta","delta":"world"}',
        '{"type":"turn.completed","usage":{"input_tokens":4,"output_tokens":2}}',
    ]
    events = codex_jsonl_to_ui_events(lines, return_code=0)
    deltas = [e.get("delta") for e in events if e.get("type") == "text-delta"]
    assert deltas == ["hello ", "world"]


def test_build_codex_runtime_env_isolates_home_and_skills(monkeypatch, tmp_path):
    from backend.codex_sdk_runtime import _build_codex_runtime_env

    cwd = tmp_path / "repo"
    (cwd / "skills" / "knowledge").mkdir(parents=True)
    (cwd / "skills" / "preference").mkdir(parents=True)
    (cwd / "skills" / "knowledge" / "SKILL.md").write_text("# knowledge", encoding="utf-8")
    (cwd / "skills" / "preference" / "SKILL.md").write_text("# preference", encoding="utf-8")

    monkeypatch.setenv("CODEX_RUNTIME_SKILLS", "knowledge,preference")
    env = _build_codex_runtime_env(cwd)

    runtime_home = cwd / ".codex-agent-runtime"
    assert env["HOME"]
    assert env["CODEX_HOME"] == str(runtime_home)
    assert (runtime_home / "config.toml").exists()
    assert (runtime_home / "skills" / "knowledge").exists()
    assert (runtime_home / "skills" / "preference").exists()
