"""
Illumination Normalization Service  (Step 2 – Phase 2)
=======================================================
Reduces sun-angle-induced illumination gradients that cause SIFT/AKAZE to
generate sparse, unbalanced descriptors on high incidence-angle lunar images.

Two complementary algorithms are provided:

1. **retinex** – Multi-Scale Retinex (MSR)
   Estimates the *illumination* component at three Gaussian scales and subtracts
   it in log-space, recovering the surface *reflectance* image that is largely
   independent of the solar angle.

   reflectance(x,y) = log(I(x,y)+1) - weighted_mean(log(I*G_sigma + 1))

2. **homomorphic** – Homomorphic high-pass filter
   Models image = illumination × reflectance => log(image) = log(ill) + log(ref)
   A Gaussian high-pass filter in the log domain attenuates the low-frequency
   illumination component, then CLAHE is applied to restore local contrast.

3. **combined** – retinex followed by CLAHE (recommended default)

4. **none** – identity pass-through (for A/B comparisons)

All methods accept and return uint8 grayscale numpy arrays.
"""

from __future__ import annotations

from typing import Tuple

import cv2
import numpy as np


# ---------------------------------------------------------------------------
# Public constants
# ---------------------------------------------------------------------------
VALID_MODES = ("retinex", "homomorphic", "combined", "none")

_MSR_SCALES: Tuple[float, ...] = (15.0, 80.0, 250.0)
_MSR_WEIGHTS: Tuple[float, ...] = (1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0)
_HOMOMORPHIC_SIGMA: float = 30.0          # px; low-freq cutoff
_HOMOMORPHIC_GAMMA_H: float = 2.5         # high-freq gain
_HOMOMORPHIC_GAMMA_L: float = 0.5         # low-freq gain
_CLAHE_CLIP: float = 3.0
_CLAHE_TILE: Tuple[int, int] = (8, 8)


# ---------------------------------------------------------------------------
# IlluminationNormalizer
# ---------------------------------------------------------------------------
class IlluminationNormalizer:
    """
    Applies illumination normalization to grayscale lunar images so that
    sun-angle-induced brightness gradients are suppressed before feature
    detection and descriptor extraction.

    Parameters
    ----------
    mode : str
        One of ``"retinex"``, ``"homomorphic"``, ``"combined"``, ``"none"``.
    msr_scales : tuple of float
        Gaussian kernel sigmas for Multi-Scale Retinex (used by retinex/combined).
    homomorphic_sigma : float
        Sigma of the Gaussian low-pass used in homomorphic filtering.
    clahe_clip : float
        clip_limit for the CLAHE step applied after normalization.
    clahe_tile : tuple of int
        tileGridSize for CLAHE.
    """

    def __init__(
        self,
        mode: str = "combined",
        msr_scales: Tuple[float, ...] = _MSR_SCALES,
        homomorphic_sigma: float = _HOMOMORPHIC_SIGMA,
        clahe_clip: float = _CLAHE_CLIP,
        clahe_tile: Tuple[int, int] = _CLAHE_TILE,
    ) -> None:
        if mode not in VALID_MODES:
            raise ValueError(
                f"Invalid illumination normalization mode '{mode}'. "
                f"Choose from {VALID_MODES}."
            )
        self.mode = mode
        self.msr_scales = msr_scales
        self.homomorphic_sigma = homomorphic_sigma
        self._clahe = cv2.createCLAHE(clipLimit=clahe_clip, tileGridSize=clahe_tile)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def normalize(self, gray: np.ndarray) -> np.ndarray:
        """
        Apply the configured normalization to a single uint8 grayscale image.

        Parameters
        ----------
        gray : np.ndarray
            Single-channel uint8 image (H x W).

        Returns
        -------
        np.ndarray
            Normalized single-channel uint8 image (H x W).
        """
        if gray is None or gray.size == 0:
            raise ValueError("Empty image passed to IlluminationNormalizer.normalize().")

        gray_u8 = self._ensure_uint8_gray(gray)

        if self.mode == "none":
            return gray_u8
        if self.mode == "retinex":
            return self._retinex(gray_u8)
        if self.mode == "homomorphic":
            return self._homomorphic(gray_u8)
        if self.mode == "combined":
            retinex_out = self._retinex(gray_u8)
            return self._clahe.apply(retinex_out)
        # Fallback (should never reach here)
        return gray_u8

    def normalize_pair(
        self, gray_src: np.ndarray, gray_ref: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Normalize both images in a registration pair independently.

        Returns
        -------
        tuple of (normalized_src, normalized_ref)
        """
        return self.normalize(gray_src), self.normalize(gray_ref)

    # ------------------------------------------------------------------
    # Algorithm implementations
    # ------------------------------------------------------------------
    def _ensure_uint8_gray(self, img: np.ndarray) -> np.ndarray:
        """Convert any numeric array to uint8 single-channel image."""
        if img.ndim == 3:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        if img.dtype != np.uint8:
            img = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
        return img

    def _retinex(self, gray_u8: np.ndarray) -> np.ndarray:
        """
        Multi-Scale Retinex (MSR).

        For each scale sigma:
            S_sigma(x,y) = log(I(x,y) + 1) - log(I * G_sigma(x,y) + 1)
        Final output: weighted mean of S_sigma values, stretched to [0, 255].
        """
        img_f = gray_u8.astype(np.float32) + 1.0          # avoid log(0)
        log_img = np.log(img_f)

        msr = np.zeros_like(log_img, dtype=np.float64)
        weights_sum = sum(_MSR_WEIGHTS)

        for sigma, w in zip(self.msr_scales, _MSR_WEIGHTS):
            # Gaussian blur; ensure odd kernel size
            ksize = max(3, int(np.ceil(sigma * 3)) | 1)
            blurred = cv2.GaussianBlur(img_f, (ksize, ksize), sigma)
            log_blur = np.log(blurred + 1.0)
            msr += (w / weights_sum) * (log_img - log_blur)

        # Map to [0, 255]
        msr_min, msr_max = msr.min(), msr.max()
        if msr_max - msr_min < 1e-7:
            return gray_u8.copy()
        normalized = ((msr - msr_min) / (msr_max - msr_min) * 255.0).astype(np.uint8)
        return normalized

    def _homomorphic(self, gray_u8: np.ndarray) -> np.ndarray:
        """
        Homomorphic filtering.

        Steps:
        1. log-transform: z = log(I + 1)
        2. DFT -> shift -> multiply by high-pass filter H(u,v)
        3. IDFT -> exp -> stretch to uint8

        H(u,v) = (gamma_H - gamma_L) * [1 - exp(-D^2 / (2*sigma^2))] + gamma_L
        where D is the distance from the DC component.
        """
        rows, cols = gray_u8.shape
        img_f = gray_u8.astype(np.float32) + 1.0
        log_img = np.log(img_f)

        # DFT (optimal padded size for speed)
        M = cv2.getOptimalDFTSize(rows)
        N = cv2.getOptimalDFTSize(cols)
        padded = np.zeros((M, N), dtype=np.float32)
        padded[:rows, :cols] = log_img

        dft = np.fft.fft2(padded)
        dft_shift = np.fft.fftshift(dft)

        # High-pass filter in frequency domain
        cy, cx = M // 2, N // 2
        Y, X = np.ogrid[:M, :N]
        D_sq = (X - cx).astype(np.float32) ** 2 + (Y - cy).astype(np.float32) ** 2
        sigma_sq = float(self.homomorphic_sigma) ** 2
        H = (
            (_HOMOMORPHIC_GAMMA_H - _HOMOMORPHIC_GAMMA_L)
            * (1.0 - np.exp(-D_sq / (2.0 * sigma_sq + 1e-10)))
            + _HOMOMORPHIC_GAMMA_L
        )

        filtered_shift = dft_shift * H
        filtered = np.fft.ifftshift(filtered_shift)
        result_complex = np.fft.ifft2(filtered)

        # Recover real part, crop, exponentiate
        result_log = np.real(result_complex)[:rows, :cols].astype(np.float32)
        result = np.exp(result_log) - 1.0

        # Stretch to [0, 255]
        r_min, r_max = result.min(), result.max()
        if r_max - r_min < 1e-7:
            return gray_u8.copy()
        out = np.clip((result - r_min) / (r_max - r_min) * 255.0, 0, 255).astype(np.uint8)
        return out
