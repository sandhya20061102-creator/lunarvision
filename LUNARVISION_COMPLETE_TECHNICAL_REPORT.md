# LUNARVISION COMPLETE TECHNICAL REPORT

## 1. Project Title
LunarVision

## 2. SIH Problem Statement
**Problem Statement 26166 (PS26166):** "Multi-modal, Sun angle and scale invariant image correspondence using Chandrayaan-2 optical images (OHRC, TMC and IIRS)."

## 3. Problem Definition
The project addresses the challenge of identifying and registering corresponding spatial regions across multi-temporal and multi-sensor lunar orbital imagery. Lunar images suffer from intense illumination variations (sun-angle differences) that drastically alter shadow patterns, scale mismatches due to varying orbital altitudes, and differing radiometric characteristics across sensors (OHRC, TMC, IIRS).

## 4. Proposed Solution
A fully automated computer vision pipeline utilizing scale-invariant feature extraction (SIFT) with an AKAZE fallback, adaptive local contrast enhancement (CLAHE), and robust geometric alignment (RANSAC). The system integrates PDS-based geospatial footprint filtering and provides structural similarity-based change detection, wrapped in an offline-capable web application with an integrated knowledge base chatbot.

## 5. Objectives
1. Automate lunar image registration across varying spatial scales.
2. Ensure robustness against severe sun-angle variations and shadow shifts.
3. Support multi-sensor correspondence (OHRC, TMC, IIRS).
4. Provide qualitative and quantitative metrics (RMSE, Inlier Ratio, SSIM).
5. Detect temporal surface changes.
6. Provide an offline-first technical support chatbot.

## 6. System Architecture
The application consists of:
*   **Backend:** A Python/FastAPI server providing dedicated REST API endpoints for computer vision tasks.
*   **Frontend:** A React (Vite) Single Page Application (SPA) utilizing Tailwind CSS for a dark, cinematic UI.
*   **Processing Core:** OpenCV, NumPy, and scikit-image for feature detection, homography estimation, and pixel-level metrics.
*   **Knowledge Base:** A local JSON-based fallback for the offline-first chatbot.

## 7. End-to-End Workflow
1. **Upload:** User uploads Source and Reference images.
2. **Preprocessing:** Dynamic range normalization, grayscale conversion, and CLAHE enhancement.
3. **Feature Detection:** Keypoints extracted via SIFT (or AKAZE if features < 15).
4. **Feature Matching:** 2-Nearest Neighbor Brute-Force matching filtered by Lowe's Ratio Test.
5. **Geometric Verification:** RANSAC algorithm filters outliers and computes the Homography matrix.
6. **Registration:** Source image is warped to the Reference coordinate frame.
7. **Metrics Calculation:** System calculates RMSE, Inlier Ratio, and a composite Confidence Score.
8. **Footprint & Metadata:** PDS label or EXIF GPS metadata is parsed to visualize spatial overlap.
9. **Change Detection (Optional):** Generates SSIM and absolute difference heatmaps to highlight potential surface alterations.

## 8. Frontend Technology Stack
*   **Framework:** React 18, Vite
*   **Styling:** Tailwind CSS
*   **Icons:** Lucide-React
*   **Metadata Extraction:** ExifReader (for EXIF fallback), custom parsing for PDS labels (`.lbl` or embedded `.img`).

## 9. Backend Technology Stack
*   **Framework:** Python 3.10+, FastAPI
*   **Computer Vision:** OpenCV (cv2), scikit-image (skimage)
*   **Data Processing:** NumPy
*   **Testing:** Pytest

## 10. Computer Vision Pipeline Overview
The core pipeline follows a classic feature-matching approach enhanced with specialized planetary preprocessing to handle extreme illumination gradients and orbital scale mismatches. It relies on deterministic algorithmic logic rather than unverified deep learning models.

## 11. Detailed Explanation of Pipeline Components
*   **Preprocessing (`preprocessing.py`):** Automatically decodes standard images or scientific `.IMG` (PDS3/PDS4/VICAR) files. Ensures memory safety by downscaling >4096px images.
*   **Grayscale/Intensity Normalization:** Converts multi-channel arrays to single-channel uint8 matrices. Uses a robust 0.5-99.5 percentile min-max normalization to discard extreme sensor noise before scaling to [0, 255].
*   **CLAHE:** Contrast Limited Adaptive Histogram Equalization (`clipLimit=2.0`, `tileGridSize=(8,8)`). This is the primary mechanism for sun-angle robustness, as it locally normalizes contrast, accentuating subtle crater rims in shadows and suppressing overexposed regolith.
*   **SIFT:** Scale-Invariant Feature Transform is the primary detector. It handles the "scale invariant" requirement of the SIH prompt natively.
*   **AKAZE Fallback:** If SIFT yields fewer than 15 features, the system automatically falls back to AKAZE, which can sometimes isolate features differently in textureless regions.
*   **BFMatcher:** Brute-Force Matcher computes the distance between descriptor vectors (L2 norm for SIFT, Hamming for AKAZE).
*   **Lowe Ratio Test:** Accepts a match only if the distance to the nearest neighbor is significantly smaller than the distance to the second-nearest neighbor (`d1/d2 < 0.75-0.80`). This eliminates ambiguous matches caused by repetitive lunar crater fields.
*   **RANSAC:** Random Sample Consensus iteratively selects random subsets of matches to construct a geometric model, discarding outliers.
*   **Homography:** A 3x3 transformation matrix calculated by RANSAC that maps the perspective of the Source image to the Reference image.
*   **Inliers & Inlier Ratio:** Inliers are the matches that geometrically fit the Homography model (within a 3.5px reprojection threshold). The Inlier Ratio is `(Inliers / Total Good Matches)`.
*   **RMSE:** Root Mean Squared Error computed on the aligned, overlapping pixel regions. Lower is better (< 3.0 is highly precise).
*   **Confidence Score:** A heuristic score (0.0 to 1.0) calculated as a weighted sum of the capped inlier count (40%), inlier ratio (35%), and normalized RMSE (25%). Scores < 0.20 trigger automatic rejection.
*   **SSIM:** Structural Similarity Index Measure compares the perceptual similarity of the aligned bounding boxes.
*   **Change Detection (`change_detection.py`):** Combines an inverted SSIM map with an absolute difference map. Applies Otsu's thresholding, morphological opening (removes salt noise), and closing (bridges gaps). Uses connected component analysis to calculate area, circularity, and aspect ratio, applying heuristic labels (e.g., "Possible crater-like change", "Possible illumination artifact").

## 12. Handling Complex Conditions
*   **Scale Changes:** Addressed fundamentally by SIFT's scale-space extrema detection.
*   **Sensor Differences:** Addressed by converting all inputs to normalized grayscale and equalizing local histograms via CLAHE, ensuring that texture (craters) is matched rather than absolute radiometric brightness.
*   **Illumination/Sun-Angle Changes:** CLAHE drastically reduces macro-illumination gradients, preserving local edge gradients that SIFT relies upon.
*   **Poor/Incorrect Matches:** Filtered first by Lowe's Ratio Test (feature space), then strictly eliminated by RANSAC (geometric space).
*   **Rejection of Non-Corresponding Images:** The system rejects pairs if it finds < 6 matches, if RANSAC fails to find a mathematically stable matrix (determinant check), or if the final Confidence Score is below 20%.

## 13. Sun-Angle Robustness Implementation
*   **Implementation:** The system attempts to extract `INCIDENCE_ANGLE` or `SUN_ELEVATION` from PDS labels or EXIF tags (`sun_angle_service.py`).
*   **Testing Setup:** The `run_batch_sun_angle_benchmark` endpoint dynamically generates 15-20 image pairs by taking a baseline image and applying a synthetic illumination algorithm (`simulate_lunar_illumination`). This algorithm uses spatial Sobel gradients and Lambertian attenuation heuristics to physically model grazing shadows across 0° to 85° sun-angle differences. The pipeline is then executed against these synthetic pairs.
*   **Validation Status:** This is an *implemented simulation testing framework*. **No claims of scientific validation against real Chandrayaan-2 cross-illumination datasets are made**, as the testing relies on synthetic shadow generation.

## 14. Multi-Sensor Correspondence
The system includes a `/multi-sensor-register` endpoint designed to accept a "Hub" image (e.g., OHRC) and align it against secondary modalities (e.g., TMC, IIRS). The system handles sensor differences by stripping radiometric data (converting to grayscale), isolating structural features via CLAHE, and using robust SIFT descriptors. Success depends heavily on spatial resolution overlap (e.g., TMC at 5m/px and OHRC at 0.25m/px require the OHRC footprint to contain enough macro-features visible in the TMC image).

## 15. Multi-Pair Validation
*   **Implementation:** Handled via the batch benchmarking workflow.
*   **Testing Workflow:** The API iterates over generated image pairs, runs the entire CV pipeline (detection, matching, RANSAC, metrics), and aggregates the results into a JSON payload.
*   **Distinction:** This is an *implemented testing workflow* for algorithmic benchmarking. It is *not* a completed experimental validation, as no pre-verified, ground-truth Chandrayaan-2 dataset results are included in the repository.

## 16. Geospatial Footprint
*   **PDS Metadata (`pdsMetadata.js`):** Parses `.lbl` or embedded `.img` headers for `MINIMUM_LATITUDE`, `MAXIMUM_LONGITUDE`, etc., establishing a bounding box. Parses polygon corners if available.
*   **EXIF Fallback (`geoMetadata.js`):** If PDS is unavailable, uses `ExifReader` to extract standard GPS Latitude/Longitude center-points.
*   **Overlap Detection:** Calculates bounding-box intersection. Generates an Intersection over Union (IoU) percentage and overlap extent area. Longitude wraparound is natively handled by normalizing max/min bounds during overlap math.
*   **Candidate Pairs:** If a spatial overlap is detected (>0 IoU), the UI flags the pair as a "Candidate Pair" suitable for CV registration.

## 17. Change Detection
*   **Implementation:** Blends SSIM structural dissimilarity with direct Absolute Pixel Differencing. Uses Otsu's dynamic thresholding to isolate regions of extreme change.
*   **Detection Focus:** Identifies morphological anomalies (e.g., new craters, rover tracks).
*   **Limitations:** Highly sensitive to severe shadow shifts. Elongated shadows from varying solar elevation can trigger false positives. The heuristics attempt to flag these as "Possible illumination artifacts" based on aspect ratio (>2.8) and low circularity (<0.28).

## 18. Offline-First Chatbot
*   **Implementation (`chatbot_service.py`):** Operates on a local `lunar_knowledge_base.json` file.
*   **Matching:** Uses a custom normalized keyword overlap algorithm combining the Jaccard index and recall ratio to match user queries against predefined FAQs and pipeline steps. Includes exact keyword triggers for core concepts (RANSAC, SIFT, OHRC, etc.).
*   **Offline/Online Behavior:** Completely functional offline using the local JSON. The "Online" mode is simulated via returning pre-cached "ISRO news" notes from the JSON when connected, clearly labeling it as a "Built-in Library".
*   **Safety:** Does not use an LLM, ensuring zero hallucinations. If no match is found, it returns a safe, predefined fallback response offering help on supported topics.

## 19. Frontend/UI
A dark, cinematic dashboard optimized for planetary data.
*   **Dashboard:** High-level project overview and metrics.
*   **Registration Page:** Image upload, parameter tuning (detector choice), and visualization of raw matches, inlier matches, and blended overlay results.
*   **Change Detection:** Displays the generated heatmap, binary mask, and annotated bounding boxes.
*   **Footprint Map (`FootprintMap.jsx`):** Renders a custom SVG spatial plot of the bounding boxes or center-points based on extracted PDS/EXIF data.
*   **Chatbot:** A floating, draggable chat window indicating offline/online status.

## 20. API/Backend Endpoints (`image_routes.py`)
1.  **`/register`**: (POST) Accepts Source and Reference images. Returns alignment metrics, homography matrix, and URLs for generated visualization artifacts.
2.  **`/multi-sensor-register`**: (POST) Accepts a Hub image and up to two secondary sensor images, running pairwise registration.
3.  **`/change-detection`**: (POST) Runs registration, then executes the change detection pipeline, returning bounding box heuristics and heatmap artifacts.
4.  **`/sun-angle-robustness`**: (POST) Evaluates a single pair, extracting and comparing their sun-angles.
5.  **`/sun-angle-batch`**: (POST) Accepts a single baseline image, generates synthetic shadow pairs, and benchmarks the pipeline's robustness across 0-85° illumination differences.

## 21. Important Project Files
*   `backend/main.py`: FastAPI application entry point.
*   `backend/routers/image_routes.py`: Contains all REST API endpoints for the CV pipeline.
*   `backend/services/preprocessing.py`: Handles custom `.IMG` decoding, dynamic range clipping, and CLAHE.
*   `backend/services/registration.py`: Executes the RANSAC algorithm and perspective warping.
*   `backend/services/sun_angle_service.py`: Contains the synthetic `simulate_lunar_illumination` logic and PDS metadata extraction.
*   `frontend/src/utils/pdsMetadata.js`: Frontend parser for PDS bounding box labels.
*   `frontend/src/components/FootprintMap.jsx`: Renders the SVG coordinate overlap map.

## 22. Testing Status
*   **IMPLEMENTED:** SIFT/AKAZE matching pipeline, RANSAC geometric filtering, PDS parsing, offline chatbot, synthetic sun-angle illumination simulation.
*   **TESTED:** Backend API endpoints and core CV unit logic are tested via Pytest (`test_api_endpoints.py`, `test_backend_cv.py`, `test_full_integration.py`).
*   **VALIDATED:** *None.* The repository does not contain large-scale, ground-truth experimental validation results on real Chandrayaan-2 datasets.
*   **PLANNED:** Large-scale scientific validation using verified ISRO datasets.

## 23. Known Limitations
1.  **Chandrayaan-2 Data:** Lack of pre-packaged, multi-temporal Chandrayaan-2 pairs in the repository limits real-world benchmarking.
2.  **Sun-Angle Testing:** The batch benchmark relies on *synthetic* shadow modeling, which may not perfectly replicate complex lunar topography scattering.
3.  **False Positives in Change Detection:** Severe differences in solar elevation can cause elongated shadows that the change detection module flags as surface changes, despite heuristic mitigation attempts.
4.  **Sensor Resolution Mismatch:** Matching OHRC (0.25m) to TMC (5m) is computationally constrained if the OHRC footprint does not capture macro-features visible in the TMC image.

## 24. SIH Problem Alignment
*   **Multi-modal:** Addressed via the `/multi-sensor-register` endpoint and intensity normalization (CLAHE) which strips radiometric biases.
*   **Sun angle invariant:** Addressed via CLAHE preprocessing which equalizes local contrast, allowing SIFT to find gradients inside deep shadows or overexposed regions.
*   **Scale invariant:** Addressed directly by the SIFT (Scale-Invariant Feature Transform) algorithm.
*   **Correspondence:** Achieved via BFMatcher, Lowe's Ratio, and mathematically verified via RANSAC Homography.

## 25. Final End-to-End Pipeline
`Upload Images` ➔ `PDS/EXIF Metadata Extraction & Footprint Overlap Check` ➔ `CLAHE Preprocessing` ➔ `SIFT Keypoint Detection` ➔ `Lowe's Ratio Matching` ➔ `RANSAC Geometric Verification` ➔ `Perspective Warping` ➔ `Metrics Calculation (RMSE/Inlier Ratio/Confidence)` ➔ `Temporal Change Detection` ➔ `Result Visualization (Overlay, Heatmaps)`

## 26. Future Improvements
*   Integration of deep-learning based feature matchers (e.g., SuperGlue) to complement SIFT in extremely textureless regions.
*   Replacing synthetic sun-angle testing with an automated script that queries and downloads real ISRO ISSDC datasets for validation.
*   Incorporating 3D Digital Elevation Models (DEMs) to orthorectify images prior to matching, drastically reducing perspective distortions.
