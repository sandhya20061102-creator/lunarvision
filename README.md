# LunarVision 🌔

**Multi-Modal Lunar Image Correspondence and Temporal Change Detection System**

LunarVision is a full-stack planetary computer vision platform engineered to register multi-temporal and multi-sensor orbital imagery of the lunar surface, compute sub-pixel geometric correspondences, evaluate quantitative alignment accuracy, and detect candidate surface alterations (such as fresh impact craters, boulder displacements, and regolith disturbances).

---

## 🌟 Key Feat- **Geometric Image Registration**: High-precision SIFT / AKAZE keypoint extraction and RANSAC perspective homography warping.
- **Scientific .IMG & Web Multi-Format Ingestion**: Ingests standard web images (PNG, JPG, TIFF, BMP) and scientific PDS3/PDS4 16-bit `.IMG` orbital datasets.
- **Explainable Quality Metrics**: Real-time evaluation of Root Mean Squared Error (RMSE), RANSAC Inlier Count, Inlier Ratio, and Registration Confidence Score.
- **Fail-Safe No-Match Rejection**: Automatically rejects degenerate or unrelated imagery to prevent false warping artifacts.
- **Temporal Change Detection**: Illumination normalization (CLAHE), Structural Similarity Index (SSIM) dissimilarity mapping, morphological noise filtering, and heuristic region classification.
- **Three-Sensor Analysis Extension**: Cross-modal pairwise framework designed for Chandrayaan-2 and Lunar Reconnaissance Orbiter payloads (**OHRC**, **TMC**, and **IIRS**).
- **Interactive Visual Comparator**: Split-view slider, RANSAC inlier correspondence lines, alpha-blend overlays, and false-color JET heatmaps.
- **Pipeline Transparency ("How It Works")**: Full 8-stage mathematical and computer vision breakdown.
- **Cloud Deployment Ready**: Pre-configured for **Render** (FastAPI backend) and **Vercel** (React frontend).

---

## 🛠️ Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | React 18, Vite 5, Tailwind CSS, Lucide React, Axios |
| **Backend** | Python 3.10+, FastAPI, Uvicorn, Pydantic |
| **Computer Vision** | OpenCV (`opencv-python` 4.13+) |
| **Image Processing & Metrics** | `scikit-image` 0.26+, `NumPy` 2.4+, `Pillow` 12.1+ |
| **Deployment Targets** | **Vercel** (Frontend) & **Render** (Backend) |

---

## 📁 Project Architecture

```text
lunarvision/
│
├── backend/
│   ├── main.py                     # FastAPI app with CORS, health check & static mounts
│   ├── requirements.txt            # Python dependencies (FastAPI, OpenCV, skimage)
│   ├── render.yaml                 # Render Blueprint deployment specification
│   ├── .env.example                # Backend environment variables template
│   ├── sample_data/                # Pre-generated lunar test imagery
│   │   ├── 01_baseline_pre_event.png
│   │   ├── 02_temporal_rotated_shifted.png
│   │   ├── 03_temporal_new_impact_crater.png
│   │   ├── 04_unrelated_lunar_terrain.png
│   │   ├── 05_scientific_lunar_reference.IMG
│   │   └── 06_scientific_lunar_transformed.IMG
│   ├── routers/
│   │   ├── __init__.py
│   │   └── image_routes.py         # Endpoints: /register, /change-detection, /multi-sensor-register
│   ├── services/
│   │   ├── __init__.py
│   │   ├── preprocessing.py        # PDS3/PDS4 16-bit support, CLAHE, intensity normalization
│   │   ├── feature_detection.py    # SIFT scale-space extrema with AKAZE fallback
│   │   ├── matching.py             # BFMatcher with Lowe's ratio test (SIFT: 0.75, AKAZE: 0.80)
│   │   ├── registration.py         # RANSAC homography estimation & perspective warp
│   │   ├── metrics.py              # Overlap-masked RMSE, inlier ratio, confidence
│   │   └── change_detection.py     # SSIM dissimilarity, morphology, heuristic labels
│   ├── uploads/                    # Temporary uploaded imagery
│   └── outputs/                    # Processed overlays, registered outputs, heatmaps
│
├── frontend/
│   ├── public/
│   │   └── favicon.svg             # LunarVision favicon
│   ├── src/
│   │   ├── components/
│   │   │   ├── Sidebar.jsx          # Left navigation with active badge indicators
│   │   │   ├── Header.jsx           # Live backend telemetry & Swagger docs link
│   │   │   ├── ImageUploader.jsx    # Drag-and-drop ingestion with .IMG preview
│   │   │   ├── MetricCard.jsx       # Scientific telemetry cards with confidence gauges
│   │   │   ├── ResultImage.jsx      # High-res viewer with pan/zoom modal & download
│   │   │   ├── ComparisonSlider.jsx # Interactive before/after split slider
│   │   │   ├── LoadingState.jsx     # Radar scanning loader with step updates
│   │   │   ├── ErrorMessage.jsx     # Diagnostic alert card for "no_match" rejection
│   │   │   ├── DownloadButton.jsx   # Direct image/data export utility
│   │   │   └── PipelineVisualizer.jsx # 6-stage CV pipeline flowchart
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx        # Project overview & quick launch
│   │   │   ├── RegistrationPage.jsx # SIFT/AKAZE + RANSAC registration interface   # Diagnostic alert card for "no_match" rejection
│   │   │   ├── DownloadButton.jsx   # Direct image/data export utility
│   │   │   └── PipelineVisualizer.jsx # 6-stage CV pipeline flowchart
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx        # Project overview & quick launch
│   │   │   ├── RegistrationPage.jsx # SIFT/ORB + RANSAC registration interface
│   │   │   ├── ThreeSensorPage.jsx  # Pairwise OHRC, TMC & IIRS extension
│   │   │   ├── ChangeDetectionPage.jsx # SSIM, heatmaps, masks, and heuristic labels
│   │   │   ├── ResultsPage.jsx      # Consolidated metrics & export center
│   │   │   └── HowItWorksPage.jsx   # 8-stage mathematical explainability guide
│   │   ├── context/
│   │   │   └── PipelineContext.jsx  # Shared state across all dashboard tabs
│   │   ├── services/
│   │   │   └── api.js               # Axios client for FastAPI endpoints
│   │   ├── App.jsx                  # Main application shell
│   │   └── index.css                # Tailwind directives & space styling
│   ├── package.json                 # Frontend dependencies
│   ├── vite.config.js               # Vite dev server with /api proxy
│   ├── tailwind.config.js           # Custom space color palette
│   ├── vercel.json                  # Vercel SPA routing rewrites
│   └── .env.example                 # Frontend environment variables template
│
├── .gitignore                       # Git ignore rules
├── test_backend_cv.py               # Algorithmic CV verification suite
├── test_api_endpoints.py            # FastAPI HTTP endpoint test suite
├── test_full_integration.py         # Full-stack integration test suite
├── generate_sample_lunar_data.py    # Synthetic lunar dataset generator
├── DEMO_GUIDE.md                    # Step-by-step judge presentation script
├── DEPLOYMENT.md                    # Cloud deployment guide for Render & Vercel
└── README.md
```

---

## 🚀 Local Installation & Startup

### 1. Prerequisites
- **Python 3.10+** (Python 3.14 tested)
- **Node.js 18+ and npm**

### 2. Backend Setup
```powershell
cd backend

# Create virtual environment (optional)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install Python packages
pip install -r requirements.txt

# Start FastAPI backend server
python -m uvicorn main:app --reload --port 8000
```
- **Backend API**: `http://localhost:8000`
- **Interactive Swagger Docs**: `http://localhost:8000/docs`
- **Health Telemetry**: `http://localhost:8000/api/health`

### 3. Frontend Setup
```powershell
cd frontend

# Install npm packages
npm install

# Start Vite dev server
npm run dev
```
- **Web Dashboard**: `http://localhost:5173`

---

## ☁️ Cloud Deployment (Render + Vercel)

The application is configured for one-click deployment:
- **Backend on Render**: Connect your GitHub repo, set root directory to `backend`, build command `pip install -r requirements.txt`, start command `uvicorn main:app --host 0.0.0.0 --port $PORT`.
- **Frontend on Vercel**: Connect your GitHub repo, set root directory to `frontend`, add environment variable `VITE_API_BASE_URL=https://your-backend.onrender.com`.

For full step-by-step instructions, see [**DEPLOYMENT.md**](file:///C:/Users/SANDHYA/.gemini/antigravity/scratch/lunarvision/DEPLOYMENT.md).

---

## 📖 Live Demonstration Guide

For a step-by-step presentation script for judges, see [**DEMO_GUIDE.md**](file:///C:/Users/SANDHYA/.gemini/antigravity/scratch/lunarvision/DEMO_GUIDE.md).
