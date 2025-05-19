"""Enums for the YouTube API"""

from enum import Enum


class ContentType(str, Enum):
    """Content type enum for YouTube videos"""

    VIDEO = "video"
    SHORT = "short"
    ALL = "all"


class SortBy(str, Enum):
    """Sort options for video results"""

    DATE = "date"
    VIEWS = "views"
    RELEVANCE = "relevance"
    OUTLIER_SCORE = "outlier_score"


class ChannelsSortBy(str, Enum):
    """Sort options for video results"""

    SUBSCRIBERS = "subscribers"
    VIEWS = "views"
    TITLE_ASCENDING = "a-z"
    TITLE_DESCENDING = "z-a"


class TimeFrame(str, Enum):
    """Time frame options for filtering"""

    TODAY = "today"
    THIS_WEEK = "this_week"
    THIS_MONTH = "this_month"
    THIS_YEAR = "this_year"
    ALL_TIME = "all_time"


class VideoStatus(str, Enum):
    """Video status enum"""

    ACTIVE = "active"
    DELETED = "deleted"
    PRIVATE = "private"
    UNLISTED = "unlisted"


class CommentCategory(str, Enum):
    """Enum for comment categories"""

    CONTROVERSIAL = "controversial"
    CRITICAL = "critical"
    APPRECIATIVE = "appreciative"
    MOST_REPLIES = "most_replies"
    HITS = "hits"
    MISSES = "misses"
