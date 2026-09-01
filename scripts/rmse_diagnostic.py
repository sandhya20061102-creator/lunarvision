"""
RMSE Diagnostic & Parameter Sweep for Pair A
Identifies root cause of 8.5px RMSE and finds optimal tuning.
"""
import sys, math
import numpy as np
import cv2

sys.path.insert(0, "backend")
from services.preprocessing   import PreprocessingService
from services.feature_detection import FeatureDetectionService
from services.matching          import FeatureMatchingService
from services.registration      import ImageRegistrationService
from services.metrics           import MetricsService

REF_PATH = "test_data/reference_test.png"
SRC_PATH = "test_data/source_test.png"

preprocess_svc = PreprocessingService(clip_limit=2.0, max_dimension=4096)

def run_pipeline(ransac_thresh, ratio_thresh, nfeatures, use_clahe=True, interp=cv2.INTER_LINEAR):
    with open(REF_PATH, "rb") as f: ref_bytes = f.read()
    with open(SRC_PATH, "rb") as f: src_bytes = f.read()

    ref_prep = preprocess_svc.preprocess_pipeline(ref_bytes)
    src_prep = preprocess_svc.preprocess_pipeline(src_bytes)

    img_ref = ref_prep["enhanced"] if use_clahe else ref_prep["normalized"]
    img_src = src_prep["enhanced"] if use_clahe else src_prep["normalized"]

    sift = cv2.SIFT_create(nfeatures=nfeatures, contrastThreshold=0.03, edgeThreshold=10, sigma=1.6)
    kp_ref, des_ref = sift.detectAndCompute(img_ref, None)
    kp_src, des_src = sift.detectAndCompute(img_src, None)

    bf = cv2.BFMatcher(cv2.NORM_L2, crossCheck=False)
    raw = bf.knnMatch(des_src, des_ref, k=2)
    good = [m for m, n in raw if m.distance < ratio_thresh * n.distance]

    if len(good) < 6:
        return None

    src_pts = np.float32([kp_src[m.queryIdx].pt for m in good]).reshape(-1,1,2)
    ref_pts = np.float32([kp_ref[m.trainIdx].pt for m in good]).reshape(-1,1,2)

    H, mask = cv2.findHomography(src_pts, ref_pts, cv2.RANSAC, ransac_thresh)
    if H is None:
        return None

    inlier_count = int(mask.sum())
    ref_color = ref_prep["original_color"]
    src_color = src_prep["original_color"]
    rh, rw = ref_color.shape[:2]

    aligned = cv2.warpPerspective(src_color, H, (rw, rh), flags=interp,
                                   borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    ones = np.ones(src_color.shape[:2], np.uint8) * 255
    warped_mask = cv2.warpPerspective(ones, H, (rw, rh), flags=cv2.INTER_NEAREST,
                                       borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    valid_mask = (warped_mask > 128).astype(np.uint8) * 255

    ref_g = cv2.cvtColor(ref_color, cv2.COLOR_BGR2GRAY)
    aln_g = cv2.cvtColor(aligned,   cv2.COLOR_BGR2GRAY)
    ref_ov = ref_g[valid_mask > 0].astype(np.float64)
    aln_ov = aln_g[valid_mask > 0].astype(np.float64)
    rmse = float(np.sqrt(np.mean((ref_ov - aln_ov)**2)))

    return {
        "rmse": rmse,
        "inliers": inlier_count,
        "good_matches": len(good),
        "kp_src": len(kp_src),
        "kp_ref": len(kp_ref),
        "H": H,
    }

# -----------------------------------------------------------------------
# DIAGNOSTIC SECTION 1 — Baseline reproduction
# -----------------------------------------------------------------------
print("=" * 70)
print("  DIAGNOSTIC: RMSE Root-Cause Analysis on Pair A")
print("=" * 70)

baseline = run_pipeline(ransac_thresh=3.5, ratio_thresh=0.75, nfeatures=0)
print(f"\n[BASELINE]  ransac=3.5px  ratio=0.75  nfeatures=default(0)")
print(f"  Keypoints  src={baseline['kp_src']}  ref={baseline['kp_ref']}")
print(f"  Good matches after ratio test: {baseline['good_matches']}")
print(f"  RANSAC inliers:  {baseline['inliers']}")
print(f"  RMSE:            {baseline['rmse']:.4f} px")

# -----------------------------------------------------------------------
# DIAGNOSTIC SECTION 2 — Sweep RANSAC reprojection threshold
# -----------------------------------------------------------------------
print("\n[SWEEP A]  Varying RANSAC reprojection threshold (ratio=0.75, nfeatures=0)")
print(f"  {'Thresh':>7}  {'RMSE':>8}  {'Inliers':>8}")
for t in [0.5, 1.0, 1.5, 2.0, 3.5, 5.0]:
    r = run_pipeline(ransac_thresh=t, ratio_thresh=0.75, nfeatures=0)
    if r:
        print(f"  {t:>7.1f}  {r['rmse']:>8.4f}  {r['inliers']:>8}")

# -----------------------------------------------------------------------
# DIAGNOSTIC SECTION 3 — Sweep Lowe's ratio threshold
# -----------------------------------------------------------------------
print("\n[SWEEP B]  Varying ratio threshold (ransac=1.5, nfeatures=0)")
print(f"  {'Ratio':>7}  {'Good':>6}  {'RMSE':>8}")
for ratio in [0.60, 0.65, 0.70, 0.75, 0.80]:
    r = run_pipeline(ransac_thresh=1.5, ratio_thresh=ratio, nfeatures=0)
    if r:
        print(f"  {ratio:>7.2f}  {r['good_matches']:>6}  {r['rmse']:>8.4f}")

# -----------------------------------------------------------------------
# DIAGNOSTIC SECTION 4 — Bicubic vs bilinear warp interpolation
# -----------------------------------------------------------------------
print("\n[SWEEP C]  Warp interpolation method (ransac=1.5, ratio=0.70)")
for name, flag in [("INTER_LINEAR", cv2.INTER_LINEAR), ("INTER_CUBIC", cv2.INTER_CUBIC), ("INTER_LANCZOS4", cv2.INTER_LANCZOS4)]:
    r = run_pipeline(ransac_thresh=1.5, ratio_thresh=0.70, nfeatures=0, interp=flag)
    if r:
        print(f"  {name:<18}  RMSE={r['rmse']:.4f} px  inliers={r['inliers']}")

# -----------------------------------------------------------------------
# BEST CONFIG
# -----------------------------------------------------------------------
best = run_pipeline(ransac_thresh=1.5, ratio_thresh=0.70, nfeatures=0, interp=cv2.INTER_CUBIC)
print(f"\n[BEST CONFIG]  ransac=1.5px  ratio=0.70  INTER_CUBIC")
print(f"  RMSE:            {best['rmse']:.4f} px")
print(f"  Improvement:     {baseline['rmse'] - best['rmse']:.4f} px  ({(1 - best['rmse']/baseline['rmse'])*100:.1f}% reduction)")
print(f"  Sub-pixel?       {'YES' if best['rmse'] < 1.0 else 'NO — ' + str(round(best['rmse'],4)) + ' px'}")
