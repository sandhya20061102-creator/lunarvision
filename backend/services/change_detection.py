"""
Temporal Change Detection Service for Lunar Surface Imagery
Performs illumination normalization, SSIM dissimilarity analysis, absolute differencing,
morphological noise reduction, connected component segmentation, heatmap visualization,
and heuristic labeling of surface alterations (craters, illumination shifts, regolith changes).
"""

from typing import List, Dict, Any, Tuple, Optional
import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim


class ChangeDetectionService:
    """
    Service responsible for detecting, segmenting, and classifying temporal changes
    between aligned lunar orbital images.
    """

    def __init__(
        self,
        min_region_area: int = 20,
        max_region_area_ratio: float = 0.40,
        ssim_weight: float = 0.5,
        absdiff_weight: float = 0.5,
        diff_threshold: int = 35
    ):
        self.min_region_area = min_region_area
        self.max_region_area_ratio = max_region_area_ratio
        self.ssim_weight = ssim_weight
        self.absdiff_weight = absdiff_weight
        self.diff_threshold = diff_threshold
        self._clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))

    def detect_changes(
        self,
        reference_img: np.ndarray,
        aligned_img: np.ndarray,
        valid_overlap_mask: Optional[np.ndarray] = None
    ) -> Dict[str, Any]:
        """
        Executes end-to-end temporal change detection on aligned lunar image pair.

        Parameters:
            reference_img: Reference image (color or grayscale).
            aligned_img: Warped source image aligned to reference frame.
            valid_overlap_mask: Binary mask of valid transformed area.

        Returns:
            Dictionary containing:
                - 'mean_ssim': float
                - 'change_mask': np.ndarray (uint8 binary 0/255)
                - 'difference_map': np.ndarray (uint8 0-255)
                - 'heatmap_image': np.ndarray (BGR heatmap overlay)
                - 'annotated_image': np.ndarray (BGR reference image with bounding boxes & labels)
                - 'detected_regions': List[Dict[str, Any]] (region metadata & heuristic labels)
                - 'disclaimer': str
        """
        # Ensure images are in grayscale for numerical comparisons
        ref_gray = cv2.cvtColor(reference_img, cv2.COLOR_BGR2GRAY) if len(reference_img.shape) == 3 else reference_img.copy()
        aln_gray = cv2.cvtColor(aligned_img, cv2.COLOR_BGR2GRAY) if len(aligned_img.shape) == 3 else aligned_img.copy()

        h, w = ref_gray.shape[:2]

        # Overlap mask handling
        if valid_overlap_mask is None:
            overlap_mask = ((aln_gray > 0) & (ref_gray > 0)).astype(np.uint8) * 255
        else:
            overlap_mask = valid_overlap_mask.copy()

        # Erode mask slightly to eliminate boundary interpolation artifacts
        kernel_erode = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
        eroded_mask = cv2.erode(overlap_mask, kernel_erode)

        # 1. Illumination Normalization on both images
        ref_enhanced = self._clahe.apply(ref_gray)
        aln_enhanced = self._clahe.apply(aln_gray)

        # 2. SSIM Dissimilarity computation
        try:
            score_ssim, ssim_full_map = ssim(ref_enhanced, aln_enhanced, full=True)
            # SSIM dissimilarity: 1.0 (no change) to -1.0 (complete change) -> scale to [0, 255]
            ssim_diff_float = np.clip((1.0 - ssim_full_map) / 2.0, 0.0, 1.0)
            ssim_diff_uint8 = (ssim_diff_float * 255.0).astype(np.uint8)
        except Exception:
            score_ssim = 0.0
            ssim_diff_uint8 = np.zeros_like(ref_gray)

        # 3. Absolute Pixel Difference
        abs_diff = cv2.absdiff(ref_enhanced, aln_enhanced)

        # 4. Blended Difference Map
        blended_diff = cv2.addWeighted(
            abs_diff,
            self.absdiff_weight,
            ssim_diff_uint8,
            self.ssim_weight,
            0
        )
        # Zero out non-overlapping and boundary regions
        blended_diff[eroded_mask == 0] = 0

        # 5. Thresholding
        # Apply Otsu's thresholding combined with minimum threshold gate
        overlap_vals = blended_diff[eroded_mask > 0]
        if len(overlap_vals) > 0:
            otsu_thresh, _ = cv2.threshold(overlap_vals, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            applied_thresh = max(self.diff_threshold, int(otsu_thresh * 0.9))
        else:
            applied_thresh = self.diff_threshold

        _, raw_mask = cv2.threshold(blended_diff, applied_thresh, 255, cv2.THRESH_BINARY)
        raw_mask[eroded_mask == 0] = 0

        # 6. Morphological Operations (Opening to remove salt noise, Closing to bridge craters)
        kernel_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))

        clean_mask = cv2.morphologyEx(raw_mask, cv2.MORPH_OPEN, kernel_open)
        clean_mask = cv2.morphologyEx(clean_mask, cv2.MORPH_CLOSE, kernel_close)

        # 7. False-Color Heatmap Generation (JET Colormap overlaid on reference image)
        # Normalize difference map for vivid contrast
        norm_diff = cv2.normalize(blended_diff, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
        color_heatmap = cv2.applyColorMap(norm_diff, cv2.COLORMAP_JET)

        # Base reference in color
        ref_bgr = cv2.cvtColor(ref_gray, cv2.COLOR_GRAY2BGR) if len(reference_img.shape) == 2 else reference_img.copy()
        heatmap_overlay = cv2.addWeighted(ref_bgr, 0.55, color_heatmap, 0.45, 0)
        # Retain original reference pixels outside overlap
        heatmap_overlay[eroded_mask == 0] = ref_bgr[eroded_mask == 0]

        # 8. Connected Component Analysis & Heuristic Labeling
        annotated_img = ref_bgr.copy()
        contours, _ = cv2.findContours(clean_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        total_image_pixels = h * w
        detected_regions: List[Dict[str, Any]] = []

        # Color mapping for bounding box categories
        category_colors = {
            "Possible crater-like change": (0, 165, 255),       # Orange
            "Potential surface change": (0, 242, 254),          # Cyan / Yellow
            "Possible illumination artifact": (255, 105, 180),  # Pink/Violet
            "Low confidence": (128, 128, 128)                   # Gray
        }

        region_idx = 1
        for cnt in contours:
            area = cv2.contourArea(cnt)

            # Filter out tiny noise and gigantic full-image masks
            if area < self.min_region_area or area > (total_image_pixels * self.max_region_area_ratio):
                continue

            x, y, rw, rh = cv2.boundingRect(cnt)
            perimeter = cv2.arcLength(cnt, True)
            circularity = (4.0 * np.pi * area) / (perimeter ** 2) if perimeter > 0 else 0.0
            aspect_ratio = float(rw) / max(rh, 1)

            # Extract region intensity properties
            roi_diff = blended_diff[y:y + rh, x:x + rw]
            mean_intensity_delta = float(np.mean(roi_diff)) if roi_diff.size > 0 else 0.0

            # Compute distance to eroded mask boundary
            dist_to_edge = min(x, y, w - (x + rw), h - (y + rh))

            # Apply Explainable Heuristic Classification
            if dist_to_edge < 8 or area < self.min_region_area * 1.5 or mean_intensity_delta < applied_thresh * 1.05:
                label = "Low confidence"
                reason = "Borderline pixel area or situated near image registration boundary."
            elif circularity >= 0.55 and (0.7 <= aspect_ratio <= 1.4) and area >= 30:
                label = "Possible crater-like change"
                reason = f"High circularity ({circularity:.2f}) and balanced aspect ratio ({aspect_ratio:.2f}) resembling lunar impact crater geometry."
            elif aspect_ratio > 2.8 or aspect_ratio < 0.35 or circularity < 0.28:
                label = "Possible illumination artifact"
                reason = f"Elongated morphology (aspect ratio {aspect_ratio:.2f}) or low circularity ({circularity:.2f}) characteristic of shifting solar elevation shadows."
            else:
                label = "Potential surface change"
                reason = f"Significant localized reflectance delta ({mean_intensity_delta:.1f}) with moderate geometric regularity."

            region_data = {
                "region_id": region_idx,
                "bounding_box": {
                    "x": int(x),
                    "y": int(y),
                    "width": int(rw),
                    "height": int(rh)
                },
                "area_pixels": int(area),
                "circularity": round(float(circularity), 3),
                "aspect_ratio": round(float(aspect_ratio), 3),
                "mean_delta": round(float(mean_intensity_delta), 2),
                "label": label,
                "heuristic_explanation": reason,
                "scientific_status": "Unconfirmed automated detection candidate"
            }
            detected_regions.append(region_data)

            # Draw labeled bounding box on annotated visualization
            box_color = category_colors.get(label, (0, 255, 0))
            cv2.rectangle(annotated_img, (x, y), (x + rw, y + rh), box_color, 2)

            # Draw tag background and label text
            tag_text = f"#{region_idx} {label.split()[0]}"
            (tw, th), _ = cv2.getTextSize(tag_text, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
            cv2.rectangle(
                annotated_img,
                (x, max(0, y - th - 6)),
                (x + tw + 6, max(th + 6, y)),
                box_color,
                -1
            )
            cv2.putText(
                annotated_img,
                tag_text,
                (x + 3, max(th, y - 4)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                (0, 0, 0),
                1,
                cv2.LINE_AA
            )

            region_idx += 1

        # Sort detected regions by area (descending)
        detected_regions.sort(key=lambda r: r["area_pixels"], reverse=True)

        return {
            "mean_ssim": round(float(score_ssim), 4),
            "change_mask": clean_mask,
            "difference_map": blended_diff,
            "heatmap_image": heatmap_overlay,
            "annotated_image": annotated_img,
            "detected_regions": detected_regions,
            "total_regions_found": len(detected_regions),
            "disclaimer": (
                "Notice: Detected candidate regions are generated via automated computer vision heuristics. "
                "These labels indicate visual morphological characteristics and do not represent scientifically confirmed planetary surface events."
            )
        }
