from enum import StrEnum

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import Engine, create_engine

from src.home_offer.dto import (
    HouseOfferDTO,
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
from src.utils.constants import PROJECT_ROOT


class AggregatorType(StrEnum):
    OTODOM = "otodom"
    IMOBILIARE = "imobiliare"
    OLX = "olx"


class SumCalculationType(StrEnum):
    NONE = "none"
    WITH_TAX = "with_tax"
    WITH_TAX_AND_DEPOSIT = "with_tax_and_deposit"
    WITH_TAX_DEPOSIT_AND_REALTOR = "with_tax_deposit_and_realtor"
    WITH_DEPOSIT = "with_deposit"
    WITH_DEPOSIT_AND_REALTOR = "with_deposit_and_realtor"
    WITH_REALTOR = "with_realtor"


ENGINES: dict[AggregatorType, Engine] = {
    AggregatorType.OTODOM: create_engine(f"sqlite:///{PROJECT_ROOT}/data/db-otodom.sqlite"),
    AggregatorType.IMOBILIARE: create_engine(f"sqlite:///{PROJECT_ROOT}/data/db-imobiliare.sqlite"),
    AggregatorType.OLX: create_engine(f"sqlite:///{PROJECT_ROOT}/data/db-olx.sqlite"),
}

for engine in ENGINES.values():
    BaseModel.metadata.create_all(engine)

SERVICES: dict[AggregatorType, HomeOfferService] = {
    AggregatorType.OTODOM: HomeOfferService(
        engine=ENGINES[AggregatorType.OTODOM],
        download_html_home_offers_service=otodom_download_html_home_offers,
        scraper=OtodomScrapper(),
    ),
    AggregatorType.IMOBILIARE: HomeOfferService(
        engine=ENGINES[AggregatorType.IMOBILIARE],
        download_html_home_offers_service=imobiliare_download_html_home_offers,
        scraper=ImobiliareScrapper(),
    ),
    AggregatorType.OLX: HomeOfferService(
        engine=ENGINES[AggregatorType.OLX],
        download_html_home_offers_service=olx_download_html_home_offers,
        scraper=OlxScrapper(),
    ),
}

CALC_CONFIGS = {
    SumCalculationType.WITH_TAX: {"include_tax": True},
    SumCalculationType.WITH_TAX_AND_DEPOSIT: {"include_tax": True, "include_deposit": True},
    SumCalculationType.WITH_TAX_DEPOSIT_AND_REALTOR: {
        "include_tax": True,
        "include_deposit": True,
        "include_realtor": True,
    },
    SumCalculationType.WITH_DEPOSIT: {"include_deposit": True},
    SumCalculationType.WITH_DEPOSIT_AND_REALTOR: {"include_deposit": True, "include_realtor": True},
    SumCalculationType.WITH_REALTOR: {"include_realtor": True},
}


def get_home_offer_service(aggregator: AggregatorType) -> HomeOfferService:
    service = SERVICES.get(aggregator)
    if not service:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Service for aggregator '{aggregator.value}' is not configured.",
        )
    return service


router = APIRouter(prefix="/api/v1/house-offers", tags=["House Offers"])


@router.post("/{aggregator}/grab", status_code=status.HTTP_202_ACCEPTED)
async def grab_offers(
    aggregator: AggregatorType,
    cache: bool = Query(default=False),
    limit_list_offers: int | None = Query(default=None),
    limit_offers: int | None = Query(default=None),
) -> dict[str, str]:
    """Start scraping ads for the selected aggregator."""
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
        default=SumCalculationType.NONE, description="Total Cost Calculation Type in Euros"
    ),
) -> list[HouseOfferDTO] | list[HouseOfferSumWithRealtorDTO]:
    """Get offers from the selected aggregator with the amount calculated in euros."""
    service = get_home_offer_service(aggregator)

    if calc_type == SumCalculationType.NONE:
        return service.get_in_euro_all()

    kwargs = CALC_CONFIGS[calc_type]
    return service.get_in_euro_sum(**kwargs)