"""
Lunar Feature Detection Service
Extracts keypoints and descriptors from lunar surface imagery using SIFT
with an automatic fallback to AKAZE if SIFT fails or detects insufficient keypoints.
"""

from typing import List, Tuple, Optional, Any
import logging
import cv2
import numpy as np

logger = logging.getLogger(__name__)


class FeatureDetectionService:
    """
    Feature detection service supporting SIFT and AKAZE for lunar orbital imagery.
    """

    def __init__(self, min_features: int = 15, max_akaze_features: int = 3000):
        self.min_features = min_features
        self.max_akaze_features = max_akaze_features
        self._sift = None
        self._akaze = None

        # Attempt to initialize SIFT
        try:
            self._sift = cv2.SIFT_create()
        except Exception as e:
            logger.warning(f"SIFT initialization failed ({e}). Will fallback to AKAZE.")

        # Initialize AKAZE
        try:
            self._akaze = cv2.AKAZE_create()
        except Exception as e:
            logger.error(f"AKAZE initialization failed: {e}")

    def detect_features(
        self,
        image: np.ndarray,
        preferred_algorithm: str = "SIFT"
    ) -> Tuple[List[cv2.KeyPoint], Optional[np.ndarray], str]:
        """
        Detects keypoints and computes descriptors on a lunar image.

        Parameters:
            image: 2D Grayscale or enhanced lunar image (uint8).
            preferred_algorithm: 'SIFT' (default) or 'AKAZE'.

        Returns:
            Tuple of (keypoints, descriptors, algorithm_used)
        """
        if image is None or image.size == 0:
            raise ValueError("Cannot detect features on an empty image.")

        # Ensure image is single-channel uint8
        if len(image.shape) == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        if image.dtype != np.uint8:
            image = (image * 255).astype(np.uint8) if image.max() <= 1.0 else image.astype(np.uint8)

        kps: List[cv2.KeyPoint] = []
        descs: Optional[np.ndarray] = None
        algo_used = preferred_algorithm.upper()

        # 1. Try SIFT if requested and available
        if algo_used == "SIFT" and self._sift is not None:
            try:
                kps, descs = self._sift.detectAndCompute(image, None)
                if kps is not None and len(kps) >= self.min_features and descs is not None:
                    return list(kps), descs, "SIFT"
                logger.info(
                    f"SIFT yielded only {len(kps) if kps is not None else 0} features (< {self.min_features}). Falling back to AKAZE."
                )
            except Exception as e:
                logger.warning(f"SIFT detection raised an exception: {e}. Falling back to AKAZE.")

        # 2. Fallback or direct execution for AKAZE
        if self._akaze is not None:
            try:
                kps, descs = self._akaze.detectAndCompute(image, None)
                if kps is not None and descs is not None:
                    return list(kps), descs, "AKAZE"
            except Exception as e:
                logger.error(f"AKAZE detection raised an exception: {e}")

        # Return empty result if detection completely failed
        return [], None, "NONE"
