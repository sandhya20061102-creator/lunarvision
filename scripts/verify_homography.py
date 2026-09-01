"""
Homography Decomposition & Ground Truth Comparison
Compares the transform applied by generate_test_pair.py with the homography
recovered by the registration pipeline on Pair A.
"""
import sys
import math
import numpy as np

sys.path.insert(0, "backend")
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# -------------------------------------------------------------------
# Ground truth applied by generate_test_pair.py (seed=42, pair A)
# -------------------------------------------------------------------
GT_ROTATION_DEG   = 6.370    # degrees (counter-clockwise)
GT_SCALE          = 0.9914   # uniform scale factor
GT_TX             = -7       # pixels X translation
GT_TY             = 36       # pixels Y translation

# -------------------------------------------------------------------
# Run the registration pipeline and capture the homography
# -------------------------------------------------------------------
print("=" * 65)
print("  LunarVision — Homography Decomposition & Ground Truth Check")
print("=" * 65)

with open("test_data/reference_test.png", "rb") as r, \
     open("test_data/source_test.png", "rb") as s:
    res = client.post("/api/images/register", files={
        "source_image":    ("source.png",    s, "image/png"),
        "reference_image": ("reference.png", r, "image/png"),
    })

data = res.json()
assert data["status"] == "success", f"Registration failed unexpectedly: {data}"

H_list = data["homography_matrix"]          # 3x3 list of lists
H = np.array(H_list, dtype=np.float64)

# -------------------------------------------------------------------
# Decompose H into rotation / uniform-scale / translation
#
# For a pure planar similarity transform (rotation + isotropic scale +
# translation), H looks like:
#
#     [s*cos(t)  -s*sin(t)  tx]
#     [s*sin(t)   s*cos(t)  ty]
#     [   0          0       1]
#
# We extract rotation and scale from the 2x2 upper-left block via SVD.
# Translation comes directly from H[0,2] and H[1,2].
# -------------------------------------------------------------------

# Normalise to make H[2,2] = 1
H = H / H[2, 2]

# Upper-left 2x2 block
A = H[:2, :2]

# SVD decomposition: A = U * diag(sv) * Vt
U, sv, Vt = np.linalg.svd(A)

# Rotation matrix R = U * Vt (closest orthogonal matrix to A)
R = U @ Vt

# Uniform scale = mean of singular values
scale_computed = float(np.mean(sv))

# Rotation angle from R
rotation_rad = math.atan2(R[1, 0], R[0, 0])
rotation_deg_computed = math.degrees(rotation_rad)

# Translation (corrected for normalisation)
tx_computed = H[0, 2]
ty_computed = H[1, 2]

# -------------------------------------------------------------------
# Residual: how much does A differ from a pure similarity transform?
# -------------------------------------------------------------------
sv_ratio = sv[0] / sv[1] if sv[1] > 1e-8 else float("inf")   # 1.0 = pure similarity

# -------------------------------------------------------------------
# Error analysis
# -------------------------------------------------------------------
rot_error   = rotation_deg_computed - GT_ROTATION_DEG
scale_error = scale_computed        - GT_SCALE
tx_error    = tx_computed           - GT_TX
ty_error    = ty_computed           - GT_TY

print()
print("STEP 1 — Ground Truth (applied by generate_test_pair.py)")
print("-" * 65)
print(f"  Rotation applied:      {GT_ROTATION_DEG:>+10.4f} deg")
print(f"  Scale applied:         {GT_SCALE:>+10.4f} x")
print(f"  Translation X applied: {GT_TX:>+10.1f} px")
print(f"  Translation Y applied: {GT_TY:>+10.1f} px")

print()
print("STEP 2 — Raw Homography Matrix (from registration.py / RANSAC)")
print("-" * 65)
for row in H.tolist():
    print(f"  [{row[0]:>12.6f}  {row[1]:>12.6f}  {row[2]:>12.6f}]")
print(f"  Singular value ratio (1.0 = pure similarity): {sv_ratio:.6f}")

print()
print("STEP 3 — Decomposed Pipeline Values")
print("-" * 65)
print(f"  Rotation recovered:    {rotation_deg_computed:>+10.4f} deg")
print(f"  Scale recovered:       {scale_computed:>+10.4f} x")
print(f"  Translation X:         {tx_computed:>+10.3f} px")
print(f"  Translation Y:         {ty_computed:>+10.3f} px")

print()
print("STEP 4 — Error (Computed - Ground Truth)")
print("-" * 65)
print(f"  Rotation error:        {rot_error:>+10.4f} deg")
print(f"  Scale error:           {scale_error:>+10.6f} x  ({abs(scale_error/GT_SCALE)*100:.3f}%)")
print(f"  Translation X error:   {tx_error:>+10.3f} px")
print(f"  Translation Y error:   {ty_error:>+10.3f} px")
print(f"  Translation magnitude: {math.hypot(tx_error, ty_error):>10.3f} px")

# Quality assessment
print()
rot_ok   = abs(rot_error)   < 0.5
scale_ok = abs(scale_error) < 0.01
trans_ok = math.hypot(tx_error, ty_error) < 3.0

print("ASSESSMENT")
print("-" * 65)
print(f"  Rotation  (threshold <0.5 deg):      {'PASS' if rot_ok   else 'FAIL'}  |  error = {rot_error:+.4f} deg")
print(f"  Scale     (threshold <1%):           {'PASS' if scale_ok else 'FAIL'}  |  error = {abs(scale_error/GT_SCALE)*100:.3f}%")
print(f"  Translate (threshold <3 px):         {'PASS' if trans_ok else 'FAIL'}  |  error = {math.hypot(tx_error, ty_error):.3f} px")
print()
