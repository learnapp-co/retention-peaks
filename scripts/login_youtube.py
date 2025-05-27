# filename: login_youtube.py

import asyncio
from playwright.async_api import async_playwright


async def run():
    async with async_playwright() as p:
        chrome_path = (
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"  # macOS
        )

        # This will persist session data to ./youtube-profile
        context = await p.chromium.launch_persistent_context(
            user_data_dir="./youtube-profile",
            executable_path=chrome_path,
            headless=False,  # So you can interact with it
        )
        page = await context.new_page()
        await page.goto("https://youtube.com")
        print("🟢 Please log in manually, then close the browser.")
        await page.wait_for_timeout(60000)  # Wait 60 seconds for manual login


asyncio.run(run())
