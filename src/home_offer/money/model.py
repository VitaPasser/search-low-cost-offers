from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from src.utils.models import BaseModel


class MoneyModel(BaseModel):
    __tablename__ = "money"

    amount: Mapped[float] = mapped_column(nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
