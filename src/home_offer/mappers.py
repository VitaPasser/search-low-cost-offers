from multipledispatch import dispatch

from src.home_offer.bucharest_sector.service import string_to_bucharest_sector
from src.home_offer.dto import HouseOfferDTO, HouseOfferSumDTO
from src.home_offer.model import HouseOfferModel
from src.home_offer.money.services import price_offer_complete_to_monies, money_model_to_money_dto, money_to_euro
from src.scraping_lib.models import OfferComplete, OfferIncludeBucharest


@dispatch(OfferComplete)
def _house_offer_to_model(offer: OfferComplete) -> HouseOfferModel:
    price, tax, deposit, realtor_service = price_offer_complete_to_monies(offer.price)
    return HouseOfferModel(
        url=offer.url,
        id_url=offer.id,
        price=price,
        tax=tax,
        deposit=deposit,
        realtor_service=realtor_service,
        is_has_been_realtor_services=offer.price.is_has_been_realtor_services,
    )


@dispatch(OfferIncludeBucharest)
def _house_offer_to_model(offer: OfferIncludeBucharest) -> HouseOfferModel:
    price, tax, deposit, realtor_service = price_offer_complete_to_monies(offer.price)
    return HouseOfferModel(
        url=offer.url,
        id_url=offer.id,
        price=price,
        tax=tax,
        deposit=deposit,
        realtor_service=realtor_service,
        is_has_been_realtor_services=offer.price.is_has_been_realtor_services,
        sector=string_to_bucharest_sector(offer.sector) if offer.sector else None,
        is_owner=offer.is_owner
    )


def _offer_model_to_model_dto(offer: HouseOfferModel) -> HouseOfferDTO:
    return HouseOfferDTO(
        id=offer.id,
        id_url=offer.id_url,
        url=offer.url,
        price=money_model_to_money_dto(offer.price),
        tax=money_model_to_money_dto(offer.tax) if offer.tax else None,
        deposit=money_model_to_money_dto(offer.deposit) if offer.deposit else None,
        realtor_service=money_model_to_money_dto(offer.realtor_service) if offer.realtor_service else None,
        is_has_been_realtor_services=offer.is_has_been_realtor_services,
        created_at=offer.created_at,
        sector=offer.sector,
        is_owner=offer.is_owner,
    )


@dispatch(HouseOfferSumDTO)
def _offer_prices_to_euro[T: HouseOfferSumDTO](offer: T) -> T:
    dto: T = type(offer)(**offer.__dict__)
    if offer.price:
        dto.price = money_to_euro(offer.price)
    return dto


@dispatch(HouseOfferDTO)
def _offer_prices_to_euro(offer: HouseOfferDTO) -> HouseOfferDTO:
    dto = HouseOfferDTO(**offer.__dict__)
    if offer.price:
        dto.price = money_to_euro(offer.price)
    if offer.tax:
        dto.tax = money_to_euro(offer.tax)
    if offer.deposit:
        dto.deposit = money_to_euro(offer.deposit)
    if offer.realtor_service:
        dto.realtor_service = money_to_euro(offer.realtor_service)
    return dto