import os

from celery import Celery
from fastapi import FastAPI

from src.utils.logging import get_logger

logger = get_logger(__name__)


REDIS_HOST = os.getenv("REDIS_HOST")
if not REDIS_HOST:
    raise ValueError("REDIS_HOST env not set")
app_celery = Celery('parsing-house-offers',
             broker=f'redis://{REDIS_HOST}:6379')
app_celery.conf.update(timezone='Europe/Kyiv',
                enable_utc=True,
                include=['src.home_offer.tasks'])
app_celery.autodiscover_tasks(["src.home_offer.tasks"])

from src.home_offer import tasks

app_celery.on_after_configure.connect(tasks.setup_periodic_tasks)

from src.home_offer import controllers
app_api = FastAPI()
app_api.include_router(controllers.router)
