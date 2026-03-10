import subprocess
import sys
from pathlib import Path


def test_check_ownership_policy_passes():
    root = Path(__file__).resolve().parents[2]
    proc = subprocess.run(
        [sys.executable, "scripts/check_ownership_policy.py"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
