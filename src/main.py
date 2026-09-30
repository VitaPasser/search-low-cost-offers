import logging
import os
from datetime import date

from celery import Celery
from dotenv import load_dotenv
from fastapi import FastAPI


load_dotenv()
log_dir = os.getenv("LOGGING_DIR_PATH")
if not log_dir:
    raise ValueError("LOGGING_DIR_PATH env not set")

if len(log_dir) > 0 and log_dir[-1] == "/":
    log_dir = log_dir[:-1]
log_dir = f"{log_dir}/{date.today()}"
# Create a 'logs' directory if it doesn't exist
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    filename=os.path.join(log_dir, "internal.log"),
    level=logging.ERROR,
    format="%(name)s %(asctime)s %(levelname)s %(message)s",
)


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
