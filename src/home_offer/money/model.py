from sqlalchemy import Enum
from sqlalchemy.orm import Mapped, mapped_column

from src.home_offer.money.cuerrency.model import Currency
from src.utils.models import BaseModel


class MoneyModel(BaseModel):
    __tablename__ = "money"

    amount: Mapped[float] = mapped_column(nullable=False)
    currency: Mapped[Currency] = mapped_column(Enum(Currency, native_enum=False, length=3), nullable=False, default=Currency.EUR)
