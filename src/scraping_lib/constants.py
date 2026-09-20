import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).parent.parent.parent
load_dotenv(f"{PROJECT_ROOT}/.env")
WEB_DRIVER_PATH = os.getenv("WEB_DRIVER_PATH")
if not WEB_DRIVER_PATH:
    WEB_DRIVER_PATH="/home/dev/app/chromium.chromedriver"