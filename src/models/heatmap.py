from datetime import datetime, UTC
from beanie import Document
from pydantic import BaseModel, Field
from typing import List


class PeakData(BaseModel):
    timestamp: str
    youtube_url: str
    start_seconds: float
    end_seconds: float


class HeatmapResponse(BaseModel):
    video_id: str
    peaks: List[PeakData]
    processed_at: datetime
    cropped_image: str = ""  # Optional default for compatibility
    reprocessed: bool = False


class heatmap_peaks(Document):
    video_id: str
    peaks: List[PeakData]
    processed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    cropped_image: str = Field(default="")
    reprocessed: bool = False

    class Settings:
        name = "heatmap_peaks"
