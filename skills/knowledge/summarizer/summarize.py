from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional

from backend.codex_sdk_runtime import _build_codex_runtime_env, _ensure_runtime_skill_home
from backend.logging_config import get_skill_logger

logger = get_skill_logger("summarizer")

_REQUIRED_FIELDS = (
    "tags",
    "summary_main_ideas",
    "summary_methods",
    "summary_results",
    "summary_limitations",
)


def _project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _fallback_summary(reason: str) -> Dict[str, Any]:
    logger.warning("summary_fallback", reason=reason)
    return {
        "tags": ["Unavailable"],
        "summary_main_ideas": "Failed to generate summary.",
        "summary_methods": "",
        "summary_results": "",
        "summary_limitations": "",
    }


def _resolve_model() -> str:
    return (
        os.environ.get("CODEX_SUMMARY_MODEL", "").strip()
        or os.environ.get("CODEX_SDK_MODEL", "").strip()
        or os.environ.get("CODEX_EXEC_MODEL", "").strip()
        or "gpt-5-codex"
    )


def _build_summary_prompt(text: str, title: str = "") -> str:
    truncated = (text or "")[:80000]
    return (
        "You are an expert research assistant.\n"
        f"Paper title: {title or 'unknown'}\n\n"
        "Analyze the paper content and return a strict JSON object with exactly these keys:\n"
        '- "tags": array of 1-6 concise topic tags\n'
        '- "summary_main_ideas": string\n'
        '- "summary_methods": string\n'
        '- "summary_results": string\n'
        '- "summary_limitations": string\n\n'
        "Rules:\n"
        "1) Return JSON only, no markdown fences.\n"
        "2) Do not include any extra keys.\n"
        "3) Each summary field should be non-empty when information is available.\n\n"
        "Paper content:\n"
        f"{truncated}"
    )


def _extract_json_object(text: str) -> Optional[Dict[str, Any]]:
    raw = (text or "").strip()
    if not raw:
        return None
    try:
        obj = json.loads(raw)
        return obj if isinstance(obj, dict) else None
    except json.JSONDecodeError:
        pass

    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    candidate = raw[start : end + 1]
    try:
        obj = json.loads(candidate)
    except json.JSONDecodeError:
        return None
    return obj if isinstance(obj, dict) else None


def _coerce_summary(obj: Dict[str, Any]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key in _REQUIRED_FIELDS:
        value = obj.get(key)
        if key == "tags":
            if isinstance(value, list):
                tags = [str(tag).strip() for tag in value if str(tag).strip()]
                result[key] = tags[:6] or ["AI"]
            elif isinstance(value, str) and value.strip():
                result[key] = [value.strip()]
            else:
                result[key] = ["AI"]
            continue
        result[key] = str(value or "").strip()
    return result


def _run_codex_summary(prompt: str) -> Optional[Dict[str, Any]]:
    root = _project_root()
    adapter_path = root / "backend" / "codex_sdk_adapter" / "run_summary.mjs"
    if not adapter_path.exists():
        logger.error("codex_summary_adapter_missing", path=str(adapter_path))
        return None
    node_bin = shutil.which("node")
    if not node_bin:
        logger.error("node_binary_missing")
        return None

    runtime_home = _ensure_runtime_skill_home(root)
    runtime_workspace = runtime_home / "workspace"
    runtime_workspace.mkdir(parents=True, exist_ok=True)

    payload: Dict[str, Any] = {
        "input": prompt,
        "model": _resolve_model(),
        "workingDirectory": str(runtime_workspace),
        "skipGitRepoCheck": True,
        "networkAccessEnabled": True,
        "codexEnv": _build_codex_runtime_env(root, runtime_home),
    }
    config_overrides_raw = os.environ.get("CODEX_CONFIG_OVERRIDES_JSON", "").strip()
    if config_overrides_raw:
        try:
            parsed = json.loads(config_overrides_raw)
            if isinstance(parsed, dict):
                payload["configOverrides"] = parsed
        except json.JSONDecodeError:
            logger.warning("invalid_codex_config_overrides_json")

    timeout_sec = int(os.environ.get("CODEX_SUMMARY_TIMEOUT_SEC", "240"))
    proc = subprocess.run(
        [node_bin, str(adapter_path)],
        cwd=str(root),
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        timeout=timeout_sec,
    )
    if proc.returncode != 0:
        logger.error(
            "codex_summary_failed",
            return_code=proc.returncode,
            stderr_tail=(proc.stderr or "")[-500:],
            stdout_tail=(proc.stdout or "")[-500:],
        )
        return None

    for line in reversed((proc.stdout or "").splitlines()):
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(msg, dict):
            continue
        if msg.get("ok") is not True:
            logger.error("codex_summary_response_error", response=msg)
            return None
        summary_text = str(msg.get("text") or "")
        parsed_summary = _extract_json_object(summary_text)
        if parsed_summary is None:
            logger.error("codex_summary_json_parse_failed", text_tail=summary_text[-500:])
            return None
        return _coerce_summary(parsed_summary)
    logger.error("codex_summary_no_json_output")
    return None


def generate_summary(text: str, title: str = "") -> Dict[str, Any]:
    """Generate paper summary through the same Codex runtime used by chat."""
    if not str(text or "").strip():
        return _fallback_summary("empty_input")
    prompt = _build_summary_prompt(text=text, title=title)
    summary = _run_codex_summary(prompt)
    if summary is None:
        return _fallback_summary("codex_unavailable")
    if not str(summary.get("summary_main_ideas", "")).strip():
        return _fallback_summary("empty_main_ideas")
    return summary
