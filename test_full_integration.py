"""
Comprehensive Full-Stack Integration & Verification Test Suite for LunarVision (Phase 5).
Tests all requirements: Health check, Registration, No-match rejection,
Temporal change detection, Multi-sensor pairwise extension, Static artifact access, and Invalid upload handling.
"""

import sys
import os
from pathlib import Path
from fastapi.testclient import TestClient

backend_dir = Path(__file__).resolve().parent / "backend"
sys.path.insert(0, str(backend_dir))

from main import app

client = TestClient(app)
sample_dir = backend_dir / "sample_data"


def test_step1_health_check():
    print("\n--- STEP 1: Backend Health Check ---")
    res = client.get("/api/health")
    assert res.status_code == 200, f"Health endpoint returned status {res.status_code}"
    data = res.json()
    assert data["status"] == "healthy", f"Unexpected status: {data}"
    assert "opencv_version" in data and "skimage_version" in data
    assert data["directories"]["outputs"] is True
    print(f"[PASSED] Health Check: Status={data['status']}, OpenCV={data['opencv_version']}, skimage={data['skimage_version']}")


def test_step2_image_registration():
    print("\n--- STEP 2: Image Registration Pipeline ---")
    src_path = sample_dir / "02_temporal_rotated_shifted.png"
    ref_path = sample_dir / "01_baseline_pre_event.png"

    with open(src_path, "rb") as f_src, open(ref_path, "rb") as f_ref:
        files = {
            "source_image": ("02_temporal_rotated_shifted.png", f_src, "image/png"),
            "reference_image": ("01_baseline_pre_event.png", f_ref, "image/png"),
        }
        data = {"preferred_detector": "SIFT"}
        res = client.post("/api/images/register", files=files, data=data)

    assert res.status_code == 200, f"Register returned status {res.status_code}: {res.text}"
    body = res.json()
    assert body["status"] == "success", f"Registration did not succeed: {body}"

    metrics = body["metrics"]
    artifacts = body["artifacts"]

    print(f"[PASSED] Registration Status: {body['status']} (Detector: {body['detector_used']})")
    print(f"         - Inliers: {metrics['inlier_count']}/{metrics['total_good_matches']} (Ratio: {metrics['inlier_ratio'] * 100:.1f}%)")
    print(f"         - RMSE: {metrics['rmse']} px")
    print(f"         - Confidence: {metrics['registration_confidence_percentage']}%")

    assert metrics["inlier_count"] >= 10, "Inlier count unexpectedly low"
    assert metrics["registration_confidence_score"] >= 0.70, "Confidence score lower than expected for valid pair"
    assert "aligned_image" in artifacts and "overlay_comparison" in artifacts
    assert "feature_matches" in artifacts and "inlier_matches" in artifacts

    # Verify static file serving for generated artifacts
    aligned_url = artifacts["aligned_image"]
    res_static = client.get(aligned_url)
    assert res_static.status_code == 200, f"Failed to retrieve static artifact: {aligned_url}"
    assert len(res_static.content) > 1000, "Retrieved artifact is empty"
    print(f"[PASSED] Static Output Serving: Aligned image verified at {aligned_url} ({len(res_static.content)} bytes)")


def test_step3_no_match_rejection():
    print("\n--- STEP 3: No Match Rejection on Unrelated Imagery ---")
    unrelated_path = sample_dir / "04_unrelated_lunar_terrain.png"
    ref_path = sample_dir / "01_baseline_pre_event.png"

    with open(unrelated_path, "rb") as f_unrel, open(ref_path, "rb") as f_ref:
        files = {
            "source_image": ("04_unrelated_lunar_terrain.png", f_unrel, "image/png"),
            "reference_image": ("01_baseline_pre_event.png", f_ref, "image/png"),
        }
        res = client.post("/api/images/register", files=files)

    assert res.status_code == 200, f"Endpoint returned unexpected status {res.status_code}"
    body = res.json()
    assert body["status"] == "no_match", f"Expected no_match, but received: {body['status']}"
    assert "reason" in body and "avoided forcing an inaccurate registration" in body["reason"].lower()
    print(f"[PASSED] No Match Handled Correctly: Status='{body['status']}'")
    print(f"         Explanation: '{body['reason']}'")


def test_step4_temporal_change_detection():
    print("\n--- STEP 4: Temporal Change Detection Pipeline ---")
    new_crater_path = sample_dir / "03_temporal_new_impact_crater.png"
    ref_path = sample_dir / "01_baseline_pre_event.png"

    with open(new_crater_path, "rb") as f_src, open(ref_path, "rb") as f_ref:
        files = {
            "source_image": ("03_temporal_new_impact_crater.png", f_src, "image/png"),
            "reference_image": ("01_baseline_pre_event.png", f_ref, "image/png"),
        }
        data = {"min_confidence": "0.35", "difference_threshold": "30"}
        res = client.post("/api/images/change-detection", files=files, data=data)

    assert res.status_code == 200, f"Change detection returned status {res.status_code}: {res.text}"
    body = res.json()
    assert body["status"] == "success", f"Change detection failed: {body}"

    change_metrics = body["change_metrics"]
    detected_regions = body["detected_regions"]
    artifacts = body["artifacts"]

    print(f"[PASSED] Change Detection Status: {body['status']}")
    print(f"         - Mean SSIM: {change_metrics['mean_ssim']}")
    print(f"         - Detected Regions: {change_metrics['total_regions_detected']}")
    print(f"         - Disclaimer: '{body['disclaimer']}'")

    assert len(detected_regions) >= 1, "Failed to isolate candidate crater region"
    primary_region = detected_regions[0]
    print(f"         - Primary Detected Region: #{primary_region['region_id']} ({primary_region['label']})")
    print(f"           Area: {primary_region['area_pixels']}px, Circularity: {primary_region['circularity']}")

    heatmap_url = artifacts["change_heatmap"]
    res_heatmap = client.get(heatmap_url)
    assert res_heatmap.status_code == 200, f"Heatmap static retrieval failed: {heatmap_url}"
    print(f"[PASSED] Static Heatmap Serving: Verified at {heatmap_url}")


def test_step5_multi_sensor_pairwise():
    print("\n--- STEP 5: Multi-Sensor Pairwise Extension ---")
    hub_path = sample_dir / "01_baseline_pre_event.png"
    sensor_a_path = sample_dir / "02_temporal_rotated_shifted.png"
    sensor_b_path = sample_dir / "03_temporal_new_impact_crater.png"

    with open(hub_path, "rb") as f_hub, open(sensor_a_path, "rb") as f_a, open(sensor_b_path, "rb") as f_b:
        files = {
            "hub_image": ("hub.png", f_hub, "image/png"),
            "sensor_a_image": ("tmc.png", f_a, "image/png"),
            "sensor_b_image": ("iirs.png", f_b, "image/png"),
        }
        data = {
            "hub_sensor_name": "OHRC",
            "sensor_a_name": "TMC",
            "sensor_b_name": "IIRS",
        }
        res = client.post("/api/images/multi-sensor-register", files=files, data=data)

    assert res.status_code == 200, f"Multi-sensor registration returned status {res.status_code}: {res.text}"
    body = res.json()
    assert body["status"] == "success"
    assert "pairwise_results" in body
    assert "OHRC ↔ TMC" in body["pairwise_results"]
    assert "OHRC ↔ IIRS" in body["pairwise_results"]

    pair1 = body["pairwise_results"]["OHRC ↔ TMC"]["result"]
    assert pair1["status"] == "success"
    print(f"[PASSED] Multi-Sensor Pair 1 (OHRC <-> TMC): Inliers={pair1['metrics']['inlier_count']}, Conf={pair1['metrics']['registration_confidence_percentage']}%")

    pair2 = body["pairwise_results"]["OHRC ↔ IIRS"]["result"]
    assert pair2["status"] == "success"
    print(f"[PASSED] Multi-Sensor Pair 2 (OHRC <-> IIRS): Inliers={pair2['metrics']['inlier_count']}, Conf={pair2['metrics']['registration_confidence_percentage']}%")


def test_step6_invalid_input_handling():
    print("\n--- STEP 6: Invalid Input & Error Handling ---")
    files = {
        "source_image": ("corrupt.png", b"not an image file data", "image/png"),
        "reference_image": ("corrupt2.png", b"also invalid bytes", "image/png"),
    }
    res = client.post("/api/images/register", files=files)
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "no_match"
    print(f"[PASSED] Corrupted File Handled Safely: Returned 'no_match' with reason: '{body['reason']}'")


def run_all_integration_tests():
    print("=" * 65)
    print("  LUNARVISION FULL INTEGRATION & VERIFICATION TEST SUITE (PHASE 5)")
    print("=" * 65)

    test_step1_health_check()
    test_step2_image_registration()
    test_step3_no_match_rejection()
    test_step4_temporal_change_detection()
    test_step5_multi_sensor_pairwise()
    test_step6_invalid_input_handling()

    print("\n" + "=" * 65)
    print("  ALL FULL INTEGRATION & END-TO-END TESTS PASSED SUCCESSFULLY!  ")
    print("=" * 65)


if __name__ == "__main__":
    run_all_integration_tests()
