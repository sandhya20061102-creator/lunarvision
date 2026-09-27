"""
LunarVision Real-Data Benchmark Service (Phase 1)
Evaluates registration performance, computes metrics, evaluates ground-truth accuracy,
and aggregates statistical summaries over illumination and scale buckets.
"""

import os
import re
import csv
import json
import time
import math
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union

import cv2
import numpy as np

from backend import config
from backend.services.preprocessing import PreprocessingService
from backend.services.feature_detection import FeatureDetectionService
from backend.services.matching import FeatureMatchingService
from backend.services.registration import ImageRegistrationService
from backend.services.metrics import MetricsService
from backend.services.sun_angle_service import SunAngleService
from backend.services.illumination import IlluminationNormalizer

logger = logging.getLogger(__name__)


class BenchmarkService:
    """
    Automated benchmark evaluation service for planetary image correspondence.
    Executes registration pipelines across manifests, compares against ground truth,
    and produces structured results.csv, summary.json, and summary.md outputs.
    """

    def __init__(
        self,
        seed: int = config.DEFAULT_RANDOM_SEED,
        success_error_thresh: float = config.BENCHMARK_SUCCESS_ERROR_THRESH,
        max_dimension: int = config.MAX_IMAGE_DIMENSION
    ):
        self.seed = seed
        self.success_error_thresh = success_error_thresh
        self.max_dimension = max_dimension

        # Seed global RNG for deterministic reproducibility
        np.random.seed(self.seed)
        cv2.setRNGSeed(self.seed)

        self.preprocess_svc = PreprocessingService(
            clip_limit=config.CLAHE_CLIP_LIMIT,
            tile_grid_size=config.CLAHE_TILE_GRID_SIZE,
            max_dimension=self.max_dimension
        )
        self.feature_svc = FeatureDetectionService(
            min_features=config.MIN_FEATURES_ROUTE,
            max_akaze_features=config.MAX_AKAZE_FEATURES
        )
        self.matching_svc = FeatureMatchingService(
            sift_ratio_thresh=config.SIFT_RATIO_THRESH,
            akaze_ratio_thresh=config.AKAZE_RATIO_THRESH
        )
        self.registration_svc = ImageRegistrationService(
            ransac_reproj_thresh=config.RANSAC_REPROJ_THRESH,
            min_matches_required=config.MIN_MATCHES_REQUIRED
        )
        self.metrics_svc = MetricsService()
        self.sun_angle_svc = SunAngleService()
        # Illumination normalizer used by the 'normalized' strategy
        self.illum_svc = IlluminationNormalizer(mode="combined")

    @staticmethod
    def extract_pds_metadata(file_bytes: bytes, filename: Optional[str] = None) -> Dict[str, Any]:
        """
        Parses PDS label text from the initial 64 KB of file bytes.
        Safely extracts sensor/instrument name, solar angles, and pixel resolution.
        Never raises exceptions on missing fields; returns null/None for unavailable items.
        """
        meta = {
            "sensor": None,
            "incidence_angle": None,
            "sun_elevation": None,
            "sun_azimuth": None,
            "pixel_resolution": None,
        }
        if not file_bytes:
            return meta

        try:
            header_chunk = file_bytes[:65536].decode("latin-1", errors="ignore")

            # 1. Sensor / Instrument
            sensor_match = re.search(
                r'\b(?:INSTRUMENT_NAME|INSTRUMENT_ID|SENSOR_NAME|SENSOR|INSTRUMENT_HOST_NAME)\s*=\s*["\']?([^"\';\r\n]+)',
                header_chunk,
                re.IGNORECASE
            )
            if sensor_match:
                meta["sensor"] = sensor_match.group(1).strip()

            # 2. Solar angles
            inc_match = re.search(
                r'\b(?:INCIDENCE_ANGLE|SOLAR_INCIDENCE_ANGLE)\s*=\s*([0-9.]+)',
                header_chunk,
                re.IGNORECASE
            )
            if inc_match:
                meta["incidence_angle"] = float(inc_match.group(1))

            elev_match = re.search(
                r'\b(?:SUN_ELEVATION|SOLAR_ELEVATION|SOLAR_ALTITUDE)\s*=\s*([0-9.]+)',
                header_chunk,
                re.IGNORECASE
            )
            if elev_match:
                meta["sun_elevation"] = float(elev_match.group(1))

            az_match = re.search(
                r'\b(?:SUN_AZIMUTH|SOLAR_AZIMUTH)\s*=\s*([0-9.]+)',
                header_chunk,
                re.IGNORECASE
            )
            if az_match:
                meta["sun_azimuth"] = float(az_match.group(1))

            # 3. Pixel resolution / Scale
            res_match = re.search(
                r'\b(?:MAP_SCALE|PIXEL_RESOLUTION|SPATIAL_RESOLUTION|SAMPLING_PARAMETER|RESOLUTION)\s*=\s*([0-9.]+)',
                header_chunk,
                re.IGNORECASE
            )
            if res_match:
                meta["pixel_resolution"] = float(res_match.group(1))

        except Exception as e:
            logger.debug(f"PDS metadata extraction exception: {e}")

        return meta

    @staticmethod
    def calculate_scale_and_downscale_factors(
        orig_shape: Tuple[int, int],
        max_dim: int = config.MAX_IMAGE_DIMENSION
    ) -> float:
        """
        Determines the downscale factor applied by PreprocessingService.load_image_from_bytes.
        Returns the scale multiplier (< 1.0 if downscaled, 1.0 otherwise).
        """
        h, w = orig_shape[:2]
        max_len = max(h, w)
        if max_len > max_dim:
            return float(max_dim) / float(max_len)
        return 1.0

    @staticmethod
    def compute_inlier_reprojection_error(
        H: Optional[np.ndarray],
        src_kps: List[cv2.KeyPoint],
        ref_kps: List[cv2.KeyPoint],
        inlier_matches: List[cv2.DMatch]
    ) -> Optional[float]:
        """
        Computes the mean Euclidean reprojection error of inlier keypoint correspondences.
        """
        if H is None or not inlier_matches:
            return None

        try:
            src_pts = np.float32([src_kps[m.queryIdx].pt for m in inlier_matches]).reshape(-1, 1, 2)
            ref_pts = np.float32([ref_kps[m.trainIdx].pt for m in inlier_matches]).reshape(-1, 1, 2)

            # Transform source points via homography
            transformed_pts = cv2.perspectiveTransform(src_pts, H)

            # Euclidean distances
            diff = transformed_pts - ref_pts
            dist = np.sqrt(diff[:, 0, 0] ** 2 + diff[:, 0, 1] ** 2)
            return float(np.mean(dist))
        except Exception:
            return None

    @staticmethod
    def evaluate_ground_truth(
        H: Optional[np.ndarray],
        gt_points: List[Dict[str, List[float]]],
        scale_src: float,
        scale_ref: float
    ) -> Tuple[Optional[float], Optional[float]]:
        """
        Warps source ground-truth points via homography and compares against reference points.
        Accounts for downscale factor applied by preprocessing.
        Returns: (mean_error, median_error) in downscaled reference pixel coordinates.
        """
        if H is None or not gt_points:
            return None, None

        errors: List[float] = []
        for pair in gt_points:
            src_pt = pair.get("src")
            ref_pt = pair.get("ref")
            if src_pt is None or ref_pt is None or len(src_pt) < 2 or len(ref_pt) < 2:
                continue

            # Scale original coordinates by preprocessing scale factor
            sx, sy = float(src_pt[0]) * scale_src, float(src_pt[1]) * scale_src
            rx, ry = float(ref_pt[0]) * scale_ref, float(ref_pt[1]) * scale_ref

            # Homogeneous transformation
            pt_homog = np.array([sx, sy, 1.0], dtype=np.float64)
            warped = H @ pt_homog
            if abs(warped[2]) < 1e-7:
                continue
            pred_rx = warped[0] / warped[2]
            pred_ry = warped[1] / warped[2]

            err = math.sqrt((pred_rx - rx) ** 2 + (pred_ry - ry) ** 2)
            errors.append(err)

        if not errors:
            return None, None

        return float(np.mean(errors)), float(np.median(errors))

    def evaluate_pair(
        self,
        pair_record: Dict[str, Any],
        strategy: str = config.DEFAULT_BENCHMARK_STRATEGY,
        base_dir: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Evaluates a single pair of lunar images according to the benchmark specification.
        Measures individual phase timings, extracts metadata, computes metrics, and validates GT.
        Catches all errors to ensure the benchmark never aborts prematurely.
        """
        # Validate strategy; 'normalized' is now implemented in Phase 2
        _supported = {"standard", "normalized"}
        if strategy not in _supported:
            raise NotImplementedError(
                f"Strategy '{strategy}' is not yet implemented (scheduled for a later phase). "
                f"Supported strategies: {sorted(_supported)}."
            )

        pair_id = str(pair_record.get("pair_id", "unknown_pair"))
        src_path_str = str(pair_record.get("source_path", ""))
        ref_path_str = str(pair_record.get("reference_path", ""))
        gt_path_str = str(pair_record.get("ground_truth_path", "") or "")

        # Resolve paths relative to base_dir if given
        src_path = Path(src_path_str) if not base_dir else (base_dir / src_path_str)
        ref_path = Path(ref_path_str) if not base_dir else (base_dir / ref_path_str)
        gt_path = (Path(gt_path_str) if not base_dir else (base_dir / gt_path_str)) if gt_path_str else None

        result_row: Dict[str, Any] = {
            "pair_id": pair_id,
            "source_path": src_path_str,
            "reference_path": ref_path_str,
            "ground_truth_path": gt_path_str,
            "source_sensor": None,
            "reference_sensor": None,
            "source_sun_incidence": None,
            "reference_sun_incidence": None,
            "source_sun_elevation": None,
            "reference_sun_elevation": None,
            "source_resolution": None,
            "reference_resolution": None,
            "sun_angle_gap": None,
            "scale_ratio": None,
            "strategy": strategy,
            "source_keypoints": 0,
            "reference_keypoints": 0,
            "good_matches": 0,
            "inliers": 0,
            "inlier_ratio": 0.0,
            "mean_reprojection_error": None,
            "confidence": 0.0,
            "confidence_percentage": 0.0,
            "verdict": "no_match",
            "mean_error": None,
            "median_error": None,
            "success": False,
            "load_time_ms": 0.0,
            "preprocess_time_ms": 0.0,
            "feature_detection_time_ms": 0.0,
            "matching_time_ms": 0.0,
            "ransac_time_ms": 0.0,
            "total_time_ms": 0.0,
            "error_message": None,
        }

        total_start = time.perf_counter()

        try:
            # 1. Load Bytes and Timing
            t0 = time.perf_counter()
            if not src_path.exists():
                raise FileNotFoundError(f"Source image not found: {src_path}")
            if not ref_path.exists():
                raise FileNotFoundError(f"Reference image not found: {ref_path}")

            with open(src_path, "rb") as f:
                src_bytes = f.read()
            with open(ref_path, "rb") as f:
                ref_bytes = f.read()

            t1 = time.perf_counter()
            result_row["load_time_ms"] = round((t1 - t0) * 1000.0, 2)

            # Extract PDS / Solar metadata
            src_pds = self.extract_pds_metadata(src_bytes, src_path.name)
            ref_pds = self.extract_pds_metadata(ref_bytes, ref_path.name)
            result_row["source_sensor"] = src_pds["sensor"]
            result_row["reference_sensor"] = ref_pds["sensor"]
            result_row["source_sun_incidence"] = src_pds["incidence_angle"]
            result_row["reference_sun_incidence"] = ref_pds["incidence_angle"]
            result_row["source_sun_elevation"] = src_pds["sun_elevation"]
            result_row["reference_sun_elevation"] = ref_pds["sun_elevation"]
            result_row["source_resolution"] = src_pds["pixel_resolution"]
            result_row["reference_resolution"] = ref_pds["pixel_resolution"]

            # Calculate sun_angle_gap
            if src_pds["incidence_angle"] is not None and ref_pds["incidence_angle"] is not None:
                result_row["sun_angle_gap"] = round(abs(src_pds["incidence_angle"] - ref_pds["incidence_angle"]), 2)
            elif src_pds["sun_elevation"] is not None and ref_pds["sun_elevation"] is not None:
                result_row["sun_angle_gap"] = round(abs(src_pds["sun_elevation"] - ref_pds["sun_elevation"]), 2)

            # Calculate scale_ratio from PDS resolutions if present
            if (
                src_pds["pixel_resolution"] is not None
                and ref_pds["pixel_resolution"] is not None
                and src_pds["pixel_resolution"] > 0
                and ref_pds["pixel_resolution"] > 0
            ):
                s_res, r_res = src_pds["pixel_resolution"], ref_pds["pixel_resolution"]
                result_row["scale_ratio"] = round(max(s_res, r_res) / min(s_res, r_res), 2)

            # 2. Preprocessing and Downscaling Check
            t1 = time.perf_counter()
            # Decode raw arrays first to detect original resolution
            src_raw = self.preprocess_svc.load_image_from_bytes(src_bytes, filename=src_path.name)
            ref_raw = self.preprocess_svc.load_image_from_bytes(ref_bytes, filename=ref_path.name)

            scale_src = self.calculate_scale_and_downscale_factors(src_raw.shape)
            scale_ref = self.calculate_scale_and_downscale_factors(ref_raw.shape)

            src_prep = self.preprocess_svc.preprocess_pipeline(src_raw)
            ref_prep = self.preprocess_svc.preprocess_pipeline(ref_raw)
            t2 = time.perf_counter()
            result_row["preprocess_time_ms"] = round((t2 - t1) * 1000.0, 2)

            # 3. Feature Detection
            # For 'normalized' strategy: apply illumination normalization before detection
            if strategy == "normalized":
                src_feat_img = self.illum_svc.normalize(src_prep["enhanced"])
                ref_feat_img = self.illum_svc.normalize(ref_prep["enhanced"])
            else:
                src_feat_img = src_prep["enhanced"]
                ref_feat_img = ref_prep["enhanced"]

            t2 = time.perf_counter()
            src_kps, src_descs, src_algo = self.feature_svc.detect_features(src_feat_img, preferred_algorithm="SIFT")
            ref_kps, ref_descs, ref_algo = self.feature_svc.detect_features(ref_feat_img, preferred_algorithm="SIFT")
            t3 = time.perf_counter()
            result_row["feature_detection_time_ms"] = round((t3 - t2) * 1000.0, 2)
            result_row["source_keypoints"] = len(src_kps)
            result_row["reference_keypoints"] = len(ref_kps)

            if len(src_kps) < config.MIN_MATCHES_REQUIRED or len(ref_kps) < config.MIN_MATCHES_REQUIRED or src_descs is None or ref_descs is None:
                result_row["verdict"] = "no_match"
                result_row["error_message"] = "Insufficient keypoints detected for correspondence"
                result_row["total_time_ms"] = round((time.perf_counter() - total_start) * 1000.0, 2)
                return result_row

            # 4. Feature Matching
            t3 = time.perf_counter()
            algo_for_matching = src_algo if src_algo == ref_algo else "SIFT"
            good_matches, total_raw = self.matching_svc.match_descriptors(src_descs, ref_descs, algorithm=algo_for_matching)
            t4 = time.perf_counter()
            result_row["matching_time_ms"] = round((t4 - t3) * 1000.0, 2)
            result_row["good_matches"] = len(good_matches)

            if len(good_matches) < config.MIN_MATCHES_REQUIRED:
                result_row["verdict"] = "no_match"
                result_row["error_message"] = f"Too few good matches ({len(good_matches)} < {config.MIN_MATCHES_REQUIRED})"
                result_row["total_time_ms"] = round((time.perf_counter() - total_start) * 1000.0, 2)
                return result_row

            # 5. RANSAC Homography & Metrics
            t4 = time.perf_counter()
            reg_res = self.registration_svc.align_images(
                source_img=src_prep["original_color"],
                reference_img=ref_prep["original_color"],
                src_keypoints=src_kps,
                ref_keypoints=ref_kps,
                matches=good_matches
            )
            t5 = time.perf_counter()
            result_row["ransac_time_ms"] = round((t5 - t4) * 1000.0, 2)

            H = reg_res["homography_matrix"]
            inliers = reg_res["inlier_count"]
            result_row["inliers"] = inliers
            result_row["inlier_ratio"] = round(float(inliers) / float(max(len(good_matches), 1)), 4)

            # Inlier mean reprojection error
            inlier_reproj = self.compute_inlier_reprojection_error(H, src_kps, ref_kps, reg_res.get("inlier_matches", []))
            result_row["mean_reprojection_error"] = round(inlier_reproj, 3) if inlier_reproj is not None else None

            if not reg_res["success"] or H is None:
                result_row["verdict"] = "no_match"
                result_row["error_message"] = reg_res.get("error_message") or "RANSAC registration failed"
                result_row["total_time_ms"] = round((time.perf_counter() - total_start) * 1000.0, 2)
                return result_row

            # Calculate registration metrics and confidence score
            metrics = self.metrics_svc.calculate_registration_metrics(
                reference_img=ref_prep["gray"],
                aligned_img=reg_res["aligned_image"],
                inlier_count=inliers,
                total_good_matches=len(good_matches),
                valid_overlap_mask=reg_res.get("valid_overlap_mask")
            )
            result_row["confidence"] = metrics["registration_confidence_score"]
            result_row["confidence_percentage"] = metrics["registration_confidence_percentage"]

            # Rejection Gate
            if metrics["registration_confidence_score"] < config.CONFIDENCE_THRESHOLD:
                result_row["verdict"] = "no_match"
                result_row["error_message"] = f"Confidence score ({metrics['registration_confidence_percentage']}%) below gate threshold"
            else:
                result_row["verdict"] = "match"

            # 6. Ground-Truth Validation (if provided)
            gt_points = None
            if gt_path and gt_path.exists():
                try:
                    with open(gt_path, "r", encoding="utf-8") as f:
                        gt_points = json.load(f)
                except Exception as e:
                    logger.warning(f"Failed to read ground truth JSON at {gt_path}: {e}")

            if gt_points and isinstance(gt_points, list):
                mean_err, med_err = self.evaluate_ground_truth(H, gt_points, scale_src, scale_ref)
                result_row["mean_error"] = round(mean_err, 3) if mean_err is not None else None
                result_row["median_error"] = round(med_err, 3) if med_err is not None else None

                # Ground Truth Success Criterion: verdict == "match" AND mean_error < 3 px
                if (
                    result_row["verdict"] == "match"
                    and mean_err is not None
                    and mean_err < self.success_error_thresh
                ):
                    result_row["success"] = True
                else:
                    result_row["success"] = False
            else:
                # If ground truth was not provided, success is defined by registration verdict
                result_row["success"] = (result_row["verdict"] == "match")

        except Exception as e:
            logger.exception(f"Unhandled exception during benchmark pair evaluation for {pair_id}: {e}")
            result_row["verdict"] = "error"
            result_row["error_message"] = str(e)
            result_row["success"] = False

        result_row["total_time_ms"] = round((time.perf_counter() - total_start) * 1000.0, 2)
        return result_row

    @staticmethod
    def get_sun_angle_bucket(gap: Optional[float]) -> str:
        """Determines the sun-angle gap bucket category."""
        if gap is None or math.isnan(gap):
            return "unknown"
        if gap < 10.0:
            return "<10"
        if gap < 30.0:
            return "10-30"
        if gap <= 60.0:
            return "30-60"
        return ">60"

    @staticmethod
    def get_scale_ratio_bucket(scale: Optional[float]) -> str:
        """Determines the scale ratio bucket category."""
        if scale is None or math.isnan(scale):
            return "unknown"
        if scale < 2.0:
            return "<2"
        if scale < 5.0:
            return "2-5"
        if scale <= 20.0:
            return "5-20"
        return ">20"

    def compute_summary(
        self,
        results: List[Dict[str, Any]],
        strategy: str = config.DEFAULT_BENCHMARK_STRATEGY
    ) -> Dict[str, Any]:
        """
        Aggregates benchmark results into summary statistics and bucket evaluations.
        """
        total = len(results)
        successes = sum(1 for r in results if r.get("success") is True)
        success_rate = round(successes / total, 4) if total > 0 else 0.0

        gt_errors = [r["mean_error"] for r in results if r.get("mean_error") is not None]
        mean_gt_err = round(float(np.mean(gt_errors)), 3) if gt_errors else None
        med_gt_err = round(float(np.median(gt_errors)), 3) if gt_errors else None

        runtimes = [r["total_time_ms"] for r in results if r.get("total_time_ms") is not None]
        mean_runtime = round(float(np.mean(runtimes)), 2) if runtimes else 0.0
        med_runtime = round(float(np.median(runtimes)), 2) if runtimes else 0.0

        # Initialize Buckets
        sun_bucket_keys = ["<10", "10-30", "30-60", ">60", "unknown"]
        scale_bucket_keys = ["<2", "2-5", "5-20", ">20", "unknown"]

        sun_buckets_data: Dict[str, List[Dict[str, Any]]] = {k: [] for k in sun_bucket_keys}
        scale_buckets_data: Dict[str, List[Dict[str, Any]]] = {k: [] for k in scale_bucket_keys}

        for r in results:
            sb = self.get_sun_angle_bucket(r.get("sun_angle_gap"))
            sun_buckets_data[sb].append(r)

            scb = self.get_scale_ratio_bucket(r.get("scale_ratio"))
            scale_buckets_data[scb].append(r)

        def aggregate_bucket(items: List[Dict[str, Any]]) -> Dict[str, Any]:
            count = len(items)
            if count == 0:
                return {
                    "count": 0,
                    "success_rate": 0.0,
                    "mean_error": None,
                    "median_runtime": 0.0
                }
            succ = sum(1 for x in items if x.get("success") is True)
            errs = [x["mean_error"] for x in items if x.get("mean_error") is not None]
            m_err = round(float(np.mean(errs)), 3) if errs else None
            rts = [x["total_time_ms"] for x in items if x.get("total_time_ms") is not None]
            m_rt = round(float(np.median(rts)), 2) if rts else 0.0
            return {
                "count": count,
                "success_rate": round(succ / count, 4),
                "mean_error": m_err,
                "median_runtime": m_rt
            }

        sun_angle_summary = {k: aggregate_bucket(sun_buckets_data[k]) for k in sun_bucket_keys}
        scale_ratio_summary = {k: aggregate_bucket(scale_buckets_data[k]) for k in scale_bucket_keys}

        return {
            "strategy": strategy,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "total_pairs": total,
            "successful_pairs": successes,
            "failed_pairs": total - successes,
            "success_rate": success_rate,
            "mean_ground_truth_error": mean_gt_err,
            "median_ground_truth_error": med_gt_err,
            "mean_runtime_ms": mean_runtime,
            "median_runtime_ms": med_runtime,
            "sun_angle_gap_buckets": sun_angle_summary,
            "scale_ratio_buckets": scale_ratio_summary
        }

    @staticmethod
    def generate_summary_markdown(summary: Dict[str, Any]) -> str:
        """
        Formats the benchmark summary into a GitHub-flavored Markdown report.
        """
        lines = [
            "# LunarVision Benchmark Execution Report",
            "",
            f"- **Execution Timestamp:** {summary.get('timestamp')}",
            f"- **Evaluation Strategy:** `{summary.get('strategy')}`",
            f"- **Total Image Pairs:** {summary.get('total_pairs')}",
            f"- **Successful Pairs:** {summary.get('successful_pairs')} / {summary.get('total_pairs')} ({summary.get('success_rate', 0.0)*100:.1f}%)",
            f"- **Mean GT Pixel Error:** {summary.get('mean_ground_truth_error') or 'N/A'} px",
            f"- **Median GT Pixel Error:** {summary.get('median_ground_truth_error') or 'N/A'} px",
            f"- **Median Runtime:** {summary.get('median_runtime_ms')} ms",
            "",
            "## Sun-Angle Gap Breakdown",
            "",
            "| Sun-Angle Gap (deg) | Count | Success Rate | Mean Error (px) | Median Runtime (ms) |",
            "| :--- | :--- | :--- | :--- | :--- |"
        ]

        for bucket, data in summary.get("sun_angle_gap_buckets", {}).items():
            err_str = f"{data['mean_error']:.3f}" if data['mean_error'] is not None else "N/A"
            lines.append(
                f"| `{bucket}` | {data['count']} | {data['success_rate']*100:.1f}% | {err_str} | {data['median_runtime']} |"
            )

        lines.extend([
            "",
            "## Scale Ratio Breakdown",
            "",
            "| Scale Ratio | Count | Success Rate | Mean Error (px) | Median Runtime (ms) |",
            "| :--- | :--- | :--- | :--- | :--- |"
        ])

        for bucket, data in summary.get("scale_ratio_buckets", {}).items():
            err_str = f"{data['mean_error']:.3f}" if data['mean_error'] is not None else "N/A"
            lines.append(
                f"| `{bucket}` | {data['count']} | {data['success_rate']*100:.1f}% | {err_str} | {data['median_runtime']} |"
            )

        lines.append("")
        return "\n".join(lines)

    def run_benchmark(
        self,
        manifest_path: Union[str, Path],
        output_dir: Union[str, Path] = config.DEFAULT_BENCHMARK_OUTPUT_DIR,
        strategy: str = config.DEFAULT_BENCHMARK_STRATEGY,
        norm_mode: str = config.DEFAULT_BENCHMARK_NORM_MODE
    ) -> Dict[str, Any]:
        """
        Runs the complete benchmark suite on an input manifest CSV.
        Produces results.csv, summary.json, and summary.md in the specified output directory.
        """
        # Validate strategy
        _supported = {"standard", "normalized"}
        if strategy not in _supported:
            raise NotImplementedError(
                f"Strategy '{strategy}' is not yet implemented (scheduled for a later phase). "
                f"Supported strategies: {sorted(_supported)}."
            )

        manifest_file = Path(manifest_path)
        if not manifest_file.exists():
            raise FileNotFoundError(f"Manifest CSV not found: {manifest_file}")

        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        manifest_base = manifest_file.parent

        # Read manifest CSV
        pairs: List[Dict[str, Any]] = []
        with open(manifest_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            rows = list(reader)

        if not rows:
            raise ValueError(f"Manifest file is empty: {manifest_file}")

        # Check for header
        header = [c.strip().lower() for c in rows[0]]
        start_idx = 0
        if "pair_id" in header or "source_path" in header:
            start_idx = 1
            col_pair = header.index("pair_id") if "pair_id" in header else 0
            col_src = header.index("source_path") if "source_path" in header else 1
            col_ref = header.index("reference_path") if "reference_path" in header else 2
            col_gt = header.index("ground_truth_path") if "ground_truth_path" in header else -1
        else:
            col_pair, col_src, col_ref, col_gt = 0, 1, 2, 3

        for i, row in enumerate(rows[start_idx:], start=start_idx):
            if not row or not any(row):
                continue
            pair_id = row[col_pair].strip() if col_pair < len(row) else f"pair_{i}"
            src_p = row[col_src].strip() if col_src < len(row) else ""
            ref_p = row[col_ref].strip() if col_ref < len(row) else ""
            gt_p = row[col_gt].strip() if 0 <= col_gt < len(row) else ""
            pairs.append({
                "pair_id": pair_id,
                "source_path": src_p,
                "reference_path": ref_p,
                "ground_truth_path": gt_p,
            })

        logger.info(f"Loaded {len(pairs)} benchmark image pairs from {manifest_file}")

        # Process each pair
        results: List[Dict[str, Any]] = []
        for pair_rec in pairs:
            res = self.evaluate_pair(pair_rec, strategy=strategy, base_dir=manifest_base)
            results.append(res)

        # Compute summary
        summary = self.compute_summary(results, strategy=strategy)

        # Write results.csv
        csv_file = out_path / "results.csv"
        csv_columns = [
            "pair_id", "source_path", "reference_path", "ground_truth_path",
            "source_sensor", "reference_sensor", "source_sun_incidence", "reference_sun_incidence",
            "source_sun_elevation", "reference_sun_elevation", "source_resolution", "reference_resolution",
            "sun_angle_gap", "scale_ratio", "strategy", "source_keypoints", "reference_keypoints",
            "good_matches", "inliers", "inlier_ratio", "mean_reprojection_error",
            "confidence", "confidence_percentage", "verdict", "mean_error", "median_error",
            "success", "load_time_ms", "preprocess_time_ms", "feature_detection_time_ms",
            "matching_time_ms", "ransac_time_ms", "total_time_ms", "error_message"
        ]
        with open(csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=csv_columns)
            writer.writeheader()
            for r in results:
                writer.writerow({col: r.get(col) for col in csv_columns})

        # Write summary.json
        json_file = out_path / "summary.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        # Write summary.md
        md_file = out_path / "summary.md"
        md_content = self.generate_summary_markdown(summary)
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(md_content)

        logger.info(f"Benchmark finished. Results saved to {out_path}")
        return summary
