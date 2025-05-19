"""Initialize services"""

import os
import logging
import beanie
from motor.motor_asyncio import AsyncIOMotorClient

# from redis import asyncio as aioredis

from src.models.workspace import Video
from src.models.heatmap import heatmap_peaks  # Import your mode
from src.models.video_retention_peaks import VideoRetentionPeaks

logger = logging.getLogger(__name__)


async def init_services():
    """Initialize services"""
    try:
        # MongoDB connection
        mongo_uri = os.getenv("MONGODB_URI", os.environ.get("MONGODB_URI"))

        client = AsyncIOMotorClient(mongo_uri, tlsAllowInvalidCertificates=True)

        # Test the connection
        await client.admin.command("ping")
        logger.info("Successfully connected to MongoDB")

        # Initialize Beanie with models
        await beanie.init_beanie(
            database=client.youbase,
            document_models=[
                Video,
                heatmap_peaks,
                VideoRetentionPeaks,
            ],
        )
        logger.info("Beanie initialized successfully")

        # # Redis connection (optional for collections testing)
        # try:
        #     redis_url = f"redis://{os.getenv('REDIS_HOST', 'localhost')}:{os.getenv('REDIS_PORT', '6379')}"
        #     redis_client = await aioredis.from_url(redis_url, decode_responses=True)
        #     logger.info("Redis connection successful")
        # except Exception as e:
        #     logger.warning("Redis connection failed (optional):%s", {e})
        #     redis_client = None

        # return redis_client

    except Exception as e:
        logger.error("Failed to initialize services:%s", {e})
        raise
