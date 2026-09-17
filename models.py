from enum import Enum
from typing import List, Self

from pandas import DataFrame

EURO_TO_ZLOTY_EXCHANGE_RATE = 4.3


class Currency(Enum):
    ZLO = "ZLO"
    EUR = "EUR"


def to_dataframe(offers: List[Offer]|List[OfferComplete]) -> DataFrame:
    offer_list = []
    for offer in offers:
        offer_dict = offer.__dict__.copy()
        offer_dict.update(offer.price.__dict__)
        offer_dict['url'] = "https://www.otodom.pl"+offer.url
        offer_list.append(offer_dict)
    return DataFrame(offer_list)


class PriceOffer:
    def __init__(self, price: float, tax: float|None):
        self.price = price
        self.tax = tax
        self.currency = Currency.ZLO

    def to_euro(self):
        if self.currency == Currency.EUR:
            return self
        price = round(self.price / EURO_TO_ZLOTY_EXCHANGE_RATE, 2)
        tax = self.tax
        if self.tax:
            tax = round(self.tax / EURO_TO_ZLOTY_EXCHANGE_RATE, 2)
        result = PriceOffer(price, tax)
        result.currency = Currency.EUR
        return result

class PriceOfferComplete(PriceOffer):
    def __init__(self, price: float, tax: float|None, deposit: float|None):
        super().__init__(price, tax)
        self.deposit = deposit

    def to_euro(self):
        if self.currency == Currency.EUR:
            return self
        price = round(self.price / EURO_TO_ZLOTY_EXCHANGE_RATE, 2)
        tax = None
        if self.tax:
            tax = round(self.tax / EURO_TO_ZLOTY_EXCHANGE_RATE, 2)
        deposit = None
        if self.deposit:
            deposit = round(self.deposit / EURO_TO_ZLOTY_EXCHANGE_RATE, 2)
        result = PriceOfferComplete(price, tax, deposit)
        result.currency = Currency.EUR

        return result


class Offer:
    def __init__(self, price: PriceOffer, url: str):
        self.price = price
        self.url = url

    def to_euro(self):
        return Offer(self.price.to_euro(), self.url)

class OfferComplete(Offer):
    def __init__(self, price: PriceOfferComplete, url: str):
        super().__init__(price, url)

    @staticmethod
    def from_offer(offer: Offer, deposit: float|None) -> OfferComplete:
        price_complete = PriceOfferComplete(offer.price.price, offer.price.tax, deposit)
        return OfferComplete(price_complete, offer.url)