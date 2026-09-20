from src.home_offer.money.cuerrency.model import Currency
from src.home_offer.money.model import MoneyModel
from src.scraping_lib.models import PriceOfferComplete


def price_offer_to_monies(price_offer: PriceOfferComplete):
    model_price = MoneyModel(
        currency=price_offer.currency,
        amount=price_offer.price
    )

    model_tax = None
    if price_offer.tax:
        model_tax = MoneyModel(
            currency=price_offer.currency,
            amount=price_offer.tax
        )

    model_deposit = None
    if price_offer.deposit:
        model_deposit = MoneyModel(
            currency=price_offer.currency,
            amount=price_offer.deposit
        )

    model_realtor_service = None
    if price_offer.realtor_service:
        model_realtor_service = MoneyModel(
            currency=price_offer.currency,
            amount=price_offer.realtor_service
        )

    return model_price, model_tax, model_deposit, model_realtor_service


EURO_TO_ZLOTY_EXCHANGE_RATE = 4.3


def money_to_euro(money_in_zloty: MoneyModel):
    money_in_euro = MoneyModel(**money_in_zloty.model_dump())
    money_in_euro.currency = Currency.EUR
    money_in_euro.amount = money_in_zloty.amount / EURO_TO_ZLOTY_EXCHANGE_RATE
    return money_in_euro
