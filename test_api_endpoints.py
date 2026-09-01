"""
FastAPI endpoints integration test for LunarVision.
Tests /api/health, /api/images/register, /api/images/change-detection, and no_match rejection.
"""

import sys
import io
from pathlib import Path
import cv2
import numpy as np
from fastapi.testclient import TestClient

backend_path = Path(__file__).resolve().parent / "backend"
sys.path.insert(0, str(backend_path))

from main import app
from test_backend_cv import create_synthetic_lunar_surface

client = TestClient(app)


def test_api_endpoints():
    print("=" * 60)
    print("Testing LunarVision FastAPI HTTP Endpoints")
    print("=" * 60)

    # 1. Health endpoint
    res_health = client.get("/api/health")
    assert res_health.status_code == 200, f"Health check failed: {res_health.text}"
    health_data = res_health.json()
    print(f"[OK] GET /api/health: {health_data['status']} (OpenCV: {health_data['opencv_version']}, scikit-image: {health_data['skimage_version']})")

    # 2. Prepare synthetic test images in memory
    ref_img = create_synthetic_lunar_surface(350, 350, seed=42)
    M = cv2.getRotationMatrix2D((175, 175), 3.0, 1.0)
    M[0, 2] += 5.0
    src_img = cv2.warpAffine(ref_img, M, (350, 350), borderMode=cv2.BORDER_REFLECT)
    cv2.circle(src_img, (150, 150), 12, (20, 20, 20), -1)

    _, ref_buf = cv2.imencode(".png", ref_img)
    _, src_buf = cv2.imencode(".png", src_img)

    # 3. Test POST /api/images/register
    files = {
        "source_image": ("source.png", io.BytesIO(src_buf.tobytes()), "image/png"),
        "reference_image": ("reference.png", io.BytesIO(ref_buf.tobytes()), "image/png")
    }
    data = {"preferred_detector": "SIFT"}
    res_reg = client.post("/api/images/register", files=files, data=data)
    assert res_reg.status_code == 200, f"Register failed: {res_reg.text}"
    reg_json = res_reg.json()
    assert reg_json["status"] == "success", f"Registration not successful: {reg_json}"
    print(f"[OK] POST /api/images/register: success (Confidence: {reg_json['metrics']['registration_confidence_percentage']}%, Inliers: {reg_json['metrics']['inlier_count']})")
    assert "artifacts" in reg_json and "aligned_image" in reg_json["artifacts"]

    # 4. Test POST /api/images/change-detection
    files_cd = {
        "source_image": ("source.png", io.BytesIO(src_buf.tobytes()), "image/png"),
        "reference_image": ("reference.png", io.BytesIO(ref_buf.tobytes()), "image/png")
    }
    data_cd = {"min_confidence": "0.35", "difference_threshold": "30"}
    res_cd = client.post("/api/images/change-detection", files=files_cd, data=data_cd)
    assert res_cd.status_code == 200, f"Change detection failed: {res_cd.text}"
    cd_json = res_cd.json()
    assert cd_json["status"] == "success", f"Change detection returned error: {cd_json}"
    print(f"[OK] POST /api/images/change-detection: success (Detected {cd_json['change_metrics']['total_regions_detected']} regions, SSIM: {cd_json['change_metrics']['mean_ssim']})")
    assert len(cd_json["detected_regions"]) > 0

    # 5. Test no_match handling with black / blank image
    blank_img = np.zeros((350, 350, 3), dtype=np.uint8)
    _, blank_buf = cv2.imencode(".png", blank_img)
    files_nomatch = {
        "source_image": ("blank.png", io.BytesIO(blank_buf.tobytes()), "image/png"),
        "reference_image": ("reference.png", io.BytesIO(ref_buf.tobytes()), "image/png")
    }
    res_nomatch = client.post("/api/images/register", files=files_nomatch)
    assert res_nomatch.status_code == 200
    nomatch_json = res_nomatch.json()
    assert nomatch_json["status"] == "no_match", f"Expected no_match, got: {nomatch_json}"
    print(f"[OK] POST /api/images/register (Blank Image): Returned status 'no_match' with reason: '{nomatch_json['reason'][:50]}...'")

    print("=" * 60)
    print("ALL FASTAPI HTTP ENDPOINT TESTS PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    test_api_endpoints()
