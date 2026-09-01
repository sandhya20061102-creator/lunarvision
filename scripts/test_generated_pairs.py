"""Quick smoke test for generated test pairs through the LunarVision registration pipeline."""
import sys
sys.path.insert(0, "backend")
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_pair(label, ref_path, src_path):
    with open(ref_path, "rb") as r, open(src_path, "rb") as s:
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
    else:
        reason = data.get("reason", "")[:120]
        print(f"[{label}] NO_MATCH | {reason}")

test_pair("PAIR A (should succeed)", "test_data/reference_test.png", "test_data/source_test.png")
test_pair("PAIR B (should reject)", "test_data/reference_nomatch.png", "test_data/source_nomatch.png")
