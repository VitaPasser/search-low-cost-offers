import hashlib
import os
from pathlib import Path
from typing import List, Callable

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.chromium.webdriver import ChromiumDriver

from src.scraping_lib.models import Offer
from src.scraping_lib.constants import PROJECT_ROOT, WEB_DRIVER_PATH


class DownloadHtmlHomeOffers:
    def __init__(self,
                 options: type[ChromiumDriver|Options],
                 options_arguments: list[str],
                 service: Callable[[],Service],
                 driver: type[WebDriver]):
        self.__options_t = options
        self.__options_arguments = options_arguments
        self.service = service
        self.driver = lambda: driver(self.options(), self.service()) # type: ignore


    @property
    def options(self):
        __options: ChromiumDriver|Options= self.__options_t()
        for argument in self.__options_arguments:
            __options.add_argument(argument)
        return lambda: __options


    def download_or_load_list_html(self, cache: bool = True) -> List[str]:
        htmls = []
        if not Path(f"{PROJECT_ROOT}/resource/offers-list/").exists():
            os.mkdir(f"{PROJECT_ROOT}/resource/offers-list")
        if not Path(f"{PROJECT_ROOT}/resource/offers-list/index-1.html").exists() or not cache:

            pagination_number_start:int = 1
            htmls.append(self.download_offers_list_page(pagination_number_start))
            bs = BeautifulSoup(htmls[0], "lxml")
            pagination_list = bs.find("ul", attrs={"data-nx-name": "Pagination"})
            if not pagination_list:
                raise IOError
            pagination_elements = pagination_list.find_all("li")
            if not pagination_elements:
                raise IOError
            pagination_number_max = int(pagination_elements[-2].text)
            for pagination_number in range(pagination_number_start + 1, pagination_number_max + 1):
                htmls.append(self.download_offers_list_page(pagination_number))

        else:
            max_pagination_len = len(os.listdir(f"{PROJECT_ROOT}/resource/offers-list/"))
            for pagination_number in range(1, max_pagination_len+1):
                with open(f"{PROJECT_ROOT}/resource/offers-list/index-{pagination_number}.html", "rt") as file:
                    htmls.append(file.read())
        return htmls


    def download_offers_list_page(self, pagination_number: int) -> str:
        url = f"https://www.otodom.pl/pl/wyniki/wynajem/mieszkanie,2-pokoje/lodzkie/lodz/lodz/lodz?limit=36&priceMax=1700&by=DEFAULT&direction=DESC&page={pagination_number}"
        driver = self.driver()
        try:
            driver.get(url)
            print("Page Title:", driver.title)
            html = driver.page_source
        finally:
            driver.quit()
        with open(f"{PROJECT_ROOT}/resource/offers-list/index-{pagination_number}.html", "wt") as file:
            file.write(html)
        return html


    def download_html_offers(self, offers: List[Offer]) -> List[str]:
        htmls: List[str] = []
        if not Path(f"{PROJECT_ROOT}/resource/offers/").exists():
            os.mkdir(f"{PROJECT_ROOT}/resource/offers/")
        for offer in offers:
            html = ""
            offer_file_name = hashlib.sha512(offer.url.encode('utf-8')).hexdigest()
            if not Path(f"{PROJECT_ROOT}/resource/offers/{offer_file_name}.html").exists():
                driver = self.driver()
                try:
                    driver.get(f"https://www.otodom.pl{offer.url}")
                    print("Page Title:", driver.title)
                    html = driver.page_source
                finally:
                    driver.quit()
                with open(f"{PROJECT_ROOT}/resource/offers/{offer_file_name}.html", "wt") as file:
                    file.write(html)
            else:
                with open(f"{PROJECT_ROOT}/resource/offers/{offer_file_name}.html", "rt") as file:
                    html = file.read()
            htmls.append(html)
        return htmls


options = Options
options_arguments = ['--no-sandbox', '--disable-dev-shm-usage']

service = lambda: Service(executable_path=WEB_DRIVER_PATH)
driver= webdriver.Chrome

downloader_Html_houses_offers_default_webdriver = DownloadHtmlHomeOffers(
    options=options,
    options_arguments=options_arguments,
    service=service,
    driver=driver
)
