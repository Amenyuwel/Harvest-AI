# logger.py
import os
import logging
from datetime import datetime

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# Configure main logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, f"app_{datetime.now().strftime('%Y%m%d')}.log")),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("HarvestAssistant")
