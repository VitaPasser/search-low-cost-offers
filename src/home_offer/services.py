from multipledispatch import dispatch
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session, aliased

from src.scraping_lib.download_html_home_offers import DownloadHtmlHomeOffersService
from src.home_offer.dto import HouseOfferDTO, HouseOfferSumWithRealtorDTO
from src.home_offer.dto import HouseOfferSumDTO
from src.home_offer.model import HouseOfferModel
from src.home_offer.money.dto import MoneyDTO
from src.home_offer.money.model import MoneyModel
from src.home_offer.money.services import money_model_to_money_dto
from src.home_offer.money.services import price_offer_complete_to_monies, money_to_euro
from src.scraping_lib.models import Offer, OfferComplete
from src.scraping_lib.scraping import parse_offers, parse_offers_deep


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
        created_at=offer.created_at
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


class HomeOfferService:
    def __init__(self, engine: Engine, download_html_home_offers_service: DownloadHtmlHomeOffersService):
        self.engine = engine
        self.download_pages_service = download_html_home_offers_service

    def grab_offers(self, cache=False):
        htmls_list_offers = self.download_pages_service.download_or_load_list_html(cache=cache)

        offers: list[Offer] = []
        for html_list_offers in htmls_list_offers:
            offers.extend(parse_offers(html_list_offers))

        print(len(offers))

        html_offers = self.download_pages_service.download_html_offers(offers)
        complete_offers = parse_offers_deep(html_offers, offers)

        with Session(self.engine) as session:
            offers_models: list[HouseOfferModel] = [_house_offer_to_model(offer) for offer in complete_offers]
            for offer in offers_models:
                instance = session.query(HouseOfferModel).filter_by(id_url=offer.id_url).first()
                if instance:
                    continue
                session.add(offer)
            session.commit()

    def get_all(self) -> list[HouseOfferDTO]:
        with Session(self.engine) as session:
            stmt = session.query(HouseOfferModel).join(HouseOfferModel.price).order_by(MoneyModel.amount)
            offers = stmt.all()
            return [_offer_model_to_model_dto(offer) for offer in offers]

    def get_in_euro_all(self) -> list[HouseOfferDTO]:
        offers_in_zlotys = self.get_all()
        return [_offer_prices_to_euro(offer) for offer in offers_in_zlotys]

    def get_in_euro_all_and_sum_with_tax(self) -> list[HouseOfferSumDTO]:
        with Session(self.engine) as session:
            price_money = aliased(MoneyModel, name="price_money")
            tax_money = aliased(MoneyModel, name="tax_money")

            total_amount_expr = price_money.amount + tax_money.amount

            stmt = (
                select(
                    HouseOfferModel.id,
                    HouseOfferModel.id_url,
                    HouseOfferModel.url,
                    total_amount_expr.label("money_price_amount"),
                    price_money.currency.label("money_price_current"),
                    HouseOfferModel.created_at,
                )
                .outerjoin(price_money, HouseOfferModel.price_id == price_money.id)
                .outerjoin(tax_money, HouseOfferModel.tax_id == tax_money.id)
            ).order_by(total_amount_expr.asc().nulls_last())

            offers_rows = session.execute(stmt).mappings().all()
            offers: list[HouseOfferSumDTO] = []
            for offer_row in offers_rows:
                offer_dict = {
                    **offer_row,
                    "price": MoneyDTO(
                        amount=offer_row["money_price_amount"],
                        currency=offer_row["money_price_current"]
                    ) if offer_row["money_price_amount"] is not None else None,
                }
                del offer_dict["money_price_amount"]
                del offer_dict["money_price_current"]
                offers.append(HouseOfferSumDTO(**offer_dict))
            return [_offer_prices_to_euro(offer) for offer in offers]

    def get_in_euro_all_and_sum_with_tax_and_deposit(self) -> list[HouseOfferSumDTO]:
        with Session(self.engine) as session:
            price_money = aliased(MoneyModel, name="price_money")
            tax_money = aliased(MoneyModel, name="tax_money")
            deposit_money = aliased(MoneyModel, name="deposit_money")

            total_amount_expr = price_money.amount + tax_money.amount + deposit_money.amount

            stmt = (
                select(
                    HouseOfferModel.id,
                    HouseOfferModel.id_url,
                    HouseOfferModel.url,
                    total_amount_expr.label("money_price_amount"),
                    price_money.currency.label("money_price_current"),
                    HouseOfferModel.created_at,
                )
                .outerjoin(price_money, HouseOfferModel.price_id == price_money.id)
                .outerjoin(tax_money, HouseOfferModel.tax_id == tax_money.id)
                .outerjoin(deposit_money, HouseOfferModel.deposit_id == deposit_money.id)
            ).order_by(total_amount_expr.asc().nulls_last())

            offers_rows = session.execute(stmt).mappings().all()
            offers: list[HouseOfferSumDTO] = []
            for offer_row in offers_rows:
                offer_dict = {
                    **offer_row,
                    "price": MoneyDTO(
                        amount=offer_row["money_price_amount"],
                        currency=offer_row["money_price_current"]
                    ) if offer_row["money_price_amount"] is not None else None,
                }
                del offer_dict["money_price_amount"]
                del offer_dict["money_price_current"]
                offers.append(HouseOfferSumDTO(**offer_dict))
            return [_offer_prices_to_euro(offer) for offer in offers]

    def get_in_euro_all_and_sum_with_tax_deposit_and_realtor(self) -> list[HouseOfferSumWithRealtorDTO]:
        with Session(self.engine) as session:
            price_money = aliased(MoneyModel, name="price_money")
            tax_money = aliased(MoneyModel, name="tax_money")
            deposit_money = aliased(MoneyModel, name="deposit_money")
            realtor_money = aliased(MoneyModel, name="realtor_money")

            total_amount_expr = price_money.amount + tax_money.amount + deposit_money.amount + realtor_money.amount

            stmt = (
                select(
                    HouseOfferModel.id,
                    HouseOfferModel.id_url,
                    HouseOfferModel.url,
                    total_amount_expr.label("money_price_amount"),
                    price_money.currency.label("money_price_current"),
                    HouseOfferModel.created_at,
                    HouseOfferModel.is_has_been_realtor_services,
                )
                .outerjoin(price_money, HouseOfferModel.price_id == price_money.id)
                .outerjoin(tax_money, HouseOfferModel.tax_id == tax_money.id)
                .outerjoin(deposit_money, HouseOfferModel.deposit_id == deposit_money.id)
                .outerjoin(realtor_money, HouseOfferModel.realtor_service_id == realtor_money.id)
            ).order_by(total_amount_expr.asc().nulls_last())

            offers_rows = session.execute(stmt).mappings().all()
            offers: list[HouseOfferSumWithRealtorDTO] = []
            for offer_row in offers_rows:
                offer_dict = {
                    **offer_row,
                    "price": MoneyDTO(
                        amount=offer_row["money_price_amount"],
                        currency=offer_row["money_price_current"]
                    ) if offer_row["money_price_amount"] is not None else None,
                }
                del offer_dict["money_price_amount"]
                del offer_dict["money_price_current"]
                offers.append(HouseOfferSumWithRealtorDTO(**offer_dict))
            return [_offer_prices_to_euro(offer) for offer in offers]
