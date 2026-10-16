from dataclasses import dataclass

from src.home_offer.money.currency.model import Currency


@dataclass
class MoneyDTO:
    amount: float
    currency: Currency