from typing import List

from sqlalchemy import Engine
from sqlalchemy.orm import Session

from src.scraping_lib.scraping_lib import download_or_load_list_html, parse_offers, download_html_offers, parse_offers_deep
from src.scraping_lib.models import Offer, OfferComplete
from src.home_offer.model import HouseOfferModel
from src.home_offer.money.services import price_offer_to_monies


def house_offer_to_model(offer: OfferComplete) -> HouseOfferModel:
    model = HouseOfferModel()
    price, tax, deposit, realtor_service = price_offer_to_monies(offer.price)
    model.price = price
    model.tax = tax
    model.deposit = deposit
    model.realtor_service = realtor_service
    model.is_has_been_realtor_services = offer.price.is_has_been_realtor_services
    model.url = offer.url
    model.id_url = offer.id
    return model


def grab_offers(engine: Engine):
    htmls_list_offers = download_or_load_list_html(cache=False)
    offers: List[Offer] = []
    for html_list_offers in htmls_list_offers:
        offers.extend(parse_offers(html_list_offers))
    print(len(offers))
    html_offers = download_html_offers(offers)
    complete_offers = parse_offers_deep(html_offers, offers)

    with Session(engine) as session:
        offers_models = [house_offer_to_model(offer) for offer in complete_offers]
        for offer in offers_models:
            instance = session.query(HouseOfferModel).filter_by(id_url=offer.id_url).first()
            if instance:
                continue
            session.add(offer)
        session.commit()
