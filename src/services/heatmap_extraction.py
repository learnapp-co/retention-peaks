import os
import base64
import cv2
import numpy as np
import traceback
import logging
import asyncio
import json
from datetime import datetime, timezone
from scipy.signal import find_peaks
from playwright.async_api import async_playwright
from playwright_stealth import stealth_sync
from ..models.heatmap import PeakData
from src.models.workspace import Video
from ..models.heatmap import HeatmapResponse, heatmap_peaks
import matplotlib.pyplot as plt
from dotenv import load_dotenv
import random

load_dotenv()


def process_cookies(cookies):
    """Process cookies to ensure they have valid sameSite values"""
    for cookie in cookies:
        if "sameSite" not in cookie or cookie["sameSite"] not in [
            "Strict",
            "Lax",
            "None",
        ]:
            cookie["sameSite"] = "Lax"  # Default to Lax
    return cookies


logger = logging.getLogger(__name__)


class HeatmapExtractionService:

    async def wait_for_heatmap(self, page, max_attempts=15, interval=3000):
        """Wait for heatmap to become visible with detailed logging."""
        logger.info("⏳ Waiting for heatmap to appear...")

        for attempt in range(max_attempts):
            try:
                heatmap_info = await page.evaluate(
                    """() => {
                        const heatmap = document.querySelector('.ytp-heat-map-container');
                        if (!heatmap) return null;
                        
                        const styles = window.getComputedStyle(heatmap);
                        const rect = heatmap.getBoundingClientRect();
                        
                        return {
                            visible: heatmap.offsetParent !== null,
                            display: styles.display,
                            opacity: styles.opacity,
                            dimensions: {
                                width: rect.width,
                                height: rect.height
                            },
                            childCount: heatmap.children.length
                        };
                    }"""
                )

                if heatmap_info:
                    print(f"Attempt {attempt + 1}: Heatmap found with properties:")
                    print(f"📏 Dimensions: {heatmap_info['dimensions']}")
                    print(f"👁️ Display: {heatmap_info['display']}")
                    print(f"🔍 Opacity: {heatmap_info['opacity']}")
                    print(f"🧩 Child elements: {heatmap_info['childCount']}")

                    if (
                        heatmap_info["visible"]
                        and heatmap_info["display"] != "none"
                        and float(heatmap_info["opacity"]) > 0
                        and heatmap_info["dimensions"]["width"] > 0
                    ):

                        logger.info("✅ Heatmap is fully visible and rendered")
                        return True

                print(f"⏳ Attempt {attempt + 1}: Heatmap not fully visible yet")
                await page.wait_for_timeout(interval)

            except Exception as e:
                print(f"⚠️ Attempt {attempt + 1} failed: {str(e)}")
                await page.wait_for_timeout(interval)

        logger.error("❌ Heatmap did not become visible after all attempts")
        return False

    async def get_peaks_by_video_id(self, video_id: str) -> HeatmapResponse:
        return await heatmap_peaks.find_one({"video_id": video_id})

    async def simulate_human_interaction(self, page):
        """Simulates human-like behavior to evade bot fingerprinting."""
        try:
            logger.info("🕹️ Simulating human interaction to evade bot fingerprinting...")

            width = 1920
            height = 1080

            for _ in range(random.randint(3, 6)):
                x = random.randint(0, width)
                y = random.randint(0, height)
                await page.mouse.move(x, y, steps=random.randint(5, 30))
                await page.wait_for_timeout(random.randint(200, 800))

            # Scroll slightly
            for _ in range(random.randint(1, 3)):
                scroll_amount = random.randint(100, 400)
                await page.mouse.wheel(0, scroll_amount)
                await page.wait_for_timeout(random.randint(300, 800))
                await page.mouse.wheel(0, -scroll_amount)
                await page.wait_for_timeout(random.randint(300, 800))

            # Random click on safe area
            await page.mouse.click(random.randint(100, 600), random.randint(100, 400))
            logger.info("✅ Human-like interaction simulated.")
        except Exception as e:
            logger.warning(f"⚠️ Failed to simulate human interaction: {e}")

    async def save_peaks(
        self, peak_data: HeatmapResponse, forceProcess: bool = False
    ) -> None:
        existing_doc = await self.get_peaks_by_video_id(peak_data.video_id)
        if not existing_doc:
            peaks_doc = heatmap_peaks(
                video_id=peak_data.video_id,
                peaks=peak_data.peaks,
                processed_at=peak_data.processed_at,
                cropped_image=peak_data.cropped_image,
            )
            await peaks_doc.insert()
            logger.info("✅ New peaks inserted for video %s", peak_data.video_id)
        else:
            if forceProcess:
                existing_doc.peaks = peak_data.peaks
                existing_doc.cropped_image = peak_data.cropped_image
                existing_doc.processed_at = datetime.now(timezone.utc)
                existing_doc.reprocessed = True
                await existing_doc.save()
                print(f"✅ Updated video: {peak_data.video_id}")
                return

            logger.info(
                "⚠️ Peaks already exist for video %s, skipping insert",
                peak_data.video_id,
            )

    async def _save_empty_peaks(self, video_id):
        no_peak_data = HeatmapResponse(
            video_id=video_id,
            peaks=None,
            heatmap_image=None,
            no_peaks=True,
            reprocessed=False,
            stop_reprocess=False,
        )
        await self.save_peaks(no_peak_data)

    async def extract_peaks(
        self, video_id: str, forceProcess: bool = False
    ) -> tuple[list[PeakData], str]:
        if not forceProcess:
            existing_data = await self.get_peaks_by_video_id(video_id)
            if existing_data:
                logger.info("✅ Found existing peaks in DB for video %s", video_id)
                return existing_data.peaks, existing_data.cropped_image

        logger.info(
            "🔄 No existing peaks found, extracting new peaks for video %s", video_id
        )

        screenshot_path = None
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        # video_recording_path = None

        on_ec2 = os.getenv("ON_EC2", "false").lower() == "true"

        executable_path = (
            "/usr/bin/google-chrome-stable"
            if on_ec2
            else "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        )
        user_data_dir = (
            "/home/ubuntu/youtube-bot/youtube-profile"
            if on_ec2
            else "/tmp/playwright-profile"
        )

        # proxy = {
        #     "server": "http://spctlnmput:Sm6gZA8q=ca3beKa8z@in.decodo.com:10000",
        #     "username": "spctlnmput",
        #     "password": "Sm6gZA8q=ca3beKa8z",  # Use full password from the dashboard
        # }

        try:
            async with async_playwright() as p:
                browser_context = await p.chromium.launch_persistent_context(
                    user_data_dir=user_data_dir,
                    headless=True,
                    # proxy=proxy,
                    args=[
                        "--start-maximized",
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--autoplay-policy=no-user-gesture-required",
                        "--disable-blink-features=AutomationControlled",
                    ],
                    viewport={"width": 1920, "height": 1080},
                    # no_viewport=True,
                    # record_video_dir=".",  # Save video in current directory
                    # record_video_size={"width": 1920, "height": 1080},
                    user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    extra_http_headers={"Accept-Language": "en-US,en;q=0.9"},
                    geolocation={"longitude": -122.4194, "latitude": 37.7749},
                    permissions=["geolocation"],
                    executable_path=executable_path,
                )

                try:
                    with open("youtube_cookies.json", "r") as f:
                        cookies = json.load(f)
                        processed_cookies = process_cookies(cookies)
                        await browser_context.add_cookies(processed_cookies)
                except Exception as e:
                    logger.error(f"Failed to load cookies: {str(e)}")

                page = (
                    browser_context.pages[0]
                    if browser_context.pages
                    else await browser_context.new_page()
                )

                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, stealth_sync, page)

                await page.goto(video_url, timeout=60000)
                await page.wait_for_timeout(5000)

                await self.simulate_human_interaction(page)

                try:
                    await page.click('button:has-text("Accept")', timeout=5000)
                except Exception:
                    logger.info("No cookie prompt found.")

                # Increase timeout and add error screenshot
                try:
                    await page.wait_for_selector(".html5-video-player", timeout=30000)
                except Exception as e:
                    logger.error("Timeout waiting for .html5-video-player: %s", str(e))
                    await self._save_empty_peaks(video_id)
                    return [], ""

                # Screenshot after video loads

                error_selector = ".ytp-error"
                try:
                    is_error = await page.is_visible(error_selector, timeout=3000)
                    if is_error:
                        error_text = await page.inner_text(
                            ".ytp-error-content-wrap", timeout=2000
                        )
                        if any(
                            err in error_text.lower()
                            for err in [
                                "can't play this video",
                                "video unavailable",
                                "this video is private",
                                "playback error",
                                "watch this video on youtube",
                            ]
                        ):
                            logger.error("❌ YouTube error: %s", error_text)
                            await self._save_empty_peaks(video_id)
                            return [], ""
                except Exception:
                    logger.info("No critical playback error found, continuing.")

                logger.info("⏳ Waiting up to 20 seconds for ads...")
                for _ in range(20):
                    skip_btn = page.locator(".ytp-skip-ad-button")
                    if await skip_btn.is_visible(timeout=100):
                        logger.info("⏭️ Skip ad button found, clicking...")
                        await skip_btn.click()
                        await page.wait_for_timeout(1000)
                        break
                    ad_showing = page.locator(".ad-showing")
                    if not await ad_showing.is_visible(timeout=100):
                        logger.info("✅ No ads detected or ad finished")
                        break

                try:
                    fullscreen_button = page.locator(".ytp-fullscreen-button")
                    if await fullscreen_button.is_visible(timeout=3000):
                        await fullscreen_button.click()
                        await page.wait_for_timeout(2000)
                    else:
                        # JS fallback to force fullscreen click
                        logger.warning(
                            "❌ Fullscreen button not visible via locator, trying JS fallback."
                        )
                        await page.evaluate(
                            """document.querySelector('.ytp-fullscreen-button')?.click()"""
                        )
                        await page.wait_for_timeout(2000)
                except Exception as e:
                    logger.warning("Fullscreen failed with error: %s", str(e))
                    await self._save_empty_peaks(video_id)
                    return [], ""

                await page.evaluate(
                    """
                    const suggestedAction = document.querySelector('.ytp-suggested-action');
                    if (suggestedAction) {
                        suggestedAction.style.opacity = 0;
                        suggestedAction.style.display = 'none';
                    }
                    const video = document.querySelector('video');
                    if (video) video.play();
                """
                )

                await page.wait_for_timeout(1000)

                await page.evaluate(
                    """
                    const captions = document.querySelector('.ytp-caption-window-container');
                    if (captions) captions.style.display = 'none';
                    const annotation = document.querySelector('.annotation');
                    if (annotation) annotation.style.display = 'none';
                    const redDot = document.querySelector('.ytp-scrubber-container');
                    if (redDot) redDot.style.display = 'none';
                """
                )

                try:
                    heatmap_info = await page.evaluate(
                        """() => {
                            const heatmap = document.querySelector('.ytp-heat-map-container');
                            if (heatmap) {
                                heatmap.style.opacity = '1';
                                heatmap.style.display = 'block';
                                heatmap.style.visibility = 'visible';

                                const children = Array.from(heatmap.children);
                                // Also ensure children are visible
                                children.forEach(child => {
                                    child.style.display = 'block';
                                    child.style.visibility = 'visible';
                                    child.style.opacity = '1';
                                });

                                const styles = window.getComputedStyle(heatmap);

                                return {
                                    childCount: children.length,
                                    visibility: styles.visibility,
                                    display: styles.display,
                                    opacity: styles.opacity,
                                    dimensions: {
                                        width: heatmap.offsetWidth,
                                        height: heatmap.offsetHeight
                                    }
                                };
                            }
                            return null;
                        }"""
                    )

                    if heatmap_info:
                        print("✅ Heatmap modified successfully:")
                        print(f"📊 Children: {heatmap_info['childCount']}")
                        print(f"👁️ Visibility: {heatmap_info['visibility']}")
                        print(f"📐 Dimensions: {heatmap_info['dimensions']}")
                    else:
                        logger.warning("⚠️ Heatmap element not found")

                except Exception as e:
                    logger.error("❌ Failed to modify heatmap visibility: %s", str(e))
                    raise

                # for _ in range(15):
                #     heatmap_visible = await page.evaluate(
                #         "document.querySelector('.ytp-heat-map-container') !== null;"
                #     )
                #     if heatmap_visible:
                #         logger.info("📊 Heatmap is visible.")
                #         await page.screenshot(path="visible_heatmap.png")
                #         break
                #     await page.wait_for_timeout(3000)
                # else:
                #     logger.error("Heatmap not found!")
                #     await self._save_empty_peaks(video_id)
                #     return [], ""

                if not await self.wait_for_heatmap(page):
                    logger.error("Failed to detect visible heatmap")
                    await self._save_empty_peaks(video_id)
                    return [], ""

                await page.evaluate(
                    """
                    const video = document.querySelector('video');
                    if (video) video.pause();
                    const container = document.querySelector('.html5-video-container');
                    if (container) {
                        container.style.opacity = '0';
                        container.style.display = 'none';
                    }
                """
                )

                await page.wait_for_timeout(1000)

                # Final screenshot for heatmap extraction
                screenshot_path = "heatmap_screenshot.png"
                await page.screenshot(path=screenshot_path)

                # Stop and save the video recording
                # try:
                #     video_recording_path = await page.video.path()
                #     logger.info(f"Screen recording saved at: {video_recording_path}")
                # except Exception as e:
                #     logger.warning(f"Could not save screen recording: {e}")

                v_id = video_url.split("?v=")[1]
                video = await Video.find_one({"video_id": v_id})
                if not video or not video.duration:
                    logger.error(
                        "❌ Video not found or duration not available for ID: %s", v_id
                    )
                    await self._save_empty_peaks(video_id)
                    return [], ""

                duration = video.duration

                peaks, base64_image = self._detect_retention_peaks(
                    screenshot_path, duration, video_id
                )

                peak_data = HeatmapResponse(
                    video_id=video_id,
                    peaks=peaks,
                    processed_at=datetime.utcnow(),
                    cropped_image=base64_image if peaks else "",
                )
                await self.save_peaks(peak_data, True)

                return peaks, base64_image if peaks else ""

        except Exception as e:
            logger.error(
                "🔥 Failed to extract peaks: %s\n%s", str(e), traceback.format_exc()
            )
            await self._save_empty_peaks(video_id)
            return [], ""
        finally:
            if screenshot_path and os.path.exists(screenshot_path):
                try:
                    os.remove(screenshot_path)
                except Exception as e:
                    logger.error("Failed to remove screenshot: %s", str(e))
            try:
                await browser_context.close()
            except Exception:
                pass

    def _detect_retention_peaks(self, image_path, duration, video_id):
        img = cv2.imread(image_path)
        if img is None:
            logger.error("Error loading image!")
            return [], ""

        img = cv2.resize(img, (1920, 1080))
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
            logger.info("❌ Red dot (playhead) not found!")
            return [], ""

        roi_y_start = img.shape[0] - 150
        roi_y_end = img.shape[0] - 50
        roi = img[roi_y_start:roi_y_end, :]

        gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        column_sums = np.sum(gray_roi, axis=0)
        non_black_columns = np.where(column_sums > 0)[0]

        if len(non_black_columns) > 0:
            left_crop = max(non_black_columns[0] - 10, 0)
            right_crop = min(non_black_columns[-1] + 10, img.shape[1] - 1)
            roi_cropped = roi[:, left_crop:right_crop]
        else:
            roi_cropped = roi

        _, buffer = cv2.imencode(".png", roi_cropped)
        base64_image = base64.b64encode(buffer).decode("utf-8")

        # Enhanced image processing
        heatmap_gray = cv2.cvtColor(roi_cropped, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        heatmap_gray = clahe.apply(heatmap_gray)

        _, mask = cv2.threshold(
            heatmap_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )
        column_profile = np.sum(mask, axis=0)
        column_profile = column_profile / (np.max(column_profile) + 1e-6)

        # Enhanced smoothing
        smoothed = np.convolve(column_profile, np.ones(30) / 30, mode="same")

        # Filter out low intensity values
        smoothed[smoothed < np.max(smoothed) * 0.3] = 0

        # Enhanced peak detection with stricter parameters
        peaks, properties = find_peaks(
            smoothed,
            height=np.mean(smoothed) * 1.5,  # Increased threshold
            distance=50,  # Increased minimum distance
            width=10,  # Minimum peak width
            prominence=0.2,  # Added prominence requirement
        )

        # Debug visualization
        plt.figure(figsize=(15, 5))
        plt.plot(smoothed)
        plt.plot(peaks, smoothed[peaks], "x")
        plt.savefig(f"debug_peaks_{video_id}.png")
        plt.close()

        logger.info("Peak heights: {properties['peak_heights']}")
        logger.info("Mean signal: {np.mean(smoothed)}")

        width = mask.shape[1]
        if not isinstance(duration, (int, float)) or duration <= 0:
            logger.error("Invalid duration value: %s", duration)
            return [], ""

        # Enhanced peak filtering
        min_peak_height = np.max(smoothed) * 0.4  # 40% of max height
        filtered_peaks = [
            (peak, properties["peak_heights"][i])
            for i, peak in enumerate(peaks)
            if properties["peak_heights"][i] > min_peak_height
        ]

        sorted_peaks = sorted(filtered_peaks, key=lambda x: x[1], reverse=True)[:9]

        results = []
        for peak, _ in sorted_peaks:
            peak_ts = (peak / width) * duration
            start_ts = max(0, peak_ts - 5)
            end_ts = min(duration, start_ts + 10)
            if end_ts - start_ts < 10:
                start_ts = max(0, end_ts - 10)

            # Only add peaks that meet minimum duration criteria
            if end_ts - start_ts >= 5:  # Minimum 5 second segments
                timestamp_str = f"{self._format_timestamp(start_ts)} - {self._format_timestamp(end_ts)}"
                peak_url = (
                    f"https://www.youtube.com/watch?v={video_id}&t={int(start_ts)}s"
                )

                results.append(
                    PeakData(
                        timestamp=timestamp_str,
                        youtube_url=peak_url,
                        start_seconds=round(start_ts, 2),
                        end_seconds=round(end_ts, 2),
                    )
                )

        logger.info("📊 Detected peaks:%s", results)
        return results, base64_image

    def _format_timestamp(self, seconds):
        minutes = int(seconds) // 60
        seconds = int(seconds) % 60
        return f"{minutes}:{seconds:02d}"
