from sqlalchemy import Engine, select, ColumnElement, Select
from sqlalchemy.orm import Session, aliased

from src.home_offer.mappers import _house_offer_to_model, _offer_model_to_model_dto, _offer_prices_to_euro
from src.home_offer.dto import HouseOfferDTO, HouseOfferSumWithRealtorDTO
from src.home_offer.dto import HouseOfferSumDTO
from src.home_offer.model import HouseOfferModel
from src.home_offer.money.dto import MoneyDTO
from src.home_offer.money.model import MoneyModel
from src.scraping_lib.download_html_home_offers.service import DownloadHtmlHomeOffersService
from src.scraping_lib.models import Offer
from src.scraping_lib.scraping.abstract_scrapper import Scrapper


def _select_to_house_offer_sum_dto(price_money: type[MoneyModel],
                                   total_amount_expr: ColumnElement[float | int],
                                   *args) -> Select:
    return select(
        HouseOfferModel.id,
        HouseOfferModel.id_url,
        HouseOfferModel.url,
        HouseOfferModel.is_owner,
        HouseOfferModel.sector,
        total_amount_expr.label("money_price_amount"),
        price_money.currency.label("money_price_current"),
        HouseOfferModel.created_at,
        *args
    )


class HomeOfferService:
    def __init__(
            self,
            engine: Engine,
            download_html_home_offers_service: DownloadHtmlHomeOffersService,
            scraper: Scrapper
    ):
        self.engine = engine
        self.download_pages_service = download_html_home_offers_service
        self.scraper = scraper

    async def grab_offers(self, cache=False):
        htmls_list_offers = await self.download_pages_service.download_or_load_list_html(cache=cache)

        offers: list[Offer] = []
        for html_list_offers in htmls_list_offers:
            offers.extend(self.scraper.parse_list_offers_page(html_list_offers))

        print(len(offers))

        html_offers = await self.download_pages_service.download_html_offers(offers)
        complete_offers = self.scraper.parse_offer_page(html_offers, offers)

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
            offers_dto = [_offer_model_to_model_dto(offer) for offer in offers]
            for offer_dto in offers_dto:
                offer_dto.url = self.download_pages_service.domain_url + offer_dto.url
            return offers_dto

    def get_in_euro_all(self) -> list[HouseOfferDTO]:
        offers_in_zlotys = self.get_all()
        return [_offer_prices_to_euro(offer) for offer in offers_in_zlotys]

    def get_in_euro_all_and_sum_with_tax(self) -> list[HouseOfferSumDTO]:
        with Session(self.engine) as session:
            price_money = aliased(MoneyModel, name="price_money")
            tax_money = aliased(MoneyModel, name="tax_money")

            total_amount_expr = price_money.amount + tax_money.amount

            stmt = (
                _select_to_house_offer_sum_dto(price_money, total_amount_expr)
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
                offer_dict["url"] = self.download_pages_service.domain_url + offer_row["url"]
                offers.append(HouseOfferSumDTO(**offer_dict))
            return [_offer_prices_to_euro(offer) for offer in offers]

    def get_in_euro_all_and_sum_with_tax_and_deposit(self) -> list[HouseOfferSumDTO]:
        with Session(self.engine) as session:
            price_money = aliased(MoneyModel, name="price_money")
            tax_money = aliased(MoneyModel, name="tax_money")
            deposit_money = aliased(MoneyModel, name="deposit_money")

            total_amount_expr = price_money.amount + tax_money.amount + deposit_money.amount

            stmt = (
                _select_to_house_offer_sum_dto(price_money, total_amount_expr)
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
                offer_dict["url"] = self.download_pages_service.domain_url + offer_row["url"]
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
                _select_to_house_offer_sum_dto(price_money, total_amount_expr, HouseOfferModel.is_has_been_realtor_services)
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
                offer_dict["url"] = self.download_pages_service.domain_url + offer_row["url"]
                offers.append(HouseOfferSumWithRealtorDTO(**offer_dict))
            return [_offer_prices_to_euro(offer) for offer in offers]

    def get_in_euro_all_and_sum_with_deposit(self) -> list[HouseOfferSumWithRealtorDTO]:
        with Session(self.engine) as session:
            price_money = aliased(MoneyModel, name="price_money")
            tax_money = aliased(MoneyModel, name="tax_money")
            deposit_money = aliased(MoneyModel, name="deposit_money")
            realtor_money = aliased(MoneyModel, name="realtor_money")

            total_amount_expr = price_money.amount + deposit_money.amount

            stmt = (
                _select_to_house_offer_sum_dto(price_money, total_amount_expr, HouseOfferModel.is_has_been_realtor_services)
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
                offer_dict["url"] = self.download_pages_service.domain_url + offer_row["url"]
                offers.append(HouseOfferSumWithRealtorDTO(**offer_dict))
            return [_offer_prices_to_euro(offer) for offer in offers]

    def get_in_euro_all_and_sum_with_deposit_and_realtor(self) -> list[HouseOfferSumWithRealtorDTO]:
        with Session(self.engine) as session:
            price_money = aliased(MoneyModel, name="price_money")
            tax_money = aliased(MoneyModel, name="tax_money")
            deposit_money = aliased(MoneyModel, name="deposit_money")
            realtor_money = aliased(MoneyModel, name="realtor_money")

            total_amount_expr = price_money.amount + deposit_money.amount + realtor_money.amount

            stmt = (
                _select_to_house_offer_sum_dto(price_money, total_amount_expr, HouseOfferModel.is_has_been_realtor_services)
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
                offer_dict["url"] = self.download_pages_service.domain_url + offer_row["url"]
                offers.append(HouseOfferSumWithRealtorDTO(**offer_dict))
            return [_offer_prices_to_euro(offer) for offer in offers]
