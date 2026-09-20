import hashlib
import json
import os
from pathlib import Path
from typing import List

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, Browser, Page, Playwright
from playwright_stealth import Stealth

from src.scraping_lib.constants import PROJECT_ROOT
from src.scraping_lib.models import Offer
from src.scraping_lib.utils.generate_session import PATH_SESSION_DIRECTORY


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


def download_offers_list_page(pagination_number: int) -> str:
    url = f"https://www.otodom.pl/pl/wyniki/wynajem/mieszkanie,2-pokoje/lodzkie/lodz/lodz/lodz?limit=36&priceMax=1700&by=DEFAULT&direction=DESC&page={pagination_number}"
    with open(PATH_SESSION_DIRECTORY, "r", encoding="utf-8") as f:
        session = json.load(f)

    with Stealth().use_sync(sync_playwright()) as p:
        try:
            browser, page = get_response(url, p, session)

            print("Page Title:", page.title())
            html = page.content()
            with open(f"{PROJECT_ROOT}/resource/offers-list/index-{pagination_number}.html", "wt") as file:
                file.write(html)
        except IOError:
            raise IOError
        finally:
            browser.close()
        return html


def download_html_offers(offers: List[Offer]) -> List[str]:
    with open(PATH_SESSION_DIRECTORY, "r", encoding="utf-8") as f:
        session = json.load(f)

    htmls: List[str] = []
    if not Path(f"{PROJECT_ROOT}/resource/offers/").exists():
        os.mkdir(f"{PROJECT_ROOT}/resource/offers/")
    for offer in offers:
        html = ""
        offer_file_name = hashlib.sha512(offer.url.encode('utf-8')).hexdigest()
        if not Path(f"{PROJECT_ROOT}/resource/offers/{offer_file_name}.html").exists():
            with Stealth().use_sync(sync_playwright()) as p:
                try:
                    url = f"https://www.otodom.pl{offer.url}"
                    browser, page = get_response(url, p, session)

                    print("Page Title:", page.title())
                    html = page.content()
                    with open(f"{PROJECT_ROOT}/resource/offers/{offer_file_name}.html", "wt") as file:
                        file.write(html)
                except IOError:
                    raise IOError
                finally:
                    browser.close()
        else:
            with open(f"{PROJECT_ROOT}/resource/offers/{offer_file_name}.html", "rt") as file:
                html = file.read()
        htmls.append(html)
    return htmls


def download_or_load_list_html(cache: bool = True) -> List[str]:
    htmls = []
    if not Path(f"{PROJECT_ROOT}/resource/offers-list/").exists():
        os.mkdir(f"{PROJECT_ROOT}/resource/offers-list")
    if not Path(f"{PROJECT_ROOT}/resource/offers-list/index-1.html").exists() or not cache:

        pagination_number_start: int = 1
        htmls.append(download_offers_list_page(pagination_number_start))
        bs = BeautifulSoup(htmls[0], "lxml")
        pagination_list = bs.find("ul", attrs={"data-nx-name": "Pagination"})
        if not pagination_list:
            raise IOError
        pagination_elements = pagination_list.find_all("li")
        if not pagination_elements:
            raise IOError
        pagination_number_max = int(pagination_elements[-2].text)
        for pagination_number in range(pagination_number_start + 1, pagination_number_max + 1):
            htmls.append(download_offers_list_page(pagination_number))

    else:
        max_pagination_len = len(os.listdir(f"{PROJECT_ROOT}/resource/offers-list/"))
        for pagination_number in range(1, max_pagination_len + 1):
            with open(f"{PROJECT_ROOT}/resource/offers-list/index-{pagination_number}.html", "rt") as file:
                htmls.append(file.read())
    return htmls
