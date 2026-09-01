# LunarVision 🌔 — Live Demo & Presentation Guide

This guide provides a structured, step-by-step script to demonstrate **LunarVision** to judges, evaluators, and technical audiences.

---

## ⚡ Quick Start: Launching the Application

### 1. Start the Backend API (FastAPI)
Open a terminal in PowerShell:
```powershell
cd C:\Users\SANDHYA\.gemini\antigravity\scratch\lunarvision\backend
python -m uvicorn main:app --reload --port 8000
```
- **Live Health Endpoint**: `http://localhost:8000/api/health`
- **Interactive Swagger Docs**: `http://localhost:8000/docs`

### 2. Start the Frontend Application (React + Vite)
Open a second terminal in PowerShell:
```powershell
cd C:\Users\SANDHYA\.gemini\antigravity\scratch\lunarvision\frontend
npm run dev
```
- **Web Dashboard**: `http://localhost:5173`

---

## 📂 Prepared Demo Dataset

High-resolution synthetic lunar orbital image pairs and scientific PDS3 datasets are pre-generated in:
`backend/sample_data/`

| File Name | Role in Demo | Purpose |
| :--- | :--- | :--- |
| **`01_baseline_pre_event.png`** | Baseline Reference Frame | Standard lunar crater field (Pre-event orbital pass) |
| **`02_temporal_rotated_shifted.png`** | Transformed Secondary Frame | Same terrain with 3.5° rotation & 8px shift (For Registration) |
| **`03_temporal_new_impact_crater.png`** | Temporal Alteration Frame | Same terrain with a fresh impact crater & ejecta rays (For Change Detection) |
| **`04_unrelated_lunar_terrain.png`** | Dissimilar Lunar Frame | Completely different surface area (For No-Match Rejection) |
| **`05_scientific_lunar_reference.IMG`** | Scientific PDS3 Baseline | 16-bit uint16 PDS3 lunar raster dataset (525 KB) |
| **`06_scientific_lunar_transformed.IMG`** | Scientific PDS3 Transformed | 16-bit uint16 PDS3 lunar raster dataset with rotation/shift |

---

## 🎬 5-Step Live Demonstration Script

### Step 1: System Overview & Telemetry (Dashboard)
1. Open `http://localhost:5173`.
2. Point out the top telemetry header showing **"Backend Connected"** with live OpenCV `4.13.0` and scikit-image `0.26.0` versions.
3. Show the **Orbital Computer Vision Pipeline Architecture** visualizer detailing the 6 processing stages.

---

### Step 2: Image Registration Demonstration
1. In the left sidebar, click **Image Registration**.
2. Upload the sample files:
   - **Secondary / Temporal Image (Source)**: Upload `02_temporal_rotated_shifted.png`
   - **Baseline Image (Reference)**: Upload `01_baseline_pre_event.png`
3. Leave detector set to **SIFT (High Precision)** and click **Start Registration**.
4. **Key Talking Points for Judges**:
   - Notice the live animated radar scanning while OpenCV extracts DoG scale-space extrema and computes RANSAC homography.
   - Point out the **Quantitative Alignment Metrics**: RMSE (~1.8 px), RANSAC Inlier Count (100 inliers), Inlier Ratio (~97%), and Registration Confidence (98.2%).
   - Switch between result tabs:
     - **Split Slider**: Drag the vertical divider to show sub-pixel alignment of crater rims.
     - **RANSAC Inliers**: Show the cyan correspondence lines verified by RANSAC.
     - **All Matches**: Show candidate Lowe's ratio test filtered correspondences.
     - **50/50 Blend**: Show transparency overlay.
   - Click **Download Aligned Image** to show real artifact export.

---

### Step 3: No-Match Rejection Demonstration (Avoiding False Warping)
1. Stay on **Image Registration**.
2. Replace the Source image with `04_unrelated_lunar_terrain.png` (leave Reference as `01_baseline_pre_event.png`).
3. Click **Start Registration**.
4. **Key Talking Points for Judges**:
   - Explain: *"A major risk in planetary vision is forcing an affine or perspective warp on unrelated images, creating distorted artifacts. LunarVision strictly gates homography on geometric inlier thresholds."*
   - Show the resulting **"No Reliable Match Detected"** scientific diagnostic card explaining why correspondence was rejected.

---

### Step 4: Temporal Change Detection Demonstration
1. Click **Temporal Change** in the sidebar.
2. Upload:
   - **Earlier Image (Source T0)**: Upload `03_temporal_new_impact_crater.png`
   - **Later Image (Reference T1)**: Upload `01_baseline_pre_event.png`
3. Click **Detect Potential Changes**.
4. **Key Talking Points for Judges**:
   - The system first executes geometric registration to ensure valid coordinates.
   - Point out the **SSIM Structural Similarity Score** and the **Change Heatmap** highlighting the new crater in vivid red/yellow.
   - Switch to **Labeled Bounding Boxes**: Show the segmented candidate region categorized with morphological heuristic labels (`Possible crater-like change` or `Potential surface change`).
   - Highlight the **Scientific Transparency Protocol**: *"Detected regions represent potential surface changes and are not scientifically confirmed discoveries."*

---

### Step 5: Three-Sensor Extension & Pipeline Explainability
1. Click **Three-Sensor Analysis**:
   - Explain: *"This module provides the multi-modal ingestion framework for Chandrayaan-2/LRO payloads: OHRC (0.25m optical), TMC (5m stereo DEM), and IIRS (infrared spectroscopy). It executes real pairwise matching against a selected Reference Hub."*
2. Click **How It Works**:
   - Walk through the 8 transparent mathematical stages (CLAHE, SIFT DoG pyramids, Lowe's ratio test, RANSAC, Homography matrix, RMSE, and SSIM) demonstrating that LunarVision is an explainable, auditable system.

---

## ⚖️ Key Limitations & Honest Talking Points for Judges

When discussing with judges, highlight these honest technical realities:
1. **Extreme Lighting & Shadow Inversion**: When solar elevation angles differ by $>40^\circ$, optical shadow inversions can challenge keypoint detection, requiring illumination compensation (CLAHE) or multi-spectral DEM relief shading.
2. **Cross-Modality Disparity**: Registering hyperspectral infrared (IIRS) against optical (OHRC) can suffer from intensity gradient reversals; future enhancements will integrate normalized mutual information (NMI) and deep structural representations.
3. **Automated Detection vs Scientific Confirmation**: All detected temporal differences are candidate surface alterations that assist planetary geologists and require solar azimuth correlation to eliminate residual illumination artifacts.
