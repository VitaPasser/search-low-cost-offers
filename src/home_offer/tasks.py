import os

from celery import Celery, shared_task
from celery.schedules import crontab

from src.home_offer.services import HomeOfferService
from src.utils.db.sqlalchemy import engine


def setup_periodic_tasks(sender: Celery, **kwargs):
    sender.add_periodic_task(
        crontab(hour=18, minute=30),
        grab_house_offers.s(),
        name="daily grab house offers at 18:30"
    )
    if bool(os.environ.get("IS_TESTING", False)):
        sender.add_periodic_task(
            60.0,
            grab_house_offers.s(),
            name='test grab house offers every 60 seconds',
        )


@shared_task(name='src.home_offer.tasks.grab_house_offers')
def grab_house_offers():
    service = HomeOfferService(engine)
    service.grab_offers()
