"""Video Retention Peaks routes"""

from typing import List
from fastapi import APIRouter
from redis.asyncio import Redis
from ..models.video_retention_peaks import (
    VideoRetentionPeaksResponse,
)
from ..services.video_retention_peaks_service import VideoRetentionPeakService


router = APIRouter(prefix="/api/video-retention-peaks", tags=["Video Retention Peaks"])

video_retention_peaks_service: VideoRetentionPeakService = None


def init_routes() -> APIRouter:
    """Initialize video retention peaks routes"""
    global video_retention_peaks_service
    video_retention_peaks_service = VideoRetentionPeakService()
    print(f"Router base path: {router.prefix}")
    print(f"Available routes: {[route.path for route in router.routes]}")
    print("Video Retention Peaks services initialized successfully")
    return router


@router.get(
    "/{video_id}",
    response_model=VideoRetentionPeaksResponse,
    summary="Get video retention peaks details",
    description="Get detailed information about a YouTube video retention peaks",
)
async def get_video(video_id: str) -> VideoRetentionPeaksResponse:
    """Get video retention peak details"""
    return await video_retention_peaks_service.get_video_retention_peak(video_id)
