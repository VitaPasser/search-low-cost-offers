from typing import List

from pandas import DataFrame

from src.home_offer.money.cuerrency.model import Currency

EURO_TO_ZLOTY_EXCHANGE_RATE = 4.3


class PriceOfferComplete:
    def __init__(self, price: float, tax: float | None, deposit: float | None = None,
                 realtor_services: float | None = None):
        self.price = price
        self.tax = tax
        self.deposit = deposit
        self.is_has_been_realtor_services = realtor_services is not None
        if not self.is_has_been_realtor_services:
            self.realtor_service = self.price * 0.5
        self.currency = Currency.ZLO


class Offer:
    def __init__(self, price: PriceOfferComplete, url: str):
        self.price = price
        self.url = url
        self.id = url.split("/")[-1].split("-")[-1]


class OfferComplete(Offer):
    def __init__(self, price: PriceOfferComplete, url: str):
        super().__init__(price, url)

    @staticmethod
    def from_offer(offer: Offer, deposit: float | None) -> OfferComplete:
        price_complete = PriceOfferComplete(offer.price.price, offer.price.tax, deposit)
        return OfferComplete(price_complete, offer.url)
