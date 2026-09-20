from sqlalchemy import Engine
from sqlalchemy.orm import Session

from home_offer.dto import HouseOfferRead
from src.home_offer.model import HouseOfferModel
from src.home_offer.money.services import price_offer_to_monies, money_to_euro
from src.scraping_lib.download_html_home_offers import download_or_load_list_html, download_html_offers
from src.scraping_lib.models import Offer, OfferComplete
from src.scraping_lib.scraping import parse_offers, parse_offers_deep


def house_offer_to_model(offer: OfferComplete) -> HouseOfferModel:
    price, tax, deposit, realtor_service = price_offer_to_monies(offer.price)
    return HouseOfferModel(
        url=offer.url,
        id_url=offer.id,
        price=price,
        tax=tax,
        deposit=deposit,
        realtor_service=realtor_service,
        is_has_been_realtor_services=offer.price.is_has_been_realtor_services,
    )


def offer_prices_to_euro(offer: HouseOfferModel) -> HouseOfferModel:
    offer_by_euro = HouseOfferModel(**offer.model_dump())
    offer_by_euro.price = money_to_euro(offer.price)
    if offer.tax:
        offer_by_euro.tax = money_to_euro(offer.tax)
    if offer.deposit:
        offer_by_euro.deposit = money_to_euro(offer.deposit)
    if offer.realtor_service:
        offer_by_euro.realtor_service = money_to_euro(offer.realtor_service)
    return offer_by_euro


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


    def get_all(self) -> list[HouseOfferRead]:
        with Session(self.engine) as session:
            offers = session.query(HouseOfferModel).all()
            return [HouseOfferRead.model_validate(offer) for offer in offers]


    def get_in_euro_all(self) -> list[HouseOfferRead]:
        with Session(self.engine) as session:
            offers_in_zlotys = session.query(HouseOfferModel).all()
            offers_in_euro = [offer_prices_to_euro(offer) for offer in offers_in_zlotys]
            return [HouseOfferRead.model_validate(offer) for offer in offers_in_euro]
