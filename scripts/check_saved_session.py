from playwright.async_api import async_playwright
import asyncio


async def run_bot():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Use headless now
        context = await browser.new_context(
            storage_state="auth.json"
        )  # Load saved session

        page = await context.new_page()
        await page.goto("https://youtube.com/watch?v=-0IxWrSBsco", timeout=60000)

        # Add your scraping or screenshot logic here
        print(await page.title())
        await asyncio.sleep(5)

        await browser.close()


asyncio.run(run_bot())
