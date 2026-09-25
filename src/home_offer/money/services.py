from src.home_offer.money.dto import MoneyDTO
from src.home_offer.money.cuerrency.model import Currency
from src.home_offer.money.model import MoneyModel
from src.scraping_lib.models import PriceOfferComplete


def money_model_to_money_dto(money: MoneyModel) -> MoneyDTO:
    return MoneyDTO(amount=money.amount, currency=money.currency)


def price_offer_complete_to_monies(price_offer: PriceOfferComplete):
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


def money_to_euro(money_in_zloty: MoneyDTO) -> MoneyDTO:
    if money_in_zloty.currency == Currency.EUR:
        return money_in_zloty
    currency = Currency.EUR
    amount = money_in_zloty.amount / EURO_TO_ZLOTY_EXCHANGE_RATE
    return MoneyDTO(amount=amount, currency=currency)
