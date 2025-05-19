from datetime import datetime
from typing import List, Optional
from beanie import Document
from pydantic import BaseModel


class VideoResult(BaseModel):
    """VideoResult"""

    def __getitem__(self, item):
        return getattr(self, item)

    id: str
    title: str
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    published_at: Optional[str] = None
    channel_title: Optional[str] = None


class SearchHistory(Document):
    """SearchHistory"""

    query: str
    results: List[VideoResult]
    created_at: datetime = datetime.now()
    user_id: Optional[str] = None

    class Settings:
        """Settings"""

        name = "search_history"
        indexes = ["query", "created_at", ["user_id", "created_at"]]
