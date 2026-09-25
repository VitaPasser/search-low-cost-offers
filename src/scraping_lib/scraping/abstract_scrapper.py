from abc import ABC, abstractmethod

from src.scraping_lib.models import Offer, OfferComplete


class Scrapper(ABC):

    @abstractmethod
    def parse_list_offers_page(self, html: str) -> list[Offer]: ...

    @abstractmethod
    def parse_offer_page[T: OfferComplete](self, htmls: list[str], offers: list[Offer]) -> list[T]: ...
