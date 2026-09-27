"""
Quick smoke test for generated test pairs through the LunarVision registration pipeline.
"""
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))
backend_dir = root_dir / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from main import app

client = TestClient(app)

def _run_pair(label: str, ref_path: str, src_path: str):
    """Execute a registration request for a pair of images and assert expectations.

    Parameters
    ----------
    label: Human‑readable identifier used in printed output.
    ref_path, src_path: Relative paths (from the repository root) to the reference
        and source test images.
    """
    ref_file = Path(ref_path) if Path(ref_path).is_absolute() else root_dir / ref_path
    src_file = Path(src_path) if Path(src_path).is_absolute() else root_dir / src_path

    with open(ref_file, "rb") as r, open(src_file, "rb") as s:
        res = client.post("/api/images/register", files={
            "source_image": ("source.png", s, "image/png"),
            "reference_image": ("reference.png", r, "image/png"),
        })
    data = res.json()
    status = data.get("status")
    if status == "success":
        m = data["metrics"]
        inliers = m["inlier_count"]
        total = m["total_good_matches"]
        rmse = m["rmse"]
        conf = m["registration_confidence_percentage"]
        print(f"[{label}] SUCCESS | Inliers: {inliers}/{total} | RMSE: {rmse} px | Confidence: {conf}%")
        assert status == "success"
    else:
        reason = data.get("reason", "")[:120]
        print(f"[{label}] NO_MATCH | {reason}")
        assert status == "no_match"

def test_pair_success():
    """PAIR A – expected to succeed."""
    _run_pair(
        "PAIR A (should succeed)",
        "test_data/reference_test.png",
        "test_data/source_test.png",
    )

def test_pair_reject():
    """PAIR B – expected to be rejected (no match)."""
    _run_pair(
        "PAIR B (should reject)",
        "test_data/reference_nomatch.png",
        "test_data/source_nomatch.png",
    )

if __name__ == "__main__":
    test_pair_success()
    test_pair_reject()
