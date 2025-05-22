"""Video retention peaks service for managing YouTube videos"""

from fastapi import HTTPException
from src.models.video_retention_peaks import (
    VideoRetentionPeaks,
    VideoRetentionPeaksResponse,
)


class VideoRetentionPeakService:
    """Service for managing YouTube videos retention peaks"""

    def __init__(
        self,
    ):
        """Initialize video retention peaks service"""

    async def get_video_retention_peak(
        self, video_id: str
    ) -> VideoRetentionPeaksResponse:
        """Get video retention peaks by video ID"""
        video_retention_peaks = await VideoRetentionPeaks.find_one(
            {"video_id": video_id}
        )

        if not video_retention_peaks:
            raise HTTPException(
                status_code=404, detail="Video retention peaks not found"
            )

        return video_retention_peaks
