"""
Quality & Alignment Metrics Service
Calculates quantitative metrics including Root Mean Squared Error (RMSE),
inlier count, inlier ratio, and registration confidence score.
"""

from typing import Dict, Any, Optional
import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim


class MetricsService:
    """
    Service responsible for computing quantitative registration quality metrics.
    """

    def calculate_registration_metrics(
        self,
        reference_img: np.ndarray,
        aligned_img: np.ndarray,
        inlier_count: int,
        total_good_matches: int,
        valid_overlap_mask: Optional[np.ndarray] = None
    ) -> Dict[str, Any]:
        """
        Calculates RMSE, inlier ratio, and confidence score for the image registration.

        Parameters:
            reference_img: Reference image (uint8 grayscale or BGR).
            aligned_img: Warped/aligned source image.
            inlier_count: Count of RANSAC inliers.
            total_good_matches: Total matches before RANSAC.
            valid_overlap_mask: 2D uint8 mask representing the valid transformed area.

        Returns:
            Dictionary with metrics:
                - rmse: float
                - inlier_count: int
                - total_good_matches: int
                - inlier_ratio: float
                - confidence_score: float (0.0 to 1.0)
                - confidence_percentage: float (0.0% to 100.0%)
                - overlap_pixel_count: int
                - ssim: float
        """
        # Convert to single channel grayscale if necessary
        ref_gray = reference_img.copy()
        if len(ref_gray.shape) == 3:
            ref_gray = cv2.cvtColor(ref_gray, cv2.COLOR_BGR2GRAY)

        aln_gray = aligned_img.copy()
        if len(aln_gray.shape) == 3:
            aln_gray = cv2.cvtColor(aln_gray, cv2.COLOR_BGR2GRAY)

        # Determine valid overlapping mask
        if valid_overlap_mask is None:
            # Fallback: non-zero pixels in aligned image
            mask = (aln_gray > 0).astype(np.uint8) * 255
        else:
            mask = valid_overlap_mask

        overlap_pixels = int(np.count_nonzero(mask > 0))

        # Calculate RMSE over the valid overlapping region
        if overlap_pixels > 100:
            ref_overlap = ref_gray[mask > 0].astype(np.float64)
            aln_overlap = aln_gray[mask > 0].astype(np.float64)

            mse = float(np.mean((ref_overlap - aln_overlap) ** 2))
            rmse = float(np.sqrt(mse))

            # Compute SSIM on overlapping bounding box
            try:
                score_ssim, _ = ssim(ref_gray, aln_gray, full=True)
                score_ssim = max(0.0, float(score_ssim))
            except Exception:
                score_ssim = 0.0
        else:
            mse = 9999.0
            rmse = 99.99
            score_ssim = 0.0

        # Calculate Inlier Ratio
        inlier_ratio = float(inlier_count / max(total_good_matches, 1))

        # Confidence Score Formulation
        # Factors:
        # 1. Match count weight (40%): Saturated at 40 inliers
        # 2. Inlier ratio weight (35%): Linear ratio (0.0 to 1.0)
        # 3. RMSE alignment quality weight (25%): Normalized (RMSE < 15 is excellent, RMSE > 60 is poor)
        match_score = min(1.0, inlier_count / 40.0)
        ratio_score = min(1.0, inlier_ratio)
        rmse_score = max(0.0, min(1.0, 1.0 - (rmse / 60.0)))

        confidence = (match_score * 0.40) + (ratio_score * 0.35) + (rmse_score * 0.25)
        confidence = float(np.clip(confidence, 0.0, 1.0))

        return {
            "rmse": round(rmse, 3),
            "mse": round(mse, 3),
            "inlier_count": int(inlier_count),
            "total_good_matches": int(total_good_matches),
            "inlier_ratio": round(inlier_ratio, 4),
            "registration_confidence_score": round(confidence, 4),
            "registration_confidence_percentage": round(confidence * 100.0, 1),
            "overlap_pixel_count": overlap_pixels,
            "ssim": round(score_ssim, 4),
        }
