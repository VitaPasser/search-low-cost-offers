from sqlalchemy import Engine
from sqlalchemy.orm import Session

from src.home_offer.dto import HouseOfferDTO
from src.home_offer.money.services import money_model_to_money_dto
from src.home_offer.model import HouseOfferModel
from src.home_offer.money.services import price_offer_complete_to_monies, money_to_euro
from src.scraping_lib.download_html_home_offers import download_or_load_list_html, download_html_offers
from src.scraping_lib.models import Offer, OfferComplete
from src.scraping_lib.scraping import parse_offers, parse_offers_deep


def house_offer_to_model(offer: OfferComplete) -> HouseOfferModel:
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


def offer_model_to_model_dto(offer: HouseOfferModel) -> HouseOfferDTO:
    return HouseOfferDTO(
        id_url=offer.id_url,
        url=offer.url,
        price=money_to_euro(offer.price),
        tax=money_model_to_money_dto(offer.tax) if offer.tax else None,
        deposit=money_model_to_money_dto(offer.deposit) if offer.deposit else None,
        realtor_service=money_model_to_money_dto(offer.realtor_service) if offer.realtor_service else None,
        is_has_been_realtor_services=offer.is_has_been_realtor_services,
        created_at=offer.created_at
    )


def offer_prices_to_euro(offer: HouseOfferModel) -> HouseOfferDTO:
    dto = offer_model_to_model_dto(offer)
    if offer.tax:
        dto.tax = money_to_euro(offer.tax)
    if offer.deposit:
        dto.deposit = money_to_euro(offer.deposit)
    if offer.realtor_service:
        dto.realtor_service = money_to_euro(offer.realtor_service)
    return dto


class HomeOfferService:
    def __init__(self, engine: Engine):
        self.engine = engine

    def grab_offers(self, cache=False):
        htmls_list_offers = download_or_load_list_html(cache=cache)
        offers: list[Offer] = []
        for html_list_offers in htmls_list_offers:
            offers.extend(parse_offers(html_list_offers))
        print(len(offers))
        html_offers = download_html_offers(offers)
        complete_offers = parse_offers_deep(html_offers, offers)

        with Session(self.engine) as session:
            offers_models: list[HouseOfferModel] = [house_offer_to_model(offer) for offer in complete_offers]
            for offer in offers_models:
                instance = session.query(HouseOfferModel).filter_by(id_url=offer.id_url).first()
                if instance:
                    continue
                session.add(offer)
            session.commit()


    def get_all(self) -> list[HouseOfferDTO]:
        with Session(self.engine) as session:
            offers = session.query(HouseOfferModel).all()
            return [offer_model_to_model_dto(offer) for offer in offers]


    def get_in_euro_all(self) -> list[HouseOfferDTO]:
        with Session(self.engine) as session:
            offers_in_zlotys = session.query(HouseOfferModel).all()
            return [offer_prices_to_euro(offer) for offer in offers_in_zlotys]
