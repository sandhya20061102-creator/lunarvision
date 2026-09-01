"""
Lunar Image Registration & Warping Service
Estimates perspective transformations (Homography) via RANSAC, prunes geometric outliers,
and warps source temporal lunar images into the reference coordinate system.
"""

from typing import List, Tuple, Optional, Dict, Any
import cv2
import numpy as np


class ImageRegistrationService:
    """
    Service responsible for robust RANSAC-based geometric alignment of temporal lunar images.
    """

    def __init__(self, ransac_reproj_thresh: float = 3.5, min_matches_required: int = 6):
        self.ransac_reproj_thresh = ransac_reproj_thresh
        self.min_matches_required = min_matches_required

    def align_images(
        self,
        source_img: np.ndarray,
        reference_img: np.ndarray,
        src_keypoints: List[cv2.KeyPoint],
        ref_keypoints: List[cv2.KeyPoint],
        matches: List[cv2.DMatch]
    ) -> Dict[str, Any]:
        """
        Calculates homography matrix and warps source image onto reference coordinate frame.

        Parameters:
            source_img: Input source image (can be color or grayscale).
            reference_img: Reference target image (provides target dimensions).
            src_keypoints: Keypoints detected on source image.
            ref_keypoints: Keypoints detected on reference image.
            matches: Filtered matches (e.g. from Lowe's ratio test).

        Returns:
            Dictionary containing:
                - 'success': bool
                - 'error_message': Optional[str]
                - 'aligned_image': Optional[np.ndarray]
                - 'homography_matrix': Optional[np.ndarray]
                - 'inlier_mask': Optional[List[int]]
                - 'inlier_matches': List[cv2.DMatch]
                - 'inlier_count': int
                - 'valid_overlap_mask': Optional[np.ndarray]
        """
        # Guard: Check minimum required matches
        if len(matches) < self.min_matches_required:
            return {
                "success": False,
                "error_message": (
                    f"Insufficient reliable feature matches ({len(matches)}). "
                    f"At least {self.min_matches_required} good matches are required for stable homography."
                ),
                "aligned_image": None,
                "homography_matrix": None,
                "inlier_mask": [],
                "inlier_matches": [],
                "inlier_count": 0,
                "valid_overlap_mask": None,
            }

        # Extract 2D coordinates of matched points
        try:
            src_pts = np.float32([src_keypoints[m.queryIdx].pt for m in matches]).reshape(-1, 1, 2)
            ref_pts = np.float32([ref_keypoints[m.trainIdx].pt for m in matches]).reshape(-1, 1, 2)
        except IndexError as e:
            return {
                "success": False,
                "error_message": f"Keypoint index mismatch during coordinate extraction: {e}",
                "aligned_image": None,
                "homography_matrix": None,
                "inlier_mask": [],
                "inlier_matches": [],
                "inlier_count": 0,
                "valid_overlap_mask": None,
            }

        # Compute Homography via RANSAC
        H, mask = cv2.findHomography(
            src_pts,
            ref_pts,
            cv2.RANSAC,
            self.ransac_reproj_thresh
        )

        if H is None or mask is None:
            return {
                "success": False,
                "error_message": "RANSAC failed to estimate a valid Homography matrix.",
                "aligned_image": None,
                "homography_matrix": None,
                "inlier_mask": [],
                "inlier_matches": [],
                "inlier_count": 0,
                "valid_overlap_mask": None,
            }

        # Validate Homography numerical stability
        det = np.linalg.det(H[:2, :2])
        if abs(det) < 1e-4 or abs(det) > 1e4:
            return {
                "success": False,
                "error_message": f"Homography matrix is degenerate or extremely distorted (determinant={det:.4f}).",
                "aligned_image": None,
                "homography_matrix": None,
                "inlier_mask": [],
                "inlier_matches": [],
                "inlier_count": 0,
                "valid_overlap_mask": None,
            }

        inlier_mask_list = mask.ravel().tolist()
        inlier_matches = [matches[i] for i, val in enumerate(inlier_mask_list) if val == 1]
        inlier_count = len(inlier_matches)

        if inlier_count < 4:
            return {
                "success": False,
                "error_message": f"Too few RANSAC geometric inliers ({inlier_count} < 4). Registration rejected.",
                "aligned_image": None,
                "homography_matrix": None,
                "inlier_mask": inlier_mask_list,
                "inlier_matches": inlier_matches,
                "inlier_count": inlier_count,
                "valid_overlap_mask": None,
            }

        # Warp source image to match reference image coordinate space
        ref_h, ref_w = reference_img.shape[:2]
        aligned_image = cv2.warpPerspective(
            source_img,
            H,
            (ref_w, ref_h),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=0
        )

        # Create binary mask of valid overlapping area (where source warped pixel exists)
        src_h, src_w = source_img.shape[:2]
        ones_mask = np.ones((src_h, src_w), dtype=np.uint8) * 255
        warped_mask = cv2.warpPerspective(
            ones_mask,
            H,
            (ref_w, ref_h),
            flags=cv2.INTER_NEAREST,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=0
        )
        valid_overlap_mask = (warped_mask > 128).astype(np.uint8) * 255

        return {
            "success": True,
            "error_message": None,
            "aligned_image": aligned_image,
            "homography_matrix": H,
            "inlier_mask": inlier_mask_list,
            "inlier_matches": inlier_matches,
            "inlier_count": inlier_count,
            "valid_overlap_mask": valid_overlap_mask,
        }
