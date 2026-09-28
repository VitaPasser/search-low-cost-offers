from enum import StrEnum

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import create_engine, Engine

from src.home_offer.dto import (
    HouseOfferDTO,
    HouseOfferSumDTO,
    HouseOfferSumWithRealtorDTO,
)
from src.home_offer.services import HomeOfferService
from src.scraping_lib.download_html_home_offers.imobiliare import imobiliare_download_html_home_offers
from src.scraping_lib.download_html_home_offers.olx import olx_download_html_home_offers
from src.scraping_lib.download_html_home_offers.otodom import otodom_download_html_home_offers
from src.scraping_lib.scraping.imobiliare import ImobiliareScrapper
from src.scraping_lib.scraping.olx import OlxScrapper
from src.scraping_lib.scraping.otodom import OtodomScrapper
from src.utils.models import BaseModel


class AggregatorType(StrEnum):
    OTODOM = "otodom"
    IMOBILIARE = "imobiliare"
    OLX = "olx"


class SumCalculationType(StrEnum):
    NONE = "none"  # Только цена
    WITH_TAX = "with_tax"  # + Налог
    WITH_TAX_AND_DEPOSIT = "with_tax_and_deposit"  # + Налог + Залог
    WITH_TAX_DEPOSIT_AND_REALTOR = "with_tax_deposit_and_realtor"  # + Налог + Залог + Риелтор
    WITH_DEPOSIT = "with_deposit"  # + Залог
    WITH_DEPOSIT_AND_REALTOR = "with_deposit_and_realtor"  # + Залог + Риелтор
    WITH_REALTOR = "with_realtor"  # + Риелтор


def get_home_offer_service(aggregator: AggregatorType) -> HomeOfferService:
    engines: dict[AggregatorType, Engine] = {
        AggregatorType.OTODOM: create_engine("sqlite:///./data/db-otodom.sqlite"),
        AggregatorType.IMOBILIARE: create_engine("sqlite:///./data/db-imobiliare.sqlite"),
        AggregatorType.OLX: create_engine("sqlite:///./data/db-olx.sqlite"),
    }

    for engine in engines.values():
        BaseModel.metadata.create_all(engine)

    services: dict[AggregatorType, HomeOfferService] = {
        AggregatorType.OTODOM: HomeOfferService(
            engine=engines[AggregatorType.OTODOM],
            download_html_home_offers_service=otodom_download_html_home_offers,
            scraper=OtodomScrapper()
        ),
        AggregatorType.IMOBILIARE: HomeOfferService(
            engine=engines[AggregatorType.IMOBILIARE],
            download_html_home_offers_service=imobiliare_download_html_home_offers,
            scraper=ImobiliareScrapper()
        ),
        AggregatorType.OLX: HomeOfferService(
            engine=engines[AggregatorType.OLX],
            download_html_home_offers_service=olx_download_html_home_offers,
            scraper=OlxScrapper()
        ),
    }

    service = services.get(aggregator)
    if not service:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Service for aggregator '{aggregator.value}' is not configured."
        )
    return service


router = APIRouter(prefix="/house-offers", tags=["House Offers"])


@router.post("/{aggregator}/grab", status_code=status.HTTP_202_ACCEPTED)
async def grab_offers(
        aggregator: AggregatorType,
        cache: bool = Query(default=False),
        limit_list_offers: int | None = Query(default=None),
        limit_offers: int | None = Query(default=None),
) -> dict[str, str]:
    """Запустить скрапинг объявлений для выбранного агрегатора."""
    service = get_home_offer_service(aggregator)
    await service.grab_offers(
        cache=cache,
        limit_list_offers=limit_list_offers,
        limit_offers=limit_offers,
    )
    return {"status": "success", "message": f"Offers grabbed for {aggregator.value}"}


@router.get("/{aggregator}")
def get_offers(
        aggregator: AggregatorType,
        calc_type: SumCalculationType = Query(
            default=SumCalculationType.NONE,
            description="Тип подсчета суммарных затрат в евро"
        ),
) -> list[HouseOfferDTO] | list[HouseOfferSumDTO] | list[HouseOfferSumWithRealtorDTO]:
    """Получить предложения выбранного агрегатора с расчетом суммы в евро."""
    service = get_home_offer_service(aggregator)

    handlers = {
        SumCalculationType.NONE: service.get_in_euro_all,
        SumCalculationType.WITH_TAX: service.get_in_euro_all_and_sum_with_tax,
        SumCalculationType.WITH_TAX_AND_DEPOSIT: service.get_in_euro_all_and_sum_with_tax_and_deposit,
        SumCalculationType.WITH_TAX_DEPOSIT_AND_REALTOR: service.get_in_euro_all_and_sum_with_tax_deposit_and_realtor,
        SumCalculationType.WITH_DEPOSIT: service.get_in_euro_all_and_sum_with_deposit,
        SumCalculationType.WITH_DEPOSIT_AND_REALTOR: service.get_in_euro_all_and_sum_with_deposit_and_realtor,
        SumCalculationType.WITH_REALTOR: service.get_in_euro_all_and_sum_with_realtor,
    }

    handler = handlers[calc_type]
    return handler()