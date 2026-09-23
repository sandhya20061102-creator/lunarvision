"""
API Routes for Lunar Image Registration and Temporal Change Detection
Provides endpoints for image upload, keypoint matching, RANSAC homography warping,
quantitative alignment scoring, multi-sensor pairwise extension, and heuristic temporal change detection.
"""

import os
import uuid
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

import cv2
import numpy as np
from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse

from backend.services.preprocessing import PreprocessingService
from backend.services.feature_detection import FeatureDetectionService
from backend.services.matching import FeatureMatchingService
from backend.services.registration import ImageRegistrationService
from backend.services.metrics import MetricsService
from backend.services.change_detection import ChangeDetectionService
from backend.services.sun_angle_service import SunAngleService

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize computer vision services
preprocess_svc = PreprocessingService(clip_limit=2.0, max_dimension=4096)
feature_svc = FeatureDetectionService(min_features=12)
matching_svc = FeatureMatchingService(sift_ratio_thresh=0.75, akaze_ratio_thresh=0.80)
registration_svc = ImageRegistrationService(ransac_reproj_thresh=3.5, min_matches_required=6)
metrics_svc = MetricsService()
change_svc = ChangeDetectionService(min_region_area=20, diff_threshold=35)

# Output directory configuration
BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUTS_DIR = BASE_DIR / "outputs"
UPLOADS_DIR = BASE_DIR / "uploads"
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

NO_MATCH_DISCLAIMER = "No reliable correspondence was found. The system avoided forcing an inaccurate registration."


def save_image_artifact(image: np.ndarray, prefix: str, session_id: str) -> str:
    """
    Saves an image NumPy array to the outputs directory and returns its relative web path.
    """
    filename = f"{session_id}_{prefix}.png"
    filepath = OUTPUTS_DIR / filename
    cv2.imwrite(str(filepath), image)
    return f"/outputs/{filename}"


def create_overlay_blend(ref_img: np.ndarray, aligned_img: np.ndarray) -> np.ndarray:
    """
    Creates an alpha-blended comparison visualization between reference and aligned source images.
    """
    ref_bgr = cv2.cvtColor(ref_img, cv2.COLOR_GRAY2BGR) if len(ref_img.shape) == 2 else ref_img.copy()
    aln_bgr = cv2.cvtColor(aligned_img, cv2.COLOR_GRAY2BGR) if len(aligned_img.shape) == 2 else aligned_img.copy()
    blend = cv2.addWeighted(ref_bgr, 0.5, aln_bgr, 0.5, 0)
    return blend


def draw_matches_visualization(
    src_img: np.ndarray,
    src_kps: list,
    ref_img: np.ndarray,
    ref_kps: list,
    matches: list,
    inlier_mask: Optional[list] = None
) -> np.ndarray:
    """
    Draws keypoint correspondences between source and reference images.
    """
    draw_params = dict(
        matchColor=(0, 255, 100),
        singlePointColor=(0, 150, 255),
        flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS
    )
    if inlier_mask is not None:
        draw_params["matchesMask"] = inlier_mask
        draw_params["matchColor"] = (0, 240, 255)  # Cyan for inliers

    vis_img = cv2.drawMatches(
        src_img,
        src_kps,
        ref_img,
        ref_kps,
        matches,
        None,
        **draw_params
    )
    return vis_img


def execute_registration_pipeline(
    src_bytes: bytes,
    ref_bytes: bytes,
    preferred_detector: str = "SIFT",
    session_id: Optional[str] = None,
    src_filename: Optional[str] = None,
    ref_filename: Optional[str] = None
) -> Dict[str, Any]:
    """
    Core reusable routine that executes preprocessing, SIFT/ORB detection,
    BF matching, RANSAC homography, and metric calculation.
    """
    sid = session_id or uuid.uuid4().hex[:10]

    # Preprocessing
    try:
        src_prep = preprocess_svc.preprocess_pipeline(
            preprocess_svc.load_image_from_bytes(src_bytes, filename=src_filename)
        )
        ref_prep = preprocess_svc.preprocess_pipeline(
            preprocess_svc.load_image_from_bytes(ref_bytes, filename=ref_filename)
        )
    except ValueError as e:
        return {
            "status": "no_match",
            "reason": f"{NO_MATCH_DISCLAIMER} (Image preprocessing failed: {str(e)})",
            "details": {"step": "preprocessing"}
        }

    # Feature Detection
    src_kps, src_descs, src_algo = feature_svc.detect_features(
        src_prep["enhanced"], preferred_algorithm=preferred_detector
    )
    ref_kps, ref_descs, ref_algo = feature_svc.detect_features(
        ref_prep["enhanced"], preferred_algorithm=preferred_detector
    )

    if len(src_kps) < 6 or len(ref_kps) < 6 or src_descs is None or ref_descs is None:
        return {
            "status": "no_match",
            "reason": (
                f"{NO_MATCH_DISCLAIMER} "
                f"Insufficient keypoints detected (Source: {len(src_kps)}, Reference: {len(ref_kps)})."
            ),
            "details": {
                "source_keypoints": len(src_kps),
                "reference_keypoints": len(ref_kps),
                "detector": src_algo
            }
        }

    # Feature Matching
    algo_for_matching = src_algo if src_algo == ref_algo else "SIFT"
    good_matches, total_raw_matches = matching_svc.match_descriptors(
        src_descs, ref_descs, algorithm=algo_for_matching
    )

    if len(good_matches) < 6:
        return {
            "status": "no_match",
            "reason": (
                f"{NO_MATCH_DISCLAIMER} "
                f"Too few reliable correspondences found ({len(good_matches)} good matches out of {total_raw_matches} candidates)."
            ),
            "details": {
                "good_matches": len(good_matches),
                "total_raw_matches": total_raw_matches,
                "detector": algo_for_matching
            }
        }

    # RANSAC Homography
    reg_result = registration_svc.align_images(
        source_img=src_prep["original_color"],
        reference_img=ref_prep["original_color"],
        src_keypoints=src_kps,
        ref_keypoints=ref_kps,
        matches=good_matches
    )

    if not reg_result["success"]:
        return {
            "status": "no_match",
            "reason": f"{NO_MATCH_DISCLAIMER} ({reg_result['error_message']})",
            "details": {
                "good_matches": len(good_matches),
                "inliers": reg_result["inlier_count"]
            }
        }

    # Metrics
    metrics = metrics_svc.calculate_registration_metrics(
        reference_img=ref_prep["gray"],
        aligned_img=reg_result["aligned_image"],
        inlier_count=reg_result["inlier_count"],
        total_good_matches=len(good_matches),
        valid_overlap_mask=reg_result["valid_overlap_mask"]
    )

    if metrics["registration_confidence_score"] < 0.20:
        return {
            "status": "no_match",
            "reason": (
                f"{NO_MATCH_DISCLAIMER} "
                f"Confidence score ({metrics['registration_confidence_percentage']}%) is below reliability threshold (20%)."
            ),
            "details": metrics
        }

    # Visual Artifacts
    matches_vis = draw_matches_visualization(
        src_prep["original_color"], src_kps,
        ref_prep["original_color"], ref_kps,
        good_matches
    )
    matches_url = save_image_artifact(matches_vis, "matches_raw", sid)

    inlier_vis = draw_matches_visualization(
        src_prep["original_color"], src_kps,
        ref_prep["original_color"], ref_kps,
        good_matches,
        inlier_mask=reg_result["inlier_mask"]
    )
    inliers_url = save_image_artifact(inlier_vis, "matches_inliers", sid)
    aligned_url = save_image_artifact(reg_result["aligned_image"], "aligned_source", sid)
    overlay_img = create_overlay_blend(ref_prep["original_color"], reg_result["aligned_image"])
    overlay_url = save_image_artifact(overlay_img, "overlay_comparison", sid)
    orig_src_url = save_image_artifact(src_prep["original_color"], "source_orig", sid)
    orig_ref_url = save_image_artifact(ref_prep["original_color"], "reference_orig", sid)

    H_matrix = reg_result["homography_matrix"].tolist() if reg_result["homography_matrix"] is not None else None

    return {
        "status": "success",
        "session_id": sid,
        "detector_used": src_algo,
        "metrics": metrics,
        "homography_matrix": H_matrix,
        "artifacts": {
            "source_image": orig_src_url,
            "reference_image": orig_ref_url,
            "feature_matches": matches_url,
            "inlier_matches": inliers_url,
            "aligned_image": aligned_url,
            "overlay_comparison": overlay_url
        },
        "_internal": {
            "src_prep": src_prep,
            "ref_prep": ref_prep,
            "reg_result": reg_result,
        }
    }


@router.post("/register")
async def register_images(
    source_image: UploadFile = File(..., description="Temporal/Secondary Lunar Image to align"),
    reference_image: UploadFile = File(..., description="Baseline Reference Lunar Image"),
    preferred_detector: Optional[str] = Form("SIFT")
) -> Dict[str, Any]:
    """
    Performs full geometric image registration between source and reference lunar images.
    """
    try:
        src_bytes = await source_image.read()
        ref_bytes = await reference_image.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read upload stream: {e}")

    result = execute_registration_pipeline(
        src_bytes,
        ref_bytes,
        preferred_detector,
        src_filename=source_image.filename,
        ref_filename=reference_image.filename
    )
    # Strip internal buffer objects before returning JSON
    if "_internal" in result:
        del result["_internal"]

    return result


@router.post("/multi-sensor-register")
async def register_multi_sensor(
    hub_image: UploadFile = File(..., description="Reference Hub Sensor Image (e.g. OHRC)"),
    sensor_a_image: UploadFile = File(..., description="Secondary Sensor A Image (e.g. TMC)"),
    sensor_b_image: Optional[UploadFile] = File(None, description="Optional Secondary Sensor B Image (e.g. IIRS)"),
    hub_sensor_name: Optional[str] = Form("OHRC"),
    sensor_a_name: Optional[str] = Form("TMC"),
    sensor_b_name: Optional[str] = Form("IIRS"),
    preferred_detector: Optional[str] = Form("SIFT")
) -> Dict[str, Any]:
    """
    Executes real pairwise cross-sensor registration between the Hub sensor and secondary sensors.
    """
    session_id = uuid.uuid4().hex[:10]

    try:
        hub_bytes = await hub_image.read()
        sensor_a_bytes = await sensor_a_image.read()
        sensor_b_bytes = await sensor_b_image.read() if sensor_b_image is not None else None
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read multi-sensor uploads: {e}")

    # Pair 1: Hub vs Sensor A
    pair_1_res = execute_registration_pipeline(
        src_bytes=sensor_a_bytes,
        ref_bytes=hub_bytes,
        preferred_detector=preferred_detector,
        session_id=f"{session_id}_pair1",
        src_filename=sensor_a_image.filename,
        ref_filename=hub_image.filename
    )
    if "_internal" in pair_1_res:
        del pair_1_res["_internal"]

    # Pair 2: Hub vs Sensor B (if provided)
    pair_2_res = None
    if sensor_b_bytes:
        pair_2_res = execute_registration_pipeline(
            src_bytes=sensor_b_bytes,
            ref_bytes=hub_bytes,
            preferred_detector=preferred_detector,
            session_id=f"{session_id}_pair2",
            src_filename=sensor_b_image.filename if sensor_b_image else None,
            ref_filename=hub_image.filename
        )
        if "_internal" in pair_2_res:
            del pair_2_res["_internal"]

    return {
        "status": "success",
        "module": "Three-Sensor Analysis Extension",
        "session_id": session_id,
        "hub_sensor": hub_sensor_name,
        "pairwise_results": {
            f"{hub_sensor_name} ↔ {sensor_a_name}": {
                "pair_name": f"{hub_sensor_name} (Hub) ↔ {sensor_a_name}",
                "result": pair_1_res
            },
            **({
                f"{hub_sensor_name} ↔ {sensor_b_name}": {
                    "pair_name": f"{hub_sensor_name} (Hub) ↔ {sensor_b_name}",
                    "result": pair_2_res
                }
            } if pair_2_res else {})
        },
        "scientific_notice": (
            "Notice: Multi-sensor registration relies on feature correspondences between distinct spectral/spatial bands. "
            "Pairwise results indicate actual computer vision correspondence without unverified cross-modal assumption."
        )
    }


@router.post("/change-detection")
async def detect_temporal_changes(
    source_image: UploadFile = File(..., description="Post-event/Secondary Lunar Image"),
    reference_image: UploadFile = File(..., description="Pre-event/Baseline Lunar Image"),
    min_confidence: Optional[float] = Form(0.35),
    difference_threshold: Optional[int] = Form(35)
) -> Dict[str, Any]:
    """
    Executes registration followed by temporal change detection on aligned lunar imagery.
    """
    session_id = uuid.uuid4().hex[:10]

    try:
        src_bytes = await source_image.read()
        ref_bytes = await reference_image.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read image stream: {e}")

    # 1. Execute Registration
    reg_out = execute_registration_pipeline(
        src_bytes,
        ref_bytes,
        session_id=session_id,
        src_filename=source_image.filename,
        ref_filename=reference_image.filename
    )
    if reg_out["status"] != "success":
        return JSONResponse(
            status_code=200,
            content={
                "status": "no_match",
                "reason": f"{NO_MATCH_DISCLAIMER} (Temporal change detection requires high-precision pre-registration: {reg_out['reason']})",
                "details": reg_out.get("details", {})
            }
        )

    metrics = reg_out["metrics"]
    if metrics["registration_confidence_score"] < min_confidence:
        return JSONResponse(
            status_code=200,
            content={
                "status": "no_match",
                "reason": (
                    f"{NO_MATCH_DISCLAIMER} "
                    f"Registration confidence ({metrics['registration_confidence_percentage']}%) "
                    f"is below the threshold ({int(min_confidence * 100)}%) required for change detection."
                ),
                "details": metrics
            }
        )

    # 2. Extract internal arrays
    src_prep = reg_out["_internal"]["src_prep"]
    ref_prep = reg_out["_internal"]["ref_prep"]
    reg_result = reg_out["_internal"]["reg_result"]

    # 3. Execute Temporal Change Detection Pipeline
    custom_change_svc = ChangeDetectionService(
        min_region_area=20,
        diff_threshold=difference_threshold
    )
    change_res = custom_change_svc.detect_changes(
        reference_img=ref_prep["original_color"],
        aligned_img=reg_result["aligned_image"],
        valid_overlap_mask=reg_result["valid_overlap_mask"]
    )

    # 4. Save Visual Artifacts
    aligned_url = save_image_artifact(reg_result["aligned_image"], "aligned_for_change", session_id)
    heatmap_url = save_image_artifact(change_res["heatmap_image"], "change_heatmap", session_id)
    mask_url = save_image_artifact(change_res["change_mask"], "change_mask", session_id)
    annotated_url = save_image_artifact(change_res["annotated_image"], "annotated_changes", session_id)
    orig_src_url = save_image_artifact(src_prep["original_color"], "source_orig", session_id)
    orig_ref_url = save_image_artifact(ref_prep["original_color"], "reference_orig", session_id)

    return {
        "status": "success",
        "session_id": session_id,
        "registration_metrics": metrics,
        "change_metrics": {
            "mean_ssim": change_res["mean_ssim"],
            "total_regions_detected": change_res["total_regions_found"]
        },
        "detected_regions": change_res["detected_regions"],
        "artifacts": {
            "source_image": orig_src_url,
            "reference_image": orig_ref_url,
            "aligned_image": aligned_url,
            "change_heatmap": heatmap_url,
            "change_mask": mask_url,
            "annotated_visualization": annotated_url
        },
        "disclaimer": "Detected regions represent potential surface changes and are not scientifically confirmed discoveries."
    }
@router.post("/sun-angle-robustness")
def analyze_sun_angle_robustness(
    source_image: UploadFile = File(..., description="Source lunar image"),
    reference_image: UploadFile = File(..., description="Reference lunar image"),
    preferred_detector: str = Form("SIFT", description="Feature detector to use"),
    manual_angle: Optional[float] = Form(None, description="Optional manual sun-angle difference in degrees")
) -> Dict[str, Any]:
    """Analyze sun-angle robustness for a single lunar image pair."""
    try:
        src_bytes = source_image.file.read()
        ref_bytes = reference_image.file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read image stream: {e}")

    service = SunAngleService()
    return service.analyze_pair_robustness(
        src_bytes=src_bytes,
        ref_bytes=ref_bytes,
        preferred_detector=preferred_detector,
        manual_angle_diff=manual_angle,
        src_filename=source_image.filename,
        ref_filename=reference_image.filename
    )


@router.post("/sun-angle-batch")
def run_sun_angle_batch(
    base_image: UploadFile = File(..., description="Baseline lunar image for batch simulation"),
    num_pairs: int = Form(18, description="Number of image pairs for batch evaluation"),
    preferred_detector: str = Form("SIFT", description="Feature detector to use")
) -> Dict[str, Any]:
    """Run sun‑angle batch benchmark and return wrapped results."""
    try:
        base_bytes = base_image.file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read uploaded image: {e}")

    try:
        service = SunAngleService()
        results = service.run_batch_sun_angle_benchmark(
            base_image_bytes=base_bytes,
            num_pairs=num_pairs,
            preferred_detector=preferred_detector,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return {"status": "success", "results": results}
