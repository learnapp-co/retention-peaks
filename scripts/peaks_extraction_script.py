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
        self,
        skip: int = 0,
        limit: int = 1000,
        min_age_days: int = 4,
        max_age_days: int = 15,
    ):
        """
        Process videos in batches with skip and limit support

        Args:
            skip: Number of videos to skip
            limit: Maximum number of videos to process (None for all)
            min_age_days: Minimum age of videos in days
            max_age_days: Maximum age of videos in days for reprocessing
        """
        try:
            current_time = datetime.now(timezone.utc)
            min_cutoff_date = current_time - timedelta(days=min_age_days)
            max_cutoff_date = current_time - timedelta(days=max_age_days)

            total_videos = await Video.count()
            processed_videos = (
                await self._get_processed_videos()
            )  # Changed to get full documents

            print(f"Total videos in database: {total_videos}")
            print(f"Already processed videos: {len(processed_videos)}")
            print(
                f"Looking for videos between ages: {min_age_days} and {max_age_days} days"
            )

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

            # Create processed videos lookup for quick access
            processed_lookup = {doc.video_id: doc for doc in processed_videos}

            video_cursor = (
                Video.find(query).skip(skip if skip else 0).limit(limit if limit else 0)
            )

            videos = await video_cursor.to_list()
            batch_size = len(videos)

            # ... rest of the setup code remains the same ...

            processed_count = 0
            for idx, video in enumerate(videos, 1):
                try:
                    # Get published date
                    if not video.published_at:
                        print(
                            f"⏭️ Skipping video {video.video_id} - missing publish date"
                        )
                        continue

                    published_at = (
                        parse(video.published_at)
                        if isinstance(video.published_at, str)
                        else video.published_at
                    )
                    if published_at.tzinfo is None:
                        published_at = published_at.replace(tzinfo=timezone.utc)

                    video_age = current_time - published_at
                    print("video_age: ", video_age)

                    # Check if video is too recent
                    if published_at >= min_cutoff_date:
                        print(f"⏭️ Skipping video {video.video_id} - too recent")
                        continue

                    # Check if video is already processed
                    if video.video_id in processed_lookup:
                        processed_doc = processed_lookup[video.video_id]
                        if processed_doc.no_peaks:
                            print(f"⏭️ Skipping video {video.video_id} - no peaks")
                            continue
                        if (
                            hasattr(processed_doc, "stop_reprocess")
                            and processed_doc.stop_reprocess
                        ):
                            print(
                                f"⏭️ Skipping video {video.video_id} - reprocessing stopped"
                            )
                            continue

                        # If video is older than max age, mark it to stop reprocessing
                        if published_at <= max_cutoff_date:
                            processed_doc.stop_reprocess = True
                            await processed_doc.save()
                            print(
                                f"⏭️ Skipping video {video.video_id} - exceeded max age"
                            )
                            continue

                    print(
                        f"Processing video {video.video_id} ({idx}/{batch_size}) "
                        f"[Overall: {skip + idx}/{total_count}]"
                    )

                    peaks, base64_image = await self.heatmap_service.extract_peaks(
                        video.video_id, True
                    )

                    if peaks and base64_image:

                        processed_count += 1
                        current_total = await self.get_total_processed_count()
                        print(
                            f"✅ Processed video: {video.video_id} (Total processed: {current_total})"
                        )
                    else:
                        print(f"❌ No peaks found for: {video.video_id}")

                except Exception as e:
                    print(f"Failed to process video {video.video_id}: {str(e)}")
                    continue

            success_rate = (processed_count / batch_size) * 100 if batch_size > 0 else 0
            final_total = current_total + processed_count
            print(
                f"Batch complete: {processed_count}/{batch_size} processed "
                f"successfully ({success_rate:.1f}%)"
            )
            print(f"Total videos processed successfully: {final_total}")

        except Exception as e:
            print(f"Batch processing error: {str(e)}")
            raise

    async def _get_processed_videos(self):
        """Get list of video IDs that have already been processed"""
        return await heatmap_peaks.find().to_list()

    async def get_total_processed_count(self) -> int:
        """Get total number of successfully processed videos"""
        return await heatmap_peaks.count()

    # async def get_peaks_by_video_id(self, video_id: str) -> heatmap_peaks:
    #     return await heatmap_peaks.find_one({"video_id": video_id})


async def main():
    """Main function to run the batch processing"""
    try:
        # Initialize service
        service = HeatmapBatchService()
        await init_services()
        # await heatmap_peaks.migrate_reprocessed_field()
        print("Migration completed")

        # Process videos in batches of 11150, starting from index 0
        BATCH_SIZE = 11150
        START_FROM = 0

        print(
            f"Starting batch processing: batch_size={BATCH_SIZE}, "
            f"starting_from={START_FROM}"
        )

        await service.process_videos_batch(
            skip=START_FROM, limit=BATCH_SIZE, min_age_days=4, max_age_days=15
        )

        print("Batch processing completed")

    except Exception as e:
        print(f"Main process failed: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
