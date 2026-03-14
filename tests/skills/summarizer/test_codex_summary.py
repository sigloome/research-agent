import json
import subprocess

from skills.knowledge.summarizer import summarize


def test_generate_summary_uses_codex_output(monkeypatch, tmp_path):
    adapter = tmp_path / "backend" / "codex_sdk_adapter" / "run_summary.mjs"
    adapter.parent.mkdir(parents=True, exist_ok=True)
    adapter.write_text("// test adapter placeholder", encoding="utf-8")
    runtime_home = tmp_path / ".codex-agent-runtime-test"
    runtime_home.mkdir(parents=True, exist_ok=True)

    payload = {
        "ok": True,
        "text": json.dumps(
            {
                "tags": ["LLM", "Agent"],
                "summary_main_ideas": "Main",
                "summary_methods": "Methods",
                "summary_results": "Results",
                "summary_limitations": "Limits",
            }
        ),
    }
    cp = subprocess.CompletedProcess(
        args=["node", "run_summary.mjs"],
        returncode=0,
        stdout=json.dumps(payload) + "\n",
        stderr="",
    )

    monkeypatch.setattr(summarize.shutil, "which", lambda _name: "/usr/bin/node")
    monkeypatch.setattr(summarize, "_project_root", lambda: tmp_path)
    monkeypatch.setattr(summarize, "_ensure_runtime_skill_home", lambda *_args, **_kwargs: runtime_home)
    monkeypatch.setattr(summarize, "_build_codex_runtime_env", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(subprocess, "run", lambda *_args, **_kwargs: cp)

    result = summarize.generate_summary("content", title="T")
    assert result["summary_main_ideas"] == "Main"
    assert result["summary_methods"] == "Methods"
    assert result["tags"] == ["LLM", "Agent"]


def test_generate_summary_fallback_on_adapter_failure(monkeypatch, tmp_path):
    adapter = tmp_path / "backend" / "codex_sdk_adapter" / "run_summary.mjs"
    adapter.parent.mkdir(parents=True, exist_ok=True)
    adapter.write_text("// test adapter placeholder", encoding="utf-8")
    runtime_home = tmp_path / ".codex-agent-runtime-test"
    runtime_home.mkdir(parents=True, exist_ok=True)

    cp = subprocess.CompletedProcess(
        args=["node", "run_summary.mjs"],
        returncode=1,
        stdout='{"ok":false,"error":"boom"}\n',
        stderr="boom",
    )

    monkeypatch.setattr(summarize.shutil, "which", lambda _name: "/usr/bin/node")
    monkeypatch.setattr(summarize, "_project_root", lambda: tmp_path)
    monkeypatch.setattr(summarize, "_ensure_runtime_skill_home", lambda *_args, **_kwargs: runtime_home)
    monkeypatch.setattr(summarize, "_build_codex_runtime_env", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(subprocess, "run", lambda *_args, **_kwargs: cp)

    result = summarize.generate_summary("content", title="T")
    assert result["summary_main_ideas"] == "Failed to generate summary."
