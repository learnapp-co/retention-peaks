"""Models for managing video retention peaks.

This module contains the data models for video retention peaks.
"""

from typing import List
from datetime import datetime, UTC
from beanie import Document
from pydantic import BaseModel, Field


class RetentionPeakData(BaseModel):
    timestamp: str
    youtube_url: str
    start_seconds: float
    end_seconds: float


class VideoRetentionPeaksResponse(BaseModel):
    video_id: str
    peaks: List[RetentionPeakData]
    processed_at: datetime
    cropped_image: str = ""  # Optional default for compatibility


class VideoRetentionPeaks(Document):
    video_id: str
    peaks: List[RetentionPeakData]
    processed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    cropped_image: str = Field(default="")

    class Settings:
        name = "heatmap_peaks"
