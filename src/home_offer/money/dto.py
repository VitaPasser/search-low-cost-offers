from sqlmodel import SQLModel

from home_offer.money.cuerrency.model import Currency


class MoneyRead(SQLModel):
    model_config = {"from_attributes": True}

    amount: float
    currency: Currency