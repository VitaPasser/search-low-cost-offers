import asyncio
import os

from celery import Celery, shared_task
from celery.schedules import crontab
from sqlalchemy import create_engine

from src.scraping_lib.download_html_home_offers.olx import olx_download_html_home_offers
from src.scraping_lib.scraping.olx import OlxScrapper
from src.scraping_lib.scraping.imobiliare import ImobiliareScrapper
from src.home_offer.services import HomeOfferService
from src.scraping_lib.download_html_home_offers.imobiliare import imobiliare_download_html_home_offers
from src.scraping_lib.download_html_home_offers.otodom import otodom_download_html_home_offers
from src.scraping_lib.scraping.otodom import OtodomScrapper
from src.utils.models import BaseModel
from src.utils.others import str_env_to_bool
from utils.constants import PROJECT_ROOT


def setup_periodic_tasks(sender: Celery, **kwargs):
    sender.add_periodic_task(
        crontab(hour=18, minute=30),
        grab_house_offers_otodom.s(),
        name="daily grab house offers at 18:30"
    )
    sender.add_periodic_task(
        crontab(hour=18, minute=40),
        grab_house_offers_otodom.s(),
        name="daily grab house offers at 18:40"
    )
    sender.add_periodic_task(
        crontab(hour=18, minute=50),
        grab_house_offers_olx.s(),
        name="daily grab house offers at 18:50"
    )
    if str_env_to_bool(os.environ.get("IS_TESTING", 'False')):
        sender.add_periodic_task(
            60.0,
            grab_house_offers_otodom.s(),
            name='test grab otodom house offers every 60 seconds',
        )
        sender.add_periodic_task(
            60.0,
            grab_house_offers_imobiliare.s(),
            name='test grab imobiliare house offers every 60 seconds',
        )
        sender.add_periodic_task(
            60.0,
            grab_house_offers_olx.s(),
            name='test grab olx house offers every 60 seconds',
        )


@shared_task(name='src.home_offer.tasks.grab_house_offers_otodom')
def grab_house_offers_otodom():
    engine = create_engine(f"sqlite:///{PROJECT_ROOT}/data/db-otodom.sqlite")
    BaseModel.metadata.create_all(engine)
    download_html_home_offers_service = otodom_download_html_home_offers
    service = HomeOfferService(
        engine,
        download_html_home_offers_service=download_html_home_offers_service,
        scraper=OtodomScrapper()
    )
    asyncio.run(service.grab_offers())


@shared_task(name='src.home_offer.tasks.grab_house_offers_imobiliare')
def grab_house_offers_imobiliare():
    engine = create_engine(f"sqlite:///{PROJECT_ROOT}/data/db-imobiliare.sqlite")
    BaseModel.metadata.create_all(engine)
    download_html_home_offers_service = imobiliare_download_html_home_offers
    service = HomeOfferService(
        engine,
        download_html_home_offers_service=download_html_home_offers_service,
        scraper=ImobiliareScrapper()
    )
    asyncio.run(service.grab_offers())


@shared_task(name='src.home_offer.tasks.grab_house_offers_olx')
def grab_house_offers_olx():
    engine = create_engine(f"sqlite:///{PROJECT_ROOT}/data/db-olx.sqlite")
    BaseModel.metadata.create_all(engine)
    download_html_home_offers_service = olx_download_html_home_offers
    service = HomeOfferService(
        engine,
        download_html_home_offers_service=download_html_home_offers_service,
        scraper=OlxScrapper()
    )
    asyncio.run(service.grab_offers())
