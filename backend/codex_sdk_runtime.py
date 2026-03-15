from __future__ import annotations

import asyncio
import json
import os
import shutil
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, Iterable, List, Optional

from backend.content_filter import ContentFilter, StreamingContentFilter


def _parse_json_line(line: str) -> Optional[Dict[str, Any]]:
    stripped = (line or "").strip()
    if not stripped or not stripped.startswith("{"):
        return None
    try:
        obj = json.loads(stripped)
    except json.JSONDecodeError:
        return None
    return obj if isinstance(obj, dict) else None


class _CodexUiEventMapper:
    """Stateful codex-event -> UI-event mapper for incremental streaming."""

    def __init__(self, *, text_part_id: str = "text-1") -> None:
        self.text_part_id = text_part_id
        self.started = False
        self.emitted_error = False
        self.diagnostics: List[str] = []
        self.usage: Dict[str, Any] = {}
        self.observed_native_tool = False
        self.agent_message_text: Dict[str, str] = {}
        self.text_filter = StreamingContentFilter()
        self.snapshot_filter = ContentFilter()

    def _start_if_needed(self, out: List[Dict[str, Any]]) -> None:
        if self.started:
            return
        self.started = True
        out.append({"type": "start"})
        out.append({"type": "start-step"})
        out.append({"type": "text-start", "id": self.text_part_id})

    def _emit_agent_text_delta(self, item: Dict[str, Any], out: List[Dict[str, Any]]) -> None:
        text = item.get("text")
        if not isinstance(text, str) or not text:
            return
        msg_id = str(item.get("id") or "agent-message")
        filtered_text = self.snapshot_filter.filter_text(text)
        prev = self.agent_message_text.get(msg_id, "")
        if prev == filtered_text:
            return
        delta = filtered_text[len(prev):] if filtered_text.startswith(prev) else filtered_text
        if not delta:
            return
        self._start_if_needed(out)
        out.append({"type": "text-delta", "id": self.text_part_id, "delta": delta})
        self.agent_message_text[msg_id] = filtered_text

    def feed_line(self, raw: str) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        event = _parse_json_line(raw)
        if event is None:
            stripped = (raw or "").strip()
            if stripped:
                self.diagnostics.append(stripped)
                if len(self.diagnostics) > 5:
                    self.diagnostics.pop(0)
            return out

        evt_type = str(event.get("type", ""))
        if evt_type in {"thread.started", "turn.started"}:
            self._start_if_needed(out)
            if evt_type == "thread.started" and isinstance(event.get("thread_id"), str):
                out.append(
                    {
                        "type": "data-provider-thread",
                        "data": {"threadId": event["thread_id"]},
                    }
                )
            return out

        if evt_type in {"response.output_text.delta", "output_text.delta"}:
            delta = event.get("delta")
            if isinstance(delta, str) and delta:
                filtered_delta = (
                    delta
                    if "<" not in delta and "`/" not in delta and "/Users/" not in delta
                    else self.text_filter.filter_chunk(delta)
                )
                if filtered_delta:
                    self._start_if_needed(out)
                    out.append({"type": "text-delta", "id": self.text_part_id, "delta": filtered_delta})
            return out

        if evt_type in {"item.started", "item.updated", "item.completed"}:
            item = event.get("item", {})
            if isinstance(item, dict) and item.get("type") == "mcp_tool_call":
                self.observed_native_tool = True
                call_id = str(item.get("id") or "mcp-call")
                server = str(item.get("server") or "mcp")
                tool = str(item.get("tool") or "tool")
                args = item.get("arguments", {})
                if evt_type == "item.started":
                    self._start_if_needed(out)
                    out.append(
                        {"type": "tool-input-start", "toolCallId": call_id, "toolName": f"{server}.{tool}"}
                    )
                    out.append(
                        {
                            "type": "tool-input-available",
                            "toolCallId": call_id,
                            "toolName": f"{server}.{tool}",
                            "input": args if isinstance(args, dict) else {"raw": args},
                        }
                    )
                    return out
                if evt_type == "item.completed":
                    self._start_if_needed(out)
                    output: Any = item.get("result")
                    if output is None and isinstance(item.get("error"), dict):
                        output = {"error": item["error"].get("message", "mcp tool failed")}
                    if output is None:
                        output = {"status": str(item.get("status", "completed"))}
                    out.append(
                        {
                            "type": "tool-output-available",
                            "toolCallId": call_id,
                            "output": output,
                        }
                    )
                    return out

            if isinstance(item, dict) and item.get("type") == "agent_message":
                self._emit_agent_text_delta(item, out)
            return out

        if evt_type == "turn.completed":
            turn_usage = event.get("usage")
            if isinstance(turn_usage, dict):
                self.usage = turn_usage
            return out

        if evt_type in {"error", "turn.failed"} and not self.emitted_error:
            self._start_if_needed(out)
            msg = event.get("message")
            if not isinstance(msg, str) and isinstance(event.get("error"), dict):
                msg = str(event["error"].get("message", "unknown error"))
            out.append({"type": "error", "errorText": msg or "codex error"})
            self.emitted_error = True
        return out

    def finalize(self, return_code: int) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        self._start_if_needed(out)
        remaining = self.text_filter.flush()
        if remaining:
            out.append({"type": "text-delta", "id": self.text_part_id, "delta": remaining})
        if return_code != 0 and not self.emitted_error:
            details = "; ".join(self.diagnostics[-3:]) if self.diagnostics else "codex exited non-zero"
            out.append({"type": "error", "errorText": details})
        if self.observed_native_tool:
            out.append({"type": "data-native-tooling", "data": {"observed": True}})
        out.append({"type": "text-end", "id": self.text_part_id})
        out.append({"type": "finish-step"})
        if return_code == 0 and self.usage:
            out.append({"type": "data-metrics", "data": self.usage})
            out.append({"type": "finish", "finishReason": "stop"})
        elif return_code == 0:
            out.append({"type": "finish", "finishReason": "stop"})
        else:
            out.append({"type": "finish", "finishReason": "error"})
        return out


def codex_jsonl_to_ui_events(lines: Iterable[str], return_code: int) -> List[Dict[str, Any]]:
    """Convert codex JSONL + diagnostics to UI-message event payloads."""
    mapper = _CodexUiEventMapper()
    events: List[Dict[str, Any]] = []
    for raw in lines:
        events.extend(mapper.feed_line(raw))
    events.extend(mapper.finalize(return_code))
    return events


def _default_runtime_config_toml() -> str:
    return (
        'approval_policy = "never"\n'
        'web_search = "live"\n'
        'model_reasoning_effort = "medium"\n'
        "\n"
        "[sandbox_workspace_write]\n"
        "network_access = true\n"
    )


def _ensure_runtime_skill_home(cwd: Path) -> Path:
    runtime_home = cwd / ".codex-agent-runtime"
    skills_home = runtime_home / "skills"
    runtime_home.mkdir(parents=True, exist_ok=True)
    skills_home.mkdir(parents=True, exist_ok=True)

    raw_names = os.environ.get("CODEX_RUNTIME_SKILLS", "knowledge,preference")
    desired = {name.strip() for name in raw_names.split(",") if name.strip()}
    if not desired:
        desired = {"knowledge", "preference"}

    # Keep runtime skills deterministic and isolated from developer Codex homes.
    for existing in skills_home.iterdir():
        if existing.name not in desired:
            if existing.is_symlink() or existing.is_file():
                existing.unlink(missing_ok=True)
            elif existing.is_dir():
                shutil.rmtree(existing, ignore_errors=True)

    for name in sorted(desired):
        source = cwd / "skills" / name
        target = skills_home / name
        if not source.exists():
            continue
        if target.exists() or target.is_symlink():
            if target.is_symlink() and target.resolve() == source.resolve():
                continue
            if target.is_symlink() or target.is_file():
                target.unlink(missing_ok=True)
            else:
                shutil.rmtree(target, ignore_errors=True)
        try:
            target.symlink_to(source, target_is_directory=True)
        except OSError:
            shutil.copytree(source, target)

    config_path = runtime_home / "config.toml"
    config_text = os.environ.get("CODEX_RUNTIME_CONFIG_TOML", "").strip() or _default_runtime_config_toml()
    config_path.write_text(config_text, encoding="utf-8")

    # Preserve Codex auth/account state while keeping runtime skills isolated.
    source_codex_home = Path(
        os.environ.get("CODEX_SOURCE_HOME", "").strip()
        or os.environ.get("CODEX_HOME", "").strip()
        or (Path.home() / ".codex")
    )
    for name in ("auth.json", "config.toml.account.toml"):
        src = source_codex_home / name
        dst = runtime_home / name
        if src.exists() and not dst.exists():
            try:
                shutil.copy2(src, dst)
            except OSError:
                pass
    return runtime_home


def _build_codex_runtime_env(cwd: Path, runtime_home: Optional[Path] = None) -> Dict[str, str]:
    runtime_home = runtime_home or _ensure_runtime_skill_home(cwd)
    env = dict(os.environ)
    # Keep original HOME so system credential helpers continue to work.
    if "HOME" in os.environ:
        env["HOME"] = os.environ["HOME"]
    env["CODEX_HOME"] = str(runtime_home)
    existing_pythonpath = env.get("PYTHONPATH", "").strip()
    env["PYTHONPATH"] = (
        str(cwd)
        if not existing_pythonpath
        else f"{cwd}{os.pathsep}{existing_pythonpath}"
    )
    return env


async def stream_codex_sdk(
    *,
    format_chunk,
    query: str,
    cwd: Path,
    codex_model: str,
    profile: Optional[str] = None,
    thread_id: Optional[str] = None,
    fallback_query: Optional[str] = None,
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
    runtime_home = _ensure_runtime_skill_home(cwd)
    runtime_workspace = runtime_home / "workspace"
    runtime_workspace.mkdir(parents=True, exist_ok=True)

    payload = {
        "input": query,
        "model": effective_model,
        "workingDirectory": str(runtime_workspace),
        "skipGitRepoCheck": True,
        "networkAccessEnabled": True,
        "codexEnv": _build_codex_runtime_env(cwd, runtime_home),
    }
    if thread_id:
        payload["threadId"] = thread_id
    config_overrides_raw = os.environ.get("CODEX_CONFIG_OVERRIDES_JSON", "").strip()
    if config_overrides_raw:
        try:
            parsed = json.loads(config_overrides_raw)
            if isinstance(parsed, dict):
                payload["configOverrides"] = parsed
        except json.JSONDecodeError:
            pass
    # The current @openai/codex-sdk thread options do not expose profile selection directly.
    if profile:
        payload["profile_note"] = profile

    async def _run_attempt(
        attempt_payload: Dict[str, Any],
        *,
        mode: str,
        cautious: bool,
        fallback_used: bool,
        fallback_error: Optional[str],
        attempt_result: Dict[str, Any],
    ) -> AsyncGenerator[str, None]:
        attempt_result["success"] = False
        proc = await asyncio.create_subprocess_exec(
            node_bin,
            str(adapter_path),
            cwd=str(cwd),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            stdin=asyncio.subprocess.PIPE,
        )

        if proc.stdin is not None:
            proc.stdin.write(json.dumps(attempt_payload, ensure_ascii=False).encode("utf-8"))
            await proc.stdin.drain()
            proc.stdin.close()

        mapper = _CodexUiEventMapper()
        mode_event = {
            "type": "data-chat-runtime",
            "data": {
                "mode": mode,
                "fallbackUsed": fallback_used,
                "error": fallback_error,
            },
        }
        commit_types = {"text-delta", "tool-input-start", "tool-input-available", "tool-output-available"}
        buffered_events: List[Dict[str, Any]] = []
        committed = not cautious
        if committed:
            yield format_chunk(mode_event)

        while True:
            if proc.stdout is None:
                break
            raw = await proc.stdout.readline()
            if not raw:
                break
            line = raw.decode("utf-8", errors="replace").rstrip("\n")
            mapped = mapper.feed_line(line)
            if committed:
                for event in mapped:
                    yield format_chunk(event)
                continue
            buffered_events.extend(mapped)
            if any(event.get("type") in commit_types for event in mapped):
                committed = True
                yield format_chunk(mode_event)
                for event in buffered_events:
                    yield format_chunk(event)
                buffered_events = []

        rc = await proc.wait()
        final_events = mapper.finalize(return_code=rc)
        if cautious and not committed and rc != 0:
            return

        if not committed:
            yield format_chunk(mode_event)
            for event in buffered_events:
                yield format_chunk(event)
        for event in final_events:
            yield format_chunk(event)
        attempt_result["success"] = rc == 0

    fallback_error: Optional[str] = None
    if thread_id:
        initial_payload = dict(payload)
        initial_result: Dict[str, Any] = {}
        async for event in _run_attempt(
            initial_payload,
            mode="resume",
            cautious=True,
            fallback_used=False,
            fallback_error=None,
            attempt_result=initial_result,
        ):
            yield event
        if initial_result.get("success"):
            return
        fallback_error = f"resume failed for stored provider thread {thread_id}"

    replay_payload = dict(payload)
    replay_payload.pop("threadId", None)
    if fallback_query:
        replay_payload["input"] = fallback_query
    async for event in _run_attempt(
        replay_payload,
        mode="replay" if thread_id else "fresh",
        cautious=False,
        fallback_used=bool(thread_id),
        fallback_error=fallback_error,
        attempt_result={},
    ):
        yield event
