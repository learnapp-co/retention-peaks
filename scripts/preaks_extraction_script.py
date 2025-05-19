import asyncio
from datetime import datetime, timedelta, timezone
from typing import List
from src.models.workspace import Video
from src.models.heatmap import heatmap_peaks
from src.services.heatmap_extraction import HeatmapExtractionService
from src.services.init_services import init_services
from dateutil.parser import parse


class HeatmapBatchService:
    def __init__(self):
        self.heatmap_service = HeatmapExtractionService()

    async def process_videos_batch(
        self, skip: int = 0, limit: int = 1000, min_age_days: int = 4
    ):
        """
        Process videos in batches with skip and limit support

        Args:
            skip: Number of videos to skip
            limit: Maximum number of videos to process (None for all)
            min_age_days: Minimum age of videos in days
        """
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=min_age_days)
            total_videos = await Video.count()
            processed_ids = await self._get_processed_video_ids()

            print(f"Total videos in database: {total_videos}")
            print(f"Already processed videos: {len(processed_ids)}")
            print(f"Looking for videos older than: {cutoff_date}")

            # Build query
            query = {
                "is_short": False,
            }

            # Get total count
            total_count = await Video.find(query).count()
            if total_count == 0:
                print(f"Videos matching criteria: {total_count}")
                print("No unprocessed videos found")
                return

            # Apply skip and limit
            video_cursor = Video.find(query).skip(skip)
            if limit:
                video_cursor = video_cursor.limit(limit)

            videos = await video_cursor.to_list()
            batch_size = len(videos)

            print(
                f"Processing batch: skip={skip}, limit={limit or 'None'}, "
                f"found {batch_size} videos out of {total_count} total"
            )

            total_processed = await self.get_total_processed_count()
            print(f"Total successfully processed videos so far: {total_processed}")

            processed_count = 0
            for idx, video in enumerate(videos, 1):
                try:
                    if video.video_id in processed_ids:
                        print(f"⏭️ Skipping video {video.video_id} - already processed")
                        continue

                    if not video.published_at:
                        print(
                            f"⏭️ Skipping video {video.video_id} - missing publish date"
                        )
                        continue

                    if isinstance(video.published_at, str):
                        published_at = parse(video.published_at)
                    else:
                        published_at = video.published_at

                    # Fix: Make sure published_at is timezone-aware
                    if published_at.tzinfo is None:
                        published_at = published_at.replace(tzinfo=timezone.utc)

                    if published_at >= cutoff_date:
                        print(f"⏭️ Skipping video {video.video_id} - too recent")
                        continue

                    print(
                        f"Processing video {video.video_id} ({idx}/{batch_size}) "
                        f"[Overall: {skip + idx}/{total_count}]"
                    )

                    peaks, base64_image = await self.heatmap_service.extract_peaks(
                        video.video_id
                    )

                    if peaks and base64_image:
                        processed_count += 1
                        current_total = total_processed + processed_count
                        print(
                            f"✅ Processed video: {video.video_id} (Total processed: {current_total})"
                        )
                    else:
                        print(f"❌ No peaks found for: {video.video_id}")

                except Exception as e:
                    print(f"Failed to process video {video.video_id}: {str(e)}")
                    continue

            success_rate = (processed_count / batch_size) * 100 if batch_size > 0 else 0
            final_total = total_processed + processed_count
            print(
                f"Batch complete: {processed_count}/{batch_size} processed "
                f"successfully ({success_rate:.1f}%)"
            )
            print(f"Total videos processed successfully: {final_total}")

        except Exception as e:
            print(f"Batch processing error: {str(e)}")
            raise

    async def _get_processed_video_ids(self) -> List[str]:
        """Get list of video IDs that have already been processed"""
        processed = await heatmap_peaks.find().to_list()
        return [doc.video_id for doc in processed]

    async def get_total_processed_count(self) -> int:
        """Get total number of successfully processed videos"""
        return await heatmap_peaks.count()


async def main():
    """Main function to run the batch processing"""
    try:
        # Initialize service
        service = HeatmapBatchService()
        await init_services()

        # Process videos in batches of 11150, starting from index 0
        BATCH_SIZE = 11150
        START_FROM = 33451

        print(
            f"Starting batch processing: batch_size={BATCH_SIZE}, "
            f"starting_from={START_FROM}"
        )

        await service.process_videos_batch(
            skip=START_FROM, limit=BATCH_SIZE, min_age_days=4
        )

        print("Batch processing completed")

    except Exception as e:
        print(f"Main process failed: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
