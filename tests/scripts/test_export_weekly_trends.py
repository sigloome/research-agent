import subprocess
import sys
from pathlib import Path


def test_export_weekly_trends_generates_files():
    root = Path(__file__).resolve().parents[2]
    proc = subprocess.run(
        [sys.executable, "tmp/interview_pack/scripts/export_weekly_trends.py"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    weekly_dir = root / "tmp/interview_pack/reports/weekly"
    assert weekly_dir.exists()
    assert any(weekly_dir.glob("weekly_trend_*.json"))
    assert any(weekly_dir.glob("weekly_trend_*.md"))
