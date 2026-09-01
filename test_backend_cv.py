"""
Comprehensive test script for LunarVision backend computer vision pipeline.
Tests preprocessing, SIFT/AKAZE detection, matching, RANSAC registration,
metrics, and temporal change detection on synthetic lunar surface pairs.
"""

import sys
from pathlib import Path
import cv2
import numpy as np

# Add backend directory to sys.path
backend_path = Path(__file__).resolve().parent / "backend"
sys.path.insert(0, str(backend_path))

from services.preprocessing import PreprocessingService
from services.feature_detection import FeatureDetectionService
from services.matching import FeatureMatchingService
from services.registration import ImageRegistrationService
from services.metrics import MetricsService
from services.change_detection import ChangeDetectionService


def create_synthetic_lunar_surface(width=400, height=400, seed=42):
    """
    Generates a realistic synthetic lunar terrain image with craters and surface texture.
    """
    np.random.seed(seed)
    # Background regolith noise
    surface = np.random.normal(120, 20, (height, width)).astype(np.float32)
    surface = cv2.GaussianBlur(surface, (11, 11), 3.0)

    # Add primary crater features
    craters = [
        (120, 140, 35, -50, 40), # (cx, cy, radius, depth_shadow, rim_highlight)
        (280, 220, 45, -60, 50),
        (200, 310, 25, -40, 30),
        (310, 100, 20, -35, 25),
        (90, 280, 30, -45, 35),
        (220, 180, 15, -25, 20),
    ]

    for cx, cy, r, depth, rim in craters:
        y, x = np.ogrid[:height, :width]
        dist = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)

        # Crater interior (darkened depression with sunlight angle)
        crater_mask = dist <= r
        # Simulate directional sunlight from upper-left
        sun_gradient = ((x - cx) + (y - cy)) / float(max(r, 1))
        surface[crater_mask] += depth * (1.0 - dist[crater_mask] / r) + (sun_gradient[crater_mask] * 15)

        # Crater rim (bright raised edge on top-left, shadow on bottom-right)
        rim_mask = (dist > (r - 4)) & (dist <= (r + 4))
        surface[rim_mask] += rim * (1.0 - abs(dist[rim_mask] - r) / 4.0)

    # Normalize to uint8 BGR
    norm_surface = cv2.normalize(surface, None, 10, 240, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
    bgr_surface = cv2.cvtColor(norm_surface, cv2.COLOR_GRAY2BGR)
    return bgr_surface


def run_full_pipeline_test():
    print("=" * 60)
    print("Testing LunarVision Computer Vision Backend Pipeline")
    print("=" * 60)

    # 1. Initialize Services
    preprocess_svc = PreprocessingService(clip_limit=2.0)
    feature_svc = FeatureDetectionService(min_features=10)
    matching_svc = FeatureMatchingService(sift_ratio_thresh=0.80)
    registration_svc = ImageRegistrationService(ransac_reproj_thresh=3.5, min_matches_required=6)
    metrics_svc = MetricsService()
    change_svc = ChangeDetectionService(min_region_area=15, diff_threshold=30)

    # 2. Generate Base Lunar Image (Reference: Time T0)
    ref_img = create_synthetic_lunar_surface(400, 400, seed=101)

    # 3. Generate Transformed Temporal Image (Source: Time T1)
    # Apply affine rotation + shift + a new impact crater
    M_rot = cv2.getRotationMatrix2D((200, 200), angle=4.0, scale=1.0)
    M_rot[0, 2] += 8.0 # x shift
    M_rot[1, 2] += -6.0 # y shift
    src_img = cv2.warpAffine(ref_img, M_rot, (400, 400), borderMode=cv2.BORDER_REFLECT)

    # Add a new impact crater in Source image (at center 180, 170)
    cv2.circle(src_img, (180, 170), 16, (30, 30, 30), -1)
    cv2.circle(src_img, (180, 170), 18, (220, 220, 220), 2)

    print("[OK] Synthetic temporal lunar image pair created.")

    # 4. Preprocessing
    ref_prep = preprocess_svc.preprocess_pipeline(ref_img)
    src_prep = preprocess_svc.preprocess_pipeline(src_img)
    print("[OK] Preprocessing executed (Grayscale, Normalization, CLAHE).")

    # 5. Feature Detection
    ref_kps, ref_descs, ref_algo = feature_svc.detect_features(ref_prep["enhanced"])
    src_kps, src_descs, src_algo = feature_svc.detect_features(src_prep["enhanced"])
    print(f"[OK] Feature Detection: Found {len(ref_kps)} ref kps and {len(src_kps)} src kps using {ref_algo}.")
    assert len(ref_kps) > 10 and len(src_kps) > 10, "Feature detection returned too few keypoints."

    # 6. Feature Matching
    good_matches, total_raw = matching_svc.match_descriptors(src_descs, ref_descs, algorithm=src_algo)
    print(f"[OK] Feature Matching: {len(good_matches)} good matches filtered from {total_raw} raw matches.")
    assert len(good_matches) >= 6, "Matching returned too few good matches."

    # 7. Image Registration (RANSAC Homography)
    reg_res = registration_svc.align_images(
        source_img=src_prep["original_color"],
        reference_img=ref_prep["original_color"],
        src_keypoints=src_kps,
        ref_keypoints=ref_kps,
        matches=good_matches
    )
    print(f"[OK] Registration success: {reg_res['success']}, Inliers: {reg_res['inlier_count']}/{len(good_matches)}")
    assert reg_res["success"], f"Registration failed: {reg_res['error_message']}"

    # 8. Metrics Calculation
    metrics = metrics_svc.calculate_registration_metrics(
        reference_img=ref_prep["gray"],
        aligned_img=reg_res["aligned_image"],
        inlier_count=reg_res["inlier_count"],
        total_good_matches=len(good_matches),
        valid_overlap_mask=reg_res["valid_overlap_mask"]
    )
    print(f"[OK] Metrics: RMSE = {metrics['rmse']}, Inlier Ratio = {metrics['inlier_ratio']}, Confidence = {metrics['registration_confidence_percentage']}%")
    assert metrics["registration_confidence_score"] > 0.30, "Registration confidence unexpectedly low."

    # 9. Temporal Change Detection
    change_res = change_svc.detect_changes(
        reference_img=ref_prep["original_color"],
        aligned_img=reg_res["aligned_image"],
        valid_overlap_mask=reg_res["valid_overlap_mask"]
    )
    print(f"[OK] Temporal Change Detection: SSIM = {change_res['mean_ssim']}, Detected Regions = {change_res['total_regions_found']}")
    assert change_res["total_regions_found"] >= 1, "Change detection failed to detect the synthetic crater."
    
    for r in change_res["detected_regions"]:
        print(f"  -> Region #{r['region_id']}: {r['label']} (Area: {r['area_pixels']}px, Circularity: {r['circularity']})")

    # 10. Test 'no_match' handling on completely unrelated noise
    noise_img = np.random.randint(0, 255, (400, 400, 3), dtype=np.uint8)
    noise_kps, noise_descs, _ = feature_svc.detect_features(noise_img)
    noise_matches, _ = matching_svc.match_descriptors(noise_descs, ref_descs)
    reg_noise = registration_svc.align_images(
        source_img=noise_img,
        reference_img=ref_img,
        src_keypoints=noise_kps,
        ref_keypoints=ref_kps,
        matches=noise_matches
    )
    print(f"[OK] No-match rejection verification: Noise alignment rejected as expected (success = {reg_noise['success']}).")
    assert not reg_noise["success"], "Registration should have rejected unrelated noise image."

    print("=" * 60)
    print("ALL TESTS PASSED SUCCESSFULLY! The CV backend pipeline is fully functional.")
    print("=" * 60)


if __name__ == "__main__":
    run_full_pipeline_test()
