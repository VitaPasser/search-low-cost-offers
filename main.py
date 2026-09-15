from pathlib import Path
from typing import List

import pandas as pd
from bs4 import BeautifulSoup, Tag
from bs4.element import AttributeValueList
from pandas import DataFrame
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

from models import PriceOffer, to_dataframe, Offer


def scraping_low_cost_offers():

    pd.set_option('display.max_columns', 100)
    pd.set_option('display.max_rows', 100)
    pd.set_option('display.width', 2000)
    pd.set_option('display.max_colwidth', 500)

    html = download_or_load_html()
    prices = parse_offers(html)

    print(to_dataframe(prices))

    prices_in_euro = [price.to_euro() for price in prices]

    prices_in_euro = to_dataframe(prices_in_euro)

    print()
    print(prices_in_euro)
    print()
    print(prices_in_euro.copy()["price"].sort_values())

    prices_in_euro_sum_tax = price_with_tax_in_euro(prices_in_euro)
    print()
    print(prices_in_euro_sum_tax)


def price_with_tax_in_euro(prices_in_euro: DataFrame) -> DataFrame:
    tax = prices_in_euro.copy()["tax"]
    prices_in_euro_sum_tax = prices_in_euro.copy()
    prices_in_euro_sum_tax["price"] += tax
    prices_in_euro_sum_tax = prices_in_euro_sum_tax.drop(columns=["tax"])
    prices_in_euro_sum_tax = prices_in_euro_sum_tax.sort_values(by=["price"])
    return prices_in_euro_sum_tax


def parse_offers(html: str) -> list[Offer]:
    bs: BeautifulSoup = BeautifulSoup(html, "html.parser")
    unordered_list = bs.find("div", attrs={"data-cy": "search.listing.organic"})
    if not unordered_list:
        raise IOError
    unordered_list = unordered_list.find("ul")
    if not unordered_list:
        raise IOError
    list_elements = unordered_list.find_all("li")
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


def download_or_load_html() -> str:
    html = ""
    if not Path('./resource/index.html').exists():
        options = Options()
        options.add_argument("--disable-dev-shm-usage")

        service = Service(executable_path="/snap/bin/chromium.chromedriver")

        driver = webdriver.Chrome(service=service, options=options)
        try:
            driver.get(
                "https://www.otodom.pl/pl/wyniki/wynajem/mieszkanie,2-pokoje/lodzkie/lodz/lodz/lodz?limit=36&priceMax=1700&by=DEFAULT&direction=DESC")
            print("Page Title:", driver.title)
            html = driver.page_source
        finally:
            driver.quit()
        with open(r"./resource/index.html", "wt") as file:
            file.write(html)
    else:
        with open(r"./resource/index.html", "rt") as file:
            html = file.read()
    return html


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