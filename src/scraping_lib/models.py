from typing import List

from pandas import DataFrame

from src.home_offer.money.cuerrency.model import Currency

EURO_TO_ZLOTY_EXCHANGE_RATE = 4.3



def to_dataframe(offers: List[Offer] | List[OfferComplete]) -> DataFrame:
    offer_list = []
    for offer in offers:
        offer_dict = offer.__dict__.copy()
        offer_dict.update(offer.price.__dict__)
        offer_dict['url'] = "https://www.otodom.pl" + offer.url
        offer_list.append(offer_dict)
    return DataFrame(offer_list)


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
        realtor_service = None
        if self.realtor_service:
            realtor_service = round(self.realtor_service / EURO_TO_ZLOTY_EXCHANGE_RATE, 2)
        result = PriceOfferComplete(price, tax, deposit, realtor_service)
        result.currency = Currency.EUR

        return result


class Offer:
    def __init__(self, price: PriceOfferComplete, url: str):
        self.price = price
        self.url = url
        self.id = url.split("/")[-1].split("-")[-1]

    def to_euro(self):
        return Offer(self.price.to_euro(), self.url)


class OfferComplete(Offer):
    def __init__(self, price: PriceOfferComplete, url: str):
        super().__init__(price, url)

    @staticmethod
    def from_offer(offer: Offer, deposit: float | None) -> OfferComplete:
        price_complete = PriceOfferComplete(offer.price.price, offer.price.tax, deposit)
        return OfferComplete(price_complete, offer.url)
