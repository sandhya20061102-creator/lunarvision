# LunarVision 🌔 — Cloud Deployment & Public Hosting Guide

This guide details how to deploy **LunarVision** to production so anyone can access it through a public website link:
- **Backend API**: Python FastAPI + OpenCV deployed on **[Render](https://render.com/)**
- **Frontend Dashboard**: React + Vite + Tailwind CSS deployed on **[Vercel](https://vercel.com/)**

---

## 📋 Prerequisites

1. A **[GitHub](https://github.com/)** account.
2. A free **[Render](https://render.com/)** account.
3. A free **[Vercel](https://vercel.com/)** account.

---

## 🛠️ Step 1: Push Code to GitHub

Open a terminal in PowerShell:

```powershell
cd C:\Users\SANDHYA\.gemini\antigravity\scratch\lunarvision

# 1. Initialize Git repository
git init

# 2. Add all files (respecting .gitignore)
git add .

# 3. Commit changes
git commit -m "Initial commit: LunarVision Full-Stack System"

# 4. Create a new repository on GitHub (e.g. named 'lunarvision') and push:
git branch -M main
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/lunarvision.git
git push -u origin main
```

---

## 🐍 Step 2: Deploy Backend to Render

1. Log in to your **[Render Dashboard](https://dashboard.render.com/)**.
2. Click **New +** and select **Web Service**.
3. Select **Build and deploy from a Git repository** and connect your `lunarvision` repository.
4. Configure the service settings:
   - **Name**: `lunarvision-backend` (or any unique name)
   - **Region**: `Oregon (US West)` (or closest region)
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: `Free`
5. Click **Advanced** and add these **Environment Variables**:
   - `PYTHON_VERSION`: `3.11.8`
   - `ALLOWED_ORIGINS`: `https://lunarvision.vercel.app` (you can update this with your actual Vercel domain once generated)
6. Click **Create Web Service**.
7. Once deployed, copy your public backend URL from the top of the Render dashboard:
   - Example: `https://lunarvision-backend.onrender.com`
8. Verify by visiting `https://lunarvision-backend.onrender.com/api/health` in your browser. It should return:
   ```json
   {
     "status": "healthy",
     "service": "LunarVision Backend",
     "opencv_version": "4.13.0",
     "skimage_version": "0.26.0",
     "cors_configured": true
   }
   ```

---

## ⚡ Step 3: Deploy Frontend to Vercel

1. Log in to your **[Vercel Dashboard](https://vercel.com/)**.
2. Click **Add New...** > **Project**.
3. Import your `lunarvision` GitHub repository.
4. In the configuration modal:
   - **Framework Preset**: `Vite`
   - **Root Directory**: Click **Edit** and choose `frontend`.
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
5. Expand the **Environment Variables** section and add:
   - **Key**: `VITE_API_BASE_URL`
   - **Value**: `https://lunarvision-backend.onrender.com` *(Use your actual Render URL from Step 2 without a trailing slash)*
6. Click **Deploy**.
7. Vercel will build and assign you a public domain:
   - Example: `https://lunarvision.vercel.app`

---

## 🔄 Step 4: Final Linkage & CORS Check

1. Copy your Vercel public URL (e.g. `https://lunarvision.vercel.app`).
2. Go back to your **Render Dashboard** > `lunarvision-backend` > **Environment Variables**.
3. Ensure `ALLOWED_ORIGINS` includes your Vercel URL:
   ```text
   ALLOWED_ORIGINS = https://lunarvision.vercel.app,http://localhost:5173
   ```
   *(Note: The backend `main.py` is also pre-configured with a regex to automatically accept all `*.vercel.app` preview branches).*
4. Open your Vercel URL in your browser.
5. The top header badge should display **"🟢 Backend Connected"**.

---

## ☁️ Cloud Deployment Notes & Limitations

1. **Render Free-Tier Spin-Down (Cold Starts)**:
   - Render free web services spin down after **15 minutes of inactivity**.
   - If you visit the site after a period of dormancy, the first API request may take **30–50 seconds** while the container starts up.
   - The frontend header will show *"Connecting..."* during this wake-up period and switch to *"Backend Connected"* once the instance is live.

2. **Ephemeral File Storage**:
   - Processed visual artifacts (`/outputs/...`) are stored in the active Render container's local disk during the session.
   - Users can view and download all artifacts immediately in real time.
   - If the container restarts or spins down, older temporary files are wiped automatically, keeping the server clean without manual disk maintenance.

3. **Memory Limits on Free Instances**:
   - Render's free tier has a 512MB RAM cap.
   - LunarVision includes built-in memory safety (`max_dimension=4096px`) in `preprocessing.py` that automatically rescales gigapixel lunar rasters to prevent out-of-memory errors.
