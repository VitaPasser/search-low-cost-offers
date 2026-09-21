from dataclasses import dataclass

from src.home_offer.money.cuerrency.model import Currency


@dataclass
class MoneyDTO:
    amount: float
    currency: Currency