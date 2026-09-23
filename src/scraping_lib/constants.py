import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).parent.parent.parent
load_dotenv(f"{PROJECT_ROOT}/.env")
WEB_DRIVER_PATH = os.getenv("WEB_DRIVER_PATH")
if not WEB_DRIVER_PATH:
    WEB_DRIVER_PATH = "/home/dev/app/chromium.chromedriver"
OTODOM_URL_LIST = "https://www.otodom.pl/pl/wyniki/wynajem/mieszkanie,2-pokoje/lodzkie/lodz/lodz/lodz?limit=36&priceMax=1700&by=DEFAULT&direction=DESC"
OTODOM_DOMAIN_URL = "https://www.otodom.pl"
OTODOM_NAME = "otodom"
PATH_SESSIONS_DIRECTORY = f'{PROJECT_ROOT}/resource/sessions'
PATH_SESSION_DIRECTORY = f"{PATH_SESSIONS_DIRECTORY}/otodom_session.json"
