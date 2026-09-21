import datetime
from dataclasses import dataclass

from src.home_offer.money.dto import MoneyDTO


@dataclass
class HouseOfferDTO:
    id_url: str
    url: str

    price: MoneyDTO
    tax: MoneyDTO | None
    deposit: MoneyDTO | None
    realtor_service: MoneyDTO | None
    is_has_been_realtor_services: bool

    created_at: datetime.datetime | None