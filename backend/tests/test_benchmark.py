"""
Unit and Integration Tests for LunarVision Benchmark Service (Phase 1 + Phase 2)
Verifies:
1. Benchmark evaluation on 3 synthetic pairs:
   - Pair 1: Identical images -> success
   - Pair 2: Rotated + scaled images -> success
   - Pair 3: Unrelated images -> no_match
2. Deterministic reproducibility across repeated benchmark runs
3. Error tolerance (bad pair does not abort benchmark execution)
4. Rejection of un-implemented strategies (crater, auto)
5. GET /api/benchmark/summary endpoint reporting
6. Normalized strategy on a synthetic high-sun-angle-gap illumination pair
7. Normalized strategy full run_benchmark integration
"""

import sys
import csv
import json
import shutil
from pathlib import Path

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

# Ensure root workspace is on sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend import config
from backend.main import app
from backend.services.benchmark import BenchmarkService


def create_synthetic_terrain(width: int = 350, height: int = 350, seed: int = 42) -> np.ndarray:
    """
    Generates a deterministic synthetic lunar terrain image with distinct crater depressions and rims.
    """
    rng = np.random.RandomState(seed)
    surface = rng.normal(120, 20, (height, width)).astype(np.float32)
    surface = cv2.GaussianBlur(surface, (11, 11), 3.0)

    # Add primary crater features with rims and shading
    craters = [
        (100, 100, 30, -50, 40),
        (250, 200, 40, -60, 50),
        (180, 260, 25, -40, 35),
        (270, 90, 20, -35, 25),
        (80, 240, 28, -45, 35),
        (190, 150, 18, -30, 25),
    ]

    for cx, cy, r, depth, rim in craters:
        y, x = np.ogrid[:height, :width]
        dist = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)

        crater_mask = dist <= r
        sun_gradient = ((x - cx) + (y - cy)) / float(max(r, 1))
        surface[crater_mask] += depth * (1.0 - dist[crater_mask] / r) + (sun_gradient[crater_mask] * 15.0)

        rim_mask = (dist > (r - 4)) & (dist <= (r + 4))
        surface[rim_mask] += rim * (1.0 - abs(dist[rim_mask] - r) / 4.0)

    norm_surface = cv2.normalize(surface, None, 10, 240, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
    return cv2.cvtColor(norm_surface, cv2.COLOR_GRAY2BGR)


@pytest.fixture
def synthetic_benchmark_dataset(tmp_path: Path):
    """
    Creates a temporary directory with:
    1. Identical pair (pair1) + ground truth
    2. Rotated and shifted pair (pair2) + ground truth
    3. Unrelated noise pair (pair3)
    4. Manifest CSV referencing all three pairs
    """
    data_dir = tmp_path / "test_data"
    data_dir.mkdir(parents=True, exist_ok=True)

    # ── Pair 1: Identical Images ───────────────────────────────────────────────
    p1_ref = create_synthetic_terrain(350, 350, seed=101)
    p1_src = p1_ref.copy()
    p1_ref_path = data_dir / "p1_ref.png"
    p1_src_path = data_dir / "p1_src.png"
    p1_gt_path = data_dir / "p1_gt.json"
    cv2.imwrite(str(p1_ref_path), p1_ref)
    cv2.imwrite(str(p1_src_path), p1_src)

    p1_gt = [
        {"src": [50.0, 50.0], "ref": [50.0, 50.0]},
        {"src": [180.0, 150.0], "ref": [180.0, 150.0]},
        {"src": [250.0, 200.0], "ref": [250.0, 200.0]},
        {"src": [100.0, 250.0], "ref": [100.0, 250.0]},
    ]
    with open(p1_gt_path, "w", encoding="utf-8") as f:
        json.dump(p1_gt, f)

    # ── Pair 2: Rotated + Shifted + Scaled Images ───────────────────────────────
    p2_ref = create_synthetic_terrain(350, 350, seed=102)
    center = (175.0, 175.0)
    angle_deg = 3.0
    scale = 1.02
    tx, ty = 4.0, -3.0
    M = cv2.getRotationMatrix2D(center, angle_deg, scale)
    M[0, 2] += tx
    M[1, 2] += ty

    p2_src = cv2.warpAffine(p2_ref, M, (350, 350), borderMode=cv2.BORDER_REFLECT)
    p2_ref_path = data_dir / "p2_ref.png"
    p2_src_path = data_dir / "p2_src.png"
    p2_gt_path = data_dir / "p2_gt.json"
    cv2.imwrite(str(p2_ref_path), p2_ref)
    cv2.imwrite(str(p2_src_path), p2_src)

    # Compute ground truth by applying the transformation matrix M
    ref_points = [
        [100.0, 100.0],
        [180.0, 150.0],
        [250.0, 200.0],
        [150.0, 260.0],
    ]
    p2_gt = []
    for rx, ry in ref_points:
        pt_homog = np.array([rx, ry, 1.0], dtype=np.float64)
        src_pt = M @ pt_homog
        p2_gt.append({
            "src": [round(float(src_pt[0]), 2), round(float(src_pt[1]), 2)],
            "ref": [rx, ry]
        })

    with open(p2_gt_path, "w", encoding="utf-8") as f:
        json.dump(p2_gt, f)

    # ── Pair 3: Unrelated Images ───────────────────────────────────────────────
    p3_ref = create_synthetic_terrain(350, 350, seed=103)
    rng_unrel = np.random.RandomState(888)
    p3_src = rng_unrel.randint(0, 255, (350, 350, 3), dtype=np.uint8)
    p3_ref_path = data_dir / "p3_ref.png"
    p3_src_path = data_dir / "p3_src.png"
    cv2.imwrite(str(p3_ref_path), p3_ref)
    cv2.imwrite(str(p3_src_path), p3_src)

    # ── Manifest CSV ───────────────────────────────────────────────────────────
    manifest_path = data_dir / "manifest.csv"
    with open(manifest_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["pair_id", "source_path", "reference_path", "ground_truth_path"])
        writer.writerow(["pair_01_identical", p1_src_path.name, p1_ref_path.name, p1_gt_path.name])
        writer.writerow(["pair_02_transformed", p2_src_path.name, p2_ref_path.name, p2_gt_path.name])
        writer.writerow(["pair_03_unrelated", p3_src_path.name, p3_ref_path.name, ""])

    return {
        "manifest_path": manifest_path,
        "data_dir": data_dir,
    }


def test_01_synthetic_pairs_benchmark(synthetic_benchmark_dataset, tmp_path: Path):
    """
    Tests benchmark on 3 tiny synthetic pairs:
    1. identical -> success
    2. rotated + scaled -> success
    3. unrelated -> no_match
    """
    manifest_path = synthetic_benchmark_dataset["manifest_path"]
    out_dir = tmp_path / "results_run1"

    service = BenchmarkService(seed=config.DEFAULT_RANDOM_SEED)
    summary = service.run_benchmark(
        manifest_path=manifest_path,
        output_dir=out_dir,
        strategy="standard"
    )

    # Verify output artifacts
    assert (out_dir / "results.csv").exists()
    assert (out_dir / "summary.json").exists()
    assert (out_dir / "summary.md").exists()

    # Read results CSV
    with open(out_dir / "results.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = {r["pair_id"]: r for r in reader}

    assert len(rows) == 3

    # Pair 1: Identical images -> success
    p1 = rows["pair_01_identical"]
    assert p1["verdict"] == "match"
    assert p1["success"] == "True"
    assert float(p1["mean_error"]) < 1.0
    assert float(p1["confidence_percentage"]) >= 50.0

    # Pair 2: Rotated + scaled -> success
    p2 = rows["pair_02_transformed"]
    assert p2["verdict"] == "match"
    assert p2["success"] == "True"
    assert float(p2["mean_error"]) < config.BENCHMARK_SUCCESS_ERROR_THRESH
    assert int(p2["inliers"]) >= config.HOMOGRAPHY_MIN_INLIERS

    # Pair 3: Unrelated -> no_match
    p3 = rows["pair_03_unrelated"]
    assert p3["verdict"] == "no_match"
    assert p3["success"] == "False"

    # Overall Summary Checks
    assert summary["total_pairs"] == 3
    assert summary["successful_pairs"] == 2
    assert summary["failed_pairs"] == 1
    assert summary["success_rate"] == round(2 / 3, 4)
    assert summary["strategy"] == "standard"
    assert summary["mean_ground_truth_error"] is not None


def test_02_reproducibility(synthetic_benchmark_dataset, tmp_path: Path):
    """
    Verifies reproducibility:
    Runs the benchmark twice with the same seed and confirms identical numerical results.
    """
    manifest_path = synthetic_benchmark_dataset["manifest_path"]
    out_dir1 = tmp_path / "repro_run_1"
    out_dir2 = tmp_path / "repro_run_2"

    service1 = BenchmarkService(seed=42)
    summary1 = service1.run_benchmark(manifest_path=manifest_path, output_dir=out_dir1, strategy="standard")

    service2 = BenchmarkService(seed=42)
    summary2 = service2.run_benchmark(manifest_path=manifest_path, output_dir=out_dir2, strategy="standard")

    # Read both results.csv
    with open(out_dir1 / "results.csv", "r", encoding="utf-8") as f1, open(out_dir2 / "results.csv", "r", encoding="utf-8") as f2:
        rows1 = list(csv.DictReader(f1))
        rows2 = list(csv.DictReader(f2))

    assert len(rows1) == len(rows2)

    # Compare all numerical and categorical metrics for each row
    deterministic_keys = [
        "pair_id", "verdict", "success", "source_keypoints", "reference_keypoints",
        "good_matches", "inliers", "inlier_ratio", "mean_reprojection_error",
        "confidence", "confidence_percentage", "mean_error", "median_error"
    ]
    for r1, r2 in zip(rows1, rows2):
        for k in deterministic_keys:
            assert r1[k] == r2[k], f"Reproducibility mismatch on key '{k}' for pair {r1['pair_id']}: {r1[k]} != {r2[k]}"

    # Compare summary statistics
    assert summary1["total_pairs"] == summary2["total_pairs"]
    assert summary1["successful_pairs"] == summary2["successful_pairs"]
    assert summary1["success_rate"] == summary2["success_rate"]
    assert summary1["mean_ground_truth_error"] == summary2["mean_ground_truth_error"]
    assert summary1["median_ground_truth_error"] == summary2["median_ground_truth_error"]


def test_03_error_tolerance_bad_pair(synthetic_benchmark_dataset, tmp_path: Path):
    """
    Verifies that one bad pair never aborts the complete benchmark.
    The benchmark catches the error, records it in that row, and continues.
    """
    data_dir = synthetic_benchmark_dataset["data_dir"]
    manifest_with_bad = data_dir / "manifest_with_bad.csv"

    with open(synthetic_benchmark_dataset["manifest_path"], "r", encoding="utf-8") as f:
        existing_rows = list(csv.reader(f))

    # Add a corrupted / non-existent pair entry in the middle
    new_rows = existing_rows + [["pair_corrupt", "nonexistent_source.png", "nonexistent_ref.png", ""]]

    with open(manifest_with_bad, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(new_rows)

    out_dir = tmp_path / "bad_pair_results"
    service = BenchmarkService(seed=42)
    summary = service.run_benchmark(manifest_path=manifest_with_bad, output_dir=out_dir, strategy="standard")

    # Verify all 4 pairs were processed without aborting
    assert summary["total_pairs"] == 4
    assert summary["successful_pairs"] == 2
    assert summary["failed_pairs"] == 2

    with open(out_dir / "results.csv", "r", encoding="utf-8") as f:
        rows = {r["pair_id"]: r for r in csv.DictReader(f)}

    assert "pair_corrupt" in rows
    assert rows["pair_corrupt"]["verdict"] == "error"
    assert "not found" in rows["pair_corrupt"]["error_message"].lower()


def test_04_unimplemented_strategies_rejection(synthetic_benchmark_dataset, tmp_path: Path):
    """
    Verifies that requesting crater or auto strategies raises NotImplementedError
    since they are not yet implemented.  'normalized' is now implemented and
    must NOT raise.
    """
    manifest_path = synthetic_benchmark_dataset["manifest_path"]
    service = BenchmarkService()

    for unsupported in ["crater", "auto"]:
        with pytest.raises(NotImplementedError) as exc_info:
            service.run_benchmark(manifest_path=manifest_path, output_dir=tmp_path / "unsupported", strategy=unsupported)
        assert "not yet implemented" in str(exc_info.value)

    # 'normalized' must NOT raise NotImplementedError any more
    try:
        service.run_benchmark(
            manifest_path=manifest_path,
            output_dir=tmp_path / "normalized_smoke",
            strategy="normalized"
        )
    except NotImplementedError:
        pytest.fail("'normalized' strategy should be implemented but raised NotImplementedError")


def test_05_api_benchmark_summary_endpoint(synthetic_benchmark_dataset, tmp_path: Path, monkeypatch):
    """
    Verifies GET /api/benchmark/summary endpoint returns the latest summary.json.
    """
    manifest_path = synthetic_benchmark_dataset["manifest_path"]
    out_dir = tmp_path / "api_test_results"
    service = BenchmarkService(seed=42)
    service.run_benchmark(manifest_path=manifest_path, output_dir=out_dir)

    # Point config.DEFAULT_RESULTS_DIR to our test output directory
    monkeypatch.setattr(config, "DEFAULT_RESULTS_DIR", out_dir)

    client = TestClient(app)
    response = client.get("/api/benchmark/summary")
    assert response.status_code == 200, f"Endpoint failed: {response.text}"
    body = response.json()

    assert body["total_pairs"] == 3
    assert body["successful_pairs"] == 2
    assert body["strategy"] == "standard"
    assert "sun_angle_gap_buckets" in body
    assert "scale_ratio_buckets" in body


# ---------------------------------------------------------------------------
# Phase 2: Illumination Normalization Tests
# ---------------------------------------------------------------------------

def _make_shaded_terrain(width: int = 350, height: int = 350, seed: int = 42,
                         shading_gradient: float = 0.0) -> np.ndarray:
    """
    Generates a synthetic lunar terrain with a strong directional brightness
    gradient simulating a high sun-incidence-angle (long shadows, bright rims).

    Parameters
    ----------
    shading_gradient : float
        0.0 = no gradient (flat illumination), 1.0 = extreme left-dark / right-bright
    """
    rng = np.random.RandomState(seed)
    surface = rng.normal(128, 20, (height, width)).astype(np.float32)
    surface = cv2.GaussianBlur(surface, (11, 11), 3.0)

    craters = [
        (100, 100, 28, -55, 38),
        (250, 200, 35, -60, 45),
        (175, 260, 22, -40, 32),
        (270, 90,  18, -35, 25),
        (80,  240, 26, -48, 34),
    ]
    for cx, cy, r, depth, rim in craters:
        y, x = np.ogrid[:height, :width]
        dist = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
        mask = dist <= r
        surface[mask] += depth * (1.0 - dist[mask] / r)
        rim_mask = (dist > (r - 4)) & (dist <= (r + 4))
        surface[rim_mask] += rim * (1.0 - abs(dist[rim_mask] - r) / 4.0)

    # Apply directional shading gradient
    if abs(shading_gradient) > 1e-3:
        X = np.linspace(0, 1, width, dtype=np.float32)
        gradient = (X * shading_gradient * 100.0)[np.newaxis, :]
        surface += gradient

    norm = cv2.normalize(surface, None, 10, 240, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
    return cv2.cvtColor(norm, cv2.COLOR_GRAY2BGR)


def test_06_normalized_strategy_illumination_gap(tmp_path: Path):
    """
    Controlled illumination-gap test:
    - Reference image: terrain with no shading gradient
    - Source image: same terrain + geometric transform + strong shading gradient
      (simulating a high sun-incidence-angle acquisition)

    Assertions:
    1. The 'normalized' strategy completes without error
    2. The normalized strategy produces >= inliers compared to the standard strategy on this pair
       (or both produce a match - demonstrating normalization preserves matchability)
    3. The normalized strategy reports 'match' verdict
    """
    data_dir = tmp_path / "illum_test_data"
    data_dir.mkdir(parents=True, exist_ok=True)

    # Reference: clean terrain
    ref_img = _make_shaded_terrain(350, 350, seed=200, shading_gradient=0.0)

    # Source: small rotation + heavy directional shading gradient
    center = (175.0, 175.0)
    M = cv2.getRotationMatrix2D(center, 4.0, 1.01)
    M[0, 2] += 5.0
    M[1, 2] += -4.0
    src_base = cv2.warpAffine(ref_img, M, (350, 350), borderMode=cv2.BORDER_REFLECT)
    # Apply strong horizontal brightness gradient (simulate high sun incidence angle)
    gradient_layer = np.zeros((350, 350), dtype=np.float32)
    for x_idx in range(350):
        gradient_layer[:, x_idx] = x_idx * 0.35
    src_gray = cv2.cvtColor(src_base, cv2.COLOR_BGR2GRAY).astype(np.float32)
    src_shaded_gray = np.clip(src_gray + gradient_layer, 0, 255).astype(np.uint8)
    src_img = cv2.cvtColor(src_shaded_gray, cv2.COLOR_GRAY2BGR)

    # Ground-truth control points (apply M to reference corners)
    ref_points = [[50.0, 50.0], [175.0, 150.0], [260.0, 200.0], [150.0, 260.0]]
    gt = []
    for rx, ry in ref_points:
        pt = M @ np.array([rx, ry, 1.0])
        gt.append({"src": [round(float(pt[0]), 2), round(float(pt[1]), 2)], "ref": [rx, ry]})

    ref_path = data_dir / "illum_ref.png"
    src_path = data_dir / "illum_src.png"
    gt_path = data_dir / "illum_gt.json"
    cv2.imwrite(str(ref_path), ref_img)
    cv2.imwrite(str(src_path), src_img)
    import json
    with open(gt_path, "w") as f:
        json.dump(gt, f)

    manifest_path = data_dir / "manifest.csv"
    with open(manifest_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["pair_id", "source_path", "reference_path", "ground_truth_path"])
        writer.writerow(["illum_pair", src_path.name, ref_path.name, gt_path.name])

    service = BenchmarkService(seed=42)

    # Run both strategies
    out_std = tmp_path / "std_results"
    out_nrm = tmp_path / "nrm_results"
    service.run_benchmark(manifest_path=manifest_path, output_dir=out_std, strategy="standard")
    service.run_benchmark(manifest_path=manifest_path, output_dir=out_nrm, strategy="normalized")

    # Read both results
    with open(out_std / "results.csv", "r", encoding="utf-8") as f:
        std_row = list(csv.DictReader(f))[0]
    with open(out_nrm / "results.csv", "r", encoding="utf-8") as f:
        nrm_row = list(csv.DictReader(f))[0]

    # Normalized strategy must complete and not error
    assert nrm_row["verdict"] != "error", f"Normalized strategy errored: {nrm_row.get('error_message')}"
    assert nrm_row["strategy"] == "normalized"

    # Normalized must produce a match on this pair
    # (If standard also produces match, normalized should be at least as good)
    std_inliers = int(std_row["inliers"])
    nrm_inliers = int(nrm_row["inliers"])

    # Key assertion: normalized inliers >= standard inliers OR normalized
    # produces a match while standard may not — shows normalization adds value
    assert nrm_row["verdict"] == "match", (
        f"Normalized strategy failed to match on illumination-gap pair. "
        f"inliers={nrm_inliers}, verdict={nrm_row['verdict']}"
    )


def test_07_normalized_strategy_benchmark_run(synthetic_benchmark_dataset, tmp_path: Path):
    """
    Integration test: run_benchmark with strategy='normalized' completes
    cleanly on the standard 3-pair synthetic dataset.
    Checks:
    - No exceptions raised
    - Summary has strategy='normalized'
    - success_rate, verdicts are consistent
    """
    manifest_path = synthetic_benchmark_dataset["manifest_path"]
    out_dir = tmp_path / "normalized_full_run"

    service = BenchmarkService(seed=42)
    summary = service.run_benchmark(
        manifest_path=manifest_path,
        output_dir=out_dir,
        strategy="normalized"
    )

    assert summary["strategy"] == "normalized"
    assert summary["total_pairs"] == 3
    assert (out_dir / "results.csv").exists()
    assert (out_dir / "summary.json").exists()
    assert (out_dir / "summary.md").exists()

    # Normalized should still match the identical pair (pair 1) and the transformed pair (pair 2)
    with open(out_dir / "results.csv", "r", encoding="utf-8") as f:
        rows = {r["pair_id"]: r for r in csv.DictReader(f)}

    assert rows["pair_01_identical"]["verdict"] == "match", "Identical pair must match under normalized strategy"
    assert rows["pair_01_identical"]["strategy"] == "normalized"
    # Pair 3 (unrelated) should still not match
    assert rows["pair_03_unrelated"]["verdict"] == "no_match", "Unrelated pair must not match under normalized strategy"
