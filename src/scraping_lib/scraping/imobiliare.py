from builtins import str
from typing import Any

from bs4 import BeautifulSoup
from bs4.element import AttributeValueList, Tag

from src.home_offer.money.cuerrency.model import Currency
from src.scraping_lib.models import Offer, PriceOfferComplete
from src.scraping_lib.models import OfferIncludeBucharest
from src.scraping_lib.scraping.abstract_scrapper import Scrapper


def _price_ordering(price_tag: Tag):
    price_text = price_tag.text
    match price_text:
        case p if p.endswith("€"):
            price = int(price_text[:-1])
            currency = Currency.EUR
        case p if p.endswith("RON"):
            price = int(price_text[:-3])
            currency = Currency.RON
        case _:
            raise IOError
    return PriceOfferComplete(price=price, currency=currency)


def _grab_rieltor_commission_percent(bs: BeautifulSoup) -> Any:
    section_rieltor_commission_tag = bs.find("section", attrs={"data-cy": "listing-amenities-component"})
    if not section_rieltor_commission_tag:
        raise IOError
    utilitati_spans = bs.find_all("span", attrs={"class": "text-title"})
    if not utilitati_spans:
        raise IOError

    commission_title_span_tag = None
    utilitati_spans.reverse()
    for span in utilitati_spans:
        if "Comision" in span.text:
            commission_title_span_tag = span
            break

    rieltor_commission_precent = None
    if commission_title_span_tag:
        div = commission_title_span_tag.parent
        if not div:
            raise IOError
        div_commission_number = div.find("div")
        if not div_commission_number:
            raise IOError
        commission_number_text = div_commission_number.text.strip()
        if commission_number_text is not None and not commission_number_text.isdigit():
            rieltor_commission_precent = 100
        else:
            rieltor_commission_precent = float(commission_number_text)
    return rieltor_commission_precent


def _has_owner(bs: BeautifulSoup) -> bool:
    agency_name_tag = bs.find("h4", attrs={"data-cy": "agency-name"})
    if not agency_name_tag:
        raise IOError
    agency_name_text = agency_name_tag.text.strip().replace("\n", "")
    agency_name_text = " ".join(list(filter(None, agency_name_text.split(" "))))
    match agency_name_text:
        case "Proprietar":
            is_owner = True
        case _:
            is_owner = False
    return is_owner


class ImobiliareScrapper(Scrapper):

    def parse_list_offers_page(self, html: str) -> list[Offer]:
        """
        XPATH: /html/body/div[2]/div/div/main/div/div/div[2]/div/div/div[3]/div - list offers


        like class-path: listing-results-container


        XPATH: /html/body/div[2]/div/div/main/div/div/div[2]/div/div/div[3]/div/div[1]/article/div/a
        :param html:
        :return:
        """
        bs: BeautifulSoup = BeautifulSoup(html, "lxml")
        unordered_list = bs.find("div",{"class": "listing-results-container"})
        if not unordered_list:
            raise IOError
        article_list = bs.find_all("article")
        if not article_list:
            raise IOError
        urls_with_none = [a.get("href") if (a := element.find("a")) else None
                          for element in article_list]
        if any(isinstance(url, type(AttributeValueList)) for url in urls_with_none):
            raise IOError
        urls_without_none = filter(lambda x: x is not None, urls_with_none)
        urls: list[str] = [str(url) for url in urls_without_none]
        price_tags = [element.find("span", {"class": "text-text-price"})
                      for element in article_list]
        price_tags_without_none = list(filter(None, price_tags))
        prices = [_price_ordering(price) for price in price_tags_without_none]
        return [Offer(price, url) for price, url in zip(prices, urls)]

    def parse_offer_page(self, htmls: list[str], offers: list[Offer]) -> list[OfferIncludeBucharest]:
        results: list[OfferIncludeBucharest] = []
        for html, offer in zip(htmls, offers):
            bs: BeautifulSoup = BeautifulSoup(html, "lxml")
            try:
                is_owner = _has_owner(bs)
                rieltor_commission_precent = _grab_rieltor_commission_percent(bs)
                nav_path_address = bs.find("nav", attrs={"data-cy": "breadcrumbs"})
                if not nav_path_address:
                    raise IOError
                lists_paths = nav_path_address.find_all("li")
                if not lists_paths and not lists_paths[4]:
                    raise IOError
                sector = lists_paths[4].text

            except IOError:
                is_owner = None
                rieltor_commission_precent = None
                sector = None
            results.append(OfferIncludeBucharest.from_bucharest_offer(offer, rieltor_commission_precent,
                                                                      is_owner=is_owner, sector=sector))

        return results
