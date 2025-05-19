"""Video routes"""

from typing import List
from fastapi import APIRouter, Query
from redis.asyncio import Redis
from ..services.video_service import VideoService
from ..models.responses import (
    CommentPhrasesResponse,
    VideoResponse,
    VideoTranscriptResponse,
)


router = APIRouter(prefix="/api/videos", tags=["Videos"])

video_service: VideoService = None


def init_routes(redis_client: Redis) -> APIRouter:
    """Initialize video routes"""
    global video_service
    video_service = VideoService(redis_client)
    print(f"Router base path: {router.prefix}")
    print(f"Available routes: {[route.path for route in router.routes]}")
    print("Video services initialized successfully")
    return router


@router.get(
    "/{video_id}",
    response_model=VideoResponse,
    summary="Get video details",
    description="Get detailed information about a YouTube video",
)
async def get_video(video_id: str) -> VideoResponse:
    """Get video details"""
    return await video_service.get_video(video_id)


@router.get(
    "/channel/{channel_id}",
    response_model=List[VideoResponse],
    summary="Get channel videos",
    description="Get all videos from a specific channel with pagination and sorting",
)
async def get_channel_videos(
    channel_id: str,
    limit: int = Query(50, ge=1, le=100, description="Number of videos to return"),
    offset: int = Query(0, ge=0, description="Number of videos to skip"),
    sort_by: str = Query("published_at", description="Field to sort by"),
    sort_order: int = Query(
        -1, ge=-1, le=1, description="Sort order (-1 for desc, 1 for asc)"
    ),
) -> List[VideoResponse]:
    """Get videos for a channel"""
    return await video_service.get_channel_videos(
        channel_id, limit=limit, offset=offset, sort_by=sort_by, sort_order=sort_order
    )


@router.get(
    "/{video_id}/transcript",
    response_model=VideoTranscriptResponse,
    summary="Get video transcript",
    description="Get the transcript of a specific video if available and processing is completed",
    responses={
        200: {
            "description": "Successfully retrieved video transcript",
            "content": {
                "application/json": {
                    "example": {
                        "video_id": "abc123xyz",
                        "title": "Sample Video Title",
                        "transcript": "{text:This is a sample transcript of the video content...,start:0.11,end:10.22}",
                    }
                }
            },
        },
        404: {
            "description": "Video not found or transcript not available",
            "content": {
                "application/json": {
                    "example": {"detail": "Video not found or transcript not available"}
                }
            },
        },
    },
)
async def get_video_transcript(
    video_id: str,
) -> VideoTranscriptResponse:
    """Get transcript for a specific video if available"""
    return await video_service.get_video_transcript(video_id)


@router.get(
    "/{video_id}/comments/phrases",
    response_model=CommentPhrasesResponse,
    summary="Get video comments phrases",
    description="Extract meaningful phrases and concepts from video comments with scoring",
    responses={
        200: {
            "description": "Successfully extracted phrases from comments",
            "content": {
                "application/json": {
                    "example": {
                        "video_id": "abc123xyz",
                        "title": "Sample Video Title",
                        "phrases": [
                            {
                                "phrase": "financial independence",
                                "score": 85,
                                "mentions": 12,
                            },
                            {"phrase": "emergency fund", "score": 67, "mentions": 8},
                            {"phrase": "index investing", "score": 52, "mentions": 6},
                        ],
                    }
                }
            },
        },
        404: {
            "description": "Video not found or no comments available",
            "content": {
                "application/json": {
                    "example": {"detail": "Comments not available for this video"}
                }
            },
        },
    },
)
async def comments_phrases(video_id: str):
    """Extract meaningful phrases and concepts from video comments with scoring"""
    return await video_service.comments_phrases(video_id)


@router.get(
    "/{video_id}/transcripts/phrases",
    response_model=CommentPhrasesResponse,
    summary="Get video transcript phrases",
    description="Extract meaningful phrases and concepts from video transcript with scoring",
    responses={
        200: {
            "description": "Successfully extracted phrases from transcript",
            "content": {
                "application/json": {
                    "example": {
                        "video_id": "abc123xyz",
                        "title": "Sample Video Title",
                        "phrases": [
                            {"phrase": "compound interest", "score": 90, "mentions": 9},
                            {
                                "phrase": "dollar cost averaging",
                                "score": 70,
                                "mentions": 7,
                            },
                            {
                                "phrase": "retirement planning",
                                "score": 60,
                                "mentions": 6,
                            },
                        ],
                    }
                }
            },
        },
        404: {
            "description": "Video not found or transcript not available",
            "content": {
                "application/json": {
                    "example": {"detail": "Transcript not available for this video"}
                }
            },
        },
    },
)
async def transcripts_phrases(video_id: str):
    """Extract meaningful phrases and concepts from video transcript with scoring"""
    return await video_service.transcripts_phrases(video_id)
