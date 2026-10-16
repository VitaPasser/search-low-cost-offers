import logging
import os
from datetime import date

import dotenv

dotenv.load_dotenv()
log_dir = os.getenv("LOGGING_DIR_PATH")
if not log_dir:
    raise ValueError("LOGGING_DIR_PATH env not set")

if len(log_dir) > 0 and log_dir[-1] == "/":
    log_dir = log_dir[:-1]
log_dir = f"{log_dir}/{date.today()}"
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    filename=os.path.join(log_dir, "internal.log"),
    level=logging.ERROR,
    format="%(name)s %(asctime)s %(levelname)s %(message)s",
)

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    return logger