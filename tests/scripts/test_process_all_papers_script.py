from __future__ import annotations


def test_process_all_papers_script_imports():
    import importlib

    module = importlib.import_module("scripts.process_all_papers")
    assert hasattr(module, "process_all_papers")
