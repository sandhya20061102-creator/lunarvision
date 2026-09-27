"""
Global Configuration and Tunable Parameters for LunarVision
Central repository for all algorithmic, threshold, and operational constants.
"""

from pathlib import Path

# Random Seed for Algorithmic Reproducibility
DEFAULT_RANDOM_SEED: int = 42

# Image Processing Limits
MAX_IMAGE_DIMENSION: int = 4096
CLAHE_CLIP_LIMIT: float = 2.0
CLAHE_TILE_GRID_SIZE: tuple = (8, 8)

# Feature Detection Parameters
MIN_FEATURES_DEFAULT: int = 15
MIN_FEATURES_ROUTE: int = 12
MAX_AKAZE_FEATURES: int = 3000
MIN_MATCHES_REQUIRED: int = 6

# Feature Matching Parameters
SIFT_RATIO_THRESH: float = 0.75
AKAZE_RATIO_THRESH: float = 0.80

# RANSAC and Homography Parameters
RANSAC_REPROJ_THRESH: float = 3.5
HOMOGRAPHY_MIN_INLIERS: int = 4
HOMOGRAPHY_DET_MIN: float = 1e-4
HOMOGRAPHY_DET_MAX: float = 1e4

# Quality Metrics and Confidence Score Weights
CONFIDENCE_THRESHOLD: float = 0.20
CHANGE_DETECTION_CONFIDENCE_THRESHOLD: float = 0.35
RMSE_NORM_MAX: float = 60.0
INLIER_COUNT_SATURATION: float = 40.0
MATCH_SCORE_WEIGHT: float = 0.40
RATIO_SCORE_WEIGHT: float = 0.35
RMSE_SCORE_WEIGHT: float = 0.25

# Change Detection Parameters
CHANGE_DIFF_THRESHOLD: int = 35
CHANGE_MIN_REGION_AREA: int = 20

# Benchmark Configuration (Phase 1)
BENCHMARK_SUCCESS_ERROR_THRESH: float = 3.0  # px for ground truth error success
BENCHMARK_SUN_ANGLE_BUCKETS: list = [10.0, 30.0, 60.0]
BENCHMARK_SCALE_RATIO_BUCKETS: list = [2.0, 5.0, 20.0]
DEFAULT_BENCHMARK_OUTPUT_DIR: str = "results"
DEFAULT_BENCHMARK_STRATEGY: str = "standard"
DEFAULT_BENCHMARK_NORM_MODE: str = "flatten"

# Project Directories
BASE_DIR: Path = Path(__file__).resolve().parent
PROJECT_ROOT: Path = BASE_DIR.parent
OUTPUTS_DIR: Path = BASE_DIR / "outputs"
UPLOADS_DIR: Path = BASE_DIR / "uploads"
DEFAULT_RESULTS_DIR: Path = PROJECT_ROOT / DEFAULT_BENCHMARK_OUTPUT_DIR
