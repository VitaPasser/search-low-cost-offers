from abc import ABC, abstractmethod

from src.scraping_lib.models import Offer, OfferComplete


class Scrapper(ABC):

    @abstractmethod
    def parse_offers(self, html: str) -> list[Offer]: ...

    @abstractmethod
    def parse_offers_deep(self, htmls: list[str], offers: list[Offer]) -> list[OfferComplete]: ...
