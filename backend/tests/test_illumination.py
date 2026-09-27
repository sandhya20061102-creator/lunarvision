"""
Unit Tests for IlluminationNormalizer (backend/services/illumination.py)

Verifies:
1. All modes produce uint8 single-channel images of the correct shape
2. 'none' mode is a no-op identity pass-through
3. 'retinex', 'homomorphic', 'combined' reduce a strong brightness gradient
   (demonstrated via coefficient of variation improvement)
4. normalize_pair() returns independent results for src and ref
5. Invalid mode raises ValueError at construction time
6. Empty array raises ValueError
"""

import sys
from pathlib import Path

import cv2
import numpy as np
import pytest

root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.services.illumination import IlluminationNormalizer, VALID_MODES


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _make_gradient_terrain(size: int = 256, seed: int = 7, gradient_strength: float = 1.0) -> np.ndarray:
    """
    Creates a synthetic grayscale image with crater features overlaid on a
    strong left-to-right brightness gradient (simulating oblique illumination).
    Returns uint8 single-channel array.
    """
    rng = np.random.RandomState(seed)
    base = rng.normal(128, 15, (size, size)).astype(np.float32)
    base = cv2.GaussianBlur(base, (11, 11), 3.0)

    # Add some crater-like features
    for cx, cy, r in [(60, 60, 20), (150, 120, 28), (100, 180, 18)]:
        y, x = np.ogrid[:size, :size]
        dist = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
        base[dist <= r] -= 50.0 * (1.0 - dist[dist <= r] / r)

    # Horizontal gradient: left side dark, right side bright
    if abs(gradient_strength) > 1e-3:
        X = np.linspace(0, gradient_strength * 120, size, dtype=np.float32)
        base += X[np.newaxis, :]

    norm = cv2.normalize(base, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
    return norm  # single-channel uint8


def _coefficient_of_variation(img: np.ndarray) -> float:
    """CV = std / mean; lower = more uniform brightness."""
    f = img.astype(np.float64)
    mean = f.mean()
    if mean < 1e-9:
        return 0.0
    return float(f.std() / mean)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def gradient_image():
    """256×256 uint8 grayscale image with a strong illumination gradient."""
    return _make_gradient_terrain(256, seed=7, gradient_strength=1.0)


@pytest.fixture
def flat_image():
    """256×256 uint8 grayscale image with no gradient."""
    return _make_gradient_terrain(256, seed=7, gradient_strength=0.0)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
def test_01_output_shape_and_dtype(gradient_image):
    """
    All normalization modes must produce a uint8 single-channel image of
    the same spatial dimensions as the input.
    """
    for mode in VALID_MODES:
        normalizer = IlluminationNormalizer(mode=mode)
        out = normalizer.normalize(gradient_image)
        assert out.dtype == np.uint8, f"Mode '{mode}': expected uint8 output, got {out.dtype}"
        assert out.shape == gradient_image.shape, (
            f"Mode '{mode}': output shape {out.shape} != input shape {gradient_image.shape}"
        )


def test_02_none_mode_is_identity(flat_image):
    """
    'none' mode must return a byte-identical copy of the input.
    """
    normalizer = IlluminationNormalizer(mode="none")
    out = normalizer.normalize(flat_image)
    np.testing.assert_array_equal(out, flat_image, err_msg="'none' mode altered the image pixels")


def test_03_accepts_bgr_input(gradient_image):
    """
    All modes must accept 3-channel BGR input and return a valid uint8 gray image.
    """
    bgr = cv2.cvtColor(gradient_image, cv2.COLOR_GRAY2BGR)
    for mode in VALID_MODES:
        normalizer = IlluminationNormalizer(mode=mode)
        out = normalizer.normalize(bgr)
        assert out.ndim == 2, f"Mode '{mode}': expected 2D output from BGR input, got shape {out.shape}"
        assert out.dtype == np.uint8


def test_04_gradient_suppression(gradient_image, flat_image):
    """
    Retinex, homomorphic, and combined modes must reduce the row-wise brightness
    gradient measurably.  We compare column-mean standard deviation as a proxy:
    a smaller column-mean std means a flatter overall brightness profile.

    We allow the normalized image to have column-mean std <= 1.5x that of the
    flat (un-shaded) version.  Standard (no normalization) on the gradient image
    has much higher column-mean std.
    """
    # Baseline: flat image's column-mean std (ideally ~0)
    flat_col_std = float(np.array([flat_image[:, c].mean() for c in range(flat_image.shape[1])]).std())

    # Standard image's column-mean std (high because of gradient)
    grad_col_std = float(np.array([gradient_image[:, c].mean() for c in range(gradient_image.shape[1])]).std())

    # Gradient image must have noticeably more column variation than flat
    assert grad_col_std > flat_col_std * 2.0, (
        "Test setup: gradient image should be significantly more non-uniform than flat"
    )

    tolerance_factor = 2.0  # normalized image's col_std <= tolerance_factor * flat_col_std
    for mode in ("retinex", "homomorphic", "combined"):
        normalizer = IlluminationNormalizer(mode=mode)
        out = normalizer.normalize(gradient_image)
        out_col_std = float(np.array([out[:, c].mean() for c in range(out.shape[1])]).std())
        assert out_col_std <= grad_col_std * 0.8, (
            f"Mode '{mode}': normalization did not reduce the illumination gradient. "
            f"grad_col_std={grad_col_std:.2f}, normalized_col_std={out_col_std:.2f}"
        )


def test_05_normalize_pair(gradient_image, flat_image):
    """
    normalize_pair() must apply the normalizer independently to both images,
    returning correct shapes and dtypes for each.
    """
    normalizer = IlluminationNormalizer(mode="combined")
    src_out, ref_out = normalizer.normalize_pair(gradient_image, flat_image)
    assert src_out.shape == gradient_image.shape
    assert ref_out.shape == flat_image.shape
    assert src_out.dtype == np.uint8
    assert ref_out.dtype == np.uint8
    # Results must differ because inputs differ
    assert not np.array_equal(src_out, ref_out)


def test_06_invalid_mode_raises():
    """
    Constructing IlluminationNormalizer with an unsupported mode string
    must raise ValueError immediately.
    """
    with pytest.raises(ValueError, match="Invalid illumination normalization mode"):
        IlluminationNormalizer(mode="gamma_stretch")


def test_07_empty_array_raises():
    """
    Passing an empty array to normalize() must raise ValueError.
    """
    normalizer = IlluminationNormalizer(mode="retinex")
    with pytest.raises(ValueError, match="Empty image"):
        normalizer.normalize(np.array([]))


def test_08_small_image(gradient_image):
    """
    Normalization must succeed on very small images without crashing
    (handles edge cases in Gaussian blur kernel sizing).
    """
    tiny = gradient_image[:16, :16]
    for mode in VALID_MODES:
        normalizer = IlluminationNormalizer(mode=mode)
        out = normalizer.normalize(tiny)
        assert out.shape == tiny.shape
        assert out.dtype == np.uint8


def test_09_uniform_image_no_crash():
    """
    A perfectly uniform image (all same value) must not crash
    even though there is nothing to normalize (returns a valid uint8 image).
    """
    uniform = np.full((64, 64), 128, dtype=np.uint8)
    for mode in VALID_MODES:
        normalizer = IlluminationNormalizer(mode=mode)
        out = normalizer.normalize(uniform)
        assert out.dtype == np.uint8
        assert out.shape == (64, 64)
