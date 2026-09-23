import os

from celery import Celery, shared_task
from celery.schedules import crontab

from src.scraping_lib.constants import OTODOM_DOMAIN_URL, OTODOM_URL_LIST, OTODOM_NAME
from src.scraping_lib.download_html_home_offers import DownloadHtmlHomeOffersService, pagination_max_number_scraper
from src.home_offer.services import HomeOfferService
from src.utils.db.sqlalchemy import engine


def setup_periodic_tasks(sender: Celery, **kwargs):
    sender.add_periodic_task(
        crontab(hour=18, minute=30),
        grab_house_offers.s(),
        name="daily grab house offers at 18:30"
    )
    is_testing_str = os.environ.get("IS_TESTING", False)
    is_testing = is_testing_str in ["True", "true", "1"]
    if is_testing:
        sender.add_periodic_task(
            60.0,
            grab_house_offers.s(),
            name='test grab house offers every 60 seconds',
        )


@shared_task(name='src.home_offer.tasks.grab_house_offers')
def grab_house_offers():
    download_html_home_offers_service = DownloadHtmlHomeOffersService(
        domain_url=OTODOM_DOMAIN_URL,
        url_list=OTODOM_URL_LIST,
        name=OTODOM_NAME,
        pagination_number_max_scraper=pagination_max_number_scraper
    )
    service = HomeOfferService(
        engine,
        download_html_home_offers_service=download_html_home_offers_service
    )
    service.grab_offers()
