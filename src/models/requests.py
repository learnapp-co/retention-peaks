"""Search request parameters with validations"""

from datetime import datetime
from typing import Optional, List, Literal
from fastapi import HTTPException
from pydantic import BaseModel, Field, field_validator

from src.models.enums import ContentType, SortBy


class SearchRequest(BaseModel):
    """Search request parameters with validations"""

    workspace_id: str = Field(..., description="Workspace ID for the channel")
    channel_ids: Optional[List[str]] = Field(
        None, description="List of channel IDs to search within"
    )
    keywords: Optional[str] = Field(None, description="Search keywords")
    start_date: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="End date (YYYY-MM-DD)")
    content_type: Optional[ContentType] = Field(
        None,
        description="Filter by content type (video, short, all)",
    )
    min_views: Optional[int] = Field(None, description="Minimum view count", ge=0)
    max_views: Optional[int] = Field(None, description="Maximum view count", ge=0)
    min_outlier_score: Optional[float] = Field(
        None, description="Minimum outlier score"
    )
    max_outlier_score: Optional[float] = Field(
        None, description="Maximum outlier score"
    )
    sortBy: Optional[SortBy] = Field(None, description="Sort by field")
    collection_id: Optional[str] = Field(
        None, description="Search within a specific collection"
    )

    @field_validator("content_type")
    def validate_content_type(cls, v):
        if v and v not in ["video", "short", "all"]:
            raise HTTPException(
                status_code=400, detail="content_type must be one of: video, short, all"
            )
        return v

    @field_validator("start_date", "end_date")
    def validate_date_format(cls, v):
        if v:
            try:
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid date format: {v}. Date must be in YYYY-MM-DD format",
                ) from e
        return v


class CollectionSearchRequest(BaseModel):
    """Request model for searching within collections"""

    collection_id: str
    prompt: Optional[str] = None
    title: Optional[bool] = Field(
        default=False, description="Include title in search and response"
    )
    description: Optional[bool] = Field(
        default=False, description="Include description in search and response"
    )
    comments: Optional[bool] = Field(
        default=False, description="Include comments in search and response"
    )
    fullTranscript: Optional[bool] = Field(
        default=False, description="Include full transcript in search and response"
    )
    introTranscript: Optional[bool] = Field(
        default=False, description="Include intro transcript in search and response"
    )
    outroTranscript: Optional[bool] = Field(
        default=False, description="Include outro transcript in search and response"
    )
    retentionPeaks: Optional[bool] = Field(
        default=False, description="Include retention peaks in search and response"
    )
    thumbnailText: Optional[bool] = Field(
        default=False, description="Include thumbnail text in search and response"
    )
    thumbnail: Optional[bool] = Field(
        default=False, description="Include thumbnail in search and response"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "collection_id": "your-collection-id",
                "prompt": "Find videos about ancient philosophy",
                "title": True,
                "description": True,
                "comments": True,
                "fullTranscript": True,
                "introTranscript": True,
                "outroTranscript": True,
                "retentionPeaks": True,
                "thumbnailText": True,
                "thumbnail": True,
            }
        }
