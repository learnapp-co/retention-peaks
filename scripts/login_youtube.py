import asyncio
from playwright.async_api import async_playwright


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False
        )  # Headed mode for manual login
        context = await browser.new_context()
        page = await context.new_page()

        print("▶ Please log in to YouTube manually in the opened browser window.")
        await page.goto("https://youtube.com")

        # Give you time to log in
        print("⏳ Waiting 2 minutes for manual login...")
        await asyncio.sleep(120)

        # Save session to file
        await context.storage_state(path="auth.json")
        print("✅ Session saved to auth.json")

        await browser.close()


asyncio.run(main())
