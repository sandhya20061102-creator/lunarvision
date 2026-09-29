import zlib
import base64

def get_kroki_url(mermaid_str):
    compressed = zlib.compress(mermaid_str.strip().encode('utf-8'), 9)
    b64_str = base64.urlsafe_b64encode(compressed).decode('utf-8')
    return f"https://kroki.io/mermaid/svg/{b64_str}"

mermaid_arch = """
flowchart TB
    subgraph Client [Client-Side Interface]
        UI[Web Dashboard]
        State[State Management]
        Net[Network Layer]
    end
    subgraph Server [Backend System]
        API[API Gateway]
        Engine[Classical CV Engine]
        subgraph Pipeline [Image Processing Pipeline]
            Pre[Preprocessing & PDS Parser]
            Feat[SIFT Feature Detection]
            Reg[RANSAC Geometric Registration]
            Change[Temporal SSIM Differencing]
        end
    end
    UI --> Net --> API --> Engine --> Pre --> Feat --> Reg --> Change
"""

mermaid_flow = """
sequenceDiagram
    participant User
    participant Frontend
    participant Backend
    participant CVPipeline

    User->>Frontend: Upload Temporal & Baseline Images
    Frontend->>Backend: Transmit Scientific Data
    Backend->>CVPipeline: Initiate Pipeline
    CVPipeline->>CVPipeline: Extract PDS Metadata & Decode
    CVPipeline->>CVPipeline: CLAHE Equalization
    CVPipeline->>CVPipeline: SIFT Keypoint Extraction
    CVPipeline->>CVPipeline: KNN Matching & Lowe Ratio Test
    CVPipeline->>CVPipeline: RANSAC Homography Calculation
    CVPipeline->>CVPipeline: Generate Confidence Metrics
    CVPipeline->>Backend: Return Registration Results
    Backend->>Frontend: JSON Payload & Visualization Artifacts
    Frontend->>User: Display Alignment & Metrics
"""

md_content = f"""# LUNARVISION — FINAL DETAILED ACADEMIC PROJECT REPORT

## 1. Title Page

**Project Title:** LunarVision: Multi-modal, Sun angle and scale invariant image correspondence using Chandrayaan-2 optical images  
**SIH Problem Statement:** PS 26166  
**Domain:** Space Technology / Computer Vision  
**Academic Year:** 2026-2027  
**Submitted By:** Team LunarVision  

---

## 2. Certificate and Declaration

**CERTIFICATE**  
This is to certify that the project report entitled "LunarVision" is a bonafide record of the work carried out by Team LunarVision under our supervision and guidance, in partial fulfillment of the requirements for the Smart India Hackathon (SIH) submission.

**DECLARATION**  
We hereby declare that the project titled "LunarVision" is our original work and has not been submitted previously for the award of any degree or diploma. All sources of information and technical methodologies have been duly acknowledged.

---

## 3. Acknowledgement

We express our deepest gratitude to the Smart India Hackathon organizers, the Indian Space Research Organisation (ISRO), and our mentors for providing the problem statement and the opportunity to work on this challenging problem in planetary science. We also thank our institution for providing the necessary infrastructure and support to bring this project to fruition.

---

## 4. Abstract

The accurate coregistration of multimodal planetary imagery is a critical prerequisite for topographical analysis, temporal change detection, and lunar landing site characterization. We present LunarVision, an end-to-end web-based architecture designed to achieve multi-modal, scale-invariant, and sun-angle robust image correspondence for Chandrayaan-2 optical sensors (OHRC, TMC, and IIRS). Because lunar terrain appearance is highly dependent on solar elevation—producing severe shadowing artifacts—conventional pixel-intensity matching methodologies frequently fail. 

LunarVision employs a classical computer vision pipeline leveraging Contrast Limited Adaptive Histogram Equalization (CLAHE) coupled with Scale-Invariant Feature Transform (SIFT) descriptors and rigorous RANSAC-based geometric validation. Furthermore, the system includes native parsing for raw Planetary Data System (PDS) binary `.IMG` arrays, bypassing the need for intermediary data conversions. The resulting application successfully outputs aligned projections, structural similarity (SSIM) metrics, and temporal change heatmaps without relying on computationally expensive deep learning models.

---

## 5. Table of Contents
1. Introduction
2. Background and Domain Study
3. Problem Statement
4. Motivation and Objectives
5. Existing Systems and Limitations
6. Proposed System Overview
7. Detailed Methodology and Algorithms
8. Implementation Details
9. Results and Observations
10. Conclusion and Future Scope
11. Appendix: Viva Questions

---

## CHAPTER 1 — INTRODUCTION

The exploration of the lunar surface relies heavily on orbital remote sensing. Satellites orbiting the Moon continuously capture high-resolution imagery, which serves as the foundation for creating topographical maps, analyzing mineralogical compositions, and identifying safe landing zones for future robotic and crewed missions. As orbital missions advance, they are equipped with an array of diverse sensors—each designed to capture specific wavelengths and spatial resolutions.

However, interpreting this orbital imagery is inherently complex. A single geographical location on the lunar surface can appear vastly different depending on when and how it is photographed. Unlike Earth, the Moon lacks an atmosphere to scatter sunlight. Consequently, solar illumination creates pitch-black, high-contrast shadows. A crater illuminated from the east during lunar dawn will cast shadows in the opposite direction when illuminated from the west during lunar dusk, completely altering the visual structure of the terrain.

Furthermore, orbital images are subject to extreme scale and rotational disparities. An image captured by a high-resolution camera may cover a few hundred square meters, while a stereoscopic mapping camera might capture kilometers of terrain in a single frame. Spacecraft attitude and orbital trajectories introduce rotational changes between consecutive passes. 

When attempting to analyze temporal changes—such as identifying a new impact crater or locating a landed rover—scientists must precisely align (or coregister) a recent image with a historical baseline image. Due to the aforementioned challenges of scale, rotation, illumination, and distinct sensor modalities, traditional automated alignment algorithms frequently fail, forcing scientists into labor-intensive manual alignment.

LunarVision was developed to solve this precise bottleneck. It is a robust, automated computer vision platform that aligns lunar imagery regardless of the scale, rotation, illumination, or sensor modality, utilizing mathematically verified invariant feature extraction.

---

## CHAPTER 2 — BACKGROUND AND DOMAIN STUDY

### Lunar Surface Imaging and Orbital Remote Sensing
Remote sensing is the science of obtaining information about objects or areas from a distance, typically from aircraft or satellites. In the context of lunar exploration, orbital remote sensing is the primary method for planetary mapping. The Chandrayaan-2 mission, launched by the Indian Space Research Organisation (ISRO), is a prime example of an advanced remote sensing platform.

### Chandrayaan-2 Optical Payloads
The Chandrayaan-2 orbiter carries three primary optical payloads critical to this project:
*   **OHRC (Orbiter High Resolution Camera):** Designed to capture sub-meter resolution (0.25m) panchromatic imagery. It is primarily used for identifying hazard-free landing zones.
*   **TMC-2 (Terrain Mapping Camera 2):** Captures 5m resolution stereoscopic data. It is used to prepare 3D topographical maps (Digital Elevation Models) of the lunar surface.
*   **IIRS (Imaging InfraRed Spectrometer):** Captures hyperspectral data (0.8 to 5.0 µm) for mapping lunar mineralogy and detecting water ice signatures.

### The Challenge of Lunar Terrain Features
The lunar surface is dominated by distinct geomorphological features:
*   **Craters:** The most common feature, characterized by a circular rim, steep inner walls, and a flat or hummocky floor.
*   **Ridges and Rilles:** Linear or sinuous topographical deformations.
*   **Regolith:** The layer of loose, fragmented rock and dust covering the solid bedrock.

Because the Moon has no atmosphere, the interaction between sunlight and these topographical features is extreme. Shadows are absolute (pitch black) because there is no ambient light scattering to illuminate shadowed regions. Therefore, the visual appearance of a crater is highly dependent on the **Illumination Geometry** (the angle of the Sun relative to the surface). 

For automated image correspondence, these features are essential because they provide structural uniqueness. However, because their appearance changes with illumination, an algorithm cannot simply look for "a dark circle" (which might just be a shadow). It must identify the structural gradient (the actual edge of the crater rim) regardless of whether the inside is illuminated or shrouded in darkness.

---

## CHAPTER 3 — PROBLEM STATEMENT

**SIH Problem Statement PS 26166:** 
"Multi-modal, Sun angle and scale invariant image correspondence using Chandrayaan-2 optical images (OHRC, TMC, and IIRS)."

### Explanation in Simple Language
Given two pictures of the Moon taken by different cameras, from different altitudes, or at different times of day, the software must be able to automatically figure out if they are looking at the same piece of land, and if so, mathematically align them so they perfectly overlap.

### Explanation in Technical Language
The system must algorithmically ingest and decode raw scientific binary payloads (PDS format). It must extract scale-invariant and rotation-invariant structural keypoints that survive severe non-linear illumination shifts. It must then compute a mathematically rigorous perspective transformation matrix (Homography) to coregister the temporal source image into the coordinate space of the baseline reference image, while explicitly rejecting false positive matches across multi-modal sensor inputs (OHRC, TMC, IIRS).

### Practical Scenario Example
*(Hypothetical Explanatory Scenario)* Image A (Baseline) is hypothetically taken by the TMC sensor at a resolution of 5m/pixel with the Sun directly overhead (0° incidence). A crater looks like a bright, flat circle. 
Image B (Temporal) is taken months later by the OHRC sensor at a resolution of 0.25m/pixel, with the Sun at a grazing angle (80° incidence). The same crater now covers the entire image, is rotated 45 degrees, and is half-filled with pitch-black shadow.
LunarVision must process both images, identify that the crater rim structurally corresponds in both pictures despite the massive 20x scale gap and lighting inversion, and perfectly align Image B onto Image A.

---

## CHAPTER 4 — MOTIVATION AND OBJECTIVES

### Motivation
Manual registration of petabytes of orbital data is impossible. By automating this process, LunarVision enables:
*   **Global Lunar Mapping:** Merging high-resolution localized images into broader topographical basemaps.
*   **Scientific Synergy:** Allowing geologists to seamlessly overlay mineralogical arrays (IIRS) onto high-resolution visual morphology (OHRC) to understand the composition of specific craters.
*   **Democratization of Data:** Providing an intuitive web interface that handles complex scientific PDS data without requiring end-users to write complex Python scripts or use specialized GIS software.

### Primary Objectives
1. Parse and decode raw binary PDS (Planetary Data System) `.IMG` formats natively without crashing standard web servers.
2. Implement a scale- and rotation-invariant feature detection computer vision pipeline.
3. Quantify physical correspondence via RANSAC homography and strict reprojection error limits.
4. Present a web-based interactive dashboard for real-time geometric registration.

### Secondary Objectives
1. Extract solar elevation/incidence angles from embedded PDS metadata to evaluate illumination differences.
2. Perform temporal change detection on aligned images using structural differencing (SSIM).
3. Simulate sun-angle variations synthetically for batch robustness testing.
4. Visualize geospatial footprint overlap using bounding box coordinates on a spatial UI component.

---

## CHAPTER 5 — EXISTING SYSTEMS AND LIMITATIONS

### Existing Approaches
Currently, aligning highly disparate orbital images relies on manual point-picking by GIS experts or standard pixel-wise correlation algorithms (e.g., Normalized Cross-Correlation or Mean Squared Error). Basic automated systems attempt to align images by matching pixel intensities directly.

### Limitations of Existing Approaches
*   **Illumination Variance:** Direct pixel correlation (like RMSE) fails entirely when shadow directions invert. An area that is bright white at lunar dawn becomes pitch black at lunar dusk, causing pixel-wise math to calculate maximum error for the exact same physical location.
*   **Scale Mismatch:** Traditional systems cannot align images with a 20x resolution gap (e.g., OHRC vs. TMC) because the template sizes drastically mismatch.
*   **Data Formatting Limitations:** Standard web applications and AI models cannot process 16-bit, 32-bit, or unheadered binary `.IMG` scientific arrays out-of-the-box. They require heavy pre-conversion pipelines.
*   **Deep Learning Data Scarcity:** Theoretical constraint: Modern CNN/Transformer approaches generally require massive datasets of labeled, perfectly co-registered multimodal lunar images to train effectively, which are notoriously scarce in the planetary science domain.

---

## CHAPTER 6 — PROPOSED SYSTEM OVERVIEW

LunarVision is an end-to-end Classical Computer Vision platform designed explicitly for lunar topography. It completely bypasses modern deep learning in favor of a deterministic, mathematically verifiable pipeline. It leverages SIFT (Scale-Invariant Feature Transform) to identify structural keypoints that remain mathematically consistent across scales and rotations, ensuring high-confidence geometric alignments.

### System Architecture
The architecture is decoupled into a React frontend Single Page Application (SPA) and a FastAPI backend service. The backend handles asynchronous multipart payloads and routes them through a sequence of classical computer vision services.

![System Architecture]({get_kroki_url(mermaid_arch)})

### System Flow
![Data Flow Diagram]({get_kroki_url(mermaid_flow)})

---

## CHAPTER 7 — DETAILED METHODOLOGY AND ALGORITHMS

The core strength of LunarVision lies in its strict adherence to verifiable mathematical algorithms.

### 7.1 Lunar Image/Data Handling (PDS Parsing)
NASA/ISRO Planetary Data System (PDS) `.IMG` formats are raw binary payloads. LunarVision natively reads the first 64 KB of the file hunting for textual labels (e.g., `RECORD_BYTES`, `SAMPLE_BITS`, `LINES`). It extracts the image dimensions and bit depth. Using `numpy.frombuffer`, it ingests the binary payload directly into a float32 or uint16 matrix. 
Large orbital strips can exceed 100,000 pixels in length. The system automatically detects arrays exceeding a 4096px maximum dimension and safely downscales them using area interpolation (`cv2.INTER_AREA`) to prevent RAM exhaustion.

### 7.2 Image Preprocessing (Percentile Normalization & CLAHE)
Raw 16-bit `.IMG` files often contain extreme outliers like absolute black voids or cosmic ray spikes (value 65535). LunarVision clips these outliers by scaling intensities between the `0.5th` and `99.5th` percentiles of the histogram.
Following this, the system applies **Contrast Limited Adaptive Histogram Equalization (CLAHE)**. Unlike global equalization which ruins lunar images by overexposing bright regolith, CLAHE divides the image into an 8x8 grid and equalizes the histogram within each tile. It uses a clip limit of `2.0` to prevent noise amplification in shadows. This explicitly highlights crater rims hidden inside shadows, providing highly robust anchor points for downstream algorithms.

### 7.3 Feature Detection (SIFT and AKAZE)
**Scale-Invariant Feature Transform (SIFT):** 
SIFT generates a Difference of Gaussians (DoG) pyramid to find extrema across varying scales. It assigns orientations to keypoints based on local image gradient directions, making the descriptors rotation-invariant. Each keypoint is represented by a 128-dimensional float vector. SIFT inherently solves the OHRC to TMC 20x scale mismatch.
**AKAZE Fallback:** 
If an image is unusually devoid of features (e.g., smooth lunar mare) and SIFT detects fewer than 12 keypoints, the system automatically falls back to Accelerated-KAZE, which utilizes non-linear diffusion filtering and binary descriptors.

### 7.4 Feature Matching (KNN and Lowe's Ratio Test)
The system uses a Brute-Force Matcher to evaluate every feature in the source image against every feature in the reference image, returning the two closest matches (`k=2`).
To mathematically prevent matching ambiguous, repetitive patterns (common in generic lunar regolith), LunarVision enforces **Lowe's Ratio Test** with a threshold of `0.75` for SIFT (and `0.80` for AKAZE fallback). A match is only accepted if the distance to its closest neighbor is significantly smaller (at least 25% closer) than the distance to its second closest neighbor.

### 7.5 Geometric Registration (RANSAC Homography)
After matching, thousands of candidates may exist. The system requires a strict minimum of 6 matches to proceed to geometric verification to prevent false geometry on sparse data. **Random Sample Consensus (RANSAC)** randomly picks sets of 4 point correspondences to calculate a hypothetical 3x3 perspective homography matrix. 
It reprojects all points using the matrix. Points falling within a strict `3.5 pixel` radius of their target are flagged as **Inliers**. The matrix yielding the highest inlier count is selected. Finally, a matrix determinant validation check (`[1e-4, 1e4]`) ensures the geometry has not degenerated into an impossible plane (like a collapsed line).

### 7.6 Temporal Change Detection (SSIM and Otsu's Binarization)
For images taken of the same location years apart, detecting new impacts is crucial.
The system calculates a **Structural Similarity (SSIM)** difference map and an Absolute pixel difference map, blending them 50/50. Instead of hardcoding a difference threshold, **Otsu's Thresholding** dynamically calculates the statistical variance of pixel intensities to find the perfect separation threshold between "unchanged regolith" and "new crater". Morphological Opening (3x3 kernel) removes noise dots, and Closing (5x5 kernel) bridges gaps in crater rims. The output is highlighted via a JET colormap heatmap.

---

## CHAPTER 8 — IMPLEMENTATION DETAILS

### 8.1 Technology Stack
*   **Frontend:** React (v18.2.0), Vite, Tailwind CSS. Used for the Single Page Application (SPA).
*   **Backend:** FastAPI (v0.110.0), Python 3.11.8. Serves the REST API endpoints asynchronously.
*   **CV Engine:** OpenCV (v4.13.0) provides SIFT, RANSAC, and Homography.
*   **Math/Metrics:** NumPy (v1.26.4) handles multi-dimensional array operations and PDS binary decoding; scikit-image (v0.22.0) computes SSIM.

### 8.2 API Endpoints
*   `POST /api/images/register`: Core geometric alignment taking source and reference images. Returns JSON metrics and static artifact URLs.
*   `POST /api/images/multi-sensor-register`: Executes pairwise multi-sensor match (Hub↔A and Hub↔B) independently.
*   `POST /api/images/change-detection`: Takes aligned images, executes SSIM/Otsu morphology, and returns a heatmap artifact.
*   `POST /api/images/sun-angle-batch`: Executes synthetic robustness testing by looping through 0°-85° applying Lambertian shading via Sobel gradients.

### 8.3 Calculation of the Confidence Score
To present a human-readable metric to the user, LunarVision fuses metrics into a weighted confidence score:
*   `40%` weighted on total inlier count (saturates at 40 inliers).
*   `35%` weighted on the inlier ratio (inliers / total matches).
*   `25%` weighted on overlapping Root Mean Square Error (RMSE).
If the fused confidence drops below the strict rejection threshold of `0.20` (20%), the system securely rejects the pair as a hallucination or "No Reliable Match", actively protecting against false positives.

---

## CHAPTER 9 — RESULTS AND OBSERVATIONS

### 9.1 Test Cases and Coverage
Integration tests were successfully run against various conditions:
1.  **Geometric Coregistration:** RANSAC found robust inliers (>70% confidence) on temporal pairs rotated and shifted.
2.  **No Match Rejection:** Feeding completely unrelated lunar terrain triggered the 0.20 confidence rejection threshold, preventing the system from hallucinating a false warp.
3.  **Temporal Change:** The SSIM and Otsu module correctly segmented a new impact crater, validating circularity and area metrics.
4.  **Multi-Sensor Handling:** The system processed Hub↔TMC and Hub↔IIRS independently returning dual metrics seamlessly without requiring sensor-specific parameter tuning.
5.  **Invalid File Handling:** OpenCV safely returns `None` on corrupted bytes without crashing the server, returning a structured error JSON instead.

### 9.2 Sun-Angle Robustness Observations
Testing proved that SIFT matching degrades predictably at grazing angles (near 85°) due to the absolute loss of structural gradients inside completely black shadows, but survives moderate illumination shifts exceptionally well due to the CLAHE preprocessing stage recovering rim edges.

---

## CHAPTER 10 — CONCLUSION AND FUTURE SCOPE

### Conclusion
LunarVision successfully addresses the complexities of multi-modal, sun-angle, and scale-invariant image correspondence for lunar exploration. By integrating robust data parsing with a mathematically verifiable Classical Computer Vision architecture, the system provides reliable geometric coregistration and change detection. The platform effectively circumvents the limitations of deep learning data scarcity and pixel-wise illumination failures, offering a highly accessible, CPU-efficient tool for planetary scientists and geospatial analysts.

### Limitations
1.  **Featureless Terrain Failure:** If images feature completely smooth mare (lunar plains) with no craters or rocks, no structural gradients exist, causing SIFT to fail at the minimum keypoint gate.
2.  **Spectral Disconnect:** If an IIRS thermal image shows subsurface mineralogical heat bands that share zero physical topographical geometry with an OHRC visual image, structural matching will fail due to lack of visible features.
3.  **2D Planar Assumption:** The system currently relies on 2D perspective warping (Homography) and does not perform true 3D orthorectification over heavily mountainous topography.

### Future Scope
1.  **Deep Learning Descriptor Fusion:** Integrating modern neural descriptors (like SuperPoint or SuperGlue) to complement SIFT, specifically to survive extreme 90-degree illumination shifts where classical gradients fail entirely.
2.  **3D DEM Orthorectification:** Ingesting height-map Digital Elevation Models (DEM) to project images onto a 3D lunar sphere rather than assuming a flat 2D perspective plane.
3.  **Automated ISSDC Downloading:** Connecting the backend directly to the ISRO payload data portal via API to automatically retrieve overlapping images based on user coordinates.

---

## CHAPTER 11 — APPENDIX: VIVA QUESTIONS

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
12. **How many points are needed to compute Homography?** A minimum of 6 matches (while Homography mathematically requires 4, the pipeline enforces a minimum of 6 for robustness).
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
"""

with open("LunarVision_Final_Detailed_Project_Report.md", "w", encoding="utf-8") as f:
    f.write(md_content)



