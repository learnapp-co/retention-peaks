import asyncio
import base64
import cv2
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import logging
from scipy.signal import find_peaks
from src.models.heatmap import heatmap_peaks
from src.services.init_services import init_services

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HeatmapValidator:
    def __init__(self):
        self.processed_count = 0
        self.removed_count = 0
        self.valid_count = 0

    def find_playhead_position(self, img):
        """Find the playhead position in the image."""
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        lower_red1 = np.array([0, 70, 50])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([170, 70, 50])
        upper_red2 = np.array([180, 255, 255])

        mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
        red_mask = cv2.bitwise_or(mask1, mask2)

        contours, _ = cv2.findContours(
            red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        if not contours:
            return None

        red_dot = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(red_dot)
        return x + w // 2  # Return center position

    def analyze_heatmap(self, cropped_image: str) -> tuple[bool, np.ndarray, str]:
        """Analyze the heatmap excluding the playhead area."""
        try:
            # Decode base64 image
            img_data = base64.b64decode(cropped_image)
            nparr = np.frombuffer(img_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if img is None:
                return False, None, "Failed to decode image"

            # Find playhead position
            playhead_center = self.find_playhead_position(img)
            if playhead_center is None:
                return False, None, "Playhead not found"

            # Enhanced image processing
            heatmap_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            heatmap_gray = clahe.apply(heatmap_gray)

            _, mask = cv2.threshold(
                heatmap_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
            )
            column_profile = np.sum(mask, axis=0)
            column_profile = column_profile / (np.max(column_profile) + 1e-6)

            # Enhanced smoothing
            smoothed = np.convolve(column_profile, np.ones(30) / 30, mode="same")
            smoothed[smoothed < np.max(smoothed) * 0.3] = 0

            # Define and apply exclusion zone around playhead
            EXCLUSION_ZONE = 50
            exclusion_mask = np.ones_like(smoothed, dtype=bool)
            exclusion_start = max(0, playhead_center - EXCLUSION_ZONE)
            exclusion_end = min(len(smoothed), playhead_center + EXCLUSION_ZONE)
            exclusion_mask[exclusion_start:exclusion_end] = False

            # Apply exclusion mask
            smoothed_filtered = smoothed.copy()
            smoothed_filtered[~exclusion_mask] = 0

            # Peak detection on filtered signal
            peaks, properties = find_peaks(
                smoothed_filtered,
                height=np.mean(smoothed_filtered[exclusion_mask]) * 1.5,
                distance=50,
                width=10,
                prominence=0.2,
            )

            # Filter peaks
            min_peak_height = np.max(smoothed_filtered) * 0.4
            filtered_peaks = [
                peak
                for i, peak in enumerate(peaks)
                if properties["peak_heights"][i] > min_peak_height
            ]

            return len(filtered_peaks) > 0, smoothed_filtered, "Success"

        except Exception as e:
            return False, None, str(e)

    async def validate_entry(
        self, entry: heatmap_peaks, save_debug_plot: bool = True
    ) -> bool:
        """Validate a single heatmap entry."""
        if not entry.cropped_image:
            logger.info(f"❌ No cropped image for video {entry.video_id}")
            return False

        has_peaks, smoothed_signal, message = self.analyze_heatmap(entry.cropped_image)

        if save_debug_plot and smoothed_signal is not None:
            plt.figure(figsize=(15, 5))
            plt.plot(smoothed_signal, label="Filtered Signal")
            plt.title(f"Heatmap Analysis - Video {entry.video_id}\n{message}")
            plt.legend()
            plt.savefig(f"validation_debug_{entry.video_id}.png")
            plt.close()

        if has_peaks:
            logger.info(f"✅ Valid peaks found for video {entry.video_id}")
            return True

        logger.info("❌ No significant peaks for video {entry.video_id}: {message}")
        return False

    async def process_entries(self, batch_size: int = 100):
        """Process all entries in the database."""
        try:
            total_count = await heatmap_peaks.count()
            logger.info(f"Total entries to process: {total_count}")

            skip = 0
            while True:
                entries = (
                    await heatmap_peaks.find().skip(skip).limit(batch_size).to_list()
                )
                if not entries:
                    break

                for entry in entries:
                    self.processed_count += 1

                    is_valid = await self.validate_entry(entry)
                    if not is_valid:
                        await entry.delete()
                        self.removed_count += 1
                    else:
                        self.valid_count += 1

                    if self.processed_count % 10 == 0:
                        self._log_progress()

                skip += batch_size

            self._log_final_results()

        except Exception as e:
            logger.error("Error processing entries: {str(e)}")
            raise

    def _log_progress(self):
        """Log current progress."""
        logger.info(
            "Progress: Processed {self.processed_count}, "
            "Valid: {self.valid_count}, "
            "Removed: {self.removed_count}"
        )

    def _log_final_results(self):
        """Log final results."""
        logger.info("=" * 50)
        logger.info("Validation Complete!")
        logger.info("Total Processed: {self.processed_count}")
        logger.info("Valid Entries: {self.valid_count}")
        logger.info("Removed Entries: {self.removed_count}")
        logger.info("=" * 50)


async def main():
    try:
        await init_services()
        validator = HeatmapValidator()

        start_time = datetime.now()
        logger.info("Starting heatmap validation...")

        await validator.process_entries(batch_size=100)

        duration = datetime.now() - start_time
        logger.info("Total execution time: {duration}")

    except Exception as e:
        logger.error("Main process failed: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
