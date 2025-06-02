from datetime import datetime, UTC
from beanie import Document
from pydantic import BaseModel, Field
from typing import Optional, List


class PeakData(BaseModel):
    timestamp: str
    youtube_url: str
    start_seconds: float
    end_seconds: float


class HeatmapResponse(BaseModel):
    video_id: str
    peaks: List[PeakData]
    processed_at: datetime
    cropped_image: str = ""
    reprocessed: bool = False
    stop_reprocess: bool = False
    no_peaks: bool = False


class heatmap_peaks(Document):
    video_id: str
    peaks: Optional[List[PeakData]]
    processed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    cropped_image: str = Optional[Field(default="")]
    reprocessed: bool = False
    stop_reprocess: bool = Field(default=False)
    no_peaks: bool = Field(default=False)

    class Settings:
        name = "heatmap_peaks"

    # @classmethod
    # async def migrate_reprocessed_field(cls):
    #     """Fix reprocessed field that might be stored as list"""
    #     collection = cls.get_motor_collection()

    #     # Find all documents where reprocessed is an array
    #     cursor = collection.find({"reprocessed": {"$type": "array"}})

    #     # Update documents directly using MongoDB operations
    #     async for doc in cursor:
    #         reprocessed_value = doc.get("reprocessed", [False])[0]
    #         await collection.update_one(
    #             {"_id": doc["_id"]}, {"$set": {"reprocessed": bool(reprocessed_value)}}
    #         )
    #         print(f"Fixed reprocessed field for document {doc['_id']}")
