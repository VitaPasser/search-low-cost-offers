from src.scraping_lib.models import PriceOfferComplete
from src.home_offer.money.model import MoneyModel


def price_offer_to_monies(price_offer: PriceOfferComplete):
    model_price = MoneyModel()
    model_price.currency = price_offer.currency.value
    model_price.amount = price_offer.price

    model_tax = None
    if price_offer.tax:
        model_tax = MoneyModel()
        model_tax.currency = price_offer.currency.value
        model_tax.amount = price_offer.tax

    model_deposit = None
    if price_offer.deposit:
        model_deposit = MoneyModel()
        model_deposit.currency = price_offer.currency.value
        model_deposit.amount = price_offer.deposit

    model_realtor_service = None
    if price_offer.realtor_service:
        model_realtor_service = MoneyModel()
        model_realtor_service.currency = price_offer.currency.value
        model_realtor_service.amount = price_offer.realtor_service

    return model_price, model_tax, model_deposit, model_realtor_service
