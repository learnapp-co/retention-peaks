"""BaseModel"""

from os import stat
from typing import Dict, List, Optional, Any
from datetime import datetime
from httpx._transports import default
from pydantic import BaseModel, Field

from src.models import collection
from src.models.workspace import (
    Bookmark,
    Channel,
    ChannelStats,
    Comment,
    Transcript,
    Video,
    Workspace,
)
from src.routes import outlier_routes


class VideoResponse(BaseModel):
    """VideoResponse"""

    def __getitem__(self, key):
        return getattr(self, key)

    id: str
    video_id: str
    channel_id: str
    channel_title: Optional[str] = None
    channel_icon: Optional[str] = None
    title: str
    description: str
    published_at: str | datetime
    views: int
    likes: int
    transcript: Optional[List[Transcript]] = None
    transcript_status: Optional[str] = None
    comment_count: int
    outlier_score: Optional[float] = None
    thumbnails: List[str]
    duration: Optional[int] = Field(default=0)
    is_short: Optional[bool] = Field(default=False)
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_video(
        cls, video: Video, channel_title: str | None, channel_icon: str | None
    ) -> "VideoResponse":
        """from_video"""
        return cls(
            id=str(video.id),
            video_id=video.video_id,
            channel_id=video.channel_id,
            channel_title=channel_title,
            channel_icon=channel_icon,
            title=video.title,
            description=video.description,
            published_at=video.published_at,
            views=video.views,
            likes=video.likes,
            comment_count=video.comment_count,
            outlier_score=(0 if video.outlier_score is None else video.outlier_score),
            thumbnails=video.thumbnails,
            duration=video.duration,
            is_short=video.is_short,
            transcript_status=video.transcript_status,
            created_at=video.created_at,
            updated_at=video.updated_at,
        )


class ChannelResponse(BaseModel):
    """ChannelResponse"""

    def __getitem__(self, key):
        return getattr(self, key)

    id: str
    channel_id: str
    handle: str
    title: str
    banner: str
    stats_history: List[ChannelStats]
    description: str
    category: Optional[str] = None
    language: Optional[str] = None
    thumbnail_url: str
    country: Optional[str]
    subscriber_count: int  # Changed from subscribers
    video_count: int  # Changed from videos
    view_count: int  # Changed from views
    published_at: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_channel(cls, channel: Channel) -> "ChannelResponse":
        """from_channel"""
        return cls(
            id=str(channel.id),
            channel_id=channel.channel_id,
            handle=channel.handle,
            title=channel.title,
            description=channel.description,
            category=channel.category,
            language=channel.language,
            thumbnail_url=channel.thumbnail_url,
            stats_history=channel.stats_history,
            banner=channel.banner,
            country=channel.country,
            subscriber_count=channel.subscribers,  # Map from database field
            video_count=channel.videos,  # Map from database field
            view_count=channel.views,  # Map from database field
            published_at=channel.published_at,
            created_at=channel.created_at,
            updated_at=channel.updated_at,
        )


class WorkspaceResponse(BaseModel):
    """WorkspaceResponse"""

    def __getitem__(self, key):
        return getattr(self, key)

    id: str
    name: str
    channel_ids: List[str]
    collection_ids: Optional[List[str]] = []
    bookmarks: Dict[str, Bookmark]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_workspace(cls, workspace: Workspace) -> "WorkspaceResponse":
        """from_workspace"""
        return cls(
            id=str(workspace.id),
            name=workspace.name,
            channel_ids=workspace.channel_ids,
            collection_ids=workspace.collection_ids,
            bookmarks=workspace.bookmarks,
            created_at=workspace.created_at,
            updated_at=workspace.updated_at,
        )


class CommentResponse(BaseModel):
    """Response model for comments"""

    id: str
    comment_id: str
    video_id: str
    text: str
    published_at: datetime
    likes: int
    reply_count: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_comment(cls, comment: Comment) -> "CommentResponse":
        return cls(
            id=str(comment.id),
            comment_id=comment.comment_id,
            video_id=comment.video_id,
            text=comment.text,
            published_at=comment.published_at,
            likes=comment.likes,
            reply_count=comment.reply_count,
            created_at=comment.created_at,
            updated_at=comment.updated_at,
        )


class CollectionSearchResponse(BaseModel):
    """Response model for collection search results"""

    video_id: str
    title: str
    metadata: Dict[str, Any]
    outlier_score: Optional[float] = Field(default=0.00)
    published_at: datetime | str
    channel_title: Optional[str] = None
    views: int

    class Config:
        json_schema_extra = {
            "example": {
                "video_id": "video123",
                "title": "Ancient Philosophy Explained",
                "metadata": {
                    "title": "Ancient Philosophy Explained",
                    "comments": ["Great explanation!", "Very informative"],
                    "transcript": "In this video, we explore ancient philosophy...",
                    "retention_peaks": [120, 240, 360],
                    "thumbnail_text": "Ancient Philosophy",
                },
                "relevance_score": 0.85,
                "matched_prompt": "This video discusses ancient philosophy concepts in detail",
            }
        }


from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class LineStyle(BaseModel):
    type: Optional[str] = None


class AreaStyle(BaseModel):
    pass


class SeriesItem(BaseModel):
    name: str
    type: str
    data: List[float]
    symbol: Optional[str] = None
    symbolSize: Optional[int] = None
    lineStyle: Optional[LineStyle] = None
    areaStyle: Optional[AreaStyle] = None


class AxisModel(BaseModel):
    type: str
    name: Optional[str] = None
    data: Optional[List[int]] = None


class TitleModel(BaseModel):
    text: str


class TooltipModel(BaseModel):
    trigger: str


class LegendModel(BaseModel):
    data: List[str]


class VideoStats(BaseModel):
    engagement_rate: float
    views_per_hour: float
    comments_to_view_ratio: float
    like_to_view_ratio: float


class PerformanceChartResponse(BaseModel):
    title: TitleModel
    tooltip: TooltipModel
    legend: LegendModel
    xAxis: AxisModel
    yAxis: AxisModel
    series: List[SeriesItem]
    stats: VideoStats


# Add this to your existing responses.py
class VideoTranscriptResponse(BaseModel):
    video_id: str
    title: str
    transcript: List[Transcript]

    class Config:
        json_schema_extra = {
            "example": {
                "video_id": "abc123xyz",
                "title": "Sample Video Title",
                "transcript": "This is a sample transcript of the video content...",
            }
        }


class ChannelNameResponse(BaseModel):
    """Response model for a channel"""

    channel_id: str
    title: str


# Add this to your existing responses.py file

from typing import List, Dict
from pydantic import BaseModel


class CommentData(BaseModel):
    text: str
    likes: int
    published_at: str
    replies: int


class TranscriptData(BaseModel):
    text: str
    start: float
    end: float


class CommentPhrase(BaseModel):
    phrase: str
    score: int
    mentions: int
    commentData: List[CommentData] | None = None
    transcriptData: List[TranscriptData] | None = None


class CommentPhrasesResponse(BaseModel):
    """Response model for comment phrases analysis"""

    video_id: str
    title: str
    phrases: List[CommentPhrase]


import json
from typing import TypedDict, List, Literal, Union, Any


# -----------------------------------------------------------------------------
# 1) The payload your tool returns, stringified in `content`:
# -----------------------------------------------------------------------------
class Source(TypedDict):
    index: int
    title: str
    video_id: str
    url: str


class KnowledgeBaseContent(TypedDict):
    Answer: str
    Sources: List[Source]


# -----------------------------------------------------------------------------
# 2) The various message shapes in response["messages"]
# -----------------------------------------------------------------------------
class CommonMessageFields(TypedDict, total=False):
    name: None
    id: str
    additional_kwargs: dict
    response_metadata: dict


class HumanMessage(TypedDict):
    type: Literal["human"]
    content: str
    example: bool
    # plus the common fields
    name: None
    id: str
    additional_kwargs: dict
    response_metadata: dict


class AIMessage(TypedDict, total=False):
    type: Literal["ai"]
    content: str
    example: bool
    tool_calls: List[Any]
    invalid_tool_calls: List[Any]
    usage_metadata: Any
    # plus the common fields
    name: None
    id: str
    additional_kwargs: dict
    response_metadata: dict


class ToolMessage(TypedDict):
    type: Literal["tool"]
    name: str  # "knowledge-base"
    tool_call_id: str  # e.g. "call_xxx"
    content: str  # <<< here goes json.dumps(KnowledgeBaseContent)
    artifact: Any
    status: str
    # plus the common fields
    id: str
    additional_kwargs: dict
    response_metadata: dict


Message = Union[HumanMessage, AIMessage, ToolMessage]


class ServiceResponse(TypedDict):
    response: dict
    # response["messages"] is a List[Message]
    # you can be more explicit if you like:
    # response: TypedDict('Inner', {'messages': List[Message]})
