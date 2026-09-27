"""
API Routes for LunarVision Benchmark Reporting (Phase 1)
Exposes endpoints to query benchmark execution summaries.
"""

import json
from pathlib import Path
from typing import Dict, Any
from fastapi import APIRouter, HTTPException

try:
    from backend import config
except ImportError:
    import config


router = APIRouter()


@router.get("/summary")
async def get_benchmark_summary() -> Dict[str, Any]:
    """
    Returns the latest benchmark summary JSON.
    Searches standard output directories for summary.json.
    """
    candidate_locations = [
        config.DEFAULT_RESULTS_DIR / "summary.json",
        config.PROJECT_ROOT / "results" / "summary.json",
        Path("results") / "summary.json",
        config.OUTPUTS_DIR / "summary.json",
    ]

    for candidate in candidate_locations:
        if candidate.exists():
            try:
                with open(candidate, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return data
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to read benchmark summary file: {e}"
                )

    raise HTTPException(
        status_code=404,
        detail="No benchmark summary found. Run the benchmark to generate summary.json."
    )
