from __future__ import annotations

"""
FastAPI Entry Point

Initializes the FastAPI application, sets up CORS middleware, includes the API router,
and mounts the static files directory to serve the frontend client.
"""

from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.api.routes import router as api_router
from src.config import HOST, PORT

app = FastAPI(
    title="HDFC Mutual Fund FAQ Assistant API",
    description="Backend API serving the facts-only QA retrieval and generation pipeline.",
    version="1.0.0",
)

# CORS configuration (allows frontend browser communication)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Attach API routes
app.include_router(api_router, prefix="/api")

# Mount Static Frontend Files (if directory exists)
# Path resolution: src/api/main.py -> resolve() -> parent.parent.parent = project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
frontend_dir = PROJECT_ROOT / "frontend"

if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    # When run directly, start the uvicorn development server
    uvicorn.run("src.api.main:app", host=HOST, port=PORT, reload=True)
