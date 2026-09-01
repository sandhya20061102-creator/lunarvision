"""
generate_test_pair.py — Synthetic Lunar Image Test Pair Generator

FOR TESTING/DEMO PURPOSES ONLY. These are synthetic test pairs derived
from a single real lunar image, not real independent acquisitions.
Do not present results from these pairs as real change detection findings.

PURPOSE:
    When only a single real decoded lunar image is available (e.g. decoded
    from a PDS3 .IMG file), this script produces a reference/source PAIR
    that exercises the full registration pipeline, including:
        - Successful high-confidence registration (pair A)
        - No-match rejection path (pair B — non-overlapping regions)

USAGE:
    python scripts/generate_test_pair.py --input <path_to_real_lunar_image.png>
    python scripts/generate_test_pair.py  # uses built-in synthetic lunar base
"""

import argparse
import os
import sys
import math
import random
from pathlib import Path

import cv2
import numpy as np

# ---------------------------------------------------------------------------
# Ensure backend services are importable (so we can share preprocessing)
# ---------------------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

OUTPUT_DIR = ROOT_DIR / "test_data"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Utility: Affine/Perspective Transform Helpers
# ---------------------------------------------------------------------------

def apply_rotation(image: np.ndarray, angle_deg: float) -> np.ndarray:
    """Rotate image around its center by angle_deg degrees."""
    h, w = image.shape[:2]
    center = (w / 2.0, h / 2.0)
    M = cv2.getRotationMatrix2D(center, angle_deg, 1.0)
    return cv2.warpAffine(
        image, M, (w, h),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_REFLECT
    )


def apply_scale(image: np.ndarray, scale: float) -> np.ndarray:
    """Scale image from its center (zoom in/out) while keeping canvas size."""
    h, w = image.shape[:2]
    center = (w / 2.0, h / 2.0)
    M = cv2.getRotationMatrix2D(center, 0.0, scale)
    return cv2.warpAffine(
        image, M, (w, h),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_REFLECT
    )


def apply_translation(image: np.ndarray, tx: int, ty: int) -> np.ndarray:
    """Shift image by (tx, ty) pixels."""
    h, w = image.shape[:2]
    M = np.float32([[1, 0, tx], [0, 1, ty]])
    return cv2.warpAffine(
        image, M, (w, h),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_REFLECT
    )


def apply_brightness_contrast(
    image: np.ndarray,
    brightness: float,   # additive (-30 to +30)
    contrast: float      # multiplicative (0.85 to 1.15)
) -> np.ndarray:
    """Simulate different solar illumination angle."""
    adjusted = image.astype(np.float32) * contrast + brightness
    return np.clip(adjusted, 0, 255).astype(np.uint8)


def apply_gaussian_noise(image: np.ndarray, std: float = 4.0) -> np.ndarray:
    """Add mild Gaussian noise simulating different sensor characteristics."""
    noise = np.random.normal(0, std, image.shape).astype(np.float32)
    noisy = image.astype(np.float32) + noise
    return np.clip(noisy, 0, 255).astype(np.uint8)


# ---------------------------------------------------------------------------
# Utility: Synthetic lunar base image generator
# ---------------------------------------------------------------------------

def generate_synthetic_lunar_base(size: int = 1024, seed: int = 42) -> np.ndarray:
    """
    Generates a realistic synthetic grayscale lunar terrain image with:
    - Perlin-like multi-scale noise for regolith texture
    - Several craters at varying radii with ejecta rays
    - Large-scale albedo variations
    """
    rng = np.random.default_rng(seed)

    # Multi-scale Gaussian noise baseline (simulates regolith texture)
    base = np.zeros((size, size), dtype=np.float32)
    for scale in [4, 8, 16, 32, 64, 128, 256]:
        small = rng.standard_normal((size // scale + 1, size // scale + 1)).astype(np.float32)
        layer = cv2.resize(small, (size, size), interpolation=cv2.INTER_CUBIC)
        base += layer / (scale ** 0.5)

    # Normalize to [50, 200] range (dark regolith to bright highlands)
    base = cv2.normalize(base, None, 50, 200, cv2.NORM_MINMAX)

    # Draw craters
    craters = [
        (size // 4,     size // 4,     60),   # Large NW crater
        (3 * size // 4, size // 3,     90),   # Large NE crater
        (size // 2,     2 * size // 3, 45),   # Central-south crater
        (size // 5,     2 * size // 3, 25),   # Small SW crater
        (3 * size // 4, 3 * size // 4, 30),   # Small SE crater
        (size // 2,     size // 4,     15),   # Tiny N crater
    ]

    for cx, cy, r in craters:
        Y, X = np.ogrid[:size, :size]
        dist = np.sqrt((X - cx) ** 2 + (Y - cy) ** 2)

        # Rim: bright ring
        rim_mask = (dist >= r - 3) & (dist <= r + 3)
        base[rim_mask] = np.clip(base[rim_mask] * 1.35, 0, 255)

        # Interior: shadow bowl
        interior_mask = dist < r - 3
        depth_factor = (dist[interior_mask] / r) ** 0.7
        base[interior_mask] = base[interior_mask] * 0.45 + 40 * depth_factor

        # Ejecta rays (6-8 radial streaks)
        n_rays = rng.integers(5, 9)
        for i in range(n_rays):
            ray_angle = 2 * math.pi * i / n_rays + rng.uniform(-0.2, 0.2)
            ray_len = rng.integers(int(r * 1.2), int(r * 2.5))
            width_factor = rng.uniform(2.0, 4.0)
            angle_diff = np.abs(np.arctan2(Y - cy, X - cx) - ray_angle)
            angle_diff = np.minimum(angle_diff, 2 * math.pi - angle_diff)
            ray_mask = (dist >= r) & (dist <= r + ray_len) & (angle_diff < (0.1 / width_factor))
            base[ray_mask] = np.clip(base[ray_mask] * 1.20, 0, 255)

    return base.astype(np.uint8)


# ---------------------------------------------------------------------------
# Core: Generate Pair A (Successful Registration)
# ---------------------------------------------------------------------------

def generate_pair_a(base_img: np.ndarray, seed: int = 7) -> dict:
    """
    Generates a well-overlapping reference/source pair with realistic
    orbital acquisition distortions applied to the source.

    Returns dict with reference, source images, and ground-truth transform params.
    """
    rng = np.random.default_rng(seed)
    h, w = base_img.shape[:2]

    # --- Reference: crop a central region ---
    crop_h = min(int(h * 0.80), h)
    crop_w = min(int(w * 0.80), w)
    ref_y = (h - crop_h) // 2
    ref_x = (w - crop_w) // 2
    reference = base_img[ref_y:ref_y + crop_h, ref_x:ref_x + crop_w].copy()

    # --- Source: same region but with synthetic orbital distortions ---
    # 1. Rotation: 2–8 degrees
    rotation_deg = float(rng.uniform(2.5, 7.5))

    # 2. Scale: 0.92x – 1.08x (zoom simulating altitude variation)
    scale_factor = float(rng.uniform(0.93, 1.07))

    # 3. Translation: ±6% of crop dimensions
    tx = int(rng.integers(-int(crop_w * 0.06), int(crop_w * 0.06) + 1))
    ty = int(rng.integers(-int(crop_h * 0.06), int(crop_h * 0.06) + 1))

    # 4. Brightness/Contrast: ±15 brightness, ±10% contrast
    brightness = float(rng.uniform(-15, 15))
    contrast = float(rng.uniform(0.90, 1.10))

    # 5. Gaussian noise: std 3–6 DN
    noise_std = float(rng.uniform(3.0, 6.0))

    # Apply transforms
    source = base_img[ref_y:ref_y + crop_h, ref_x:ref_x + crop_w].copy()
    source = apply_rotation(source, rotation_deg)
    source = apply_scale(source, scale_factor)
    source = apply_translation(source, tx, ty)
    source = apply_brightness_contrast(source, brightness, contrast)
    source = apply_gaussian_noise(source, noise_std)

    # Convert to BGR for saving (3-channel)
    reference_bgr = cv2.cvtColor(reference, cv2.COLOR_GRAY2BGR) if len(reference.shape) == 2 else reference.copy()
    source_bgr = cv2.cvtColor(source, cv2.COLOR_GRAY2BGR) if len(source.shape) == 2 else source.copy()

    return {
        "reference": reference_bgr,
        "source": source_bgr,
        "ground_truth": {
            "rotation_deg": round(rotation_deg, 3),
            "scale_factor": round(scale_factor, 4),
            "translation_x_px": tx,
            "translation_y_px": ty,
            "brightness_shift": round(brightness, 2),
            "contrast_factor": round(contrast, 4),
            "noise_std_dn": round(noise_std, 2),
            "overlap_region": "~80% shared terrain between reference and source",
            "expected_pipeline_outcome": "SUCCESS — High-confidence registration expected"
        }
    }


# ---------------------------------------------------------------------------
# Core: Generate Pair B (No-Match / Non-Overlapping)
# ---------------------------------------------------------------------------

def generate_pair_b(base_img: np.ndarray, seed: int = 13) -> dict:
    """
    Generates a deliberately non-overlapping pair to exercise the
    no-match rejection path in the registration pipeline.
    """
    rng = np.random.default_rng(seed)
    h, w = base_img.shape[:2]

    crop_h = int(h * 0.45)
    crop_w = int(w * 0.45)

    # Reference: top-left quadrant
    reference = base_img[0:crop_h, 0:crop_w].copy()

    # Source: bottom-right quadrant (zero spatial overlap)
    src_y = h - crop_h
    src_x = w - crop_w
    source_raw = base_img[src_y:src_y + crop_h, src_x:src_x + crop_w].copy()

    # Add extreme appearance difference (very different illumination)
    source_raw = apply_brightness_contrast(source_raw, brightness=40, contrast=0.55)
    source_raw = apply_gaussian_noise(source_raw, std=12.0)

    reference_bgr = cv2.cvtColor(reference, cv2.COLOR_GRAY2BGR) if len(reference.shape) == 2 else reference.copy()
    source_bgr = cv2.cvtColor(source_raw, cv2.COLOR_GRAY2BGR) if len(source_raw.shape) == 2 else source_raw.copy()

    return {
        "reference": reference_bgr,
        "source": source_bgr,
        "ground_truth": {
            "overlap": "~0% — deliberately non-overlapping terrain regions",
            "region_ref": "Top-left quadrant (0–45% of image area)",
            "region_source": "Bottom-right quadrant (55–100% of image area)",
            "brightness_shift": "+40 (extreme illumination bias)",
            "contrast_factor": 0.55,
            "noise_std_dn": 12.0,
            "expected_pipeline_outcome": "NO_MATCH — Registration rejection expected"
        }
    }


# ---------------------------------------------------------------------------
# Main Execution
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description=(
            "Generate synthetic lunar image test pairs from a single real lunar image "
            "or a built-in synthetic lunar base. FOR TESTING/DEMO PURPOSES ONLY."
        )
    )
    parser.add_argument(
        "--input", "-i",
        type=str,
        default=None,
        help="Path to a real decoded lunar image (grayscale PNG/TIFF). "
             "If omitted, a built-in synthetic lunar terrain is generated."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducible output (default: 42)"
    )
    parser.add_argument(
        "--noise",
        action="store_true",
        default=True,
        help="Apply mild Gaussian noise to source images (default: enabled)"
    )
    args = parser.parse_args()

    print("=" * 65)
    print("  LunarVision Synthetic Test Pair Generator")
    print("  FOR TESTING/DEMO PURPOSES ONLY")
    print("=" * 65)

    # --- Load or generate base image ---
    if args.input:
        input_path = Path(args.input)
        if not input_path.exists():
            print(f"[ERROR] Input file not found: {input_path}")
            sys.exit(1)
        base_img = cv2.imread(str(input_path), cv2.IMREAD_GRAYSCALE)
        if base_img is None:
            print(f"[ERROR] Failed to decode image at: {input_path}")
            sys.exit(1)
        print(f"\n[INFO] Loaded real lunar image: {input_path}")
        print(f"       Image size: {base_img.shape[1]}x{base_img.shape[0]} px")
    else:
        print("\n[INFO] No --input provided. Generating synthetic lunar terrain base image...")
        base_img = generate_synthetic_lunar_base(size=1024, seed=args.seed)
        print(f"       Generated synthetic base: {base_img.shape[1]}x{base_img.shape[0]} px")

    # --- Pair A: Registration success case ---
    print("\n[GENERATING] Pair A — Overlapping acquisition with orbital distortions...")
    pair_a = generate_pair_a(base_img, seed=args.seed)

    ref_a_path = OUTPUT_DIR / "reference_test.png"
    src_a_path = OUTPUT_DIR / "source_test.png"
    cv2.imwrite(str(ref_a_path), pair_a["reference"])
    cv2.imwrite(str(src_a_path), pair_a["source"])

    gt = pair_a["ground_truth"]
    print(f"\n  [PAIR A] GROUND-TRUTH TRANSFORM (Source <- applied to Reference crop):")
    print(f"    Rotation:         {gt['rotation_deg']:>8.3f}°")
    print(f"    Scale factor:     {gt['scale_factor']:>8.4f}x")
    print(f"    Translation X:    {gt['translation_x_px']:>8d} px")
    print(f"    Translation Y:    {gt['translation_y_px']:>8d} px")
    print(f"    Brightness shift: {gt['brightness_shift']:>8.2f} DN")
    print(f"    Contrast factor:  {gt['contrast_factor']:>8.4f}x")
    print(f"    Noise (Gaussian): {gt['noise_std_dn']:>8.2f} std DN")
    print(f"    Overlap region:   {gt['overlap_region']}")
    print(f"    Expected result:  {gt['expected_pipeline_outcome']}")
    print(f"\n  Saved: {ref_a_path}")
    print(f"  Saved: {src_a_path}")

    # --- Pair B: No-match rejection case ---
    print("\n[GENERATING] Pair B — Non-overlapping terrain regions (no-match path)...")
    pair_b = generate_pair_b(base_img, seed=args.seed + 7)

    ref_b_path = OUTPUT_DIR / "reference_nomatch.png"
    src_b_path = OUTPUT_DIR / "source_nomatch.png"
    cv2.imwrite(str(ref_b_path), pair_b["reference"])
    cv2.imwrite(str(src_b_path), pair_b["source"])

    gt_b = pair_b["ground_truth"]
    print(f"\n  [PAIR B] CONFIGURATION (Non-overlapping regions):")
    for k, v in gt_b.items():
        print(f"    {k.replace('_', ' ').title():25s}: {v}")
    print(f"\n  Saved: {ref_b_path}")
    print(f"  Saved: {src_b_path}")

    print("\n" + "=" * 65)
    print("  Output files written to:", str(OUTPUT_DIR))
    print()
    print("  PAIR A — Registration test files:")
    print(f"    Reference image:  reference_test.png  ({ref_a_path.stat().st_size // 1024} KB)")
    print(f"    Source image:     source_test.png     ({src_a_path.stat().st_size // 1024} KB)")
    print()
    print("  PAIR B — No-match rejection test files:")
    print(f"    Reference image:  reference_nomatch.png  ({ref_b_path.stat().st_size // 1024} KB)")
    print(f"    Source image:     source_nomatch.png     ({src_b_path.stat().st_size // 1024} KB)")
    print()
    print("  DISCLAIMER: These are synthetic test images derived from a single")
    print("  source. They are not real independent orbital acquisitions. Do not")
    print("  present registration or change detection results from these files")
    print("  as real scientific findings.")
    print("=" * 65)


if __name__ == "__main__":
    main()
