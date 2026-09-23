import hashlib
import json
import os
from functools import cached_property
from pathlib import Path
from typing import List, Callable

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, Browser, Page, Playwright
from playwright_stealth import Stealth

from src.scraping_lib.constants import PATH_SESSIONS_DIRECTORY
from src.scraping_lib.constants import PROJECT_ROOT
from src.scraping_lib.models import Offer


def get_response(url: str, p: Playwright, session) -> tuple[Browser, Page]:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        user_agent=session["user_agent"],
    )
    context.add_cookies(session["cookies"])
    page = context.new_page()

    response = page.goto(url)
    page.wait_for_timeout(3000)

    if response is None:
        raise IOError

    if (response.status != 410) and response.status != 200:
        raise IOError
    return browser, page


def pagination_max_number_scraper(html: str) -> int:
    bs = BeautifulSoup(html, "lxml")
    pagination_list = bs.find("ul", attrs={"data-nx-name": "Pagination"})
    if not pagination_list:
        raise IOError
    pagination_elements = pagination_list.find_all("li")
    if not pagination_elements:
        raise IOError
    pagination_number_max = int(pagination_elements[-2].text)
    return pagination_number_max


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
    def browser_session_path(self):
        return f"{PATH_SESSIONS_DIRECTORY}/{self.name}_session.json"

    @cached_property
    def offers_list_path(self):
        return f"{self.resource_path}/offers-list/"

    @cached_property
    def offers_path(self):
        return f"{self.resource_path}/offers/"

    def download_offers_list_page(self, pagination_number: int) -> str:
        url = f"{self.url_list}&page={pagination_number}"
        if pagination_number == 1:
            url = f"{self.url_list}"
        with open(self.browser_session_path, "r", encoding="utf-8") as f:
            session = json.load(f)

        with Stealth().use_sync(sync_playwright()) as p:
            try:
                browser, page = get_response(url, p, session)

                print("Page Title:", page.title())
                html = page.content()
                with open(f"{self.offers_list_path}/index-{pagination_number}.html", "wt") as file:
                    file.write(html)
            except IOError:
                raise IOError
            finally:
                browser.close()
            return html

    def download_or_load_list_html(self, cache: bool = True) -> List[str]:
        htmls: list[str] = []

        if not Path(self.offers_list_path).exists():

            os.mkdir(self.offers_list_path)

        if Path(f"{self.offers_list_path}/index-1.html").exists() and cache:

            max_pagination_len = len(os.listdir(f"{self.offers_list_path}"))
            for pagination_number in range(1, max_pagination_len + 1):

                with open(f"{self.offers_list_path}index-{pagination_number}.html", "rt") as file:
                    htmls.append(file.read())

            return htmls

        pagination_number_start: int = 1
        htmls.append(self.download_offers_list_page(pagination_number_start))

        pagination_number_max = self.pagination_number_max_scraper(htmls[0])
        for pagination_number in range(pagination_number_start + 1, pagination_number_max + 1):

            htmls.append(self.download_offers_list_page(pagination_number))

        return htmls

    def download_html_offers(self, offers: List[Offer]) -> List[str]:
        with open(self.browser_session_path, "r", encoding="utf-8") as f:
            session = json.load(f)

        if not Path(self.offers_path).exists():
            os.mkdir(self.offers_path)

        htmls: List[str] = []
        for offer in offers:

            html = ""
            offer_file_name = hashlib.sha512(offer.url.encode('utf-8')).hexdigest()
            if Path(f"{self.offers_path}/{offer_file_name}.html").exists():

                with open(f"{self.offers_path}/{offer_file_name}.html", "rt") as file:
                    html = file.read()
                    htmls.append(html)
                    continue

            with Stealth().use_sync(sync_playwright()) as p:
                try:
                    url = f"{self.domain_url}{offer.url}"
                    browser, page = get_response(url, p, session)

                    print("Page Title:", page.title())

                    html = page.content()
                    with open(f"{self.offers_path}/{offer_file_name}.html", "wt") as file:
                        file.write(html)

                except IOError:
                    raise IOError

                finally:
                    browser.close()

            htmls.append(html)

        return htmls
