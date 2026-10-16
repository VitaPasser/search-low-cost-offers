from sqlalchemy import Engine, select
from sqlalchemy.orm import Session, aliased

from src.home_offer.dto import HouseOfferDTO, HouseOfferSumWithRealtorDTO, HouseOfferSumDTO
from src.home_offer.mappers import _house_offer_to_model, _offer_model_to_model_dto, _offer_prices_to_euro
from src.home_offer.model import HouseOfferModel
from src.home_offer.money.dto import MoneyDTO
from src.home_offer.money.model import MoneyModel
from src.scraping_lib.download_html_home_offers.service import DownloadHtmlHomeOffersService
from src.scraping_lib.models import Offer
from src.scraping_lib.scraping.abstract_scrapper import Scrapper


class HomeOfferService:
    def __init__(
        self,
        engine: Engine,
        download_html_home_offers_service: DownloadHtmlHomeOffersService,
        scraper: Scrapper,
    ):
        self.engine = engine
        self.download_pages_service = download_html_home_offers_service
        self.scraper = scraper

    def _normalize_url(self, url: str) -> str:
        if not url.startswith("http"):
            return self.download_pages_service.domain_url + url
        return url

    async def grab_offers(self, cache: bool = False, limit_list_offers: int | None = None, limit_offers: int | None = None):
        htmls_list_offers = await self.download_pages_service.download_or_load_list_html(
            cache=cache, max_pages_limit=limit_list_offers
        )

        offers: list[Offer] = []
        for html_list_offers in htmls_list_offers:
            for _ in range(5):
                try:
                    offers.extend(self.scraper.parse_list_offers_page(html_list_offers))
                    break
                except IOError:
                    continue

        html_offers = await self.download_pages_service.download_html_offers(offers, max_pages_limit=limit_offers)
        complete_offers = self.scraper.parse_offer_page(html_offers, offers)

        with Session(self.engine) as session:
            offers_models = [_house_offer_to_model(offer) for offer in complete_offers]
            for offer in offers_models:
                if not session.query(HouseOfferModel).filter_by(id_url=offer.id_url).first():
                    session.add(offer)
            session.commit()

    def get_all(self) -> list[HouseOfferDTO]:
        with Session(self.engine) as session:
            offers = session.query(HouseOfferModel).join(HouseOfferModel.price).order_by(MoneyModel.amount).all()
            offers_dto = [_offer_model_to_model_dto(offer) for offer in offers]
            for offer_dto in offers_dto:
                offer_dto.url = self._normalize_url(offer_dto.url)
            return offers_dto

    def get_in_euro_all(self) -> list[HouseOfferDTO]:
        return [_offer_prices_to_euro(offer) for offer in self.get_all()]

    def get_in_euro_sum(
        self,
        include_tax: bool = False,
        include_deposit: bool = False,
        include_realtor: bool = False,
    ) -> list[HouseOfferSumWithRealtorDTO|HouseOfferSumDTO]:
        """Единый метод расчета суммарной стоимости с опциональными компонентами."""
        with Session(self.engine) as session:
            price_money = aliased(MoneyModel, name="price_money")
            tax_money = aliased(MoneyModel, name="tax_money")
            deposit_money = aliased(MoneyModel, name="deposit_money")
            realtor_money = aliased(MoneyModel, name="realtor_money")

            total_expr = price_money.amount
            if include_tax:
                total_expr = total_expr + tax_money.amount
            if include_deposit:
                total_expr = total_expr + deposit_money.amount
            if include_realtor:
                total_expr = total_expr + realtor_money.amount

            stmt = select(
                HouseOfferModel.id,
                HouseOfferModel.id_url,
                HouseOfferModel.url,
                HouseOfferModel.is_owner,
                HouseOfferModel.sector,
                total_expr.label("money_price_amount"),
                price_money.currency.label("money_price_current"),
                HouseOfferModel.created_at,
                HouseOfferModel.is_has_been_realtor_services,
            ).outerjoin(price_money, HouseOfferModel.price_id == price_money.id)

            if include_tax:
                stmt = stmt.outerjoin(tax_money, HouseOfferModel.tax_id == tax_money.id)
            if include_deposit:
                stmt = stmt.outerjoin(deposit_money, HouseOfferModel.deposit_id == deposit_money.id)
            if include_realtor:
                stmt = stmt.outerjoin(realtor_money, HouseOfferModel.realtor_service_id == realtor_money.id)

            stmt = stmt.order_by(total_expr.asc().nulls_last())
            rows = session.execute(stmt).mappings().all()

            offers: list[HouseOfferSumWithRealtorDTO] = []
            for row in rows:
                price = (
                    MoneyDTO(amount=row["money_price_amount"], currency=row["money_price_current"])
                    if row["money_price_amount"] is not None
                    else None
                )
                offers.append(
                    HouseOfferSumWithRealtorDTO(
                        id=row["id"],
                        id_url=row["id_url"],
                        url=self._normalize_url(row["url"]),
                        sector=row["sector"],
                        is_owner=row["is_owner"],
                        created_at=row["created_at"],
                        price=price,
                        is_has_been_realtor_services=row["is_has_been_realtor_services"],
                    )
                )

            return [_offer_prices_to_euro(offer) for offer in offers]