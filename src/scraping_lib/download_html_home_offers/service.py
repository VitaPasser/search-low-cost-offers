import hashlib
import json
from pathlib import Path
from typing import List, Callable, Optional

import anyio
from anyio import open_file
from playwright.async_api import async_playwright, Browser, Page, Error as PlaywrightError
from playwright_stealth import Stealth

from src.scraping_lib.models import Offer
from src.utils.constants import PROJECT_ROOT
from src.utils.logging import get_logger

logger = get_logger(__name__)

class NetworkService:

    def __init__(self, browser: Browser, session_data: dict, max_retries: int = 15):
        self.browser = browser
        self.session_data = session_data
        self.max_retries = max_retries

    async def get_page(self, url: str) -> Page:
        context = await self.browser.new_context(
            user_agent=self.session_data.get("user_agent")
        )
        if "cookies" in self.session_data:
            await context.add_cookies(self.session_data["cookies"])

        page = await context.new_page()

        for try_count in range(self.max_retries):
            try:
                response = await page.goto(url)
                await page.wait_for_timeout(3000)

                if response is None:
                    raise IOError(f"No response received for {url}")

                status = response.status
                if status in (200, 410, 404):
                    return page
                elif status in (403, 400):
                    await anyio.sleep(3 * (try_count + 1))
                    continue
                else:
                    body = await response.text()
                    logger.error(f"Bad status {status} for URL {url}. Body: {body[:200]}...")
                    raise IOError(f"Unexpected status code: {status}")

            except (PlaywrightError, IOError) as e:
                logger.warning(f"Attempt {try_count + 1} failed for {url}: {e}")
                await anyio.sleep(2 * (try_count + 1))

        await context.close()
        raise IOError(f"Max retries exceeded for URL: {url}")


class DownloadHtmlHomeOffersService:
    def __init__(
            self,
            domain_url: str,
            url_list: str,
            name: str,
            pagination_number_max_scraper: Callable[[str], int]
    ):
        self.domain_url = domain_url
        self.url_list = url_list
        self.name = name
        self.pagination_number_max_scraper = pagination_number_max_scraper

        self.resource_path.mkdir(parents=True, exist_ok=True)
        self.offers_list_path.mkdir(parents=True, exist_ok=True)
        self.offers_path.mkdir(parents=True, exist_ok=True)

    @property
    def resource_path(self) -> Path:
        return Path(PROJECT_ROOT) / "resource" / self.name

    @property
    def browser_session_directory_path(self) -> Path:
        return Path(PROJECT_ROOT) / "resource" / "sessions"

    @property
    def browser_session_path(self) -> Path:
        return self.browser_session_directory_path / f"{self.name}_session.json"

    @property
    def offers_list_path(self) -> Path:
        return self.resource_path / "offers-list"

    @property
    def offers_path(self) -> Path:
        return self.resource_path / "offers"

    async def _load_session(self) -> dict:
        if not self.browser_session_path.exists():
            raise FileNotFoundError(
                f"Session file not found at {self.browser_session_path}. Run save_session() first."
            )
        async with await open_file(self.browser_session_path, "r", encoding="utf-8") as f:
            return json.loads(await f.read())

    async def download_offers_list_page(self, pagination_number: int, net_service: NetworkService) -> str:
        url = f"{self.url_list}&page={pagination_number}" if pagination_number > 1 else self.url_list
        page = await net_service.get_page(url)

        try:
            print("Page Title:", await page.title())
            html = await page.content()
            file_path = self.offers_list_path / f"index-{pagination_number}.html"

            async with await open_file(file_path, "wt", encoding="utf-8") as file:
                await file.write(html)
            return html
        finally:
            await page.context.close()

    async def download_or_load_list_html(self, cache: bool = True, max_pages_limit: Optional[int] = None) -> List[str]:
        htmls: List[str] = []
        first_page_path = self.offers_list_path / "index-1.html"

        if first_page_path.exists() and cache:
            files = list(self.offers_list_path.glob("index-*.html"))
            max_pagination_len = len(files)
            if max_pages_limit:
                max_pagination_len = min(max_pagination_len, max_pages_limit)

            for pagination_number in range(1, max_pagination_len + 1):
                file_path = self.offers_list_path / f"index-{pagination_number}.html"
                if file_path.exists():
                    async with await open_file(file_path, "rt", encoding="utf-8") as file:
                        htmls.append(await file.read())
            return htmls

        session = await self._load_session()

        async with Stealth().use_async(async_playwright()) as p:
            browser = await p.chromium.launch(headless=True)
            net_service = NetworkService(browser, session)

            try:
                first_page_html = await self.download_offers_list_page(1, net_service)
                htmls.append(first_page_html)

                pagination_number_max = self.pagination_number_max_scraper(first_page_html)
                if max_pages_limit:
                    pagination_number_max = min(pagination_number_max, max_pages_limit)

                for pagination_number in range(2, pagination_number_max + 1):
                    html = await self.download_offers_list_page(pagination_number, net_service)
                    htmls.append(html)
            finally:
                await browser.close()

        return htmls

    async def download_html_offers(self, offers: List[Offer], max_pages_limit: Optional[int] = None) -> List[str]:
        session = await self._load_session()
        offers_limited = offers[:max_pages_limit] if max_pages_limit else offers
        htmls: List[str] = [""] * len(offers_limited)
        limiter = anyio.CapacityLimiter(10)

        async with Stealth().use_async(async_playwright()) as p:
            browser = await p.chromium.launch(headless=True)
            net_service = NetworkService(browser, session)

            try:
                async def fetch_one(index: int, offer: Offer):
                    async with limiter:
                        offer_file_name = hashlib.sha512(offer.url.encode('utf-8')).hexdigest()
                        file_path = self.offers_path / f"{offer_file_name}.html"

                        if file_path.exists():
                            async with await open_file(file_path, "rt", encoding="utf-8") as file:
                                htmls[index] = await file.read()
                            return

                        url = offer.url if offer.url.startswith("http") else f"{self.domain_url}{offer.url}"

                        try:
                            page = await net_service.get_page(url)
                            print(f"{index + 1}/{len(htmls)}: Page Title:", await page.title())
                            html = await page.content()

                            async with await open_file(file_path, "wt", encoding="utf-8") as file:
                                await file.write(html)

                            htmls[index] = html
                            await page.context.close()
                        except Exception as e:
                            logger.exception(f"Failed to fetch offer {url}: {e}")

                async with anyio.create_task_group() as tg:
                    for i, offer in enumerate(offers_limited):
                        tg.start_soon(fetch_one, i, offer) # noqa
            finally:
                await browser.close()

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

            self.browser_session_directory_path.mkdir(parents=True, exist_ok=True)
            async with await open_file(self.browser_session_path, "wt", encoding="utf-8") as f:
                await f.write(json.dumps(session_data, indent=4, ensure_ascii=False))
                print("[*] Complete Successfully")

            await browser.close()