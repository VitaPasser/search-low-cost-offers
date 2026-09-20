from celery import Celery, shared_task
from celery.schedules import crontab

from src.home_offer.services import grab_offers
from src.utils.db.sqlalchemy import engine


def setup_periodic_tasks(sender: Celery, **kwargs):
    sender.add_periodic_task(
        crontab(hour=18, minute=30),
        grab_house_offers.s(),
        name="daily grab house offers at 18:30"
    )
    sender.add_periodic_task(
        60.0,
        grab_house_offers.s(),
        name='test grab house offers every 60 seconds',
    )


@shared_task(name='src.home_offer.tasks.grab_house_offers')
def grab_house_offers():
    grab_offers(engine=engine)
