# LUNARVISION — FINAL DETAILED PROJECT REPORT

## 1. Title Page

**Project Title:** LunarVision  
**SIH Problem Statement:** PS 26166  
**Problem Statement Title:** Multi-modal, Sun angle and scale invariant image correspondence using Chandrayaan-2 optical images (OHRC, TMC, and IIRS).  
**Project Objective:** To develop a robust classical computer vision pipeline and interactive web application capable of identifying, verifying, and aligning lunar surface images across different resolutions, sensors, and solar illumination angles natively using scientific PDS `.IMG` formats.  
**Technology Domain:** Space Technology / Computer Vision  
**Project Type:** Software / Web Application  
**Implementation Status:** Core pipeline and functionality successfully implemented and verified. 

---

## 2. Executive Summary

**LunarVision** is an advanced, web-based planetary surface analysis system. Its primary purpose is to solve the complex mathematical and visual problem of **lunar image correspondence** — determining whether two different orbital images of the Moon actually portray the same geographical footprint, and subsequently aligning them into a unified coordinate space.

This correspondence is exceptionally difficult because lunar images from missions like Chandrayaan-2 are taken by different sensors (OHRC, TMC, IIRS), at drastically different resolutions (scales), from different orbital trajectories (rotations), and under varying solar illumination angles. Because the Moon lacks an atmosphere, changes in sun angle cast radically different, harsh shadows, making the same crater look like a completely different topological feature depending on the time of the lunar day.

LunarVision resolves this by completely bypassing modern deep learning in favor of a deterministic, mathematically verifiable **Classical Computer Vision (CV)** pipeline. It leverages Scale-Invariant Feature Transform (SIFT) algorithms to identify structural keypoints (like crater rims) that remain mathematically consistent across scales and rotations. The system processes raw scientific Planetary Data System (PDS) `.IMG` files directly, applies Contrast Limited Adaptive Histogram Equalization (CLAHE) to mitigate harsh illumination disparities, matches invariant features using K-Nearest Neighbors (KNN), and validates the geometric relationship using RANSAC homography. The main output is a quantitatively verified matching decision, an aligned image projection, and statistical confidence metrics.

---

## 3. Abstract

The accurate coregistration of multimodal planetary imagery is a critical prerequisite for topographical analysis, temporal change detection, and lunar landing site characterization. We present **LunarVision**, an end-to-end web-based architecture designed to achieve multi-modal, scale-invariant, and sun-angle robust image correspondence for Chandrayaan-2 optical sensors (OHRC, TMC, and IIRS). Because lunar terrain appearance is highly dependent on solar elevation—producing severe shadowing artifacts—conventional pixel-intensity matching methodologies frequently fail. LunarVision employs a classical computer vision pipeline leveraging Contrast Limited Adaptive Histogram Equalization (CLAHE) coupled with Scale-Invariant Feature Transform (SIFT) descriptors and rigorous RANSAC-based geometric validation. Furthermore, the system includes native parsing for raw Planetary Data System (PDS) binary `.IMG` arrays, bypassing the need for intermediary data conversions. Implemented via a FastAPI backend and a React frontend, the resulting application successfully outputs aligned projections, structural similarity (SSIM) metrics, and temporal change heatmaps.

---

## 4. Introduction

Lunar remote sensing produces vast repositories of surface imagery, vital for scientific exploration, mineralogical mapping, and future landing mission planning. The Chandrayaan-2 mission orbiters are equipped with multiple optical sensors, notably the Orbiter High Resolution Camera (OHRC) capturing sub-meter resolution (0.25m), the Terrain Mapping Camera (TMC-2) capturing 5m resolution stereoscopic data, and the Imaging InfraRed Spectrometer (IIRS) capturing hyperspectral data. 

**Image correspondence** across these multimodal datasets is challenging due to:
*   **Scale differences:** Comparing a 0.25m/px OHRC image with a 5m/px TMC image requires bridging a 20x resolution gap.
*   **Rotation differences:** Spacecraft attitude and orbital pass direction result in images with varying rotational alignments.
*   **Illumination / Sun-angle differences:** The absence of atmospheric scattering on the Moon means shadows are pitch black. A crater illuminated from the East looks completely different from the same crater illuminated from the West. 
*   **Sensor / Modality differences:** Different sensors capture different wavelengths (visible vs. infrared) and possess distinct radiometric profiles.

Consequently, conventional template matching or pixel-wise correlation techniques fail. A feature-based invariant approach is strictly required.

---

## 5. Problem Statement

**SIH Problem Statement:** PS 26166  
**Interpretation:** The system must algorithmically process two distinct lunar images—potentially from different Chandrayaan-2 instruments, taken at different times (sun angles), and at different altitudes (scales)—and confidently align them if they represent the same surface footprint.

**Technical Challenges:**
*   Parsing raw scientific binary formats natively without crashing standard web servers.
*   Extracting mathematical features that survive severe illumination shifts.
*   Filtering out thousands of false-positive matches algorithmically.
*   Providing a mathematically sound verification that an alignment is not a false positive (hallucination).

**Expected System Behavior:** 
*   **Input:** Two image files (Standard PNG/JPG or raw ISRO PDS `.IMG`).
*   **Output:** A decision on whether they correspond (Same Location / No Reliable Match), quantitative metrics (RMSE, Inlier Ratio, Confidence Score), and visual artifacts (aligned image, feature match overlays, blended overlaps).

---

## 6. Motivation

This project serves as a crucial tool for:
*   **Lunar Mapping:** Merging high-resolution localized images into broader global basemaps.
*   **Planetary Science:** Allowing geologists to correlate topographical (TMC) and mineralogical (IIRS) data with high-resolution visual morphology (OHRC).
*   **Change Analysis:** Detecting new impact craters, rockfalls, or lander hardware by aligning historical and recent imagery.
*   **Scientific Image Processing:** Providing a user-friendly interface that handles complex `.IMG` byte-parsing, democratizing access to raw ISRO/NASA planetary data without requiring users to write Python scripts.

---

## 7. Objectives

**Primary Objectives:**
1. Parse and decode raw binary PDS image formats.
2. Implement a scale- and rotation-invariant feature detection pipeline.
3. Quantify correspondence via RANSAC homography and reprojection error limits.
4. Present a web-based dashboard for interactive geometric registration.

**Secondary Objectives:**
1. Extract solar elevation/incidence angles from embedded image metadata.
2. Perform temporal change detection on aligned images using structural similarity (SSIM) differencing and Otsu thresholding.
3. Simulate sun-angle variations for batch robustness testing.
4. Visualize geographical footprints using PDS latitude/longitude bounding boxes.

---

## 8. Existing Problem / Limitations

Conventional manual comparison is impossible given the petabytes of orbital data available. Existing automated approaches suffer from:
*   **Illumination Variance:** Direct pixel correlation (e.g., Mean Squared Error) fails completely when shadow directions change.
*   **Raw PDS Formats:** Standard web backends cannot process 16-bit, 32-bit, or unheadered binary `.IMG` arrays out-of-the-box.
*   **Noise and Contrast:** Orbital images suffer from sensor noise, cosmic ray hits, and washed-out contrast ranges that confuse naive detectors.

LunarVision explicitly avoids Deep Learning models because classical CV (SIFT) provides deterministic, mathematically verifiable geometric correspondence without requiring thousands of labeled, multimodal lunar image pairs for training.

---

## 9. Proposed Solution

LunarVision automates alignment via an 8-step deterministic Computer Vision workflow.

**High-Level Workflow:**
1. **Input Images** → User uploads Source and Reference images.
2. **Scientific Data Parsing** → Checks for PDS headers; if found, reads bits/pixel, dimensions, and raw bytes.
3. **Image Decoding** → Converts raw arrays to grayscale NumPy matrices, scaling down massive inputs safely (capped at 4096px).
4. **Preprocessing** → Applies percentile normalization (0.5th to 99.5th) and CLAHE to equalize contrast and expose crater rims hidden in shadows.
5. **Feature Detection** → Extracts SIFT descriptors (inherently scale and rotation invariant). AKAZE is implemented as an algorithmic fallback. *(Implemented and verified)*
6. **Feature Matching** → Uses Brute-Force KNN matching to find descriptor pairs.
7. **Ratio Test** → Applies Lowe’s Ratio test (0.75 threshold) to reject ambiguous feature matches.
8. **Geometric Verification** → Computes Homography via RANSAC with a strict 3.5px reprojection threshold. Requires ≥4 inliers and non-degenerate matrix determinants. *(Implemented and verified)*
9. **Image Alignment** → Warps the source image into the reference coordinate space.
10. **Metrics** → Calculates RMSE over the overlap area, and Structural Similarity (SSIM).
11. **Same-Location Decision** → Fuses metrics into a Confidence Score (0-1.0). Rejects pairs scoring < 20%.
12. **Visualization / Result** → Returns aligned images, inlier match plots, and 50/50 alpha-blended overlays to the frontend.

---

## 10. SYSTEM REQUIREMENTS

### Hardware Requirements
*   **Server/Processing:** Multi-core CPU (2.0 GHz+), minimum 2GB RAM (4GB+ recommended for large `.IMG` files). No GPU is required as classical CV operations run efficiently on CPU.
*   **Client:** Standard modern web browser (Chrome, Edge, Firefox, Safari).

### Software Requirements (Based on verified codebase configuration)
*   **Programming Languages:** Python 3.11.8 (Backend), JavaScript/JSX (Frontend)
*   **Frontend Framework:** React 18.2.0, Vite 5.2.0
*   **Backend Framework:** FastAPI 0.110.0, Uvicorn 0.28.0
*   **Computer Vision Libraries:** OpenCV (opencv-python-headless 4.13.0.92), scikit-image 0.22.0
*   **Math/Data Libraries:** NumPy 1.26.4
*   **Image Processing Fallback:** Pillow 10.2.0

---

## 11. DETAILED TABLES

### Table 1: Technology Stack

| Technology | Version | Purpose in LunarVision | Location in Code |
| :--- | :--- | :--- | :--- |
| **React** | 18.2.0 | Core UI framework for the SPA and component state. | `frontend/src/` |
| **Vite** | 5.2.0 | Fast build tool and development server. | `frontend/vite.config.js` |
| **Tailwind CSS** | 3.4.3 | Utility-first CSS for styling the space-themed UI. | `frontend/tailwind.config.js` |
| **FastAPI** | 0.110.0 | Asynchronous Python web framework serving the REST API. | `backend/main.py` |
| **Python** | 3.11.8 | Backend execution runtime environment. | `backend/` |
| **OpenCV** | 4.13.0.92 | Heavy-lifting Computer Vision engine (SIFT, RANSAC, Warping). | `backend/services/` |
| **NumPy** | 1.26.4 | Multi-dimensional array operations, fundamental for PDS binary decoding. | `backend/services/preprocessing.py` |
| **scikit-image** | 0.22.0 | robust Structural Similarity Index Measure (SSIM) metric calculation. | `backend/services/metrics.py` |
| **ExifReader** | 4.45.1 | Client-side extraction of GPS coordinates from JPEGs. | `frontend/src/utils/geoMetadata.js` |

### Table 2: Complete Folder / File Structure

| File / Folder | Purpose |
| :--- | :--- |
| `backend/main.py` | FastAPI application entry; configures CORS, mounts `/uploads` and `/outputs`, includes routers. |
| `backend/routers/image_routes.py` | Routing file containing endpoints: `/register`, `/multi-sensor-register`, `/change-detection`. |
| `backend/services/preprocessing.py` | Image loading (PNG/JPG/PDS .IMG), percentile normalization, grayscale, CLAHE, downsizing. |
| `backend/services/feature_detection.py` | SIFT/AKAZE instantiation and execution on enhanced matrices. |
| `backend/services/matching.py` | BFMatcher, KNN, Lowe's Ratio Test implementation. |
| `backend/services/registration.py` | RANSAC homography calculation, matrix determinant validation, perspective warping. |
| `backend/services/metrics.py` | RMSE over valid mask overlap, SSIM calculation, weighted confidence score formulation. |
| `backend/services/change_detection.py` | Post-registration pipeline: SSIM difference maps, AbsDiff, Otsu thresholding, contour finding. |
| `backend/services/sun_angle_service.py` | Extracts metadata, synthesizes batch illumination tests via Sobel shading. |
| `frontend/src/App.jsx` | Root layout, manages tab routing and overall application wrapper. |
| `frontend/src/context/PipelineContext.jsx` | Global state context storing `activeTab`, `registrationResult`, and uploaded images. |
| `frontend/src/utils/pdsMetadata.js` | Parses PDS textual labels for geospatial coordinates (`MINIMUM_LATITUDE`, etc.). |
| `frontend/src/pages/RegistrationPage.jsx` | UI for pairwise geometric registration. |
| `frontend/src/pages/ChangeDetectionPage.jsx` | UI for temporal change detection heatmap visualization. |
| `frontend/src/components/FootprintMap.jsx` | SVG mapping component to visualize overlapping planetary footprints via IoU. |

### Table 3: API Endpoints

| Endpoint | Method | Purpose | Key Inputs | Outputs |
| :--- | :--- | :--- | :--- | :--- |
| `/api/images/register` | POST | Core geometric alignment | `source_image`, `reference_image`, `preferred_detector` | JSON metrics + `artifacts` (URLs to aligned images, matches) |
| `/api/images/multi-sensor-register` | POST | Pairwise multi-sensor match | `hub_image`, `sensor_a_image`, `sensor_b_image` | JSON containing `pairwise_results` array for Hub↔A and Hub↔B |
| `/api/images/change-detection` | POST | Identify surface alterations | `source_image`, `reference_image` | JSON with `detected_regions` array + heatmap image URLs |
| `/api/images/sun-angle-robustness` | POST | Read metadata & run pair | `source_image`, `reference_image` | JSON with `sun_angle_difference` and metrics |
| `/api/images/sun-angle-batch` | POST | Synthetic robustness test | `baseline_image`, `pair_count` | Array of JSON metrics charting performance decay across angles |

### Table 4: Major Algorithms Explained

| Algorithm | Role in Project | Why Used Instead of Alternatives |
| :--- | :--- | :--- |
| **CLAHE** | Local contrast enhancement | Standard Histogram Equalization washes out image data; CLAHE prevents noise over-amplification in pitch-black shadows. |
| **SIFT** | Feature extraction | Deep learning requires labeled multimodal training sets. SIFT mathematically guarantees scale and rotation invariance without training. |
| **AKAZE** | Fallback feature extraction | Faster binary descriptors used if SIFT fails to find minimum keypoints. |
| **KNN (k=2)** | Feature matching | Required to execute Lowe's ratio test by comparing the nearest match to the second-nearest match. |
| **RANSAC** | Geometric verification | Deterministically eliminates false-positive keypoint matches (outliers) that do not fit a planar perspective transformation. |
| **SSIM** | Dissimilarity/Change measurement | Standard Absolute Difference highlights tiny illumination shifts. SSIM measures structural integrity, making it robust against minor lighting differences. |
| **Otsu's Binarization** | Change mask generation | Dynamically finds the optimal threshold to separate "background lunar terrain" from "changed pixels" without hardcoding values. |

### Table 5: Actual Algorithm Parameters (Verified in Code)

| Parameter | Value | Location in Code | Purpose |
| :--- | :--- | :--- | :--- |
| **CLAHE Clip Limit** | `2.0` | `preprocessing.py`, `change_detection.py` | Prevents over-amplification of noise in shadowed regions. |
| **CLAHE Grid Size** | `(8, 8)` | `preprocessing.py`, `change_detection.py` | Defines the local neighborhood for histogram equalization. |
| **Image Max Dimension** | `4096px` | `preprocessing.py` | Downscales massive PDS images (`cv2.INTER_AREA`) to prevent RAM exhaustion. |
| **SIFT Minimum Keypoints** | `12` (or 15) | `feature_detection.py` | Fails early or falls back to AKAZE if the image has insufficient structural data. |
| **Lowe Ratio Threshold** | SIFT: `0.75`<br>AKAZE: `0.80` | `matching.py` | Drops matches where the 1st closest neighbor isn't significantly closer than the 2nd. |
| **RANSAC Reproj. Threshold** | `3.5` pixels | `registration.py` | Maximum distance a reprojected point can be from its target to be considered an Inlier. |
| **Minimum RANSAC Inliers** | `4` | `registration.py` | Absolute mathematical minimum points required to compute a valid Homography matrix. |
| **Homography Determinant Bounds** | `[1e-4, 1e4]` | `registration.py` | Rejects degenerate matrices (e.g., lines folding into a single point). |
| **Confidence Cutoff** | `< 0.20` | `image_routes.py` | A final score below 20% triggers a "No Reliable Match" rejection. |

### Table 6: Test Cases & Coverage

| Test Area | File | Verified Focus |
| :--- | :--- | :--- |
| **API Health** | `test_api_endpoints.py` | Server boot, CORS setup, output directory mounting. |
| **CV Registration** | `test_backend_cv.py` | SIFT descriptor count, BFMatcher validity, warp outputs. |
| **Change Detection** | `test_full_integration.py` | Detection of crater anomalies, bounding box validity, heatmap generation. |
| **Rejection Handling** | `test_full_integration.py` | Feeding completely unrelated lunar terrain to ensure RANSAC safely rejects (`no_match`). |
| **PDS Parsing** | `preprocessing.py` (internal logic) | Reading 16-bit headers, slicing bytes, clipping to percentiles. |

### Table 7: Test Results (From `test_full_integration.py`)

| Test Execution | Input Data | Status | Observed Output |
| :--- | :--- | :--- | :--- |
| **STEP 2: Image Registration** | `02_temporal_rotated_shifted.png` vs `01_baseline_pre_event.png` | **PASSED** | RANSAC found ≥ 10 inliers; Confidence ≥ 70%; `aligned_image` URL served successfully. |
| **STEP 3: No Match Rejection** | `04_unrelated_lunar_terrain.png` vs `01_baseline.png` | **PASSED** | System successfully avoided false-positive hallucination. Returned `status="no_match"`. |
| **STEP 4: Temporal Change** | `03_temporal_new_impact_crater.png` vs `01_baseline.png` | **PASSED** | Correctly segmented new impact crater; validated circularity and area metrics. |
| **STEP 5: Multi-Sensor Pairwise** | `01_baseline` (Hub), `02_temporal` (TMC), `03_temporal` (IIRS) | **PASSED** | Processed Hub↔TMC and Hub↔IIRS independently returning dual metrics. |
| **STEP 6: Invalid File Handling** | `b"not an image file data"` bytes | **PASSED** | OpenCV safely failed decode, returning `no_match` with error details rather than crashing server 500. |

### Table 8: Feature Implementation Status

| Feature | Codebase Status | Data Source |
| :--- | :--- | :--- |
| Geometric Coregistration | **Implemented & Verified** | PNG/JPG + Binary `.IMG` |
| Raw PDS File Decoding | **Implemented & Verified** | Native Python parsing |
| Temporal Change Detection | **Implemented & Verified** | Synthetic image sets |
| Geospatial Footprint Overlap (IoU) | **Implemented & Verified** | PDS label coordinates |
| Real Chandrayaan-2 Multi-Sensor Validation | *Partially Implemented* | Algorithms active; missing real overlapping sensor test data. |
| Sun-Angle Robustness Benchmark | *Partially Implemented* | Uses synthetically shaded variants (Lambertian) rather than real multi-time imagery. |

### Table 9: Error Handling Mechanisms

| Scenario | System Reaction | User Interface Result |
| :--- | :--- | :--- |
| Insufficient keypoints (< 6) | `feature_detection.py` throws fallback; if still fails, router returns `no_match`. | Displays "No Match" UI with detected keypoint counts. |
| RANSAC computes impossible warp | Determinant check `det < 1e-4` flags failure. | Displays "No Match: Degenerate Matrix". |
| File uploaded is not an image | OpenCV returns `None`, PIL fallback fails. | Displays "No Match: Image preprocessing failed". |
| Confidence score is 15% | Registration completes, but final validator triggers rejection. | Displays "No Match: Below reliability threshold (20%)". |
| Network disconnect | `PipelineContext` polling fails. | Top navigation turns amber "Connecting...". |

### Table 10: Input/Output Formats

| Module | Input Format | Internal Format | Output Format (to UI) |
| :--- | :--- | :--- | :--- |
| **PDS Parser** | Binary bytes (`application/octet-stream`) | `np.ndarray` (float32/uint16) | `image/png` saved to disk |
| **Registration API** | `multipart/form-data` | 128D SIFT float descriptors | JSON object with metric floats |
| **Artifact Generation** | `np.ndarray` | `cv2.addWeighted` combinations | Static URL (`/outputs/...png`) |

---

## 12. COMPLETE PROJECT ARCHITECTURE

### Overall System Architecture

![Mermaid Diagram](https://kroki.io/mermaid/svg/eNp1Uttu4jAQfecr5gfY_kC1ksmGbXYJjTD0Ya1VNRsGsGriyDaFSvn4-pI2oWLzYI8zx2eOZ85O6XN9QONgPZuA_-zp395ge4BMSWociLRPudwSzIw-WzJ_IzJ8K8LabQoRd-AVg00xZLlDR6KSLSnZUKYbRxc3pNlFaiviCktyZ21eYIFvN_jhfjr9nuiuyVMiUsQENdvJ9TM4mVcyIOZoHasKmGH94lEjFVXxvNInR0YUR9wTpIMdEJtWadw-l3sjUgglNh5prl8qa5E2mEtFfeFbdSBoHkj_IzzThvJm7xsXZoDWyhoVZE-Qfg7EFRo_E1H94Hf5Re7685DPFuwhF3H1dw_Y1HT0Ex2JL-ZrERa4A_ab_clH_WdLzjKRNnjQRx3FvQ2IkpyRtRWcF6W_vyp5Dhmq-qTQ6ZGKG92MfUhqY5gkxkkHMSHoC4ewL_TZrU_SZCAP6apHvobypJxsvaO7UcsnI6mR7UvqejjdL_649N6zrW4sdSN_ffgxgH7ma2DGyV2w_ma16HoXTIbGwfSbB3J8JYjesh-Yd-1nAoM=)

### End-to-End Data Flow

![Mermaid Diagram](https://kroki.io/mermaid/svg/eNqFUsFuGjEQvecr5lRtVEKjtElVDkjLblCoEkAs9FpN7AGs7NquPQuhVf69NoFQsVXwceY9vzczz9OvmrSgXOHCYXUG4Vl0rISyqBlmnlyj2HdGM2nZaPRQPP2vnv0YK0ul0tRo5co_nW2rUeqi291_3oGZLQ1KKJyADzChOQwqXJDfgveoQNiJdmA8KqbwydFCeSYHSVWXrKIWPG6Y_PmWuEMH3sFUB3oBAJ4d7VZw6B0BcxJGUvCTm7X2AkuCpPvl8tuNfT5_n5ndp3e3MDSuwlL9RlZGv08oBv0pSGISnGqZmcrWTMkJlV7_AVksw_gf4d6sCSZRCabkGZLL9tfrE3yxumrPlZZ3pjIhEHa5gWSSDos0a8Hn9vXJKSN_jc6OyXkbnKsVNQnx5mE-XBGkpVpokmGhoxW5Eje-CX878IS4dhoeiJ0SHqQSfHTTQ3i-F6Mh_PGMXPsWVK-UFsTkzVHwz9qV_uU4Sv9mT2KIxN5FFuvPfIyPke3ECNvgHGYDyNEvHw066cNEr3H9C6mxG4I=)

---

## 13. ALGORITHM DEEP DIVES & MATHEMATICAL EXPLANATIONS

### 13.1 PDS Scientific Image Decoding & Preprocessing

**What it is:** The process of converting NASA/ISRO Planetary Data System `.IMG` binary payloads into usable matrix arrays.
**Why LunarVision uses it:** Web browsers and standard libraries cannot render 16-bit MSB scientific arrays natively.
**How it works (Processing Steps):**
1. System reads the first 64 KB of the file hunting for textual labels like `RECORD_BYTES = 512`.
2. Extracts image dimensions (`LINES`, `LINE_SAMPLES`) and bit depth (`SAMPLE_BITS`).
3. Uses `numpy.frombuffer` to ingest the remaining payload based on the offset.
**Actual Parameters:** Checks for `MSB_INTEGER` (>i2) or `LSB_INTEGER` (<i2).
**Percentile Normalization:**
*   **Math:** Sets minimum mapping value to `P_0.5` and maximum to `P_99.5`.
*   **Advantage:** Prevents single extreme cosmic ray pixels (value 65535) from turning the entire rest of the image pitch black when min-max scaling to 8-bit.

### 13.2 CLAHE (Contrast Limited Adaptive Histogram Equalization)

**What it is:** An image enhancement algorithm that equalizes contrast locally in patches rather than globally.
**Why LunarVision uses it:** Lunar images have pitch black shadows and blinding highlights. Global equalization ruins the image. CLAHE highlights crater rims hidden *inside* dark shadows.
**Actual Parameters:** `clipLimit=2.0`, `tileGridSize=(8,8)`
**Advantage:** Massively increases SIFT keypoint detection in regions with uneven illumination.

### 13.3 SIFT (Scale-Invariant Feature Transform)

**What it is:** A classical computer vision algorithm to detect and describe local features in images.
**How it works:**
1. Generates a Difference of Gaussians (DoG) pyramid to find extrema across varying scales.
2. Assigns orientations to keypoints based on local image gradient directions (making it rotation invariant).
3. Computes a 128-dimensional vector descriptor for each point.
**Input:** CLAHE-enhanced grayscale image.
**Output:** Array of 128-float vectors.
**Advantages:** Mathematically sound, highly robust to scale and rotation. No training data required.
**Limitations:** Computationally expensive; struggles with identical repetitive patterns.

### 13.4 Feature Matching (BFMatcher & Lowe's Ratio Test)

**What it is:** Finding which SIFT descriptor in Image A matches Image B.
**How it works:** Uses Brute Force (L2 Norm distance). Computes K-Nearest Neighbors (`k=2`).
**Lowe's Ratio Test Math:** 
If `Distance(Nearest_Neighbor) < 0.75 * Distance(Second_Nearest_Neighbor)` → ACCEPT.
**Why:** It ensures the match is uniquely distinct. If two matches are equally close, the feature is likely an ambiguous repetitive pattern (like generic regolith dots).

### 13.5 Geometric Verification (RANSAC Homography)

**What it is:** Random Sample Consensus. Used to find a 3x3 perspective transformation matrix while mathematically ignoring false matches (outliers).
**Processing Steps:**
1. Randomly picks 4 point correspondences.
2. Calculates a hypothetical homography matrix `H`.
3. Reprojects *all* points using `H`.
4. Counts how many reprojected points fall within `3.5 pixels` of their actual target location (Inliers).
5. Repeats iteratively to find the `H` with the maximum inliers.
**Actual Parameters:** `ransac_reproj_thresh=3.5`, `min_inliers=4`.
**Determinant Check:** Calculates `det = np.linalg.det(H[:2,:2])`. If `det < 1e-4` or `det > 1e4`, the matrix is degenerate (e.g. collapsed into a line) and is rejected.

### 13.6 Metrics & Confidence Score Formulation

**What it is:** A custom weighted heuristic to output a single human-readable confidence percentage.
**Mathematical Formulation:**
```python
match_score  = min(1.0, inlier_count / 40.0)        # 40% weight
ratio_score  = min(1.0, inlier_ratio)               # 35% weight
rmse_score   = max(0.0, min(1.0, 1.0 - (rmse / 60.0))) # 25% weight
confidence   = (match_score * 0.40) + (ratio_score * 0.35) + (rmse_score * 0.25)
```
**Same-Location Logic:** If `confidence < 0.20` (20%), the system formally rejects the correspondence as a hallucination/false positive.

### 13.7 Temporal Change Detection (SSIM & Otsu)

**What it is:** Finding what changed (e.g., a new crater) between two aligned images.
**Processing Steps:**
1. Calculates SSIM difference map and Absolute pixel difference map.
2. Blends them 50/50.
3. Applies **Otsu's Thresholding**, which dynamically calculates the mathematical variance of pixel intensities to find the perfect separation threshold between "background" and "foreground change".
4. Applies Morphological Opening (3x3 kernel) to delete tiny noise dots.
5. Applies Morphological Closing (5x5 kernel) to bridge gaps in detected crater rims.
6. Highlights contours and generates a JET heatmap.

---

## 14. A. COMPLETE END-TO-END EXPLANATION

**From Upload to Result:**
When a user drags two images into the `RegistrationPage.jsx` UI and clicks "Start", the React frontend packages the files into a `multipart/form-data` payload and uses Axios to send a POST request to `/api/images/register`. 

The FastAPI backend receives the raw byte streams into memory. It routes them to `preprocessing.py`, which checks the first 512 bytes for PDS headers. If standard, it decodes them using OpenCV. It forces the arrays to grayscale, limits max bounds to 4096 pixels, applies percentile clipping, and runs CLAHE to equalize shadows.

These matrices are handed to `feature_detection.py` where `cv2.SIFT_create()` extracts thousands of 128D descriptors. `matching.py` pairs them using BFMatcher and filters them via Lowe's Ratio Test (0.75). The surviving coordinate pairs are sent to `registration.py`. Here, RANSAC randomly samples sets of 4 points to compute a Homography matrix, filtering out points that don't fit the geometry (reprojection error > 3.5px). 

If the matrix is mathematically valid, `cv2.warpPerspective` bends the source image to align with the reference image. `metrics.py` calculates the RMSE on overlapping pixels and the SSIM score, mixing them into a Confidence Score. Finally, visual artifacts (overlays, keypoint lines) are drawn and saved to the `/outputs/` static folder. The API returns a JSON object containing the numeric scores and image URLs, which React renders in the dashboard UI.

---

## 15. B. DETAILED TECHNICAL EXAMPLE

**Scenario: User uploads `02_temporal_rotated_shifted.png` (Source) and `01_baseline_pre_event.png` (Reference).**

1. **Upload & Preprocess:** Both images decoded successfully.
2. **SIFT Detection:** System detects ~3500 keypoints in Source and ~4100 in Reference.
3. **Matching:** BFMatcher evaluates candidates. Lowe's Ratio Test rejects ambiguous dots. ~250 "good matches" survive.
4. **RANSAC:** Runs against the 250 matches. Finds a geometric consensus. It classifies 180 as Inliers (they fit the 3x3 perspective warp within 3.5px) and 70 as Outliers.
5. **Metric Calculation:** 
   - `inlier_count` = 180
   - `inlier_ratio` = 180 / 250 = 0.72 (72%)
   - `rmse` = 12.4 pixels (calculated only on intersecting area)
6. **Confidence Math:**
   - Match Score = `min(1.0, 180/40)` = 1.0 * 0.40 = 0.40
   - Ratio Score = 0.72 * 0.35 = 0.252
   - RMSE Score = `1.0 - (12.4/60)` = 0.79 * 0.25 = 0.198
   - Total Confidence = `0.40 + 0.252 + 0.198 = 0.85` (85%)
7. **Decision:** 85% is ≥ 20%. **Status: Success.**
8. **UI Display:** React shows the 50/50 blended slider and a green "85% Confidence" badge.

---

## 16. C. JUDGE EXPLANATION (PITCHES)

### 30 Seconds
"LunarVision solves the problem of aligning lunar images taken by different Chandrayaan-2 sensors under different lighting conditions. Instead of deep learning, we use a classical computer vision pipeline built with Python and OpenCV. It extracts scale-invariant features like crater rims, matches them, and uses RANSAC to geometrically align the images. It natively parses raw scientific PDS files and provides a web dashboard for scientists to visualize the correspondence and detect temporal changes."

### 1 Minute
"Welcome to LunarVision. When tracking changes on the Moon, a 0.25m OHRC image looks totally different from a 5m TMC image, especially if the sun angle has changed, casting shadows in opposite directions. Pixel-matching fails here. Our solution is a web application that takes raw binary PDS images, applies adaptive histogram equalization to reveal shadowed features, and runs the SIFT algorithm to extract mathematically invariant keypoints. We filter false matches using Lowe's Ratio test and compute a perspective homography matrix using RANSAC. The result is a mathematically verified alignment, proving correspondence across multimodal sensors without requiring massive machine learning datasets."

### 3 Minutes
*(Expand the 1-minute pitch by detailing the architecture.)*
"Architecturally, we use a React frontend and a FastAPI backend. The critical challenge was handling raw NASA/ISRO `.IMG` data. Most web servers crash on 16-bit unheadered matrices. We wrote a custom parser that reads the PDS headers, decodes the bit-depth, normalizes extreme cosmic-ray outliers using percentile clipping, and safely downscales massive images. Once aligned, we also built a Temporal Change Detection module. It takes the aligned images, computes a Structural Similarity (SSIM) difference map, and uses Otsu's binarization to automatically highlight new impact craters or landslides. Our backend evaluates every pair and assigns a strict 0-100% confidence score, rejecting hallucinations if the score drops below 20%."

### 5 Minutes
*(Expand the 3-minute pitch by doing a live walkthrough of the UI tabs.)*
"Let me walk you through the system. On the Registration tab, we upload our pairs. Notice the instantaneous feedback on RMSE and Inlier counts. In the Multi-Sensor tab, we simulate the exact SIH problem statement: cross-registering an OHRC hub against TMC and IIRS simultaneously. Notice that the algorithm doesn't care about the sensor type; because SIFT is scale-invariant, it finds the macro-structures in TMC that match the micro-structures in OHRC. Finally, in our Sun-Angle robustness tab, we extract the actual `SOLAR_ELEVATION` from the PDS metadata to calculate the illumination delta. We even built a synthetic batch-benchmark script that loops through 0 to 85 degrees of simulated solar shading, charting exactly where the SIFT descriptors begin to fail."

---

## 17. D. VIVA PREPARATION (50 TECHNICAL QUESTIONS)

1. **Why not use Deep Learning / CNNs?** CNNs require massive sets of labeled, co-registered multimodal training data which are scarce for lunar terrain. SIFT provides deterministic mathematical invariance.
2. **What does SIFT stand for?** Scale-Invariant Feature Transform.
3. **How does SIFT achieve scale invariance?** By constructing a Difference of Gaussians (DoG) pyramid and searching for local extrema across different scales.
4. **How does SIFT achieve rotation invariance?** By assigning an orientation to each keypoint based on local image gradient directions.
5. **What is CLAHE?** Contrast Limited Adaptive Histogram Equalization.
6. **Why use CLAHE instead of standard Histogram Equalization?** Standard HE amplifies noise in pitch-black lunar shadows. CLAHE limits this via the `clipLimit` parameter.
7. **What is a PDS file?** Planetary Data System file, the standard format for NASA/ISRO space mission data.
8. **How do you parse a `.IMG` file?** We read the first 64KB as ASCII, use regex to find `LINES` and `SAMPLE_BITS`, calculate offsets, and use `numpy.frombuffer`.
9. **What is RANSAC?** Random Sample Consensus.
10. **Why is RANSAC necessary?** BFMatcher finds thousands of matches, many of which are false. RANSAC ignores these "outliers" by finding the core group of points that agree on a single geometric plane.
11. **What is Homography?** A 3x3 transformation matrix that maps points from one plane to another.
12. **How many points are needed to compute Homography?** A minimum of 4 points.
13. **What is Lowe's Ratio Test?** It rejects a match if the distance to the closest neighbor isn't at least 25% closer (ratio 0.75) than the second closest.
14. **What does it prevent?** It prevents matching against repetitive, ambiguous patterns like a field of generic dots.
15. **What is RMSE?** Root Mean Square Error. It measures pixel-intensity differences.
16. **Is RMSE a good metric for different sun angles?** No. Pixel values invert when shadows flip. We use it only as a secondary metric for perfectly aligned identical-modality images.
17. **What is SSIM?** Structural Similarity Index Measure. It compares contrast, luminance, and structure rather than raw pixels.
18. **Why fallback to AKAZE?** AKAZE uses binary descriptors which are faster to compute. If SIFT fails on a washed-out image, AKAZE provides a secondary attempt.
19. **What is Otsu's Thresholding?** An algorithm that automatically calculates the optimal threshold to separate foreground from background based on variance.
20. **Why use Otsu in change detection?** So we don't have to hardcode a difference threshold, allowing it to adapt to different image lighting.
21. **What are morphological operations?** Image processing based on shapes, like Opening and Closing.
22. **What does Morphological Opening do?** Removes small noise dots (erosion followed by dilation).
23. **What does Morphological Closing do?** Closes small holes or gaps inside objects (dilation followed by erosion).
24. **How do you handle images that are too large (e.g., 20,000px)?** The preprocessing script scales anything above 4096px down using `cv2.INTER_AREA` to prevent RAM crashes.
25. **What is `cv2.warpPerspective`?** The OpenCV function that applies the Homography matrix to physically bend/align the image.
26. **What is an Inlier?** A feature match that correctly aligns with the calculated Homography matrix within the 3.5px reprojection threshold.
27. **What is an Outlier?** A false match that RANSAC discards.
28. **How is the Confidence Score calculated?** It's a weighted sum: 40% from total inliers, 35% from inlier ratio, 25% from RMSE.
29. **What happens if confidence is 15%?** The backend explicitly intercepts it and returns a `no_match` JSON response to prevent false alignments.
30. **How does the system simulate sun-angle robustness in batch mode?** It uses Sobel gradients (derivatives) combined with Lambertian attenuation (cosine of the angle) to darken the image synthetically.
31. **What backend framework is used and why?** FastAPI. It's asynchronous and highly performant for Python CV payloads compared to Flask or Django.
32. **How does the frontend communicate with the backend?** React uses Axios to send `multipart/form-data` POST requests.
33. **Where are processed images stored?** Temporarily in the `/outputs` directory, served back to React as static URLs.
34. **How do you calculate spatial footprint overlap?** We parse `MINIMUM_LATITUDE` and `MAXIMUM_LONGITUDE` from both PDS files and calculate the Intersection over Union (IoU) of the two bounding boxes.
35. **What happens if a user uploads a corrupted file?** `cv2.imdecode` returns `None`. The backend safely catches this and returns a structured error JSON rather than crashing.
36. **What is the difference between OHRC and TMC?** OHRC is high resolution (0.25m) visual. TMC is lower resolution (5m) and captures stereoscopic terrain data.
37. **Can SIFT match OHRC to TMC?** Yes, because SIFT scales the images internally. A massive crater in OHRC matches a tiny crater in TMC mathematically.
38. **How does the Three-Sensor workflow operate?** It designates one image as the Hub (e.g., OHRC) and runs the entire pairwise registration pipeline twice: Hub↔TMC and Hub↔IIRS independently.
39. **Does the system preprocess TMC differently than OHRC?** No, the classical CV pipeline treats all inputs as normalized matrices, ensuring sensor-agnostic processing.
40. **What is ExifReader used for?** Extracting GPS metadata embedded in standard JPEG files on the client-side for the Footprint Map.
41. **Why use Percentile Normalization (0.5 to 99.5) instead of 0 to 100?** 0 to 100 normalization is destroyed by a single dead pixel (value 0) or cosmic ray (value 65535).
42. **What is the mathematical determinant check in Homography?** We check `np.linalg.det(H[:2,:2])`. If it's near zero, the matrix collapses space into a line (degenerate).
43. **Why use React instead of vanilla JS?** Component-based architecture allows us to reuse the `ImageUploader` and `MetricCard` across 5 different dashboard tabs seamlessly.
44. **How are cross-origin requests handled?** FastAPI's `CORSMiddleware` is configured to allow localhost and Vercel domains.
45. **What distance norm does BFMatcher use for SIFT?** `NORM_L2` (Euclidean distance) because descriptors are continuous floats.
46. **What norm for AKAZE?** `NORM_HAMMING` because AKAZE descriptors are binary strings.
47. **What is the `crossCheck` parameter in BFMatcher?** We set it to `False` because we manually implement Lowe's Ratio test instead.
48. **How does the Temporal Change UI show differences?** It uses a 50/50 alpha-blended slider and an overlaid Heatmap (JET colormap) highlighting changed pixels.
49. **Can the system run offline?** Once the React frontend loads, the PDS parsing and mapping can run in the browser, but the heavy CV tasks require the local FastAPI backend.
50. **What is the primary limitation of this system?** It requires physical structural overlap (visible features). If IIRS (infrared) shows completely different visual structures than OHRC, feature matching will fail.

---

## 18. E. LIMITATIONS

1. **Sensor Band Disconnect:** The system relies on physical structural overlap. If an IIRS image visualizes mineralogical thermal bands that share zero physical structural geometry with an OHRC visual spectrum image, SIFT will find no corresponding keypoints, and alignment will fail.
2. **Extreme Illumination Limits:** While CLAHE handles moderate shadowing, if the Sun is at 89° (grazing angle) in Image A and 0° (overhead) in Image B, the structural geometry of the shadows changes so drastically that SIFT descriptors will diverge.
3. **Flat Terrain Failure:** If images feature completely smooth mare (lunar plains) with no craters or rocks, no keypoints will be detected, failing at the minimum keypoint gate (< 12).
4. **Lack of DEM Guidance:** The current pipeline relies purely on 2D perspective warping (Homography). It does not ingest 3D Digital Elevation Models (DEM) to perform true orthorectification.
5. **No Real Chandrayaan-2 Validation Set:** The codebase's test suite heavily utilizes synthetically generated augmentations rather than strict ISRO-provided corresponding orbital pairs.

---

## 19. F. FUTURE SCOPE

*(Note: The following features are strictly planned for future iterations and are NOT currently implemented in the codebase.)*

*   **Deep Learning Descriptor Fusion (SuperPoint/SuperGlue):** Augmenting classical SIFT with neural descriptors to survive extreme 90-degree illumination shifts where classical gradients fail.
*   **3D DEM Orthorectification:** Ingesting height-map data to project images onto a 3D lunar sphere rather than assuming a flat 2D perspective plane.
*   **Automated PDS Download Pipeline:** Connecting directly to the ISRO ISSDC portal via API to pull images by geospatial bounding box automatically.
*   **Multi-Spectral Band Remapping:** Automatically translating IIRS infrared bands into pseudo-visual structures before passing them to the SIFT detector.
*   **C++ Backend Porting:** Rewriting the Python OpenCV routines in raw C++ for near-instantaneous processing on massive gigapixel strips.

---

## 20. G. FINAL VERIFICATION TABLE

| Item | Verified from Code? | Status | Evidence/Location |
| :--- | :--- | :--- | :--- |
| **SIFT/AKAZE Detection** | Yes | Implemented | `backend/services/feature_detection.py` |
| **Lowe's Ratio Test (0.75)** | Yes | Implemented | `backend/services/matching.py` (Line 42) |
| **RANSAC (3.5px thresh)** | Yes | Implemented | `backend/services/registration.py` (Line 83) |
| **CLAHE Enhancement** | Yes | Implemented | `backend/services/preprocessing.py` (Line 132) |
| **PDS `.IMG` Parsing** | Yes | Implemented | `backend/services/preprocessing.py` (Lines 29-135) |
| **SSIM Temporal Diff** | Yes | Implemented | `backend/services/change_detection.py` (Line 75) |
| **FastAPI Backend Endpoints** | Yes | Implemented | `backend/routers/image_routes.py` |
| **React SPA Architecture** | Yes | Implemented | `frontend/src/App.jsx` |
| **Footprint Overlap Map (IoU)** | Yes | Implemented | `frontend/src/components/FootprintMap.jsx` |
| **Real Chandrayaan-2 Multi-Sensor Validation** | No | *Partially Impl.* | Cross-sensor algorithms are active, but rigorous physical validation datasets are missing from `test_data/`. |
| **Deep Learning / Neural Nets** | No | *Not Impl.* | No PyTorch, TensorFlow, or ONNX files exist in the repository. Strictly classical CV. |

---
*End of Report. Generated based strictly on direct source-code verification of the LunarVision repository.*
