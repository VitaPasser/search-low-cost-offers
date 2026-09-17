import hashlib
import os
from pathlib import Path
from typing import List

import pandas as pd
from bs4 import BeautifulSoup, Tag
from bs4.element import AttributeValueList
from pandas import DataFrame
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

from models import PriceOffer, to_dataframe, Offer, OfferComplete


def scraping_low_cost_offers():

    pd.set_option('display.max_columns', 100)
    pd.set_option('display.max_rows', 100)
    pd.set_option('display.width', 2000)
    pd.set_option('display.max_colwidth', 500)

    htmls_list_offers = download_or_load_list_html()
    offers: List[Offer] = []
    for html_list_offers in htmls_list_offers:
        offers.extend(parse_offers(html_list_offers))
    print(len(offers))

    print("\nВ злотых цена и налог")
    print(to_dataframe(offers))

    prices_in_euro = [offer.to_euro() for offer in offers]

    prices_in_euro = to_dataframe(prices_in_euro)

    print("\nВ евро цена и налог")
    print(prices_in_euro)
    print("\nВ евро цена, без налога")
    print(prices_in_euro.copy().drop(columns=["tax"]).sort_values(by=["price"]))

    prices_in_euro_sum_tax = price_with_tax_in_euro(prices_in_euro)
    print("\nВ евро сума цены и налога")
    print(prices_in_euro_sum_tax)


def price_with_tax_in_euro(prices_in_euro: DataFrame) -> DataFrame:
    tax = prices_in_euro.copy()["tax"]
    prices_in_euro_sum_tax = prices_in_euro.copy()
    prices_in_euro_sum_tax["price"] += tax
    prices_in_euro_sum_tax = prices_in_euro_sum_tax.drop(columns=["tax"])
    prices_in_euro_sum_tax = prices_in_euro_sum_tax.sort_values(by=["price"])
    return prices_in_euro_sum_tax


def parse_offers(html: str) -> list[Offer]:
    bs: BeautifulSoup = BeautifulSoup(html, "lxml")
    unordered_list = bs.find("div", attrs={"data-cy": "search.listing.organic"})
    if not unordered_list:
        raise IOError
    unordered_list = unordered_list.find_all("ul")
    if not unordered_list:
        raise IOError
    list_elements = unordered_list[-1].find_all("li")
    if not list_elements:
        raise IOError
    prices_tags = [element.find("div", attrs={"data-cy": "listing-item-price"}) for
                   element in list_elements]
    prices_tags = filter(None, prices_tags)
    prices = [price_ordering(price) for price in prices_tags]
    urls_with_none = [a.get("href") if (a := element.find("a", attrs={"data-cy": "listing-item-link"})) else None
                      for element in list_elements]
    if any(isinstance(url, type(AttributeValueList)) for url in urls_with_none):
        raise IOError
    urls_without_none = filter(lambda x: x is not None, urls_with_none)
    urls: List[str] = [str(url) for url in urls_without_none]
    return [Offer(price, url) for price, url in zip(prices, urls)]


def parse_offers_deep(htmls: List[str], offers: List[Offer]) -> list[OfferComplete]:
    DEPOSIT_ROW_NAME = "Kaucja"
    results: List[OfferComplete] = []
    for html, offer in zip(htmls, offers):
        bs: BeautifulSoup = BeautifulSoup(html, "lxml")
        table_descriptions = bs.find("div", attrs={"data-sentry-element": "StyledListContainer"})
        if not table_descriptions:
            raise IOError
        table_description = table_descriptions.find("div")
        if not table_description:
            raise IOError
        deposit_div = table_description.find("div", string=DEPOSIT_ROW_NAME)
        if not deposit_div:
            raise IOError
        deposit_parent = deposit_div.parent
        if not deposit_parent:
            raise IOError
        deposit_row = deposit_parent.find_all("div")
        if not deposit_row:
            raise IOError
        deposit_value = deposit_row[1]
        if not deposit_value:
            raise IOError
        deposit: int|None = None
        if deposit_value.text.isdigit():
            deposit = int(deposit_value.text)

        results.append(OfferComplete.from_offer(offer, deposit))

    return results


def download_or_load_list_html() -> List[str]:
    htmls = []
    if not Path("./resource/offers-list/").exists():
        os.mkdir("./resource/offers-list")
    if not Path('./resource/offers-list/index-1.html').exists():
        options = Options()
        options.add_argument("--disable-dev-shm-usage")

        service = Service(executable_path="/snap/bin/chromium.chromedriver")

        pagination_number_start:int = 1
        htmls.append(download_offers_list_page(service, options, pagination_number_start))
        bs = BeautifulSoup(htmls[0], "lxml")
        pagination_list = bs.find("ul", attrs={"data-nx-name": "Pagination"})
        if not pagination_list:
            raise IOError
        pagination_elements = pagination_list.find_all("li")
        if not pagination_elements:
            raise IOError
        pagination_number_max = int(pagination_elements[-2].text)
        for pagination_number in range(pagination_number_start + 1, pagination_number_max + 1):
            htmls.append(download_offers_list_page(service, options, pagination_number))

    else:
        max_pagination_len = len(os.listdir("./resource/offers-list/"))
        for pagination_number in range(1, max_pagination_len+1):
            with open(f"./resource/offers-list/index-{pagination_number}.html", "rt") as file:
                htmls.append(file.read())
    return htmls


def download_offers_list_page(service: Service, options: Options, pagination_number: int) -> str:
    driver = webdriver.Chrome(service=service, options=options)
    url = f"https://www.otodom.pl/pl/wyniki/wynajem/mieszkanie,2-pokoje/lodzkie/lodz/lodz/lodz?limit=36&priceMax=1700&by=DEFAULT&direction=DESC&page={pagination_number}"
    try:
        driver.get(url)
        print("Page Title:", driver.title)
        html = driver.page_source
    finally:
        driver.quit()
    with open(f"./resource/offers-list/index-{pagination_number}.html", "wt") as file:
        file.write(html)
    return html


def download_html_offers(offers: List[Offer]) -> List[str]:
    htmls: List[str] = []
    options = Options()
    options.add_argument("--disable-dev-shm-usage")

    service = Service(executable_path="/snap/bin/chromium.chromedriver")
    if not Path("./resource/offers/").exists():
        os.mkdir("./resource/offers/")
    for offer in offers:
        offer_file_name = hashlib.sha512(offer.url.encode('utf-8')).hexdigest()
        if not Path(f"./resource/offers/{offer_file_name}.html").exists():
            driver = webdriver.Chrome(service=service, options=options)
            try:
                driver.get(offer.url)
                print("Page Title:", driver.title)
                htmls.append(driver.page_source)
            finally:
                driver.quit()
            with open(f"./resource/offers/{offer_file_name}.html", "wt") as file:
                file.write(html)
        else:
            with open(f"./resource/offers/{offer_file_name}.html", "rt") as file:
                html = file.read()
    return htmls


def price_ordering(price_tags: Tag):
    prices = price_tags.find_all("span")
    price = prices[0] if prices else None
    if not price:
        raise IOError
    price = int("".join([c for c in price.text if c.isdigit() and c != "²"]))
    tax = prices[1]
    tax_text = tax.text
    tax = None
    if "czynsz" in tax_text:
        tax = int("".join([c for c in tax_text if c.isdigit() and c != "²"]))
    return PriceOffer(price, tax)


if __name__ == '__main__':
    scraping_low_cost_offers()