from typing import Self

from src.home_offer.money.cuerrency.model import Currency

EURO_TO_ZLOTY_EXCHANGE_RATE = 4.3


class PriceOfferComplete:
    def __init__(self, price: float, tax: float | None = None, deposit: float | None = None,
                 realtor_services: float | None = None, currency: Currency | None = None):
        self.price = price
        self.tax = tax
        self.deposit = deposit
        self.is_has_been_realtor_services = realtor_services is not None
        if not self.is_has_been_realtor_services:
            self.realtor_service = self.price * 0.5
        else:
            self.realtor_service = realtor_services
        self.currency = currency
        if not currency:
            self.currency = Currency.ZLO


class Offer:
    def __init__(self, price: PriceOfferComplete, url: str):
        self.price = price
        self.url = url
        self.id = url.split("/")[-1].split("-")[-1]


class OfferComplete(Offer):
    def __init__(self, price: PriceOfferComplete, url: str):
        super().__init__(price, url)

    @classmethod
    def from_offer(cls,
                   offer: Offer,
                   deposit: float | None) -> Self:
        price_complete = PriceOfferComplete(offer.price.price, offer.price.tax, deposit)
        return cls(price_complete, offer.url)


class OfferIncludeBucharest(OfferComplete):
    def __init__(self, price: PriceOfferComplete, url: str, is_owner: bool|None, sector: str|None):
        super().__init__(price, url)
        self.is_owner = is_owner
        self.sector = sector

    @classmethod
    def from_bucharest_offer(cls,
                   offer: Offer,
                   realtor_percent_services: float | None,
                   is_owner:bool | None,
                   sector:str | None) -> Self:
        realtor_service_price = offer.price.price * (realtor_percent_services / 100) if realtor_percent_services else None
        price_complete = PriceOfferComplete(
            price=offer.price.price,
            deposit=offer.price.price,
            realtor_services=realtor_service_price,
            currency=offer.price.currency,
        )
        if sector:
            sector = sector.strip().lower()
        return cls(price_complete, offer.url, is_owner=is_owner, sector=sector)
