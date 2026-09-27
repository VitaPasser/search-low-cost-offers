from builtins import str

from bs4 import BeautifulSoup
from bs4.element import AttributeValueList, Tag

from src.home_offer.money.cuerrency.model import Currency
from src.scraping_lib.models import Offer, PriceOfferComplete
from src.scraping_lib.models import OfferIncludeBucharest
from src.scraping_lib.scraping.abstract_scrapper import Scrapper


def _price_ordering(price_tag: Tag):
    price_text = price_tag.contents[0].text.replace(",", ".")
    match price_text:
        case p if p.endswith("€"):
            price = float(price_text[:-1])
            currency = Currency.EUR
        case p if p.endswith("RON"):
            price = float(price_text[:-3])
            currency = Currency.RON
        case _:
            raise IOError
    return PriceOfferComplete(price=price, currency=currency)


def _has_owner_olx(bs: BeautifulSoup) -> bool:
    ad_container_tag = bs.find("div", attrs={"data-testid": "ad-parameters-container"})
    if not ad_container_tag:
        raise IOError
    ad_tags = ad_container_tag.find_all("p")
    if not ad_tags:
        raise IOError

    is_owner = False
    for ad_tag in ad_tags:
        ad_text = ad_tag.text.strip().replace("\n", "")
        match ad_text:
            case "Persoana fizica":
                is_owner = True
                break
            case "Firma":
                is_owner = False
                break
            case _:
                is_owner = False

    return is_owner


def _has_owner_storia(bs: BeautifulSoup) -> bool:
    table_descriptions = bs.find("div", attrs={"data-sentry-element": "StyledListContainer"})
    if not table_descriptions:
        raise IOError
    table_description = table_descriptions.find("div")
    if not table_description:
        raise IOError
    rows_divs = table_description.find_all("div", attrs={"data-sentry-element": "ItemGridContainer"})
    if not rows_divs:
        raise IOError
    owner_row_div = rows_divs[8].find_all("div")
    if not owner_row_div:
        raise IOError
    owner_value = owner_row_div[1].text
    if not owner_value:
        raise IOError
    match owner_value:
        case "privat":
            is_owner = True
        case "agenție":
            is_owner = False
        case _:
            is_owner = False

    return is_owner


def _get_sector(bs: BeautifulSoup) -> str:
    nav_lists_paths = bs.find_all("li", attrs={"data-testid": "breadcrumb-item"})
    if not nav_lists_paths and not nav_lists_paths[-1]:
        raise IOError
    sector = nav_lists_paths[-1].text.split('-')[-1].strip()
    return sector


def _get_sector_storia(bs: BeautifulSoup) -> str:
    a_path = bs.find("a", attrs={"href": "#map"})
    if not a_path:
        raise IOError
    sector = a_path.text.split(',')[-2].strip()
    return sector


def _olx_page_offer(html: str, offer: Offer):
    bs: BeautifulSoup = BeautifulSoup(html, "lxml")
    try:
        is_owner = _has_owner_olx(bs)
        sector = _get_sector(bs)
    except IOError:
        is_owner = None
        sector = None
    return OfferIncludeBucharest.from_bucharest_offer(offer, is_owner=is_owner, sector=sector)


def _storia_page_offer(html: str, offer: Offer):
    bs: BeautifulSoup = BeautifulSoup(html, "lxml")
    try:
        is_owner = _has_owner_storia(bs)
        sector = _get_sector_storia(bs)
    except IOError:
        is_owner = None
        sector = None
    return OfferIncludeBucharest.from_bucharest_offer(offer, is_owner=is_owner, sector=sector)


class OlxScrapper(Scrapper):

    def parse_list_offers_page(self, html: str) -> list[Offer]:
        bs: BeautifulSoup = BeautifulSoup(html, "lxml")
        cards = bs.find_all("div",{"data-testid": "l-card"})
        if not cards:
            raise IOError(f"Html: {html}\n\n Cards: {cards}")
        urls_with_none = [a.get("href") if (a := element.find("a")) else None
                          for element in cards]
        if any(isinstance(url, type(AttributeValueList)) for url in urls_with_none):
            raise IOError
        urls_without_none = filter(lambda x: x is not None, urls_with_none)
        urls: list[str] = [str(url).split("?")[0] for url in urls_without_none]
        price_tags = [element.find("p", {"data-testid": "ad-price"})
                      for element in cards]
        price_tags_without_none = list(filter(None, price_tags))
        prices = [_price_ordering(price) for price in price_tags_without_none]
        return [Offer(price, url) for price, url in zip(prices, urls)]

    def parse_offer_page(self, htmls: list[str], offers: list[Offer]) -> list[OfferIncludeBucharest]:
        results: list[OfferIncludeBucharest] = []
        for html, offer in zip(htmls, offers):
            match offer.url:
                # Storia
                case f if f.startswith("https://www.storia.ro"): results.append(_storia_page_offer(html, offer))
                # OLX
                case f if f.startswith("/d/oferta/"): results.append(_olx_page_offer(html, offer))
                case _: raise IOError

        return results
