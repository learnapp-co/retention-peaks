"""
main.py
"""

import logging
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv

from .routes import (
    heatmap,
    video_retention_peaks,
)
from .services.init_services import init_services

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


app = FastAPI(
    title="YouTube Search Bot",
    description="A Python-based YouTube search bot using FastAPI and YouTube Data API v3",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    redirect_slashes=False,
)

# Initialize CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Add a simple health check endpoint that doesn't depend on database connection
@app.get("/health", include_in_schema=False)
async def health_check():
    return {"status": "ok"}


# Initialize services on startup
@app.on_event("startup")
async def startup_event():
    print("All services initialized successfully")
    logger.info("Starting application...")

    try:
        # Initialize Redis and other services
        await init_services()

        # Initialize and include all routers
        app.include_router(heatmap.init_routes())
        app.include_router(video_retention_peaks.init_routes())

        logger.info("All services initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing services: {str(e)}")
        # Still allow the application to start even if services fail
        # This way the health check endpoint will still work


# Add CORS middleware to the FastAPI ap
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Run with Uvicorn
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        timeout_keep_alive=120,
    )
