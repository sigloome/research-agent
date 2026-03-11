from __future__ import annotations

import asyncio
import json
import os
import shutil
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, Iterable, List, Optional


def _parse_json_line(line: str) -> Optional[Dict[str, Any]]:
    stripped = (line or "").strip()
    if not stripped or not stripped.startswith("{"):
        return None
    try:
        obj = json.loads(stripped)
    except json.JSONDecodeError:
        return None
    return obj if isinstance(obj, dict) else None


def codex_jsonl_to_ui_events(lines: Iterable[str], return_code: int) -> List[Dict[str, Any]]:
    """Convert codex JSONL + diagnostics to UI-message event payloads.

    This helper is deterministic and used by tests to validate parser behavior.
    """
    events: List[Dict[str, Any]] = []
    started = False
    emitted_error = False
    diagnostics: List[str] = []
    usage: Dict[str, Any] = {}
    text_part_id = "text-1"

    def start_if_needed() -> None:
        nonlocal started
        if started:
            return
        started = True
        events.append({"type": "start"})
        events.append({"type": "start-step"})
        events.append({"type": "text-start", "id": text_part_id})

    for raw in lines:
        event = _parse_json_line(raw)
        if event is None:
            stripped = (raw or "").strip()
            if stripped:
                diagnostics.append(stripped)
                if len(diagnostics) > 5:
                    diagnostics.pop(0)
            continue

        evt_type = str(event.get("type", ""))
        if evt_type in {"thread.started", "turn.started"}:
            start_if_needed()
            continue

        if evt_type == "item.completed":
            item = event.get("item", {})
            if isinstance(item, dict) and item.get("type") == "agent_message":
                text = str(item.get("text", ""))
                if text:
                    start_if_needed()
                    events.append({"type": "text-delta", "id": text_part_id, "delta": text})
            continue

        if evt_type == "turn.completed":
            turn_usage = event.get("usage")
            if isinstance(turn_usage, dict):
                usage = turn_usage
            continue

        if evt_type in {"error", "turn.failed"} and not emitted_error:
            start_if_needed()
            msg = event.get("message")
            if not isinstance(msg, str) and isinstance(event.get("error"), dict):
                msg = str(event["error"].get("message", "unknown error"))
            events.append({"type": "error", "errorText": msg or "codex error"})
            emitted_error = True

    start_if_needed()
    if return_code != 0 and not emitted_error:
        details = "; ".join(diagnostics[-3:]) if diagnostics else "codex exited non-zero"
        events.append({"type": "error", "errorText": details})
    events.append({"type": "text-end", "id": text_part_id})
    events.append({"type": "finish-step"})
    if return_code == 0 and usage:
        events.append({"type": "data-metrics", "data": usage})
        events.append({"type": "finish", "finishReason": "stop"})
    elif return_code == 0:
        events.append({"type": "finish", "finishReason": "stop"})
    else:
        events.append({"type": "finish", "finishReason": "error"})
    return events


async def stream_codex_sdk(
    *,
    format_chunk,
    query: str,
    cwd: Path,
    codex_model: str,
    profile: Optional[str] = None,
) -> AsyncGenerator[str, None]:
    """Run local @openai/codex-sdk adapter and stream UI-message SSE chunks."""
    node_bin = shutil.which("node")
    text_part_id = "text-1"
    adapter_path = cwd / "backend" / "codex_sdk_adapter" / "run_stream.mjs"

    if not node_bin:
        yield format_chunk({"type": "start"})
        yield format_chunk({"type": "start-step"})
        yield format_chunk({"type": "text-start", "id": text_part_id})
        yield format_chunk({"type": "error", "errorText": "node binary not found in PATH"})
        yield format_chunk({"type": "text-end", "id": text_part_id})
        yield format_chunk({"type": "finish-step"})
        yield format_chunk({"type": "finish", "finishReason": "error"})
        return

    if not adapter_path.exists():
        yield format_chunk({"type": "start"})
        yield format_chunk({"type": "start-step"})
        yield format_chunk({"type": "text-start", "id": text_part_id})
        yield format_chunk({"type": "error", "errorText": f"codex sdk adapter missing: {adapter_path}"})
        yield format_chunk({"type": "text-end", "id": text_part_id})
        yield format_chunk({"type": "finish-step"})
        yield format_chunk({"type": "finish", "finishReason": "error"})
        return

    effective_model = (
        os.environ.get("CODEX_SDK_MODEL", "").strip()
        or os.environ.get("CODEX_EXEC_MODEL", "").strip()
        or codex_model
    )
    payload = {
        "input": query,
        "model": effective_model,
        "workingDirectory": str(cwd),
        "skipGitRepoCheck": True,
        "networkAccessEnabled": True,
    }
    # The current @openai/codex-sdk thread options do not expose profile selection directly.
    if profile:
        payload["profile_note"] = profile

    proc = await asyncio.create_subprocess_exec(
        node_bin,
        str(adapter_path),
        cwd=str(cwd),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        stdin=asyncio.subprocess.PIPE,
    )

    if proc.stdin is not None:
        proc.stdin.write(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
        await proc.stdin.drain()
        proc.stdin.close()

    lines: List[str] = []
    while True:
        if proc.stdout is None:
            break
        raw = await proc.stdout.readline()
        if not raw:
            break
        lines.append(raw.decode("utf-8", errors="replace").rstrip("\n"))

    rc = await proc.wait()
    for payload in codex_jsonl_to_ui_events(lines, return_code=rc):
        yield format_chunk(payload)
