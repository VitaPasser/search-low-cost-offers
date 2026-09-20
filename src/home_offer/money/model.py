from sqlmodel import Field

from src.home_offer.money.cuerrency.encoder import CurrencyEncode
from src.home_offer.money.cuerrency.model import Currency
from src.utils.models import BaseModel


class MoneyModel(BaseModel, table=True):
    __tablename__ = "money"

    amount: float
    currency: Currency = Field(sa_type=CurrencyEncode, default=Currency.ZLO)
