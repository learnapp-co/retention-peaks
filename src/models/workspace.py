"""Models for managing workspaces and channels in the application.

This module contains the data models for workspaces and channels,
including creation and storage models.
"""

from typing import Dict, List, Optional
from datetime import datetime
from beanie import Document
from pydantic import BaseModel, Field


class Bookmark(BaseModel):
    name: str
    url: str
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "bookmarks"


class ChannelStats(BaseModel):
    """Channel statistics at a point in time"""

    date: datetime | str = Field(description="Date of the stats")
    subscribers: int = Field(default=0)
    views: int = Field(default=0)
    videos: int = Field(default=0)

    @classmethod
    def validate_date(cls, v):
        """Convert various date formats to datetime"""
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v.replace("Z", "+00:00"))
            except ValueError:
                try:
                    # Handle JavaScript date string format
                    return datetime.strptime(v, "%a %b %d %Y %H:%M:%S GMT%z")
                except ValueError:
                    raise ValueError(f"Invalid date format: {v}")
        return v


class Channel(Document):
    """YouTube channel model"""

    channel_id: str
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    language: Optional[str] = None
    thumbnail_url: Optional[str] = None
    country: Optional[str] = None
    handle: Optional[str] = None
    subscribers: int = Field(default=0)
    videos: int = Field(default=0)
    views: int = Field(default=0)
    published_at: str
    banner: Optional[str] = Field(default=None)
    long_video_count: int
    short_video_count: int
    long_video_view_count: int
    short_video_view_count: int
    stats_history: List[ChannelStats] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=datetime.now)
    created_at: datetime = Field(default_factory=datetime.now)

    @classmethod
    def model_validate(cls, obj: dict):
        """Handle MongoDB NumberLong format"""
        if isinstance(obj.get("views"), dict) and "$numberLong" in obj["views"]:
            obj["views"] = int(obj["views"]["$numberLong"])
        if (
            isinstance(obj.get("subscribers"), dict)
            and "$numberLong" in obj["subscribers"]
        ):
            obj["subscribers"] = int(obj["subscribers"]["$numberLong"])
        if isinstance(obj.get("videos"), dict) and "$numberLong" in obj["videos"]:
            obj["videos"] = int(obj["videos"]["$numberLong"])
        return super().model_validate(obj)

    # Optional Fields for testing -

    # channel_id: str
    # title: Optional[str] = None
    # handle: Optional[str] = None
    # description: Optional[str] = None
    # country: Optional[str] = None
    # thumbnail_url: Optional[str] = None
    # banner_url: Optional[str] = None
    # subscribers: Optional[int] = 0
    # views: Optional[int] = 0
    # videos: Optional[int] = 0
    # published_at: Optional[datetime] = None

    class Settings:
        """Settings for the Channel document."""

        name = "channels"


class WorkspaceCreate(BaseModel):
    """Model for creating a new workspace.

    Attributes:
        name: Name of the workspace
        channel_ids: List of channel IDs to include in the workspace
    """

    name: str
    channel_ids: List[str] = []


class WorkspaceUpdateReq(BaseModel):
    """Model for updating an existing workspace.
    Attributes:
        name: New name for the workspace
        channel_ids: New list of channel IDs to include in the workspace
    """

    name: Optional[str] = None
    channel_ids: Optional[List[str]] = None
    collection_ids: Optional[List[str]] = None


class Workspace(Document):
    """Database model for storing workspace information.

    Attributes:
        name: Name of the workspace
        channel_ids: List of channel IDs included in the workspace
        created_at: Timestamp when the workspace was created
        updated_at: Timestamp when the workspace was last updated
    """

    def __getitem__(self, key):
        """Get an attribute by key."""
        return getattr(self, key)

    name: str
    channel_ids: List[str] = []
    collection_ids: Optional[List[str]] = Field(default=[])
    bookmarks: Dict[str, Bookmark] = {}  # Using dict to ensure unique names
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        """Settings for the Workspace document."""

        name = "workspaces"


# Import Field from Pydantic


class Transcript(BaseModel):
    """Represents a TypeScript type."""

    text: Optional[str] = None
    start: Optional[float] = None
    end: Optional[float] = None


class VideoStatsHist(BaseModel):
    """Represents video statistics."""

    date: datetime
    views: int = Field(default=0)
    likes: int = Field(default=0)
    comment_count: int = Field(default=0)


class Video(Document):
    """Represents a YouTube video with comprehensive information."""

    video_id: str
    channel_id: str
    title: str
    channel_title: Optional[str] = None
    channel_icon: Optional[str] = None
    description: str
    published_at: str | datetime
    views: int
    likes: int
    transcript: Optional[List[Transcript]] = None
    comment_count: int
    transcript_status: Optional[str] = None
    outlier_score: Optional[float] = Field(default=0.00)
    thumbnails: List[str]
    duration: Optional[int] = Field(default=0)  # Made optional with default value
    is_short: Optional[bool] = Field(default=False)  # Made optional with default value
    embedding: Optional[List[float]] = None
    stats_history: Optional[List[VideoStatsHist]] = None
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

    class Settings:
        name = "videos"


class Comment(Document):
    """Represents a YouTube comment"""

    comment_id: str
    video_id: str
    text: str
    published_at: datetime
    likes: int = Field(default=0)
    reply_count: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Settings:
        """Settings for the Comment document."""

        name = "comments"
