import hashlib
import json
import os
from functools import cached_property
from pathlib import Path
from typing import List, Callable

from anyio import open_file
from playwright.async_api import async_playwright, Playwright, Browser, Page
from playwright_stealth import Stealth

from src.scraping_lib.constants import PROJECT_ROOT
from src.scraping_lib.models import Offer


async def get_response(url: str, p: Playwright, session) -> tuple[Browser, Page]:
    browser = await p.chromium.launch(headless=True)
    context = await browser.new_context(
        user_agent=session["user_agent"],
    )
    await context.add_cookies(session["cookies"])
    page = await context.new_page()

    response = await page.goto(url)
    await page.wait_for_timeout(3000)

    if response is None:
        raise IOError

    if (response.status != 410) and response.status != 200:
        raise IOError
    return browser, page


class DownloadHtmlHomeOffersService:
    def __init__(self, domain_url: str, url_list: str, name: str, pagination_number_max_scraper: Callable[[str], int]):
        self.domain_url = domain_url
        self.url_list = url_list
        self.pagination_number_max_scraper = pagination_number_max_scraper

        self.name = name
        if not Path(self.resource_path).exists():

            os.mkdir(self.resource_path)

    @cached_property
    def resource_path(self):
        return f"{PROJECT_ROOT}/resource/{self.name}"

    @cached_property
    def browser_session_directory_path(self):
        return f"{PROJECT_ROOT}/resource/sessions/"

    @cached_property
    def browser_session_path(self):
        return f"{self.browser_session_directory_path}{self.name}_session.json"

    @cached_property
    def offers_list_path(self):
        return f"{self.resource_path}/offers-list/"

    @cached_property
    def offers_path(self):
        return f"{self.resource_path}/offers/"

    async def download_offers_list_page(self, pagination_number: int) -> str:
        url = f"{self.url_list}&page={pagination_number}"
        if pagination_number == 1:
            url = f"{self.url_list}"
        async with await open_file(self.browser_session_path, "r", encoding="utf-8") as f:
            session = json.loads(await f.read())

        async with Stealth().use_async(async_playwright()) as p:
            try:
                browser, page = await get_response(url, p, session)

                print("Page Title:", await page.title())
                html = await page.content()
                async with await open_file(f"{self.offers_list_path}/index-{pagination_number}.html", "wt") as file:
                    await file.write(html)
            except IOError:
                raise IOError
            finally:
                await browser.close()
            return html

    async def download_or_load_list_html(self, cache: bool = True) -> List[str]:
        htmls: list[str] = []

        if not Path(self.offers_list_path).exists():

            os.mkdir(self.offers_list_path)

        if Path(f"{self.offers_list_path}/index-1.html").exists() and cache:

            max_pagination_len = len(os.listdir(f"{self.offers_list_path}"))
            for pagination_number in range(1, max_pagination_len + 1):

                async with await open_file(f"{self.offers_list_path}index-{pagination_number}.html", "rt") as file:
                    htmls.append(await file.read())

            return htmls

        pagination_number_start: int = 1
        htmls.append(await self.download_offers_list_page(pagination_number_start))

        pagination_number_max = self.pagination_number_max_scraper(htmls[0])
        for pagination_number in range(pagination_number_start + 1, pagination_number_max + 1):

            htmls.append(await self.download_offers_list_page(pagination_number))

        return htmls

    async def download_html_offers(self, offers: List[Offer]) -> List[str]:
        async with await open_file(self.browser_session_path, "r", encoding="utf-8") as f:
            session = json.loads(await f.read())

        if not Path(self.offers_path).exists():
            os.mkdir(self.offers_path)

        htmls: List[str] = []
        for offer in offers:

            html = ""
            offer_file_name = hashlib.sha512(offer.url.encode('utf-8')).hexdigest()
            if Path(f"{self.offers_path}{offer_file_name}.html").exists():

                async with await open_file(f"{self.offers_path}{offer_file_name}.html", "rt") as file:
                    html = await file.read()
                    htmls.append(html)
                    continue

            async with Stealth().use_async(async_playwright()) as p:
                try:
                    url = f"{self.domain_url}{offer.url}"
                    browser, page = await get_response(url, p, session)

                    print("Page Title:", await page.title())

                    html = await page.content()
                    async with await open_file(f"{self.offers_path}{offer_file_name}.html", "wt") as file:
                        await file.write(html)

                except IOError:
                    raise IOError

                finally:
                    await browser.close()

            htmls.append(html)

        return htmls

    async def save_session(self):
        async with Stealth().use_async(async_playwright()) as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()

            print("[*] Go to the page in GUI mode...")
            await page.goto(self.url_list)
            await page.wait_for_timeout(5000)

            cookies = await context.cookies()
            user_agent = await page.evaluate("navigator.userAgent")

            session_data = {
                "user_agent": user_agent,
                "cookies": cookies
            }

            if not os.path.exists(self.browser_session_directory_path):
                os.mkdir(self.browser_session_directory_path)
            async with await open_file(self.browser_session_path, "w", encoding="utf-8") as f:
                json.dump(session_data, await f, indent=4, ensure_ascii=False)
                print("[*] Complete Successfully")


            await browser.close()
