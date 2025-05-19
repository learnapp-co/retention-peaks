import asyncio
from datetime import datetime, timezone
from typing import List
from src.models.heatmap import heatmap_peaks, HeatmapResponse
from src.services.heatmap_extraction import HeatmapExtractionService
from src.services.init_services import init_services


class HeatmapReprocessService:
    def __init__(self):
        self.heatmap_service = HeatmapExtractionService()

    async def reprocess_peaks_batch(self, skip: int = 0, limit: int = 100):
        try:
            # Get videos with existing peaks
            query = {"peaks": {"$exists": True, "$not": {"$size": 0}}}

            total_count = await heatmap_peaks.find(query).count()
            if total_count == 0:
                print("No videos found with existing peaks")
                return

            cursor = heatmap_peaks.find(query).skip(skip)
            if limit:
                cursor = cursor.limit(limit)

            videos = await cursor.to_list()

            for idx, video in enumerate(videos, 1):
                video_id = video.video_id
                try:
                    # Check if video has already been reprocessed
                    if hasattr(video, "reprocessed") and video.reprocessed:
                        print(f"⏭️ Skipping {video_id} - already reprocessed")
                        continue

                    print(f"Processing {video_id} ({idx}/{len(videos)})")

                    # Extract peaks with debug mode enabled
                    peaks, base64_image = await self.heatmap_service.extract_peaks(
                        video.video_id, True
                    )
                    if peaks and base64_image:
                        print(f"✅ Updated {video_id} - Found {len(peaks)} peaks")
                    else:
                        print(f"❌ No peaks found for {video_id}")

                except Exception as e:
                    print(f"❌ Error processing {video_id}: {str(e)}")
                    continue

        except Exception as e:
            print(f"❌ Batch processing error: {str(e)}")
            raise


async def main():
    try:
        await init_services()
        service = HeatmapReprocessService()

        BATCH_SIZE = 10600
        START_FROM = 0

        print(
            f"Starting reprocessing: batch_size={BATCH_SIZE}, starting_from={START_FROM}"
        )

        await service.reprocess_peaks_batch(skip=START_FROM, limit=BATCH_SIZE)

        print("✅ Reprocessing completed")

    except Exception as e:
        print(f"❌ Main process failed: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
