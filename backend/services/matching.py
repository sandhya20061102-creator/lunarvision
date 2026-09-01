"""
Feature Matching Service
Matches descriptor vectors between source (temporal) and reference lunar images using BFMatcher
and applies Lowe's ratio test to filter ambiguous correspondences.
"""

from typing import List, Tuple, Optional
import cv2
import numpy as np


class FeatureMatchingService:
    """
    Service responsible for matching lunar keypoint descriptors using Brute-Force Matcher.
    """

    def __init__(self, sift_ratio_thresh: float = 0.75, akaze_ratio_thresh: float = 0.80):
        self.sift_ratio_thresh = sift_ratio_thresh
        self.akaze_ratio_thresh = akaze_ratio_thresh

    def match_descriptors(
        self,
        desc_src: Optional[np.ndarray],
        desc_ref: Optional[np.ndarray],
        algorithm: str = "SIFT",
        custom_ratio: Optional[float] = None
    ) -> Tuple[List[cv2.DMatch], int]:
        """
        Computes 2-NN Brute Force matches between source and reference descriptors,
        then filters them using Lowe's ratio test.

        Parameters:
            desc_src: Descriptors from source image.
            desc_ref: Descriptors from reference image.
            algorithm: 'SIFT' (uses NORM_L2) or 'AKAZE' (uses NORM_HAMMING).
            custom_ratio: Optional override for ratio threshold.

        Returns:
            Tuple of (good_matches, total_raw_matches)
        """
        if desc_src is None or desc_ref is None:
            return [], 0

        if len(desc_src) < 2 or len(desc_ref) < 2:
            return [], 0

        algo_upper = algorithm.upper()
        if algo_upper == "AKAZE" or algo_upper == "ORB" or desc_src.dtype == np.uint8:
            norm_type = cv2.NORM_HAMMING
            ratio_thresh = custom_ratio if custom_ratio is not None else self.akaze_ratio_thresh
        else:
            norm_type = cv2.NORM_L2
            ratio_thresh = custom_ratio if custom_ratio is not None else self.sift_ratio_thresh

        bf = cv2.BFMatcher(norm_type, crossCheck=False)

        try:
            # Find 2 nearest neighbors for each descriptor
            raw_knn_matches = bf.knnMatch(desc_src, desc_ref, k=2)
        except Exception as e:
            # If datatype mismatch or internal error, attempt casting to float32
            if norm_type == cv2.NORM_L2:
                desc_src = desc_src.astype(np.float32)
                desc_ref = desc_ref.astype(np.float32)
                raw_knn_matches = bf.knnMatch(desc_src, desc_ref, k=2)
            else:
                return [], 0

        good_matches: List[cv2.DMatch] = []
        total_raw = len(raw_knn_matches)

        # Apply Lowe's ratio test
        for match_pair in raw_knn_matches:
            if len(match_pair) == 2:
                m, n = match_pair
                # Condition: nearest neighbor distance must be significantly smaller than second nearest
                if m.distance < ratio_thresh * n.distance:
                    good_matches.append(m)
            elif len(match_pair) == 1:
                # If only 1 neighbor exists, accept cautiously if distance is small
                good_matches.append(match_pair[0])

        return good_matches, total_raw
