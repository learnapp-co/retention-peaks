import os
import sys

from beanie import PydanticObjectId

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services import embedding_service, init_services
from src.models.workspace import Channel, Video
import asyncio


async def generate_all_embeddings():
    await init_services.init_services()
    channel_ids = [
            "67ee8f52c548c07496d577e3",
            "67ee9275c548c07496d577f2",
            "67ee9403c548c07496d577fe",
            "67ee93e0c548c07496d577fc",
            "67ee94b1c548c07496d57802",
            "67efe1c9c548c07496d57809",
            "67efe8d7c548c07496d57822",
            "67efe24cc548c07496d5780d",
            "67ee8bf8c548c07496d577d6",
            "67ee91c6c548c07496d577ec",
            "67faa6b2d788270ce0a17f1c",
            "67ee8c73c548c07496d577d7",
            "67efe8f8c548c07496d57823",
            "67ee9240c548c07496d577ef",
            "67fe4d1dd7715318a453c945",
            "67ef885fc548c07496d57803",
            "67ee8d2cc548c07496d577d9",
            "67efe1b4c548c07496d57808"
        ]
    channels = await Channel.find({}).to_list()
    print(f"Found {len(channels)} channels")
    
    total_processed_count = 0
    total_videos_count = 0
    
    for channel in channels:
        videos = await Video.find({"channel_id":channel.channel_id}).to_list()
        print(f"Processing channel: {channel.channel_id}")
        print(f"Found {len(videos)} videos")
        total_videos = len(videos)
        total_videos_count += total_videos

        # Limit concurrent API calls
        semaphore = asyncio.Semaphore(100)
        embedding_service_instance = embedding_service.EmbeddingService()

        async def process_video(video):
            async with semaphore:
                if not hasattr(video, "embedding") or video.embedding is None:
                    print(f"Generating embedding for video {video.video_id}")
                    return await embedding_service_instance.store_video_embedding(video)
                return False

        # Process in batches of 50
        batch_size = 50
        processed_count = 0

        for i in range(0, total_videos, batch_size):
            batch = videos[i : i + batch_size]
            results = await asyncio.gather(*[process_video(video) for video in batch])
            processed_count += sum(1 for r in results if r)
            print(
                f"Processed batch {i//batch_size + 1}/{(total_videos + batch_size - 1)//batch_size}"
            )
        
        total_processed_count += processed_count
        print(f"Finished processing channel. Processed {processed_count} out of {total_videos} videos.")

    print(
        f"\nEmbedding generation complete. Total processed: {total_processed_count} out of {total_videos_count} videos."
    )


if __name__ == "__main__":
    asyncio.run(generate_all_embeddings())
