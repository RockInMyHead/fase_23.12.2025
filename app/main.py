"""
FaceRelis - Modern Face Recognition Application

Main FastAPI application with clean architecture
"""
import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from .core.config import settings
from .core.logging import setup_logging, get_logger
from .api.routes import files, clustering, tasks
from .models.schemas import DriveInfoResponse
from .utils.file_utils import get_logical_drives

# Setup logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager"""
    logger.info("Starting FaceRelis application")

    # Startup tasks
    yield

    # Shutdown tasks
    logger.info("Shutting down FaceRelis application")


# Create FastAPI application
app = FastAPI(
    title="FaceRelis",
    description="Modern Face Recognition and Clustering Application",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_path = Path(__file__).parent.parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Include API routes - order matters for path matching
# More specific routes first
app.include_router(
    files.router,
    prefix="/api",
    tags=["files"]
)

app.include_router(
    clustering.router,
    prefix="/api",
    tags=["clustering"]
)

app.include_router(
    tasks.router,
    prefix="/api/task",
    tags=["tasks"]
)


@app.get("/", response_class=HTMLResponse)
async def get_index():
    """Serve main application page"""
    try:
        index_path = static_path / "index.html"
        if index_path.exists():
            return HTMLResponse(content=index_path.read_text(encoding='utf-8'))
        else:
            return HTMLResponse(content="<h1>FaceRelis</h1><p>Application is starting...</p>")
    except Exception as e:
        logger.error(f"Failed to serve index page: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/drives", response_model=List[DriveInfoResponse])
async def get_drives():
    """Get available drives"""
    try:
        drives = get_logical_drives()
        return [
            DriveInfoResponse(
                name=drive["name"],
                path=drive["path"]
            )
            for drive in drives
        ]
    except Exception as e:
        logger.error(f"Failed to get drives: {e}")
        raise HTTPException(status_code=500, detail="Failed to get drives")


@app.get("/favicon.ico")
async def favicon():
    """Serve favicon"""
    return {"detail": "No favicon available"}


@app.get("/__routes", include_in_schema=False)
def __routes():
    """Debug endpoint to list all registered routes"""
    out = []
    for r in app.router.routes:
        methods = sorted(list(getattr(r, "methods", []) or []))
        out.append({
            "path": getattr(r, "path", ""),
            "methods": methods,
            "name": getattr(r, "name", "")
        })
    return out


@app.api_route("/preview", methods=["GET", "HEAD"], include_in_schema=False)
@app.api_route("/preview/", methods=["GET", "HEAD"], include_in_schema=False)
async def preview_alias(request: Request):
    """
    Alias for /api/image/preview to support legacy frontend requests
    Redirects /preview?... to /api/image/preview?...
    """
    qs = str(request.query_params)
    if not qs:
        return JSONResponse(status_code=400, content={"detail": "Missing query params"})

    return RedirectResponse(url=f"/api/image/preview?{qs}", status_code=307)


if __name__ == "__main__":
    import uvicorn

    logger.info(f"Starting server on {settings.host}:{settings.port}")
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info"
    )
