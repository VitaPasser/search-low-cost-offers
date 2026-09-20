import os

from celery import Celery
from dotenv import load_dotenv

load_dotenv()
REDIS_HOST = os.getenv("REDIS_HOST")
if not REDIS_HOST:
    raise ValueError("REDIS_HOST env not set")
app = Celery('parsing-house-offers',
             broker=f'redis://{REDIS_HOST}:6379')
app.conf.update(timezone='Europe/Kyiv',
                enable_utc=True,
                include=['src.home_offer.tasks'])
app.autodiscover_tasks(["src.home_offer.tasks"])

from src.home_offer import tasks

app.on_after_configure.connect(tasks.setup_periodic_tasks)
