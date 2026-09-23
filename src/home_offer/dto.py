import datetime
from dataclasses import dataclass

from src.home_offer.money.dto import MoneyDTO


@dataclass
class BaseHouseOfferDTO:
    id: int
    id_url: str
    url: str

    created_at: datetime.datetime | None


@dataclass
class HouseOfferDTO(BaseHouseOfferDTO):
    is_has_been_realtor_services: bool
    price: MoneyDTO
    tax: MoneyDTO | None = None
    deposit: MoneyDTO | None = None
    realtor_service: MoneyDTO | None = None


@dataclass
class HouseOfferSumDTO(BaseHouseOfferDTO):
    price: MoneyDTO | None

@dataclass
class HouseOfferSumWithRealtorDTO(HouseOfferSumDTO):
    is_has_been_realtor_services: bool