from typing import List

import pandas as pd
from bs4 import BeautifulSoup, Tag
from bs4.element import AttributeValueList
from pandas import DataFrame

from src.scraping_lib.download_html_home_offers import download_html_offers, download_or_load_list_html
from src.scraping_lib.models import to_dataframe, Offer, OfferComplete, PriceOfferComplete


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
    html_offers = download_html_offers(offers)
    offers = parse_offers_deep(html_offers, offers)

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

    prices_in_euro_sum_tax_deposit = price_with_tax_and_deposit_in_euro(prices_in_euro)
    print("\nВ евро сума цены, налога и депозита")
    print(prices_in_euro_sum_tax_deposit)

    prices_in_euro_sum_tax_deposit_rieltor = price_with_tax_deposit_and_rieltor_in_euro(prices_in_euro)
    print("\nВ евро сума цены, налога, депозита и возможной оплаты услуг риелтора")
    print(prices_in_euro_sum_tax_deposit_rieltor)


def price_with_tax_in_euro(prices_in_euro: DataFrame) -> DataFrame:
    tax = prices_in_euro.copy()["tax"]
    prices_in_euro_sum_tax = prices_in_euro.copy()
    prices_in_euro_sum_tax["price"] += tax
    prices_in_euro_sum_tax = prices_in_euro_sum_tax.drop(columns=["tax"])
    prices_in_euro_sum_tax = prices_in_euro_sum_tax.sort_values(by=["price"])
    return prices_in_euro_sum_tax


def price_with_tax_and_deposit_in_euro(prices_in_euro: DataFrame) -> DataFrame:
    tax = prices_in_euro.copy()["tax"]
    deposit = prices_in_euro.copy()["deposit"]
    prices_in_euro_sum_tax_and_deposit = prices_in_euro.copy()
    prices_in_euro_sum_tax_and_deposit["price"] += tax
    prices_in_euro_sum_tax_and_deposit["price"] += deposit
    prices_in_euro_sum_tax_and_deposit = prices_in_euro_sum_tax_and_deposit.drop(columns=["tax"])
    prices_in_euro_sum_tax_and_deposit = prices_in_euro_sum_tax_and_deposit.drop(columns=["deposit"])
    prices_in_euro_sum_tax_and_deposit = prices_in_euro_sum_tax_and_deposit.sort_values(by=["price"])
    return prices_in_euro_sum_tax_and_deposit


def price_with_tax_deposit_and_rieltor_in_euro(prices_in_euro: DataFrame) -> DataFrame:
    tax = prices_in_euro.copy()["tax"]
    deposit = prices_in_euro.copy()["deposit"]
    price = prices_in_euro.copy()["price"]
    rieltor = price * 0.5
    prices_in_euro_sum_tax_and_deposit = prices_in_euro.copy()
    prices_in_euro_sum_tax_and_deposit["price"] += tax
    prices_in_euro_sum_tax_and_deposit["price"] += deposit
    prices_in_euro_sum_tax_and_deposit["price"] += rieltor
    prices_in_euro_sum_tax_and_deposit = prices_in_euro_sum_tax_and_deposit.drop(columns=["tax"])
    prices_in_euro_sum_tax_and_deposit = prices_in_euro_sum_tax_and_deposit.drop(columns=["deposit"])
    prices_in_euro_sum_tax_and_deposit = prices_in_euro_sum_tax_and_deposit.sort_values(by=["price"])
    return prices_in_euro_sum_tax_and_deposit


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
    results: List[OfferComplete] = []
    for html, offer in zip(htmls, offers):
        bs: BeautifulSoup = BeautifulSoup(html, "lxml")
        table_descriptions = bs.find("div", attrs={"data-sentry-element": "StyledListContainer"})
        try:
            if not table_descriptions:
                raise IOError
            table_description = table_descriptions.find("div")
            if not table_description:
                raise IOError
            rows_divs = table_description.find_all("div", attrs={"data-sentry-element": "ItemGridContainer"})
            if not rows_divs:
                raise IOError
            deposit_row_div = rows_divs[7].find_all("div")
            if not deposit_row_div:
                raise IOError
            deposit_value = "".join([c for c in deposit_row_div[1].text if c.isdigit() and c != "²"])
            if not deposit_value:
                raise IOError
            deposit: int | None = int(deposit_value)
        except IOError:
            deposit = None
        results.append(OfferComplete.from_offer(offer, deposit))

    return results


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
    return PriceOfferComplete(price, tax)


if __name__ == '__main__':
    scraping_low_cost_offers()
