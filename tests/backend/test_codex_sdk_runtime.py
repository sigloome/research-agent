from __future__ import annotations

import os

import pytest


@pytest.mark.asyncio
async def test_agent_uses_single_codex_sdk_provider(monkeypatch):
    from backend.agent import MainAgent

    agent = MainAgent()
    assert agent.provider == "codex_sdk"

    async def fake_exec(**_kwargs):
        yield agent._format_chunk({"type": "start"})
        yield agent._format_chunk({"type": "finish", "finishReason": "stop"})

    monkeypatch.setattr(agent, "_run_codex_sdk", fake_exec, raising=False)

    chunks = [
        chunk
        async for chunk in agent.run(
            query="hello",
            chat_id="default",
            user_preferences=None,
            conversation_history=None,
            runtime_profile=None,
        )
    ]

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
