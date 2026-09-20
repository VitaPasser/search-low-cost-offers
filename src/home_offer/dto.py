import datetime

from sqlmodel import SQLModel

from home_offer.money.dto import MoneyRead


class HouseOfferRead(SQLModel):
    model_config = {"from_attributes": True}

    id_url: str
    url: str

    price_id: int | None
    price: MoneyRead

    tax_id: int | None
    tax: MoneyRead | None

    deposit_id: int | None
    deposit: MoneyRead | None

    realtor_service_id: int | None
    realtor_service: MoneyRead | None

    is_has_been_realtor_services: bool

    created_at: datetime.datetime | None