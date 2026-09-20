import asyncio
import json
import os

from playwright.async_api import async_playwright
from playwright_stealth import Stealth

from scraping_lib.constants import PROJECT_ROOT

URL = "https://www.otodom.pl/pl/wyniki/wynajem/mieszkanie,2-pokoje/lodzkie/lodz/lodz/lodz?limit=36&priceMax=1700&by=DEFAULT&direction=DESC"
PATH_SESSIONS_DIRECTORY = f'{PROJECT_ROOT}/resource/sessions'
PATH_SESSION_DIRECTORY = f"{PATH_SESSIONS_DIRECTORY}/otodom_session.json"


async def save_session():
    async with Stealth().use_async(async_playwright()) as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        print("[*] Переходим на страницу в GUI режиме...")
        await page.goto(URL)
        await page.wait_for_timeout(5000)

        cookies = await context.cookies()
        user_agent = await page.evaluate("navigator.userAgent")

        session_data = {
            "user_agent": user_agent,
            "cookies": cookies
        }

        if not os.path.exists(PATH_SESSIONS_DIRECTORY):
            os.mkdir(PATH_SESSIONS_DIRECTORY)
        with open(PATH_SESSION_DIRECTORY, "w", encoding="utf-8") as f:
            json.dump(session_data, f, indent=4, ensure_ascii=False)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(save_session())
