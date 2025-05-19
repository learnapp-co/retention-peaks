"""YouTube API service module"""

from typing import List, Dict, Any, Optional
import logging
import re
import asyncio
from fastapi import HTTPException
from redis.asyncio import Redis
from src.models.enums import SortBy
from src.models.requests import SearchRequest
from src.models.responses import VideoResponse
from src.models.workspace import Channel, Video, Workspace
from src.services.search_service import SearchService

logger = logging.getLogger(__name__)


class YouTubeService:
    """Main YouTube service orchestrator"""

    def __init__(self, redis_client: Redis):
        """Initialize with required services"""
        self.redis_client = redis_client
        self.search_service = SearchService(redis_client)

    async def search(self, request: SearchRequest) -> List[VideoResponse]:
        """Search for channels on YouTube with filters."""
        try:
            # Extract search parameters from request
            params = self._extract_search_params(request)

            # Check for YouTube URL in keywords
            if params["keywords"]:
                video_response = await self._check_for_youtube_url(params["keywords"])
                if video_response:
                    return video_response

                # Check for channel name match
                channel_videos = await self._search_by_channel_name(params)
                if channel_videos:
                    x = self._sort_results(channel_videos, params["sortBy"])
                    return self._convert_to_response_objects(x)

            # Get workspace
            workspace = await self._get_workspace(params["workspace_id"])

            # Search videos across all channels in workspace (now in parallel)
            results = await self._search_videos_in_workspace(workspace, params)

            # Apply keyword-based search if needed
            if params["keywords"]:
                results = await self.search_service.search_by_embedding(
                    params["keywords"], results
                )

            # Sort results
            sorted_results = self._sort_results(results, params["sortBy"])

            # Convert to response objects
            return self._convert_to_response_objects(sorted_results)

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Error in search: %s", e)
            raise HTTPException(status_code=500, detail=str(e)) from e

    def _extract_search_params(self, request: SearchRequest) -> Dict[str, Any]:
        """Extract and organize search parameters from request"""
        request_dict = request.model_dump()  # Use model_dump() instead of vars()
        return {
            "workspace_id": request_dict["workspace_id"],
            "keywords": request_dict.get("keywords"),
            "channel_ids": request_dict.get("channel_ids", []),
            "start_date": request_dict.get("start_date"),
            "end_date": request_dict.get("end_date"),
            "content_type": request_dict.get("content_type"),
            "min_views": request_dict.get("min_views"),
            "max_views": request_dict.get("max_views"),
            "min_outlier_score": request_dict.get("min_outlier_score"),
            "max_outlier_score": request_dict.get("max_outlier_score"),
            "sortBy": request_dict.get("sortBy"),
        }

    async def _check_for_youtube_url(
        self, keywords: str
    ) -> Optional[List[VideoResponse]]:
        """Check if keywords contain a YouTube URL and return video if found"""
        youtube_url_patterns = [
            r"(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:watch\?v=|embed\/)|youtu\.be\/)([a-zA-Z0-9_-]{11})",
        ]

        for pattern in youtube_url_patterns:
            match = re.search(pattern, keywords)
            if match:
                video_id = match.group(1)
                logger.info(f"YouTube URL detected, extracting video ID: {video_id}")

                # Find the specific video
                video = await Video.find_one({"video_id": video_id})
                if video:
                    channel = await Channel.find_one({"channel_id": video.channel_id})
                    if channel:
                        video.channel_title = channel.title
                        return [self._create_video_response(video)]
        return None

    async def _get_workspace(self, workspace_id: str) -> Workspace:
        """Get workspace by ID"""
        workspace = await Workspace.get(workspace_id)
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")
        return workspace

    async def _search_by_channel_name(self, params: Dict[str, Any]) -> List[Video]:
        """Search for videos by channel name"""
        keywords = params["keywords"]
        workspace_id = params["workspace_id"]

        # Get workspace
        workspace = await Workspace.get(workspace_id)
        if not workspace:
            return []

        if params.get("channel_ids"):
            # If specific channel IDs are provided, use those (but only if they exist in the workspace)
            workspace_channel_ids = set(workspace.channel_ids)
            channel_ids = [
                cid for cid in params["channel_ids"] if cid in workspace_channel_ids
            ]

            if len(channel_ids) > 5:
                raise HTTPException(
                    status_code=400,
                    detail="Too many channel IDs provided. Maximum allowed is 5.",
                )
        else:
            # Otherwise use all channels in the workspace
            channel_ids = workspace.channel_ids

        # Find channels matching the name
        channels = await Channel.find(
            {
                "title": {"$regex": keywords, "$options": "i"},
                "channel_id": {"$in": channel_ids},
            }
        ).to_list()
        if not channels:
            return []

        # Filter channels to only those in the workspace
        workspace_channel_ids = set(workspace.channel_ids)
        matching_channels = [
            c for c in channels if c.channel_id in workspace_channel_ids
        ]

        if not matching_channels:
            return []

        # Process channels in parallel
        tasks = []
        for channel in matching_channels:
            tasks.append(self._process_channel_videos(channel, params))

        # Wait for all tasks to complete
        channel_results = await asyncio.gather(*tasks)

        # Flatten results
        results = []
        for videos in channel_results:
            if videos:
                results.extend(videos)

        return results

    async def _process_channel_videos(
        self, channel: Channel, params: Dict[str, Any]
    ) -> List[Video]:
        """Process videos for a single channel"""
        # Build query filter for this channel
        query = self._build_query_filter(channel.channel_id, params)

        # Get videos matching query
        channel_videos = await Video.find(query).to_list()

        # Apply outlier score filter
        if channel_videos:
            filtered_videos = self._filter_by_outlier_score(
                channel_videos,
                params["min_outlier_score"],
                params["max_outlier_score"],
            )

            # Add channel title to videos
            for video in filtered_videos:
                video.channel_title = channel.title
                video.channel_icon = channel.thumbnail_url

            return filtered_videos

        return []

    async def _search_videos_in_workspace(
        self, workspace: Workspace, params: Dict[str, Any]
    ) -> List[Video]:
        """Search for videos across all channels in workspace using parallel processing"""
        # Determine which channel IDs to search
        if params.get("channel_ids"):
            # If specific channel IDs are provided, use those (but only if they exist in the workspace)
            workspace_channel_ids = set(workspace.channel_ids)
            channel_ids = [
                cid for cid in params["channel_ids"] if cid in workspace_channel_ids
            ]

            if len(channel_ids) > 5:
                raise HTTPException(
                    status_code=400,
                    detail="Too many channel IDs provided. Maximum allowed is 5.",
                )
        else:
            # Otherwise use all channels in the workspace
            channel_ids = workspace.channel_ids

        # Get all channels first (to avoid duplicate queries)
        channels = await Channel.find({"channel_id": {"$in": channel_ids}}).to_list()

        # Create a mapping for quick lookup
        channel_map = {channel.channel_id: channel for channel in channels}

        # Create tasks for parallel processing
        tasks = []
        for channel_id in channel_ids:
            channel = channel_map.get(channel_id)
            if not channel:
                continue

            tasks.append(self._process_channel_videos(channel, params))

        # Execute all tasks in parallel
        results_list = await asyncio.gather(*tasks)

        # Flatten results
        results = []
        for videos in results_list:
            if videos:
                results.extend(videos)

        return results

    def _build_query_filter(
        self, channel_id: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build MongoDB query filter based on search parameters"""
        query = {"channel_id": channel_id}

        # Date filter
        if params["start_date"] or params["end_date"]:
            date_filter = {}
            if params["start_date"]:
                date_filter["$gte"] = params["start_date"]
            if params["end_date"]:
                date_filter["$lte"] = params["end_date"]
            if date_filter:
                query["published_at"] = date_filter

        # Content type filter
        if params["content_type"] and params["content_type"] != "all":
            query["is_short"] = params["content_type"] == "short"

        # Views filter
        if params["min_views"] is not None or params["max_views"] is not None:
            view_filter = {}
            if params["min_views"] is not None:
                view_filter["$gte"] = params["min_views"]
            if params["max_views"] is not None:
                view_filter["$lte"] = params["max_views"]
            if view_filter:
                query["views"] = view_filter

        return query

    def _filter_by_outlier_score(
        self,
        videos: List[Video],
        min_score: Optional[float],
        max_score: Optional[float],
    ) -> List[Video]:
        """Filter videos by outlier score"""
        if min_score is None and max_score is None:
            return videos

        return [
            video
            for video in videos
            if video.outlier_score is not None
            and (min_score is None or video.outlier_score >= min_score)
            and (max_score is None or video.outlier_score <= max_score)
        ]

    def _sort_results(
        self, results: List[Video], sort_by: Optional[SortBy]
    ) -> List[Video]:
        """Sort results based on sort criteria"""
        if not results or not sort_by:
            return results

        if sort_by == SortBy.VIEWS:
            results.sort(key=lambda x: x.views or 0, reverse=True)
        elif sort_by == SortBy.OUTLIER_SCORE:
            results.sort(key=lambda x: x.outlier_score or 0, reverse=True)
        elif sort_by == SortBy.DATE:
            results.sort(key=lambda x: x.published_at or "", reverse=True)

        return results

    def _convert_to_response_objects(self, results: List[Video]) -> List[VideoResponse]:
        """Convert Video objects to VideoResponse objects"""
        return [self._create_video_response(result) for result in results]

    def _create_video_response(self, video: Video) -> VideoResponse:
        """Create a VideoResponse object from a Video object"""
        return VideoResponse(
            id=video.video_id,
            video_id=video.video_id,
            likes=video.likes,
            channel_id=video.channel_id,
            channel_icon=video.channel_icon,
            comment_count=video.comment_count,
            thumbnails=video.thumbnails,
            is_short=video.is_short or False,
            created_at=video.created_at,
            updated_at=video.updated_at,
            title=video.title,
            outlier_score=video.outlier_score,
            views=video.views,
            description=video.description,
            published_at=video.published_at,
            channel_title=video.channel_title,
            duration=video.duration or 0,
        )
