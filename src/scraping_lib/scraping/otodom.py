from bs4 import BeautifulSoup
from bs4.element import AttributeValueList, Tag

from src.scraping_lib.models import Offer, OfferComplete, PriceOfferComplete
from src.scraping_lib.scraping.abstract_scrapper import Scrapper


def _price_ordering(price_tags: Tag):
    prices = price_tags.find_all("span")
    price = prices[0] if prices else None
    if not price:
        raise IOError
    price = int("".join([c for c in price.text if c.isdigit() and c != "²"]))
    tax_text = None
    if len(prices) != 1:
        tax = prices[1]
        tax_text = tax.text
    tax = None
    if tax_text is not None and "czynsz" in tax_text:
        tax = int("".join([c for c in tax_text if c.isdigit() and c != "²"]))
    return PriceOfferComplete(price, tax)


class OtodomScrapper(Scrapper):

    def parse_offers(self, html: str) -> list[Offer]:
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
        urls_with_none = [a.get("href") if (a := element.find("a", attrs={"data-cy": "listing-item-link"})) else None
                          for element in list_elements]
        if any(isinstance(url, type(AttributeValueList)) for url in urls_with_none):
            raise IOError
        urls_without_none = filter(lambda x: x is not None, urls_with_none)
        urls: list[str] = [str(url) for url in urls_without_none]
        prices_tags = [element.find("div", attrs={"data-cy": "listing-item-price"}) for
                       element in list_elements]
        prices_tags_without_nome = list(filter(None, prices_tags))
        prices = [_price_ordering(price) for price in prices_tags_without_nome]
        return [Offer(price, url) for price, url in zip(prices, urls)]

    def parse_offers_deep(self, htmls: list[str], offers: list[Offer]) -> list[OfferComplete]:
        results: list[OfferComplete] = []
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

