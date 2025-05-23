import asyncio
from playwright.async_api import async_playwright


async def run():
    user_data_dir = "youtube-user-data"  # stores cookies, etc.

    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,  # Show UI via XVFB
            args=["--start-maximized"],
        )

        page = await browser.new_page()
        await page.goto("https://www.youtube.com/")

        print("✅ Please manually log in to YouTube.")
        print("🕐 Script will close in 2 minutes. Ctrl+C to stop earlier.")

        await asyncio.sleep(120)
        await browser.close()


asyncio.run(run())
