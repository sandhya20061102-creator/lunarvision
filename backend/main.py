import os
import sys
from pathlib import Path

# Ensure both backend directory and repo root are in sys.path so imports resolve
# seamlessly regardless of whether run from workspace root or inside backend/
BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parent
for p in [str(BASE_DIR), str(REPO_ROOT)]:
    if p not in sys.path:
        sys.path.insert(0, p)

import cv2
import numpy as np
import skimage
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

try:
    from backend.routers.image_routes import router as image_router
    from backend.routers.benchmark_routes import router as benchmark_router
    from backend.routers.chat_routes import router as chat_router
except ImportError:
    from routers.image_routes import router as image_router
    from routers.benchmark_routes import router as benchmark_router
    from routers.chat_routes import router as chat_router


# Initialize application directories
UPLOADS_DIR = BASE_DIR / "uploads"
OUTPUTS_DIR = BASE_DIR / "outputs"

UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="LunarVision API",
    description="Backend API for Lunar Image Correspondence and Temporal Change Detection",
    version="1.0.0"
)

# Dynamic CORS Configuration for Production and Localhost
default_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://localhost:5175",
    "http://127.0.0.1:5175",
    "http://localhost:5176",
    "http://127.0.0.1:5176",
    "http://localhost:5177",
    "http://127.0.0.1:5177",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://lunarvision-1.onrender.com",
    "https://lunarvision.onrender.com",
    "https://lunarvision.vercel.app",
]

# Read optional comma-separated ALLOWED_ORIGINS from environment variable (e.g. from Render dashboard)
env_origins_str = os.getenv("ALLOWED_ORIGINS", "")
if env_origins_str:
    env_origins = [origin.strip() for origin in env_origins_str.split(",") if origin.strip()]
    origins = list(set(default_origins + env_origins))
else:
    origins = default_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"https://.*(\.vercel\.app|\.onrender\.com)",  # Permit all Vercel and Render deployment URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static directories for file access
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")
app.mount("/outputs", StaticFiles(directory=str(OUTPUTS_DIR)), name="outputs")

# Include Routers
app.include_router(image_router, prefix="/api/images", tags=["Images"])
app.include_router(benchmark_router, prefix="/api/benchmark", tags=["Benchmark"])
app.include_router(chat_router, prefix="/api/chat", tags=["Chatbot"])


@app.get("/")
async def root():
    return {
        "app": "LunarVision API",
        "status": "online",
        "environment": os.getenv("RENDER_SERVICE_NAME", "local_development"),
        "version": "1.0.0",
        "docs_url": "/docs"
    }


@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "LunarVision Backend",
        "environment": os.getenv("RENDER_SERVICE_NAME", "local_development"),
        "python_version": sys.version,
        "opencv_version": cv2.__version__,
        "numpy_version": np.__version__,
        "skimage_version": skimage.__version__,
        "cors_configured": True,
        "directories": {
            "uploads": UPLOADS_DIR.exists(),
            "outputs": OUTPUTS_DIR.exists()
        }
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)

